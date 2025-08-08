function [convertedValue, outputUnit] = convertENG(value, targetPrefix, baseUnit)
%CONVERTENG Konvertiert einen Wert in eine SI-Präfix-Einheit oder Euro-Format.
%   Die Funktion gibt den rein numerischen, konvertierten Wert und die
%   dazugehörige Einheit als String zurück. Es findet keine
%   String-Formatierung statt.
%
%   Syntax: [convertedValue, outputUnit] = convertENG(value, targetPrefix, baseUnit)

    % Definition der SI-Präfixe und ihrer numerischen Faktoren.
    prefixes = {'p', 'n', 'mu', 'm', '', 'k', 'M', 'G'};
    factors = [1e-12, 1e-9, 1e-6, 1e-3, 1, 1e3, 1e6, 1e9];

    % Definition der Suffixe und Faktoren für große Euro-Beträge.
    largeNumSuffixes = {' Mio.', ' Mrd.', ' Bil.'};
    largeNumFactors = [1e6, 1e9, 1e12];

    % Fall 1: Die Basiseinheit ist Euro.
    if strcmp(baseUnit, '€')
        abs_value = abs(value);
        factor = 1;
        suffix = '';

        % Wähle den passenden Faktor und Suffix basierend auf der Größe des Wertes.
        if abs_value >= largeNumFactors(3)
            factor = largeNumFactors(3);
            suffix = largeNumSuffixes{3};
        elseif abs_value >= largeNumFactors(2)
            factor = largeNumFactors(2);
            suffix = largeNumSuffixes{2};
        elseif abs_value >= largeNumFactors(1)
            factor = largeNumFactors(1);
            suffix = largeNumSuffixes{1};
        end
        % Berechne den Wert und die zugehörige Einheit.
        convertedValue = value / factor;
        outputUnit = strcat(suffix, baseUnit);

    % Fall 2: Standard-SI-Einheit.
    else
        % Setze leeren Präfix, falls keiner angegeben wird.
        if nargin < 2 || isempty(targetPrefix); targetPrefix = ''; end

        % Finde den Index des gewünschten Präfixes.
        idx = find(strcmp(prefixes, targetPrefix), 1);
        if isempty(idx); error('Unbekannter SI-Präfix: %s', targetPrefix); end

        % Berechne den Wert und die zugehörige Einheit.
        convertedValue = value / factors(idx);
        outputUnit = strcat(targetPrefix, baseUnit);
    end
end