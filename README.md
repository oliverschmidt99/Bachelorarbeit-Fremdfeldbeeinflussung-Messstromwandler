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

```mermaid
gantt
    title Projektplan Bachelorarbeit Elektrotechnik
    dateFormat  YYYY-MM-DD
    axisFormat  %W
    
    section Recherche & Analyse
    Literaturrecherche       :done,    des1, 2025-01-10, 2025-01-24
    Anforderungsanalyse      :active,  des2, 2025-01-25, 3d
    Materialbeschaffung      :         des3, after des2, 5d

    section Implementierung
    Schaltungsentwurf (PCB)  :         imp1, after des3, 10d
    Software-Entwicklung (C/C++) :     imp2, 2025-02-15, 20d
    Prototypen-Bau           :         imp3, after imp1, 5d

    section Schreiben
    Rohfassung Theorie       :         doc1, after des1, 10d
    Ergebnisse auswerten     :         doc2, after imp2, 5d
    Korrekturlesen & Formatierung :    doc3, after doc2, 7d
    Abgabe                   :crit,    2025-04-15, 1d
