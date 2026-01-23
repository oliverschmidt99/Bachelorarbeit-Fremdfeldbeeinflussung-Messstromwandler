import pandas as pd
import numpy as np
import re
import os
import glob

# --- KONFIGURATION ---
OUTPUT_FILE = "messdaten_db.parquet"
SEARCH_DIR = "messungen_sortiert"
TARGET_LEVELS = [5, 20, 50, 80, 90, 100, 120]
PHASES = ["L1", "L2", "L3"]

# Keywords für Referenz-Erkennung
REF_KEYWORDS = ["pac1", "einspeisung", "ref", "source", "norm", "powermeter"]

# Metadaten-Spalten, die wir direkt in der DB führen und retten wollen
META_COLS = ["Preis (€)", "L (mm)", "B (mm)", "H (mm)", "Kommentar"]


def extract_base_type(wandler_key):
    """
    Generiert den Basis-Typ (ohne Bürde, Phase, Anordnung) für die Zuordnung der Stammdaten.
    """
    s = str(wandler_key)
    tokens = re.split(r"[_\s\-]+", s)
    clean_tokens = []
    for t in tokens:
        # Filter: Bürde (Zahl + R + Zahl, z.B. 8R1, 10R)
        if re.match(r"^\d+R\d*$", t, re.IGNORECASE):
            continue
        # Filter: Parallel/Dreieck/Messstrecke/Phasen Infos
        if t.lower() in ["parallel", "dreieck", "messstrecke", "l1", "l2", "l3"]:
            continue
        if not t:
            continue
        clean_tokens.append(t)
    return " ".join(clean_tokens)


def extract_metadata(filepath):
    filename = os.path.basename(filepath)
    original_name = filename.replace("_sortiert.csv", "")
    folder_name = os.path.basename(os.path.dirname(filepath))

    match_amp = re.search(r"[-_](\d+)A[-_]", original_name)
    nennstrom = float(match_amp.group(1)) if match_amp else 0.0

    lower_name = original_name.lower()
    if "messstrecke" in lower_name:
        manufacturer = "Messstrecke"
    elif "mbs" in lower_name:
        manufacturer = "MBS"
    elif "celsa" in lower_name:
        manufacturer = "Celsa"
    elif "redur" in lower_name:
        manufacturer = "Redur"
    else:
        manufacturer = "Andere"

    # Modellnamen raten
    try:
        parts = original_name.split("-")
        candidates = [
            p
            for p in parts
            if not re.match(r"^\d{4}", p)
            and manufacturer.lower() not in p.lower()
            and str(int(nennstrom)) not in p
        ]
        model_str = "_".join(candidates) if candidates else original_name
    except:
        model_str = original_name

    wandler_key = f"{manufacturer} {model_str}"

    return {
        "filepath": filepath,
        "folder": folder_name,
        "hersteller": manufacturer,
        "nennstrom": nennstrom,
        "wandler_key": wandler_key,
        "dateiname": filename,
    }


def analyze_sorted_file(filepath, meta):
    try:
        df = pd.read_csv(filepath, sep=";")
    except:
        return [], "Lesefehler"

    df.columns = [c.strip() for c in df.columns]
    value_cols = [c for c in df.columns if "_I" in c]
    if not value_cols:
        return [], "Keine Strom-Daten gefunden"

    results = []

    for level in TARGET_LEVELS:
        lvl_str = f"{level:02d}"
        nominal_amp = meta["nennstrom"] * (level / 100.0)

        for phase in PHASES:
            # 1. Relevante Spalten finden
            relevant_cols = [
                c for c in value_cols if c.startswith(f"{lvl_str}_{phase}")
            ]
            if not relevant_cols:
                continue

            devices_map = {}
            for col in relevant_cols:
                # Format: 05_L1_PAC1_I oder 05_L1_I_Einspeisung
                match_new = re.search(rf"{lvl_str}_{phase}_(.+)_I$", col)
                match_old = re.search(rf"{lvl_str}_{phase}_I_(.+)$", col)

                if match_new:
                    devices_map[match_new.group(1)] = col
                elif match_old:
                    devices_map[match_old.group(1)] = col

            if not devices_map:
                continue

            # 2. Referenz identifizieren
            phys_ref_device = None
            for kw in REF_KEYWORDS:
                for dev in devices_map.keys():
                    if kw in dev.lower():
                        phys_ref_device = dev
                        break
                if phys_ref_device:
                    break

            # Fallback: Erstes Gerät alphabetisch, falls keine Keywords passen
            if not phys_ref_device:
                phys_ref_device = sorted(list(devices_map.keys()))[0]

            col_phys_ref = devices_map[phys_ref_device]
            vals_phys_ref = pd.to_numeric(df[col_phys_ref], errors="coerce").dropna()

            phys_ref_mean = vals_phys_ref.mean() if not vals_phys_ref.empty else 0
            phys_ref_std = vals_phys_ref.std() if not vals_phys_ref.empty else 0

            # 3. Berechnungen für alle Geräte
            for dev, col_dut in devices_map.items():
                vals_dut = pd.to_numeric(df[col_dut], errors="coerce").dropna()
                if vals_dut.empty:
                    continue

                dut_mean = vals_dut.mean()
                dut_std = vals_dut.std()

                # --- FIX: Generischen Namen "Pruefling" ersetzen ---
                final_dut_name = dev
                if dev.lower() in ["pruefling", "prüfling", "dut", "messwandler"]:
                    # Wir nutzen den Hersteller als Namen, damit man es im Dashboard findet
                    final_dut_name = f"{meta['hersteller']} (Prüfling)"

                base_entry = {
                    "wandler_key": meta["wandler_key"],
                    "folder": meta["folder"],
                    "phase": phase,
                    "target_load": level,
                    "nennstrom": meta["nennstrom"],
                    "val_dut_mean": dut_mean,
                    "val_dut_std": dut_std,
                    "dut_name": final_dut_name,
                    "raw_file": meta["dateiname"],
                }

                # FALL A: Gerät gegen Messgerät (Relativ)
                if dev != phys_ref_device and phys_ref_mean > 0:
                    entry = base_entry.copy()
                    entry.update(
                        {
                            "val_ref_mean": phys_ref_mean,
                            "val_ref_std": phys_ref_std,
                            "ref_name": phys_ref_device,
                            "comparison_mode": "device_ref",
                        }
                    )
                    results.append(entry)

                # FALL B: Gerät gegen Nennwert (Absolut)
                if nominal_amp > 0:
                    entry = base_entry.copy()
                    entry.update(
                        {
                            "val_ref_mean": nominal_amp,
                            "val_ref_std": 0.0,
                            "ref_name": "Nennwert",
                            "comparison_mode": "nominal_ref",
                        }
                    )
                    results.append(entry)

    return results, "OK"


def main():
    print("--- Start: DB-Update (Integrierte Stammdaten & Namens-Fix) ---")

    # 1. Bestehende Stammdaten retten
    existing_meta_map = {}
    if os.path.exists(OUTPUT_FILE):
        print("💾 Lese existierende DB, um Stammdaten (Preise etc.) zu retten...")
        try:
            old_df = pd.read_parquet(OUTPUT_FILE)
            if "base_type" not in old_df.columns:
                old_df["base_type"] = old_df["wandler_key"].apply(extract_base_type)

            # Wir speichern uns ein Dict: base_type -> {Preis: 12.50, L: 10, ...}
            # drop_duplicates, um pro Typ nur einen Eintrag zu haben
            meta_df = old_df[
                ["base_type"] + [c for c in META_COLS if c in old_df.columns]
            ].drop_duplicates(subset=["base_type"])
            existing_meta_map = meta_df.set_index("base_type").to_dict(orient="index")
            print(f"✅ {len(existing_meta_map)} Stammdatensätze im Speicher gesichert.")
        except Exception as e:
            print(f"⚠️ Warnung: Konnte alte DB nicht lesen ({e}). Starte blank.")

    # 2. Neue Dateien scannen
    files = glob.glob(os.path.join(SEARCH_DIR, "**", "*_sortiert.csv"), recursive=True)
    print(f"🔍 {len(files)} sortierte Dateien gefunden.")

    all_data = []
    for f in files:
        meta = extract_metadata(f)
        stats, status = analyze_sorted_file(f, meta)
        if stats:
            all_data.extend(stats)
            print(f"✅ {os.path.basename(f)} ({len(stats)} Einträge)")
        else:
            print(f"⚠️ {os.path.basename(f)}: {status}")

    if not all_data:
        print("❌ Keine Daten extrahiert.")
        return

    df_new = pd.DataFrame(all_data)

    # Dubletten bereinigen
    # WICHTIG: "raw_file" muss im subset sein, sonst löscht er die zweite Messung desselben Wandlers!
    df_new = df_new.drop_duplicates(
        subset=[
            "wandler_key",
            "folder",
            "phase",
            "target_load",
            "dut_name",
            "comparison_mode",
            "raw_file",
        ],
        keep="last",
    )

    # 3. Base Type generieren
    df_new["base_type"] = df_new["wandler_key"].apply(extract_base_type)

    # 4. Stammdaten anfügen (Gerettete oder Defaults)
    # Spalten initialisieren
    for col in META_COLS:
        if col not in df_new.columns:
            df_new[col] = 0.0 if "Preis" in col or "mm" in col else ""
            if col == "Kommentar":
                df_new[col] = df_new[col].astype(str)

    # Mapping anwenden
    print("🔄 Führe Stammdaten (alt) und Messdaten (neu) zusammen...")

    for col in META_COLS:
        # Mapping Series: Key=BaseType, Value=Wert aus alter DB
        map_series = pd.Series(
            {k: v.get(col, 0.0) for k, v in existing_meta_map.items()}
        )

        if not map_series.empty:
            mapped_values = df_new["base_type"].map(map_series)
            # Nur da überschreiben, wo wir im Mapping was gefunden haben
            df_new[col] = mapped_values.fillna(df_new[col])

    df_new.to_parquet(OUTPUT_FILE)
    print(f"✅ Datenbank gespeichert: {OUTPUT_FILE} ({len(df_new)} Einträge)")
    print("Spalten:", list(df_new.columns))


if __name__ == "__main__":
    main()
