+--------------------------------------------------------------------------------------------------+
| FB1: Initialisierung (Netzwerk 1)                                                                |
| Setze Temp-Variable #Soll_Intern = 0.0 [cite: 56, 58]                                            |
+--------------------------------------------------------------------------------------------------+
| Reset gedrückt? (#Reset == TRUE) [cite: 74, 103]                                                 |
+----------------------------------------+---------------------------------------------------------+
| JA                                     | NEIN                                                    |
+----------------------------------------+---------------------------------------------------------+
| Schrittkette zurücksetzen:             | Normale Bearbeitung                                     |
| #Schritt_old = 0                       |                                                         |
| #Schritt_new = 0                       |                                                         |
| #Start = FALSE                         |                                                         |
| [cite: 76, 118, 144]                   |                                                         |
+----------------------------------------+---------------------------------------------------------+
|                                        v                                                         |
+--------------------------------------------------------------------------------------------------+
| FALLUNTERSCHEIDUNG: Aktueller Schritt (#Schritt_old) [cite: 200, 241, 1109]                      |
+-------+--------+--------+--------+--------+--------+--------+--------+--------+--------+---------+
| 0     | 10     | 20     | 22     | 24     | 26     | 30     | 40     | 50     | 99     | Sonst   |
| Idle  | 5%     | 20%    | 50%    | 80%    | 90%    | 100%   | 120%   | Rampe  | Ende   |         |
+-------+--------+--------+--------+--------+--------+--------+--------+--------+--------+---------+
| Prüfe | Soll = | Soll = | Soll = | Soll = | Soll = | Soll = | Soll = | Soll = | Setze  | Keine   |
| Start | I_Max  | I_Max  | I_Max  | I_Max  | I_Max  | I_Max  | I_Max  | 0.0 A  | #Fertig| Akt.    |
| Bed.  | * 0.05 | * 0.20 | * 0.50 | * 0.80 | * 0.90 | * 1.00 | * 1.20 |        | = TRUE |         |
| (FC4  |        |        |        |        |        |        |        |   | 1211]  |         |
| 0A)   | 265]   | 301]   | 341]   | 387]   | 426]   | 472]   | 510]   |        | Reset  |         |
|  |        |        |        |        |        |        |        |        |        |         |
+-------+--------+--------+--------+--------+--------+--------+--------+--------+--------+---------+
|                                        v                                                         |
+--------------------------------------------------------------------------------------------------+
| Toleranzprüfung & Timer (Netzwerk 14-17)                                                         |
| 1. Aufruf FC4: Prüfe ob Istwerte L1, L2, L3 im Bereich "Soll +/- Toleranz" sind.                 |
|    Ergebnis -> #Im_Fenster_Schrittkette [cite: 573, 574]                                         |
| 2. Entprellung (Timer T1, T2): Filtert Rauschen -> #Fenster_Stabil [cite: 635, 687]              |
| 3. Messzeit (Timer T3): Läuft wenn #Fenster_Stabil.                                              |
|    Wenn Zeit abgelaufen -> #Fenster_gemessen = TRUE [cite: 746, 797]                             |
+--------------------------------------------------------------------------------------------------+
| Transitionen (Schrittweiterschaltung) (Netzwerk 5, 18-25)                                        |
+--------------------------------------------------------------------------------------------------+
| Bedingung erfüllt?                                                                               |
+-------------------------------------------------------+------------------------------------------+
| JA                                                    | NEIN                                     |
+-------------------------------------------------------+------------------------------------------+
| Schritt 0  & Start & 0A-Check -> Schritt 10           | Schritt beibehalten                      |
| Schritt 10 & Fenster_gemessen -> Schritt 20           |                                          |
| Schritt 20 & Fenster_gemessen -> Schritt 22           |                                          |
| Schritt 22 & Fenster_gemessen -> Schritt 24           |                                          |
| Schritt 24 & Fenster_gemessen -> Schritt 26           |                                          |
| Schritt 26 & Fenster_gemessen -> Schritt 30           |                                          |
| Schritt 30 & Fenster_gemessen -> Schritt 40           |                                          |
| Schritt 40 & Fenster_gemessen -> Schritt 50           |                                          |
| Schritt 50 & Fenster_gemessen -> Schritt 99           |                                          |
|                                                       |                                          |
+-------------------------------------------------------+------------------------------------------+
|                                        v                                                         |
+--------------------------------------------------------------------------------------------------+
| Ausgangstreiber & Housekeeping (Netzwerk 26-29)                                                  |
| 1. Schreibe #Soll_Intern auf Ausgang #Sollwert_Out [cite: 1140]                                  |
| 2. Aktualisiere Schrittanzeige für Visu [cite: 1181]                                             |
| 3. Merker aktualisieren: #Schritt_old = #Schritt_new [cite: 1222]                                |
+--------------------------------------------------------------------------------------------------+