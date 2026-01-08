import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re
from pathlib import Path

# --- KONFIGURATION ---
TRACKING_CSV = "manuelle_ergebnisse.csv"
TARGET_LEVELS = [5, 20, 50, 80, 90, 100, 120]
PHASES = ["L1", "L2", "L3"]
OUTPUT_ROOT_DIR = "messungen_sortiert"

st.set_page_config(layout="wide", page_title="Manueller Rohdaten-Export (Multi-Device)")

# --- INITIALISIERUNG SESSION STATE ---
for level in TARGET_LEVELS:
    if f"s_{level}" not in st.session_state:
        st.session_state[f"s_{level}"] = 0
    if f"e_{level}" not in st.session_state:
        st.session_state[f"e_{level}"] = 0


# --- CALLBACKS ---
def update_start_callback(lvl):
    """Berechnet Start = Ende - 500"""
    end_key = f"e_{lvl}"
    start_key = f"s_{lvl}"
    current_end = st.session_state[end_key]
    new_start = max(0, current_end - 500)
    st.session_state[start_key] = new_start


def reset_values():
    """Setzt alle Felder auf 0 zurück"""
    for level in TARGET_LEVELS:
        st.session_state[f"s_{level}"] = 0
        st.session_state[f"e_{level}"] = 0


# --- HELFER: GERÄTE ERKENNUNG ---
def identify_devices(df):
    """
    Analysiert die Spaltennamen und findet heraus, welche Geräte existieren.
    Ignoriert Phasen (L1-L3) und ValueY/Time, um den reinen Gerätenamen zu finden.
    """
    df.columns = [c.strip().strip('"').strip("'") for c in df.columns]
    val_cols = [c for c in df.columns if "ValueY" in c]

    devices = set()
    for col in val_cols:
        # 1. "ValueY" entfernen
        name = col.replace("ValueY", "").strip()
        # 2. Phasen L1, L2, L3 entfernen (case insensitive)
        name = re.sub(r"[_ ]?L[123][_ ]?", "", name, flags=re.IGNORECASE)
        # 3. Übrige Unterstriche am Rand entfernen
        name = name.strip("_ ")

        if name:
            devices.add(name)

    return sorted(list(devices))


# --- DATEI- & LADE-FUNKTIONEN ---


def get_files():
    files = []
    for root, _, filenames in os.walk("."):
        if any(
            x in root for x in ["venv", ".git", ".idea", "__pycache__", OUTPUT_ROOT_DIR]
        ):
            continue
        for f in filenames:
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
def load_file_preview(filepath):
    """Lädt nur Header für die Geräteerkennung"""
    df = None
    encodings = ["utf-16", "utf-8", "cp1252", "latin1"]

    # Verschiedene CSV Formate probieren
    configs = [
        {"sep": ";", "decimal": ","},
        {"sep": ",", "decimal": "."},
        {"sep": ",", "decimal": ","},
    ]

    for enc in encodings:
        for conf in configs:
            try:
                temp = pd.read_csv(
                    filepath,
                    sep=conf["sep"],
                    decimal=conf["decimal"],
                    encoding=enc,
                    engine="python",
                    nrows=5,
                )
                if len(temp.columns) > 1:
                    df = temp
                    break
            except:
                continue
        if df is not None:
            break

    if df is None:
        return []
    return identify_devices(df)


@st.cache_data
def load_all_data(filepath, all_devices):
    """
    Lädt die Daten für ALLE erkannten Geräte in ein Dictionary.
    """
    df = None
    encodings = ["utf-16", "utf-8", "cp1252", "latin1"]

    configs = [
        {"sep": ";", "decimal": ","},
        {"sep": ",", "decimal": "."},
        {"sep": ",", "decimal": ","},
    ]

    for enc in encodings:
        for conf in configs:
            try:
                temp = pd.read_csv(
                    filepath,
                    sep=conf["sep"],
                    decimal=conf["decimal"],
                    encoding=enc,
                    engine="python",
                )
                if len(temp.columns) > 1:
                    df = temp
                    break
            except:
                continue
        if df is not None:
            break

    if df is None:
        return None, None

    df.columns = [c.strip().strip('"').strip("'") for c in df.columns]
    val_cols = [c for c in df.columns if "ValueY" in c]

    full_data = {dev: {} for dev in all_devices}
    t = []

    for device in all_devices:
        for phase in PHASES:
            target_col = None
            for col in val_cols:
                clean_name = col.replace("ValueY", "").strip()
                dev_name_check = re.sub(
                    r"[_ ]?L[123][_ ]?", "", clean_name, flags=re.IGNORECASE
                ).strip("_ ")

                if dev_name_check == device and phase in col:
                    target_col = col
                    break

            if target_col:
                vals = pd.to_numeric(df[target_col], errors="coerce").fillna(0)
                full_data[device][phase] = vals
                if not t and len(vals) > 0:
                    t = list(range(len(vals)))
            else:
                full_data[device][phase] = None

    return t, full_data


def load_status_tracking():
    if os.path.exists(TRACKING_CSV):
        return pd.read_csv(TRACKING_CSV, index_col=0)
    return pd.DataFrame(columns=["Status"])


def save_tracking_status(base_name, status):
    df_track = load_status_tracking()
    df_track.loc[base_name, "Status"] = status
    df_track.to_csv(TRACKING_CSV)


def save_sorted_raw_data(original_filepath, full_data, start_end_map, selected_devices):
    """
    Speichert die Daten.
    WICHTIG: Iteriert nur über 'selected_devices'.
    """
    orig_path = Path(original_filepath)
    target_dir = Path(OUTPUT_ROOT_DIR) / orig_path.parent
    base_name = orig_path.stem
    new_filename = f"{base_name}_sortiert.csv"
    output_path = target_dir / new_filename

    df_export = pd.DataFrame()

    try:
        target_dir.mkdir(parents=True, exist_ok=True)

        for level in TARGET_LEVELS:
            s, e = start_end_map.get(level, (0, 0))

            if s > 0 and e > s:
                # Loop über die AUSGEWÄHLTEN Geräte
                for device in sorted(selected_devices):
                    for phase in PHASES:
                        # Prüfen, ob Daten da sind
                        if device in full_data and phase in full_data[device]:
                            vals = full_data[device][phase]

                            if vals is not None and e <= len(vals):
                                slice_data = vals.iloc[s:e].reset_index(drop=True)

                                col_t = f"{level:02d}_{phase}_{device}_t"
                                col_I = f"{level:02d}_{phase}_{device}_I"

                                df_export[col_t] = pd.Series(range(len(slice_data)))
                                df_export[col_I] = slice_data

        df_export.to_csv(output_path, index=False, sep=";")
        print(f"✅ {new_filename:<40} -> Gespeichert in '{target_dir}'")
        return str(output_path)
    except Exception as e:
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
    icon = "❌"
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

selected_display = st.sidebar.selectbox(
    "Datei wählen:", files_options, on_change=reset_values
)
selected_file_path = file_map[selected_display]

# --- HAUPTBEREICH ---
if selected_file_path:
    wandler_name, nennstrom = extract_metadata(selected_file_path)
    st.header(f"Export: {wandler_name}")

    # 1. Vorschau laden, um Geräte zu finden
    detected_devices = load_file_preview(selected_file_path)

    if not detected_devices:
        st.error("Keine Geräte erkannt. Prüfe Spaltennamen.")
        st.stop()

    # --- AUTOMATISCHE REFERENZ-WAHL ---
    default_ref_index = 0
    for i, dev in enumerate(detected_devices):
        if any(x in dev.lower() for x in ["pac1", "einspeisung", "ref", "source"]):
            default_ref_index = i
            break

    # --- SIDEBAR: ANZEIGE & EXPORT EINSTELLUNGEN ---
    st.sidebar.markdown("### 📊 Anzeige")
    st.sidebar.info(f"Geräte gefunden: {len(detected_devices)}")

    # Auswahl für das Diagramm (nur Anzeige)
    ref_device_for_plot = st.sidebar.selectbox(
        "Referenz für Diagramm (L1):", detected_devices, index=default_ref_index
    )

    st.sidebar.markdown("---")

    # --- NEU: Export Auswahl ---
    st.sidebar.markdown("### 💾 Export-Auswahl")
    selected_export_devices = st.sidebar.multiselect(
        "Geräte in CSV speichern:",
        options=detected_devices,
        default=detected_devices,  # Standardmäßig alle ausgewählt
        help="Nur die angehakten Geräte werden in die _sortiert.csv Datei geschrieben.",
    )

    col_info, col_status = st.columns([3, 1])
    with col_info:
        if nennstrom > 0:
            st.info(f"Nennstrom: **{int(nennstrom)} A**")
        else:
            nennstrom = st.number_input("Nennstrom manuell setzen [A]:", value=2000.0)

    # 2. Alle Daten laden
    t, full_data = load_all_data(selected_file_path, detected_devices)

    if not t:
        st.error("Fehler beim Laden der Daten.")
        st.stop()

    # --- PLOT (Nur Referenz L1) ---
    ref_l1 = full_data[ref_device_for_plot]["L1"]

    if ref_l1 is not None:
        ref_pct = (ref_l1 / nennstrom) * 100
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=t,
                y=ref_pct,
                mode="lines",
                name=f"{ref_device_for_plot} L1 [%]",
                line=dict(color="orange", width=2),
            )
        )
        for level in TARGET_LEVELS:
            fig.add_hline(y=level, line_dash="dot", line_color="rgba(150,150,150,0.5)")
        fig.update_layout(
            title=f"Verlauf {ref_device_for_plot} - L1 (Zur Orientierung)",
            xaxis_title="Zeit [Index]",
            yaxis_title="Last [%]",
            height=350,
            hovermode="x unified",
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.warning(f"Keine L1 Daten für {ref_device_for_plot} gefunden.")

    # --- EINGABE (TAB OPTIMIERT) ---
    st.markdown("### ✂️ Bereiche definieren")

    status_selection = st.radio("Status:", ["OK", "Problem (⚠️)"], horizontal=True)
    st.markdown("---")

    def chunked(iterable, n):
        return [iterable[i : i + n] for i in range(0, len(iterable), n)]

    batches = chunked(TARGET_LEVELS, 4)

    for batch in batches:
        # Header
        cols_head = st.columns(4)
        for i, level in enumerate(batch):
            cols_head[i].markdown(f"**{level}%**")

        # Ende Felder
        cols_ende = st.columns(4)
        for i, level in enumerate(batch):
            cols_ende[i].number_input(
                f"Ende",
                min_value=0,
                step=1,
                key=f"e_{level}",
                on_change=update_start_callback,
                args=(level,),
                label_visibility="collapsed",
            )

        # Start Felder
        cols_start = st.columns(4)
        for i, level in enumerate(batch):
            cols_start[i].number_input(
                f"Start",
                min_value=0,
                step=1,
                key=f"s_{level}",
                label_visibility="collapsed",
            )
        st.markdown("")

    st.markdown("---")

    # --- EXPORT BUTTON ---
    if st.button("🚀 Rohdaten Exportieren", type="primary"):
        if not selected_export_devices:
            st.error("⚠️ Bitte wähle mindestens ein Gerät für den Export aus (Sidebar)!")
        else:
            start_end_map = {}
            for level in TARGET_LEVELS:
                s_val = st.session_state[f"s_{level}"]
                e_val = st.session_state[f"e_{level}"]
                start_end_map[level] = (s_val, e_val)

            # Hier wird jetzt die Auswahl (selected_export_devices) übergeben
            new_file_path = save_sorted_raw_data(
                selected_file_path, full_data, start_end_map, selected_export_devices
            )

            if new_file_path:
                status_code = "WARNING" if "Problem" in status_selection else "OK"
                save_tracking_status(wandler_name, status_code)
                st.success(
                    f"Datei erstellt.\n\n"
                    f"Ausgewählte Geräte: **{', '.join(selected_export_devices)}**\n"
                    f"Pfad: `{new_file_path}`"
                )
