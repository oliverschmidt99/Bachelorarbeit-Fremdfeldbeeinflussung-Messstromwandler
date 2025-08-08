function printfENG(value, targetPrefix, baseUnit)
    %PRINTFENG Formatiert und druckt einen Wert in Ingenieursnotation oder als Währung.
    %   Diese Funktion konvertiert eine Zahl und gibt sie formatiert im
    %   Command Window aus. Sie unterstützt SI-Einheiten und eine spezielle
    %   Darstellung für Euro, inklusive Tausendertrenner und Währungssuffixen.
    %
    %   Syntax: printfENG(value, targetPrefix, baseUnit)

    % Schritt 1: Konvertiere den numerischen Wert und erhalte die Einheit.
    % Die eigentliche Logik der Umrechnung ist in 'convertENG' gekapselt.
    [convertedValue, outputUnit] = convertENG(value, targetPrefix, baseUnit);

    % --- Schritt 2: Formatiere den Wert für die Ausgabe ---
    isCurrency = strcmp(baseUnit, '€');

    % Behandle das Vorzeichen separat, um die Formatierung zu vereinfachen.
    signChar = '';

    if convertedValue < 0
        signChar = '-';
        numericValueToFormat = abs(convertedValue);
    else
        numericValueToFormat = convertedValue;
    end

    % Wähle das Zahlenformat basierend auf dem Einheitentyp.
    if isCurrency
        formatSpec = '%.2f'; % Zwei Nachkommastellen für Währung.
    else
        formatSpec = '%.3f'; % Drei Nachkommastellen für technische Einheiten.
    end

    % Formatiere den Wert als String und ersetze den Dezimalpunkt durch ein Komma.
    formattedValueStr_Abs = sprintf(formatSpec, numericValueToFormat);
    formattedValueStr_Abs = strrep(formattedValueStr_Abs, '.', ',');

    % Füge Tausendertrennzeichen (Leerzeichen) hinzu.
    parts = strsplit(formattedValueStr_Abs, ',');
    integerPart = parts{1};
    decimalPart = parts{2};
    integerPart_Formatted = regexprep(integerPart, '(\d)(?=(\d{3})+(?!\d))', '$1 ');

    % Setze den formatierten String wieder zusammen.
    formattedValue = strcat(signChar, integerPart_Formatted, ',', decimalPart);

    % Füge ein Leerzeichen zwischen Wert und Einheit ein, außer bei speziellen €-Suffixen.
    separator = ' ';

    if isCurrency && (contains(outputUnit, 'Mio.') || contains(outputUnit, 'Mrd.') || contains(outputUnit, 'Bil.'))
        separator = ''; % Kein Leerzeichen, da es im Suffix enthalten ist.
    end

    % Gib das Endergebnis im Command Window aus.
    fprintf('%s%s%s\n', formattedValue, separator, outputUnit);
end
