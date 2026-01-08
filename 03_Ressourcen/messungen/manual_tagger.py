import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re
from pathlib import Path  # Neu hinzugefügt für robustes Pfad-Management

# --- KONFIGURATION ---
TRACKING_CSV = "manuelle_ergebnisse.csv"  # Nur für Status-Tracking (✅/❌)
TARGET_LEVELS = [5, 20, 50, 80, 90, 100, 120]
PHASES = ["L1", "L2", "L3"]
OUTPUT_ROOT_DIR = "messungen_sortiert"  # Name des neuen Hauptordners

st.set_page_config(layout="wide", page_title="Manueller Rohdaten-Export")

# --- FUNKTIONEN ---


def get_files():
    files = []
    # Wir nutzen hier os.walk, konvertieren aber später zu Path für saubereres Handling
    for root, _, filenames in os.walk("."):
        if any(
            x in root for x in ["venv", ".git", ".idea", "__pycache__", OUTPUT_ROOT_DIR]
        ):
            continue
        for f in filenames:
            # Wir suchen CSVs, ignorieren aber Output-Dateien und Tracking-Dateien
            if (
                f.lower().endswith(".csv")
                and "manuelle_ergebnisse" not in f
                and "_sortiert" not in f
            ):
                files.append(os.path.join(root, f))
    return sorted(files)


def extract_metadata(filepath):
    filename = os.path.basename(filepath)
    match_amp = re.search(r"[-_](\d+)A[-_]", filename)
    nennstrom = float(match_amp.group(1)) if match_amp else 0.0
    clean_name = filename.replace(".csv", "")
    return clean_name, nennstrom


@st.cache_data
def load_file_data(filepath):
    # Versucht verschiedene Encodings
    df = None
    encodings = ["utf-16", "utf-8", "cp1252", "latin1"]
    for enc in encodings:
        try:
            temp = pd.read_csv(
                filepath, sep=";", decimal=",", encoding=enc, engine="python"
            )
            if len(temp.columns) < 2:
                temp = pd.read_csv(
                    filepath, sep=",", decimal=".", encoding=enc, engine="python"
                )
            if len(temp.columns) > 1:
                df = temp
                break
        except:
            continue

    if df is None:
        return None, None

    # Spalten säubern
    df.columns = [c.strip().strip('"').strip("'") for c in df.columns]
    val_cols = [c for c in df.columns if "ValueY" in c]

    if len(val_cols) < 2:
        return None, None

    prefixes = sorted(list(set([c.split("_")[0] for c in val_cols])))
    if len(prefixes) < 2:
        return None, None

    dev_ref = prefixes[0]  # Einspeisung (Referenz)
    dev_dut = prefixes[1]  # Prüfling

    data_dict = {}

    # Wir laden alle 3 Phasen für Ref und Dut
    for phase in PHASES:
        col_ref = next((c for c in val_cols if dev_ref in c and phase in c), None)
        col_dut = next((c for c in val_cols if dev_dut in c and phase in c), None)

        if col_ref and col_dut:
            vals_ref = pd.to_numeric(df[col_ref], errors="coerce").fillna(0)
            vals_dut = pd.to_numeric(df[col_dut], errors="coerce").fillna(0)
            data_dict[phase] = (vals_ref, vals_dut)
        else:
            data_dict[phase] = (None, None)

    # Zeitachse (basierend auf L1 Ref Länge)
    if data_dict["L1"][0] is not None:
        t = list(range(len(data_dict["L1"][0])))
    else:
        t = []

    return t, data_dict


def load_status_tracking():
    # Lädt nur den Status, um Haken in der Sidebar anzuzeigen
    if os.path.exists(TRACKING_CSV):
        return pd.read_csv(TRACKING_CSV, index_col=0)
    else:
        return pd.DataFrame(columns=["Status"])


def save_tracking_status(base_name, status):
    df_track = load_status_tracking()
    df_track.loc[base_name, "Status"] = status
    df_track.to_csv(TRACKING_CSV)


def save_sorted_raw_data(original_filepath, data_dict, start_end_map):
    """
    Erstellt die neue CSV mit den sortierten Rohdaten in einer gespiegelten Ordnerstruktur.
    Gibt Icons im Terminal aus.
    """
    # 1. Pfade vorbereiten mit pathlib
    orig_path = Path(original_filepath)

    # Hier wird die Struktur definiert:
    # ./messungen_sortiert / <original_unterordner> / datei_sortiert.csv
    # Wir nehmen den parent des Originals, um die Struktur (z.B. messungen/01_Parallel) zu erhalten
    target_dir = Path(OUTPUT_ROOT_DIR) / orig_path.parent

    base_name = orig_path.stem
    new_filename = f"{base_name}_sortiert.csv"
    output_path = target_dir / new_filename

    # Wir bauen ein großes DataFrame zusammen
    df_export = pd.DataFrame()

    try:
        # Ordnerstruktur erstellen, falls nicht vorhanden
        target_dir.mkdir(parents=True, exist_ok=True)

        for level in TARGET_LEVELS:
            s, e = start_end_map.get(level, (0, 0))

            # Nur wenn gültige Zeiten eingegeben wurden
            if s > 0 and e > s:

                # --- EINSPEISUNG (Referenz) ---
                for phase in PHASES:
                    ref_vals, _ = data_dict[phase]
                    if ref_vals is not None and e <= len(ref_vals):
                        # Ausschnitt holen und Index resetten
                        slice_data = ref_vals.iloc[s:e].reset_index(drop=True)
                        time_col = pd.Series(range(len(slice_data)))

                        col_t = f"{level:02d}_{phase}_t_Einspeisung"
                        col_I = f"{level:02d}_{phase}_I_Einspeisung"

                        df_export[col_t] = time_col
                        df_export[col_I] = slice_data

                # --- PRÜFLING (DUT) ---
                for phase in PHASES:
                    _, dut_vals = data_dict[phase]
                    if dut_vals is not None and e <= len(dut_vals):
                        slice_data = dut_vals.iloc[s:e].reset_index(drop=True)
                        time_col = pd.Series(range(len(slice_data)))

                        col_t = f"{level:02d}_{phase}_t_Pruefling"
                        col_I = f"{level:02d}_{phase}_I_Pruefling"

                        df_export[col_t] = time_col
                        df_export[col_I] = slice_data

        # Speichern
        df_export.to_csv(output_path, index=False, sep=";")

        # Terminal Ausgabe mit Icon (wie gewünscht)
        print(f"✅ {new_filename:<40} -> Gespeichert in '{target_dir}'")
        return str(output_path)

    except Exception as e:
        # Fehler im Terminal ausgeben
        print(f"❌ {new_filename:<40} -> Fehler: {e}")
        st.error(f"Fehler beim Speichern: {e}")
        return None


# --- SIDEBAR ---
st.sidebar.title("🛠️ Rohdaten Export")
all_files = get_files()
df_status = load_status_tracking()

files_options = []
file_map = {}

for f in all_files:
    name, _ = extract_metadata(f)
    # Icon Logik für Sidebar
    icon = "❌"  # Standard: noch nicht bearbeitet
    if name in df_status.index:
        s = df_status.loc[name, "Status"]
        if s == "OK":
            icon = "✅"
        elif s == "WARNING":
            icon = "⚠️"

    display_str = f"{icon} {name}"
    files_options.append(display_str)
    file_map[display_str] = f

if not files_options:
    st.warning("Keine CSV-Dateien gefunden.")
    st.stop()

selected_display = st.sidebar.selectbox("Datei wählen:", files_options)
selected_file_path = file_map[selected_display]

# --- HAUPTBEREICH ---
if selected_file_path:
    wandler_name, nennstrom = extract_metadata(selected_file_path)

    st.header(f"Export: {wandler_name}")

    col_info, col_status = st.columns([3, 1])
    with col_info:
        if nennstrom > 0:
            st.info(f"Nennstrom: **{int(nennstrom)} A**")
        else:
            nennstrom = st.number_input("Nennstrom manuell setzen [A]:", value=2000.0)

    # Daten laden
    t, data_dict = load_file_data(selected_file_path)

    if not t:
        st.error("Fehler beim Laden der Daten.")
        st.stop()

    # Plot L1 Ref
    ref_l1, dut_l1 = data_dict["L1"]
    if ref_l1 is not None:
        ref_pct = (ref_l1 / nennstrom) * 100

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=t,
                y=ref_pct,
                mode="lines",
                name="L1 Ref [%]",
                line=dict(color="orange", width=2),
            )
        )

        for level in TARGET_LEVELS:
            fig.add_hline(y=level, line_dash="dot", line_color="rgba(150,150,150,0.5)")

        fig.update_layout(
            title="Verlauf L1 (Plateaus suchen)",
            xaxis_title="Zeit [Index]",
            yaxis_title="Last [%]",
            height=350,
            hovermode="x unified",
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Keine L1 Daten gefunden.")

    # --- EINGABE ---
    st.markdown("### ✂️ Bereiche definieren & Exportieren")

    with st.form("export_form"):
        status_selection = st.radio("Status:", ["OK", "Problem (⚠️)"], horizontal=True)
        st.markdown("---")

        cols = st.columns(4)
        inputs_start = {}
        inputs_end = {}

        for i, level in enumerate(TARGET_LEVELS):
            col = cols[i % 4]
            with col:
                st.markdown(f"**{level}%**")
                inputs_start[level] = st.number_input(
                    f"Start", min_value=0, value=0, key=f"s_{level}"
                )
                inputs_end[level] = st.number_input(
                    f"Ende", min_value=0, value=0, key=f"e_{level}"
                )

        st.markdown("---")
        submitted = st.form_submit_button("🚀 Rohdaten Exportieren", type="primary")

        if submitted:
            # 1. Map erstellen
            start_end_map = {}
            for level in TARGET_LEVELS:
                start_end_map[level] = (inputs_start[level], inputs_end[level])

            # 2. Exportieren (Hier passiert die Magie mit den Ordnern und Icons)
            new_file_path = save_sorted_raw_data(
                selected_file_path, data_dict, start_end_map
            )

            if new_file_path:
                # 3. Status speichern
                status_code = "WARNING" if "Problem" in status_selection else "OK"
                save_tracking_status(wandler_name, status_code)

                st.success(f"Datei erfolgreich erstellt:\n`{new_file_path}`")

                # Button zum Neuladen, damit Icons in der Sidebar aktualisiert werden
                st.rerun()
