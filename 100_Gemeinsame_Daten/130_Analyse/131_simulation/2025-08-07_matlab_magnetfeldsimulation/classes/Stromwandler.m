classdef Stromwandler
    % STROMWANDLER Definiert einen Stromwandler mit seinen Eigenschaften und Berechnungen.
    
    properties
        Uebersetzung (1,1) double % Numerisches Übersetzungsverhältnis (z.B. 40 für 200/5)
        Buerde (1,1) double       % Bürde in Ohm
        Kernflaeche_m2 (1,1) double % Kernfläche in m^2
        BSat (1,1) double         % Sättigungsflussdichte des Kerns in T
        RatioStr (1,1) string     % Das Verhältnis als Text (z.B. "200/5")
    end
    
    methods
        %% Konstruktor: Erstellt ein neues Stromwandler-Objekt
        function obj = Stromwandler(ctRatio_str, burden_Ohm, coreArea_mm2, b_sat)
            obj.RatioStr = ctRatio_str;
            obj.Buerde = burden_Ohm;
            obj.Kernflaeche_m2 = coreArea_mm2 / 1e6; % Direkt in m^2 speichern
            obj.BSat = b_sat;
            
            % Übersetzungsverhältnis berechnen und speichern
            ratio_parts = split(ctRatio_str, '/');
            obj.Uebersetzung = str2double(ratio_parts{1}) / str2double(ratio_parts{2});
        end
        
        %% Methode zur Analyse
        function results = analyse(obj, I_peak, f)
            % Diese Methode führt die komplette Analyse durch.
            % Sie benötigt den Spitzenstrom der Phase und die Frequenz.
            
            I_prim_rms = I_peak / sqrt(2);
            I_sek_ideal_rms = I_prim_rms / obj.Uebersetzung;
            U_sek_rms = I_sek_ideal_rms * obj.Buerde;
            
            N_sek = obj.Uebersetzung; % Annahme N_prim = 1
            
            flux_peak_needed = U_sek_rms / (4.44 * f * N_sek);
            B_peak_needed = flux_peak_needed / obj.Kernflaeche_m2;
            
            % Ergebnisse in einer Struktur bündeln und zurückgeben
            results.B_peak_benoetigt = B_peak_needed;
            results.I_sek_rms = I_sek_ideal_rms;
            results.isSaturated = B_peak_needed > obj.BSat;
        end
    end
end