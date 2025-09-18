@echo off
echo ==========================================================
echo  Die Ordnerstruktur wird auf deutsche Namen umgestellt...
echo ==========================================================
echo.

:: Prüfen, ob die Ordner existieren
if not exist "02_Inhalt\01_frontmatter" (
    echo Fehler: Der Ordner "01_frontmatter" wurde nicht gefunden.
    echo Das Skript wurde möglicherweise bereits ausgeführt.
    pause
    exit /b
)

:: 1. Ordner umbenennen
echo Benenne Ordner um...
ren "02_Inhalt\01_frontmatter" "01_Vorspann"
ren "02_Inhalt\02_mainmatter" "02_Hauptteil"
ren "02_Inhalt\03_backmatter" "03_Nachspann"
echo.

:: 2. Pfade in der main.tex anpassen
echo Passe die Pfade in main.tex an...

powershell -Command "(Get-Content main.tex) | ForEach-Object { $_ -replace '01_frontmatter', '01_Vorspann' } | Set-Content main.tex"
powershell -Command "(Get-Content main.tex) | ForEach-Object { $_ -replace '02_mainmatter', '02_Hauptteil' } | Set-Content main.tex"
powershell -Command "(Get-Content main.tex) | ForEach-Object { $_ -replace '03_backmatter', '03_Nachspann' } | Set-Content main.tex"

echo.
echo ==========================================================
echo  Die Ordner wurden erfolgreich umbenannt.
echo ==========================================================
pause