import pandas as pd
import numpy as np
import re
import os
import glob

# --- KONFIGURATION ---
OUTPUT_FILE = "messdaten_db.parquet"
TARGET_LEVELS = [5, 20, 50, 80, 90, 100, 120]
LEVEL_TOLERANCE_PCT = 3.0
MIN_PLATEAU_DURATION_SEC = 10
ASSUMED_SAMPLING_RATE_SEC = 1.0


def extract_metadata(filepath):
    filename = os.path.basename(filepath)
    dirname = os.path.dirname(filepath)
    folder_name = os.path.basename(dirname).replace("_", " ")

    match_amp = re.search(r"[-_](\d+)A[-_]", filename)
    nennstrom = float(match_amp.group(1)) if match_amp else 0.0

    lower_name = filename.lower()
    if "mbs" in lower_name:
        manufacturer = "MBS"
    elif "celsa" in lower_name:
        manufacturer = "Celsa"
    elif "redur" in lower_name:
        manufacturer = "Redur"
    else:
        manufacturer = "Unbekannt"

    try:
        parts = filename.split("-")
        candidates = [
            p
            for p in parts
            if not re.match(r"^\d{4}", p)
            and p.lower() != manufacturer.lower()
            and str(int(nennstrom)) not in p
            and ".csv" not in p
        ]
        model_str = "_".join(candidates) if candidates else "Standard"
    except:
        model_str = "Unknown"

    wandler_key = f"{manufacturer} {model_str} ({int(nennstrom)}A)"

    return {
        "filepath": filepath,
        "folder": folder_name,
        "hersteller": manufacturer,
        "nennstrom": nennstrom,
        "wandler_key": wandler_key,
        "dateiname": filename,
    }


def analyze_file(filepath, meta):
    if meta["nennstrom"] == 0:
        return [], "Kein Nennstrom"

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
        return [], "Lesefehler"

    try:
        df.columns = [c.strip().strip('"').strip("'") for c in df.columns]
        val_cols = [c for c in df.columns if "ValueY" in c]
        if len(val_cols) < 2:
            return [], "Keine Messdaten"

        prefixes = sorted(list(set([c.split("_")[0] for c in val_cols])))
        if len(prefixes) < 2:
            return [], "Geräte nicht erkannt"

        dev_ref, dev_dut = prefixes[0], prefixes[1]
        results = []

        for phase in ["L1", "L2", "L3"]:
            col_ref = next((c for c in val_cols if dev_ref in c and phase in c), None)
            col_dut = next((c for c in val_cols if dev_dut in c and phase in c), None)
            if not col_ref or not col_dut:
                continue

            vals_ref = pd.to_numeric(df[col_ref], errors="coerce").fillna(0)
            vals_dut = pd.to_numeric(df[col_dut], errors="coerce").fillna(0)

            pct_ref = (vals_ref / meta["nennstrom"]) * 100

            for target in TARGET_LEVELS:
                mask = (pct_ref >= target - LEVEL_TOLERANCE_PCT) & (
                    pct_ref <= target + LEVEL_TOLERANCE_PCT
                )
                if not mask.any():
                    continue

                valid_idx = np.where(mask)[0]
                if len(valid_idx) < (
                    MIN_PLATEAU_DURATION_SEC / ASSUMED_SAMPLING_RATE_SEC
                ):
                    continue

                ref_plateau = vals_ref.iloc[valid_idx]
                dut_plateau = vals_dut.iloc[valid_idx]

                # Filter Nullen
                valid_m = ref_plateau != 0
                ref_plateau = ref_plateau[valid_m]
                dut_plateau = dut_plateau[valid_m]

                if len(ref_plateau) == 0:
                    continue

                # Speichern der Statistiken (Mean + Std)
                results.append(
                    {
                        "wandler_key": meta["wandler_key"],
                        "folder": meta["folder"],
                        "phase": phase,
                        "target_load": target,
                        "nennstrom": meta["nennstrom"],
                        # Absolutwerte speichern
                        "val_ref_mean": ref_plateau.mean(),
                        "val_ref_std": ref_plateau.std(),  # WICHTIG für Zeile 3
                        "val_dut_mean": dut_plateau.mean(),
                        "val_dut_std": dut_plateau.std(),  # WICHTIG für Zeile 1+2
                        "raw_file": meta["dateiname"],
                    }
                )

        return results, "OK"
    except Exception as e:
        return [], str(e)


def main():
    print("--- Start: Messdaten-Aufbereitung (V3 - mit StdDev) ---")
    files = []
    for root, _, filenames in os.walk("."):
        if any(x in root for x in ["venv", ".git"]):
            continue
        for f in filenames:
            if f.lower().endswith(".csv") and "messungen_auswerten" not in f:
                files.append(os.path.join(root, f))

    print(f"{len(files)} Dateien gefunden.")
    all_data = []

    for f in files:
        meta = extract_metadata(f)
        stats, _ = analyze_file(f, meta)
        if stats:
            all_data.extend(stats)
            print(f"✅ {os.path.basename(f)}")

    if not all_data:
        print("Keine Daten.")
        return

    pd.DataFrame(all_data).to_parquet(OUTPUT_FILE)
    print(f"\n✅ Datenbank aktualisiert: {OUTPUT_FILE}")
    print("Starte jetzt: streamlit run dashboard.py")


if __name__ == "__main__":
    main()
