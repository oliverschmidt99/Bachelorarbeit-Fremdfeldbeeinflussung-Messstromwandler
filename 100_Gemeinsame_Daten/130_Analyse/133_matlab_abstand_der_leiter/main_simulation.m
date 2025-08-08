%% Hauptskript zur Simulation der Fremdfeldbeeinflussung von Stromwandlern
%
% Beschreibung:
% Dieses Skript dient als zentrale Steuerungseinheit. Es liest die Konfiguration
% verschiedener Stromwandler, führt für jeden Hersteller eine separate
% Simulation durch, erstellt Grafiken und speichert diese automatisch als
% passgenaue PDF-Dateien im 'output'-Ordner ab.

% =========================================================================
% INITIALISIERUNG
% =========================================================================
clear; clc; close all;

% --- Fügt die Ordner für Klassen und Funktionen zum MATLAB-Pfad hinzu ---
addpath('classes', 'src');

%% 1. ZENTRALE KONFIGURATION DER WANDLER
% =========================================================================
% Hier werden alle zu simulierenden Wandler, gruppiert nach Hersteller,
% definiert. Dies ist der primäre Ort für Anpassungen.

config.hersteller.MBS = { ...
                             Stromwandler('MBS', 'ASK 41.4 (600A/5A)', 600, 'rechteckig', {70, 88.5, 40, ((70 - 40.5) * 40) / 2}); ...
                             Stromwandler('MBS', 'ASK 51.4 (800A/5A)', 800, 'rechteckig', {85, 98.5, 45, ((85 - 40.4) * 40) / 2}); ...
                             Stromwandler('MBS', 'ASK 63.6 (1000A/5A)', 1000, 'rechteckig', {88, 129, 60, ((88 - 60.5) * 60) / 2}); ...
                             Stromwandler('MBS', 'ASK 51.4 (1250A/5A)', 1250, 'rechteckig', {85, 98.5, 45, ((85 - 50.5) * 40) / 2}); ...
                             Stromwandler('MBS', 'ASK 63.6 (1600A/5A)', 1600, 'rechteckig', {88, 129, 60, ((88 - 60.5) * 60) / 2}); ...
                             Stromwandler('MBS', 'ASK 101.4 (2000A/5A)', 2000, 'rechteckig', {130, 144, 45, ((130 - 100.5) * 40) / 2}); ...
                             Stromwandler('MBS', 'ASK 105.6 (2500A/5A)', 2500, 'rechteckig', {129, 167, 60, ((129 - 100.5) * 60) / 2}); ...
                             Stromwandler('MBS', 'ASK 105.6 (3250A/1A)', 3250, 'rechteckig', {129, 167, 60, ((129 - 100.5) * 60) / 2}); ...
                             Stromwandler('MBS', 'ASK 127.6 (4000A/5A)', 4000, 'rechteckig', {205, 206, 60, ((205 - 120.5) * 60) / 2}); ...
                             Stromwandler('MBS', 'ASK 129.10 (5000A/5A)', 5000, 'rechteckig', {250, 250, 100, ((250 - 122) * 100) / 2}) ...
                         };


config.hersteller.Celsa = { ...
                               Stromwandler('Celsa', 'ALO 4012 (600A/5A)', 600, 'rechteckig', {70, 92, 31, ((70 - 40) * 31) / 2}); ...
                               Stromwandler('Celsa', 'ALO 5012 (800A/5A)', 800, 'rechteckig', {85, 110, 31, ((85 - 50) * 31) / 2}); ...
                               Stromwandler('Celsa', 'ALO 6015.8 (1000A/5A)', 1000, 'rechteckig', {86, 110, 31, ((86 - 60) * 31) / 2}); ...
                               Stromwandler('Celsa', 'AST615 (1250A/5A)', 1250, 'rechteckig', {96, 121, 30, ((96 - 60) * 30) / 2}); ...
                               Stromwandler('Celsa', 'AST815 (1600A/5A)', 1600, 'rechteckig', {105, 132, 30, ((105 - 80) * 30) / 2}); ...
                               Stromwandler('Celsa', 'ALO 10030 (2000A/5A)', 2000, 'rechteckig', {129, 158, 31, ((129 - 100) * 31) / 2}); ...
                               Stromwandler('Celsa', 'ALO 10030 (2500A/5A)', 2500, 'rechteckig', {129, 158, 31, ((129 - 100) * 31) / 2}); ...
                               Stromwandler('Celsa', 'AST1056 (3200A/5A)', 3200, 'rechteckig', {131, 160, 30, ((131 - 105) * 30) / 2}); ...
                               Stromwandler('Celsa', 'AST1272 (4000A/5A)', 4000, 'rechteckig', {159, 188, 30, ((159 - 122) * 30) / 2}); ...
                               Stromwandler('Celsa', 'AST1659 (5000A/5A)', 5000, 'rechteckig', {223, 171, 35, ((223 - 165) * 35) / 2}) ...
                           };


%% 2. SIMULATIONSPARAMETER
% =========================================================================
config.simulation.D_max_mm = 10000;
config.simulation.n_punkte = 3000;

%% 3. HAUPTSCHLEIFE: SIMULATION PRO HERSTELLER
% =========================================================================
hersteller_namen = fieldnames(config.hersteller);

for i = 1:length(hersteller_namen)
    aktueller_hersteller = hersteller_namen{i};
    wandler_liste_unsortiert = config.hersteller.(aktueller_hersteller);

    if isempty(wandler_liste_unsortiert)
        fprintf('-> Überspringe Hersteller %s (keine Wandler definiert).\n', aktueller_hersteller);
        continue;
    end

    fprintf('\n--- Starte Simulation für Hersteller: %s ---\n', aktueller_hersteller);

    % --- Datenaufbereitung (Sortierung) ---
    stromstaerken = cellfun(@(w) w.I_pr, wandler_liste_unsortiert);
    [~, sortier_indizes] = sort(stromstaerken);
    wandler_liste = wandler_liste_unsortiert(sortier_indizes);

    % --- Vorbereitung ---
    num_wandler = length(wandler_liste);
    D_sim_mm = linspace(10, config.simulation.D_max_mm, config.simulation.n_punkte);
    D_sim_m = D_sim_mm / 1000;
    colors = generate_color_palette(num_wandler);

    % --- Grafik erstellen ---
    fig = figure('Name', ['Fremdfeld: ' aktueller_hersteller]);
    hold on;

    for k = 1:num_wandler
        wandler = wandler_liste{k};
        [B, D_valid_m] = wandler.berechneFlussdichte(D_sim_m);

        if ~isempty(B)
            plot(D_valid_m * 1000, B, 'LineWidth', 2, 'Color', colors(k, :), 'DisplayName', wandler.Name);
            fprintf('Max. Flussdichte für %s: ', wandler.Name);
            printfENG(max(B), 'm', 'T');
        end

    end

    hold off;

    % --- Grafik formatieren und speichern ---
    title(sprintf('Vergleich der Wandler von %s', aktueller_hersteller), 'FontSize', 14);
    xlabel('Abstand der Phasen D [mm]', 'FontSize', 12);
    ylabel('Induzierte Flussdichte B [T]', 'FontSize', 12);
    grid on; box on;
    legend('show', 'Location', 'northeast', 'Interpreter', 'none');
    set(gca, 'XScale', 'log', 'YScale', 'log');

    output_filename = sprintf('Vergleich_%s.pdf', aktueller_hersteller);
    saveMyPlot(output_filename, 'output', fig);
end

disp('Alle Simulationen erfolgreich abgeschlossen.');

%% HILFSFUNKTION FÜR FARBPALETTE
% =========================================================================
function colors = generate_color_palette(num_colors)
    if num_colors == 0; colors = []; return; end
    n_groups = 3;
    n_per_group = floor(num_colors / n_groups);
    remainder = mod(num_colors, n_groups);
    group_sizes = n_per_group * ones(1, n_groups);
    for i = 1:remainder; group_sizes(i) = group_sizes(i) + 1; end

    maps = {
            [linspace(0, 0.5, group_sizes(1))', linspace(0, 0.8, group_sizes(1))', linspace(0.5, 1, group_sizes(1))']; % Blue
            [linspace(0, 0.6, group_sizes(2))', linspace(0.4, 1, group_sizes(2))', linspace(0, 0.6, group_sizes(2))']; % Green
            [linspace(0.6, 1, group_sizes(3))', linspace(0, 0.6, group_sizes(3))', linspace(0, 0.6, group_sizes(3))'] % Red
            };
    colors = vertcat(maps{:});
end
