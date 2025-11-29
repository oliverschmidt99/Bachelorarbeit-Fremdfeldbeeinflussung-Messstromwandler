# Bachelorarbeit: Fremdfeldbeeinflussung auf Messstromwandler in der Niederspannung

![Status](https://img.shields.io/badge/Status-In_Bearbeitung-yellow)
![Fachbereich](https://img.shields.io/badge/Bereich-Elektrotechnik-blue)

## 📄 Projektübersicht

Im Rahmen dieser Bachelorarbeit wird die Messgenauigkeit von Stromwandlern in Niederspannungsschaltanlagen untersucht. Ein besonderer Fokus liegt auf der **magnetischen Kopplung** zwischen benachbarten Phasen bzw. externen Stromschienen. Diese Fremdfelder wurden in Voruntersuchungen als signifikante Störgröße identifiziert, die zu relevanten Messabweichungen führen.

Das Projekt umfasst sowohl die **experimentelle Quantifizierung** dieser Fehler am Hochstrom-Prüfstand als auch die **technische Optimierung** der Messkette (Retrofit durch digitale Messtechnik und SPS-Automatisierung).

## 📅 Zeitplan & Projektmanagement

Der folgende Projektplan visualisiert die Meilensteine, Reviews und die Schreibphasen der Bachelorarbeit.

```mermaid
gantt
    title Projektplan Bachelorarbeit – Messstromwandler & Fremdfelder
    dateFormat  YYYY-MM-DD
    axisFormat %d/%m
    excludes    2025-12-24, 2025-12-25, 2025-12-26, 2026-01-01, sunday

    %% ==============================================================================
    %% MEILENSTEINE (Alle 14 Tage)
    %% ==============================================================================
    section Meilensteine
    Start der Arbeit                    :active, milestone, start, 2025-12-01, 0d

    Zwischenkontrolle 1                 :milestone, zk1, 2025-12-15, 0d
    Zwischenkontrolle 2                 :milestone, zk2, 2025-12-29, 0d
    Zwischenkontrolle 3                 :milestone, zk3, 2026-01-12, 0d
    Zwischenkontrolle 4                 :milestone, zk4, 2026-01-26, 0d
    Zwischenkontrolle 5                 :milestone, zk5, 2026-02-09, 0d

    Abschluss Messung                   :crit, milestone, mess_ende, after messung_1, 0d
    Abgabe der Bachelorarbeit           :crit, milestone, abgabe, 2026-02-25, 0d


    %% ==============================================================================
    %% PRÜFEN (Reviews immer 2 Tage VOR dem Meilenstein/Meeting)
    %% ==============================================================================
    section Prüfen
    %% ZK1 ist am 15.12 (Mo) -> Prüfung am Do/Fr davor
    Review Methodik & Aufbau            :crit, rev1, 2025-12-11, 2d

    %% ZK2 ist am 29.12 (Mo) -> 24-26 sind frei -> Prüfung am 22./23.12
    Review Experimente                  :crit, rev2, 2025-12-22, 2d

    %% ZK3 ist am 12.01 (Mo) -> Prüfung am Do/Fr davor (08./09.01)
    Review Auswertung                   :crit, rev3, 2026-01-08, 2d

    %% ZK4 ist am 26.01 (Mo) -> Prüfung am Do/Fr davor (22./23.01)
    Review Zusammenfassung              :crit, rev4, 2026-01-22, 2d


    %% ==============================================================================
    %% SCHREIBEN (Passt sich an die Reviews an)
    %% ==============================================================================
    section Schreiben
    %% Phase 1: Bis zum ersten Review
    Versuchsaufbau und Methodik         :active, write1, 2025-12-01, 8d

    %% Phase 2: Nach ZK1 bis zum nächsten Review (Weihnachtspause beachten!)
    Experimentelle Untersuchung         :write2, after zk1, 5d

    %% Phase 3: Nach ZK2 bis zum nächsten Review
    Auswertung und Diskussion           :write3, after zk2, 8d

    %% Phase 4: Nach ZK3 bis zum nächsten Review
    Zusammenfassung und Ausblick        :write4, after zk3, 8d

    %% Feinschliff bis zur Abgabe
    Endkorrektur                        :write5, after zk4, 20d


    %% ============================
    %% Messreihen & Datenerhebung
    %% ============================
    section Messen
    Programmierung SPS                  :active, crit, prog_1, 2025-11-29, 4d
    Durchführung der Messreihen         :active, messung_1, 2025-12-01, 12d

    %% ============================
    %% Meetings (Manuell berechnet)
    %% ============================
    section Meetings
    Regelmäßiges Meeting 1              :meeting_1, 2025-12-01, 1d
    Regelmäßiges Meeting 2              :meeting_2, 2025-12-15, 1d
    Regelmäßiges Meeting 3              :meeting_3, 2025-12-29, 1d
    Regelmäßiges Meeting 4              :meeting_4, 2026-01-12, 1d
    Regelmäßiges Meeting 5              :meeting_5, 2026-01-26, 1d
    Regelmäßiges Meeting 6              :meeting_6, 2026-02-09, 1d
```

# Autor

Oliver Schmidt Student Elektrotechnik

# Lizenz & Rechtliche Hinweise

![Status](https://img.shields.io/badge/Status-Propriet%C3%A4r%2FGeschlossen-red)

Dieses Projekt, einschließlich aller Daten, Quellcodes und Dokumentationen, ist urheberrechtlich geschützt und enthält vertrauliche Informationen des Kooperationspartners.

**Copyright © 2025 Oliver Schmidt & Rolf Janssen GmbH Elektrotechnische Werke**

- Alle Rechte vorbehalten.
- Die Inhalte sind ausschließlich zur Vorlage bei der prüfenden Hochschule bestimmt.
- Jede Art der Vervielfältigung, Verbreitung, Veröffentlichung oder Weitergabe an Dritte ist ohne ausdrückliche schriftliche Genehmigung der Rechteinhaber streng untersagt.
