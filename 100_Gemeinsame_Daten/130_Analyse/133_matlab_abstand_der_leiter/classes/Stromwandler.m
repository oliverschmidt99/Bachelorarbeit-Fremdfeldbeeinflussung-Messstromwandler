% Stromwandler.m - Eine Klasse zur Kapselung der Eigenschaften von Stromwandlern
%
% Diese Klasse modelliert die physikalischen und geometrischen Eigenschaften
% eines Stromwandlers zur Analyse der Fremdfeldbeeinflussung.

classdef Stromwandler

    properties
        Hersteller (1, 1) string
        Name (1, 1) string
        I_pr (1, 1) double
        Form (1, 1) string
        R_eff (1, 1) double
        W (1, 1) double
        A (1, 1) double
    end

    methods
        % --- KONSTRUKTOR ---
        function obj = Stromwandler(hersteller, name, i_pr, form, geo_params_mm)
            obj.Hersteller = hersteller;
            obj.Name = name;
            obj.I_pr = i_pr;
            obj.Form = form;

            switch form
                case 'rund'

                    if numel(geo_params_mm) ~= 3 || ~isnumeric(cell2mat(geo_params_mm))
                        error('Für Form "rund" werden 3 numerische geo_params benötigt: {R_aussen, W, A}');
                    end

                    aussenradius_mm = geo_params_mm{1};
                    kernbreite_W_mm = geo_params_mm{2};
                    flaeche_A_mm2 = geo_params_mm{3};

                    obj.R_eff = aussenradius_mm / 1000;
                    obj.W = kernbreite_W_mm / 1000;
                    obj.A = flaeche_A_mm2 / 1e6;

                case 'rechteckig'

                    if numel(geo_params_mm) ~= 4 || ~isnumeric(cell2mat(geo_params_mm))
                        error('Für Form "rechteckig" werden 4 numerische geo_params benötigt: {B, H, T, A}');
                    end

                    aussenbreite_mm = geo_params_mm{1};
                    aussenhoehe_mm = geo_params_mm{2};
                    kerntiefe_W_mm = geo_params_mm{3};
                    flaeche_A_mm2 = geo_params_mm{4};

                    obj.R_eff = max(aussenbreite_mm, aussenhoehe_mm) / 2/1000;
                    obj.W = kerntiefe_W_mm / 1000;
                    obj.A = flaeche_A_mm2 / 1e6;

                otherwise
                    error("Ungültige Form: '%s'. Nur 'rund' oder 'rechteckig' verwenden.", form);
            end

        end

        % --- BERECHNUNGSMETHODE ---
        % Berechnet die magnetische Flussdichte B nach der Formel von Pfuntner.
        % Quelle: R.A. Pfuntner, The accuracy of current transformers adjacent
        %         to heavy current buses, AIEE Trans., vol. 70, 1951
        %         Angepasst wie auf www.schutztechnik.com dargestellt.
        function [B, D_valid] = berechneFlussdichte(obj, D_vektor_m)
            gueltige_indizes = D_vektor_m > obj.R_eff;
            D_valid = D_vektor_m(gueltige_indizes);

            if isempty(D_valid)
                B = [];
                warning('Keine gültigen Abstände (D > R_eff) für "%s" gefunden.', obj.Name);
                return;
            end

            faktor1 = 10 ^ -6 * obj.I_pr * (obj.R_eff + 0.5 * obj.W) / obj.A;
            faktor2 = log10((D_valid + obj.R_eff) ./ (D_valid - obj.R_eff));

            B = faktor1 * faktor2;
        end

    end

end
