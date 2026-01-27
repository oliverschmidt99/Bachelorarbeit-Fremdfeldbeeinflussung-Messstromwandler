import pandas as pd
import numpy as np
import re
import os
import glob

# --- KONFIGURATION ---
import os
# ... andere imports ...

# --- KONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "daten")

OUTPUT_FILE = os.path.join(DATA_DIR, "messdaten_db.parquet")
SEARCH_DIR = "messungen_sortiert"

TARGET_LEVELS = [5, 20, 50, 80, 90, 100, 120]
PHASES = ["L1", "L2", "L3"]




# Priorität für Referenz: PAC1 steht ganz oben!
REF_KEYWORDS = ["pac1", "einspeisung", "ref", "source", "norm"]


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
            # 1. Spalten identifizieren
            relevant_cols = [
                c for c in value_cols if c.startswith(f"{lvl_str}_{phase}")
            ]
            if not relevant_cols:
                continue

            devices_map = {}
            for col in relevant_cols:
                # Format: 05_L1_PAC1_I
                match_new = re.search(rf"{lvl_str}_{phase}_(.+)_I$", col)
                # Format: 05_L1_I_Einspeisung
                match_old = re.search(rf"{lvl_str}_{phase}_I_(.+)$", col)

                if match_new:
                    devices_map[match_new.group(1)] = col
                elif match_old:
                    devices_map[match_old.group(1)] = col

            if not devices_map:
                continue

            # 2. Referenz identifizieren
            phys_ref_device = None
            # Wir gehen die Keywords durch. Sobald eines passt (z.B. "pac1"), ist das die Ref.
            for kw in REF_KEYWORDS:
                for dev in devices_map.keys():
                    if kw in dev.lower():
                        phys_ref_device = dev
                        break
                if phys_ref_device:
                    break

            # Fallback
            if not phys_ref_device:
                phys_ref_device = sorted(list(devices_map.keys()))[0]

            # Referenz-Daten laden
            col_phys_ref = devices_map[phys_ref_device]
            vals_phys_ref = pd.to_numeric(df[col_phys_ref], errors="coerce").dropna()

            phys_ref_mean = vals_phys_ref.mean() if not vals_phys_ref.empty else 0
            phys_ref_std = vals_phys_ref.std() if not vals_phys_ref.empty else 0

            # 3. Berechnungen für ALLE Geräte (DUTs)
            for dev, col_dut in devices_map.items():
                vals_dut = pd.to_numeric(df[col_dut], errors="coerce").dropna()
                if vals_dut.empty:
                    continue

                dut_mean = vals_dut.mean()
                dut_std = vals_dut.std()

                # --- FALL A: Gerät gegen Messgerät (Relativ) ---
                # WICHTIG: Wir überspringen das Gerät, wenn es selbst die Referenz ist.
                # PAC1 vs PAC1 macht keinen Sinn.
                if dev != phys_ref_device and phys_ref_mean > 0:
                    results.append(
                        {
                            "wandler_key": meta["wandler_key"],
                            "folder": meta["folder"],
                            "phase": phase,
                            "target_load": level,
                            "nennstrom": meta["nennstrom"],
                            "val_ref_mean": phys_ref_mean,
                            "val_ref_std": phys_ref_std,
                            "val_dut_mean": dut_mean,
                            "val_dut_std": dut_std,
                            "dut_name": dev,
                            "ref_name": phys_ref_device,
                            "comparison_mode": "device_ref",  # <--- Relativ
                            "raw_file": meta["dateiname"],
                        }
                    )

                # --- FALL B: Gerät gegen Nennwert (Absolut) ---
                # Hier nehmen wir AUCH die Referenz (PAC1) mit auf!
                if nominal_amp > 0:
                    results.append(
                        {
                            "wandler_key": meta["wandler_key"],
                            "folder": meta["folder"],
                            "phase": phase,
                            "target_load": level,
                            "nennstrom": meta["nennstrom"],
                            "val_ref_mean": nominal_amp,  # <--- Absolut
                            "val_ref_std": 0.0,
                            "val_dut_mean": dut_mean,
                            "val_dut_std": dut_std,
                            "dut_name": dev,
                            "ref_name": "Nennwert",
                            "comparison_mode": "nominal_ref",  # <--- Absolut
                            "raw_file": meta["dateiname"],
                        }
                    )

    return results, "OK"


def main():
    print("--- Start: DB-Update (Strikte Trennung PAC1/Nennwert) ---")

    files = glob.glob(os.path.join(SEARCH_DIR, "**", "*_sortiert.csv"), recursive=True)
    print(f"{len(files)} sortierte Dateien gefunden.")

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

    df_all = pd.DataFrame(all_data)

    df_clean = df_all.drop_duplicates(
        subset=[
            "wandler_key",
            "folder",
            "phase",
            "target_load",
            "dut_name",
            "comparison_mode",
        ],
        keep="last",
    )

    df_clean.to_parquet(OUTPUT_FILE)
    print(f"\n✅ Datenbank gespeichert: {OUTPUT_FILE} ({len(df_clean)} Einträge)")


if __name__ == "__main__":
    main()
