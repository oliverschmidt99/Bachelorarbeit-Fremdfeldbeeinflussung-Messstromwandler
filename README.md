# Bachelorarbeit: Fremdfeldbeeinflussung auf Messstromwandler in der Niederspannung

## Projektübersicht

Diese Bachelorarbeit befasst sich mit der Analyse von Messfehlern bei Stromwandlern, die in Niederspannungsschaltanlagen eingesetzt werden. Der Schwerpunkt der Untersuchung liegt auf der magnetischen Kopplung zwischen Stromwandlern benachbarter Phasen, welche als eine wesentliche Ursache für Messabweichungen identifiziert wurde.

## Ziele

- **Theoretische Analyse:** Erarbeitung der physikalischen Grundlagen der magnetischen Feldkopplung und deren Auswirkungen auf Messstromwandler.
- **Experimentelle Untersuchung:** Durchführung von Messreihen an einem praxisnahen Versuchsaufbau zur Quantifizierung der Fremdfeldbeeinflussung.
- **Datenanalyse und Validierung:** Vergleich der gewonnenen Messdaten mit den theoretisch ermittelten Modellen zur Validierung der Hypothesen.
- **Entwicklung von Lösungsansätzen:** Ausarbeitung von konkreten Handlungsempfehlungen und technischen Maßnahmen zur Minimierung der festgestellten Messfehler.

# Zeitplan Bachelorarbeit

Hier ist der aktuelle Stand der Planung.

# Projektplan

```mermaid
gantt
    title Projektplan Bachelorarbeit – Messstromwandler & Fremdfelder
    dateFormat  YYYY-MM-DD
    axisFormat %d/%m
    excludes    2025-12-24, 2025-12-25, 2025-12-26, 2026-01-01, 2026-01-06, weekends

    %% ==============================================================================
    %% LEGENDE / BEFEHLE
    %% ==============================================================================
    %% :milestone -> Erzeugt eine Raute (Wichtig: Dauer auf 0d setzen!)
    %% :crit      -> Roter Rahmen/Füllung (Kritisch)
    %% :active    -> In Bearbeitung
    %% :done      -> Erledigt
    %% ==============================================================================


    %% ============================
    %% Wichtige Meilensteine (NEU)
    %% ============================
    section Meilensteine
    Start der Arbeit                    :active,milestone, start, 2025-12-01, 0d
    Messung                             :active, crit, milestone, after messung_1, 0d
    Zwischenkontrolle                   :milestone, after pruefung_1, 2025-12-20, 0d
    Zwischenkontrolle                   :milestone, after pruefung_1, 2026-01-06, 0d
    Abgabe der Bachelorarbeit           :crit, milestone, abgabe, 2026-02-25, 0d

    %% ============================
    %% Bachelorarbeit – Schreiben
    %% ============================
    section Schreiben
    Versuchsaufbau und Methodik         :active, methodik_1, 2025-12-01, 5d
    Experimentelle Untersuchung         :experiment_1, after methodik_1, 10d
    Auswertung und Diskussion           :auswertung_1, after experiment_1, 7d
    Zusammenfassung der Ergebnisse      :zusammenfassung_1, after auswertung_1, 5d
    Einleitung                          :einleitung_1, after zusammenfassung_1, 3d
    Ausblick                            :ausblick_1, after einleitung_1, 3d

    %% ============================
    %% Messreihen & Datenerhebung
    %% ============================
    section Messen
    Programmierung der SPS              :active, programmierung_1, 2025-11-29, 3d
    Durchführung der Messreihen         :messung_1, after programmierung_1, 12d


    %% ============================
    %% Prüfung
    %% ============================
    section Prüfen
    Überprüfung der Daten               :crit, active, pruefung_1, 2025-12-01, 12d

    %% ============================
    %% Meetings
    %% ============================
    section Meetings
    Regelmäßiges Meeting (Block)        :meeting_1, 2025-12-19, 1d
```

# Autor

Oliver Schmidt

Lizenz

Dieses Projekt ist unter der MIT License lizenziert. Weitere Details finden sich in der LICENSE.md-Datei.

```

```
