import pandas as pd
import json
import os
import re
from pathlib import Path

# --- KONFIGURATION ---
CONFIG_JSON = "saved_configs.json"
TARGET_LEVELS = [5, 20, 50, 80, 90, 100, 120]
PHASES = ["L1", "L2", "L3"]
OUTPUT_ROOT_DIR = "messungen_sortiert"
NEW_DURATION = 560  # 5 Minuten * 2 Hz


def try_read_csv(filepath, nrows=None):
    """Versucht verschiedene Encodings und Trennzeichen"""
    encodings = ["utf-16", "utf-8", "cp1252", "latin1"]
    separators = [(";", ","), (",", ".")]  # (sep, decimal)

    for enc in encodings:
        for sep, dec in separators:
            try:
                df = pd.read_csv(
                    filepath,
                    sep=sep,
                    decimal=dec,
                    encoding=enc,
                    engine="python",
                    nrows=nrows,
                )
                if df.shape[1] > 1:
                    return df
            except:
                continue
    return None


def identify_devices(df):
    """Geräte aus Header erkennen"""
    df.columns = [c.strip().strip('"').strip("'") for c in df.columns]
    val_cols = [c for c in df.columns if "ValueY" in c]
    devices = set()
    for col in val_cols:
        name = col.replace("ValueY", "").strip()
        name = re.sub(r"[_ ]?L[123][_ ]?", "", name, flags=re.IGNORECASE).strip("_ ")
        if name:
            devices.add(name)
    return sorted(list(devices))


def load_raw_data(filepath, devices):
    """Lädt die Rohdaten"""
    df = try_read_csv(filepath)
    if df is None:
        return None

    df.columns = [c.strip().strip('"').strip("'") for c in df.columns]
    val_cols = [c for c in df.columns if "ValueY" in c]

    full_data = {dev: {} for dev in devices}

    for device in devices:
        for phase in PHASES:
            target_col = None
            for col in val_cols:
                clean_name = col.replace("ValueY", "").strip()
                dev_check = re.sub(
                    r"[_ ]?L[123][_ ]?", "", clean_name, flags=re.IGNORECASE
                ).strip("_ ")
                if dev_check == device and phase in col:
                    target_col = col
                    break
            if target_col:
                full_data[device][phase] = pd.to_numeric(
                    df[target_col], errors="coerce"
                ).fillna(0)
            else:
                full_data[device][phase] = None
    return full_data


def main():
    print(f"--- START: Korrektur auf {NEW_DURATION} Samples (5 min) ---")

    if not os.path.exists(CONFIG_JSON):
        print("Fehler: saved_configs.json nicht gefunden.")
        return

    with open(CONFIG_JSON, "r") as f:
        config_data = json.load(f)

    # Alle Rohdateien finden
    raw_files_map = {}
    for root, _, filenames in os.walk("."):
        if OUTPUT_ROOT_DIR in root or "venv" in root:
            continue
        for f in filenames:
            if (
                f.endswith(".csv")
                and "manuelle" not in f
                and "sortiert" not in f
                and "plot_data" not in f
            ):
                clean_name = f.replace(".csv", "")
                raw_files_map[clean_name] = os.path.join(root, f)

    files_processed = 0

    for filename_key, ranges in config_data.items():
        if filename_key not in raw_files_map:
            if not filename_key.startswith("dia_"):
                print(f"⚠️ Überspringe {filename_key} (Rohdatei nicht gefunden)")
            continue

        raw_path = raw_files_map[filename_key]
        print(f"Bearbeite: {filename_key} ...")

        # A. Neue Startzeiten berechnen
        new_ranges = {}
        for lvl_str, (old_s, end) in ranges.items():
            if end == 0:
                new_ranges[lvl_str] = (0, 0)
                continue
            new_start = max(0, end - NEW_DURATION)
            new_ranges[lvl_str] = (new_start, end)

        config_data[filename_key] = new_ranges

        # B. Sortierte Datei neu erstellen
        df_prev = try_read_csv(raw_path, nrows=5)
        if df_prev is None:
            print(f"  ❌ Fehler beim Lesen von {filename_key}")
            continue

        devices = identify_devices(df_prev)
        full_data = load_raw_data(raw_path, devices)
        if not full_data:
            print("  ❌ Fehler beim Laden der Voll-Daten")
            continue

        ref_device = "PAC1"
        for d in devices:
            if "pac1" in d.lower() or "einspeisung" in d.lower():
                ref_device = d
                break

        remaining = sorted([d for d in devices if d != ref_device])
        sorted_devs = [ref_device] + remaining if ref_device in devices else remaining

        # --- OPTIMIERUNG: Dictionary statt direkter DataFrame ---
        export_data = {}

        target_dir = Path(OUTPUT_ROOT_DIR) / Path(raw_path).parent
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / f"{filename_key}_sortiert.csv"

        for lvl_int in TARGET_LEVELS:
            lvl_str = str(lvl_int)
            if lvl_str in new_ranges:
                s, e = new_ranges[lvl_str]
                if s > 0 and e > s:
                    for phase in PHASES:
                        for dev in sorted_devs:
                            vals = full_data[dev][phase]
                            if vals is not None and e <= len(vals):
                                slice_data = vals.iloc[s:e].reset_index(drop=True)

                                col_t = f"{lvl_int:02d}_{phase}_t_{dev}"
                                col_I = f"{lvl_int:02d}_{phase}_I_{dev}"

                                # In Dict speichern statt direkt in DF
                                export_data[col_t] = pd.Series(range(len(slice_data)))
                                export_data[col_I] = slice_data

        # Jetzt erst DataFrame erstellen (verhindert PerformanceWarning)
        df_export = pd.DataFrame(export_data)
        df_export.to_csv(output_path, index=False, sep=";")
        files_processed += 1

    # 3. Aktualisierte JSON speichern
    with open(CONFIG_JSON, "w") as f:
        json.dump(config_data, f, indent=4)

    print(
        f"\n✅ Fertig! {files_processed} Dateien aktualisiert (600 Samples & neues Format)."
    )


if __name__ == "__main__":
    main()
