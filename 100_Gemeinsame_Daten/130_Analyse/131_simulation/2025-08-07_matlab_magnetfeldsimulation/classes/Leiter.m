classdef Leiter
    % LEITER Definiert einen einzelnen, stromführenden Leiter, der optional
    % einen Stromwandler zur Analyse tragen kann.
    
    properties
        Position (1,2) double
        IsEnabled logical
        Momentanstrom double
        Phasenverschiebung double
        Wandler Stromwandler = Stromwandler.empty
    end
    
    methods
        %% Konstruktor
        function obj = Leiter(startPosition, phaseShift_rad, isEnabled)
            % ... (bleibt unverändert) ...
            obj.Position = startPosition;
            obj.Phasenverschiebung = phaseShift_rad;
            if nargin < 3
                isEnabled = true;
            end
            obj.IsEnabled = isEnabled;
            obj.Momentanstrom = 0;
        end
        
        %% VERBESSERTE Methode, um einen Wandler hinzuzufügen
        function obj = addWandler(obj, I_prim, I_sek, options)
            % Nimmt Nennströme direkt entgegen.
            % Andere Parameter sind optional (Name-Wert-Paare).
            % Beispiel: L1.addWandler(400, 5, Buerde=2.0, Kernflaeche=300)
            
            arguments
                obj
                I_prim (1,1) double
                I_sek (1,1) double
                % Optionale Parameter mit Standardwerten
                options.Buerde (1,1) double = 1.0
                options.Kernflaeche (1,1) double = 250
                options.BSat (1,1) double = 1.8
            end
            
            % Den Ratio-String für den Konstruktor zusammensetzen
            ctRatio_str = sprintf('%d/%d', I_prim, I_sek);
            
            % Das Stromwandler-Objekt intern erstellen
            wandler_obj = Stromwandler(ctRatio_str, options.Buerde, options.Kernflaeche, options.BSat);
            
            % Das neue Objekt der Eigenschaft zuweisen
            obj.Wandler = wandler_obj;
        end
        
        %% Methode zur Strom-Aktualisierung
        function obj = updateCurrent(obj, I_peak, omega, t)
            % ... (bleibt unverändert) ...
             if obj.IsEnabled
                obj.Momentanstrom = I_peak * sin(omega * t + obj.Phasenverschiebung);
            else
                obj.Momentanstrom = 0;
            end
        end
        
        %% Methode zur Feldberechnung
        function [Bx, By] = calculateField(obj, X, Y)
            % ... (bleibt unverändert) ...
            if ~obj.IsEnabled || obj.Momentanstrom == 0
                Bx = zeros(size(X)); By = zeros(size(Y)); return;
            end
            mu_0 = 4*pi*1e-7;
            rx = X - obj.Position(1); ry = Y - obj.Position(2);
            r = sqrt(rx.^2 + ry.^2); r(r < 1e-6) = 1e-6;
            B_mag = (mu_0 * obj.Momentanstrom) ./ (2 * pi * r);
            Bx = -B_mag .* (ry ./ r); By =  B_mag .* (rx ./ r);
        end
    end
end