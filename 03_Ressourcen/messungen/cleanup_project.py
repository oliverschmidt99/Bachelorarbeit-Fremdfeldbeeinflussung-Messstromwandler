import os
import shutil

# --- KONFIGURATION ---

# 1. Diese Dateien kommen nach /daten
FILES_FOR_DATEN = [
    "messdaten_db.parquet",
    "messdaten_db.parquet.backup",
    "saved_configs.json",
    "manuelle_ergebnisse.csv",
    "messungen_auswerten.xlsm",
    "Archiv.zip",             # Optional: Zips auch zu Daten
    "messungen_sortiert.zip"
]

# 2. Diese Dateien kommen nach /src (Helfer-Code)
FILES_FOR_SRC = [
    "fix_duration_600.py",
    "create_db.py",
    "delete_file.py",
    "inspect_db.py",
    "create_plots.m",
    # Alte Versionen auch in src (oder einen Unterordner archive)
    "v1-dashboard.py",
    "v2-dashboard.py",
    "v3-dashboard.py",
    "v4-dashboard.py"
]

# 3. Diese Dateien BLEIBEN im Hauptordner (werden ignoriert)
# - visualisierungs_dashboard.py
# - messdaten_selektor.py
# - daten_aggregator.py
# - tree.py
# - requirements.txt
# - venv/
# - messungen/
# - messungen_sortiert/

def move_files(file_list, target_folder_name):
    # Pfad zum Zielordner erstellen (z.B. ./daten)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, target_folder_name)

    # Ordner erstellen, falls nicht existent
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"📁 Ordner erstellt: {target_folder_name}")

    count = 0
    for filename in file_list:
        src_path = os.path.join(base_dir, filename)
        dst_path = os.path.join(target_dir, filename)

        if os.path.exists(src_path):
            try:
                shutil.move(src_path, dst_path)
                print(f"  -> Verschoben: {filename} nach /{target_folder_name}")
                count += 1
            except Exception as e:
                print(f"  ❌ Fehler bei {filename}: {e}")
        # Wenn Datei nicht da ist, ignorieren wir sie stillschweigend
    
    return count

def main():
    print("--- 🧹 Starte Projekt-Aufräumung ---")
    
    # Daten verschieben
    n_daten = move_files(FILES_FOR_DATEN, "daten")
    
    # Source verschieben
    n_src = move_files(FILES_FOR_SRC, "src")
    
    print("-" * 30)
    print(f"✅ Fertig! {n_daten} Dateien nach 'daten/' und {n_src} Dateien nach 'src/' verschoben.")
    print("⚠️  WICHTIG: Du musst jetzt die Pfade in deinen Python-Skripten anpassen!")
    print("    (Siehe Code-Snippets unten)")

if __name__ == "__main__":
    main()