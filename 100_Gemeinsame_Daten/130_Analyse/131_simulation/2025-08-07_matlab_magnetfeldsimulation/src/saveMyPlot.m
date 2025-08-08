function saveMyPlot(fileNameWithExt, basePath, figHandle)
%SAVEMYPLOT Speichert eine MATLAB-Abbildung als PDF mit exakter Größenanpassung.
%   Die Funktion speichert eine Grafik passgenau als PDF im Zielverzeichnis
%   und erstellt dieses, falls es nicht existiert.
%
%   Syntax: saveMyPlot(fileNameWithExt, basePath, figHandle)

    % --- Argumente prüfen ---
    if nargin < 2; error('Benötigt: fileNameWithExt, basePath'); end
    if nargin < 3 || isempty(figHandle); figHandle = gcf; end
    if ~isgraphics(figHandle, 'figure'); error('figHandle ist kein gültiges Figure-Handle.'); end

    % --- Zielverzeichnis erstellen ---
    if ~isfolder(basePath); mkdir(basePath); end
    fullSavePath = fullfile(basePath, fileNameWithExt);

    % --- Abbildung für den Druck vorbereiten und speichern ---
    fprintf('Speichere Abbildung als PDF nach:\n%s\n', fullSavePath);

    originalUnits = get(figHandle, 'Units');
    originalPaperUnits = get(figHandle, 'PaperUnits');
    originalPaperPositionMode = get(figHandle, 'PaperPositionMode');

    try
        set(figHandle, 'Units', 'centimeters');
        pos = get(figHandle, 'OuterPosition');
        set(figHandle, 'PaperUnits', 'centimeters');
        set(figHandle, 'PaperSize', [pos(3), pos(4)]);
        set(figHandle, 'PaperPosition', [0, 0, pos(3), pos(4)]);
        print(figHandle, fullSavePath, '-dpdf', '-r0');
        fprintf('Speichern erfolgreich.\n');
    catch ME
        fprintf('FEHLER beim Speichern der Abbildung: %s\n', ME.message);
    finally
        % Ursprüngliche Einstellungen wiederherstellen
        set(figHandle, 'Units', originalUnits, 'PaperUnits', originalPaperUnits, ...
            'PaperPositionMode', originalPaperPositionMode);
    end
end