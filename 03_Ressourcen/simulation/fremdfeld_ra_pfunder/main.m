%% Initialisierung
clear; clc; close all;

%% 1. Parameter Definition
mu_factor = 10^-6;  % Vorfaktor
A_cross = 2e-4;     % Querschnitt [m^2]
D_max = 3.0;        % Maximaler Abstand [m]

% Ströme (Angepasst auf 1000 und 2000 A)
Ip_low = 1000;      % 1000 A (Helle Farbe)
Ip_high = 2000;     % 2000 A (Dunkle Farbe)

% --- Geometrie 1: "Kompakt" (Blau) ---
R_klein = 0.10;     % Radius 10 cm
W_klein = 0.05;     % Breite 5 cm
% Startet ab 11 cm Abstand
D_vec_klein = linspace(R_klein + 0.01, D_max, 1000);

% --- Geometrie 2: "Voluminös" (Rot) ---
R_gross = 0.30;     % Radius 30 cm
W_gross = 0.15;     % Breite 15 cm
% Startet ab 31 cm Abstand
D_vec_gross = linspace(R_gross + 0.01, D_max, 1000);

%% 2. Berechnung (Basis-Terme ohne Strom)
% Berechnung für Kompakten Kern
term_geo_k = (R_klein + 0.5 * W_klein) / A_cross;
term_log_k = log10((D_vec_klein + R_klein) ./ (D_vec_klein - R_klein));
B_base_klein = mu_factor .* term_geo_k .* term_log_k;

% Berechnung für Voluminösen Kern
term_geo_g = (R_gross + 0.5 * W_gross) / A_cross;
term_log_g = log10((D_vec_gross + R_gross) ./ (D_vec_gross - R_gross));
B_base_gross = mu_factor .* term_geo_g .* term_log_g;

%% 3. Berechnung der Flüsse (Strom anwenden)
% Kompakt (Blau)
Phi_klein_low = (B_base_klein * Ip_low) .* A_cross;   % 1000 A
Phi_klein_high = (B_base_klein * Ip_high) .* A_cross; % 2000 A

% Voluminös (Rot)
Phi_gross_low = (B_base_gross * Ip_low) .* A_cross;   % 1000 A
Phi_gross_high = (B_base_gross * Ip_high) .* A_cross; % 2000 A

%% 4. Plotting
f = figure('Name', 'Vergleich Geometrie und Strom', 'Color', 'w', 'Position', [100, 100, 1000, 700]);
hold on;

% --- Farben definieren ---
c_blau_hell = '#4DBEEE';   % Helles Cyan-Blau
c_blau_dunkel = '#00008B'; % Dunkles Marineblau
c_rot_hell = '#FF7F7F';    % Helles Lachsrot
c_rot_dunkel = '#8B0000';  % Dunkles Blutrot

% --- Plotten: Kompakter Kern (Blau) ---
% 1000 A
plot(D_vec_klein, Phi_klein_low * 1e6, 'LineWidth', 2, 'Color', c_blau_hell, ...
    'DisplayName', ['Kern R=' num2str(R_klein) 'm bei ' num2str(Ip_low) ' A']);

% 2000 A
plot(D_vec_klein, Phi_klein_high * 1e6, 'LineWidth', 2, 'Color', c_blau_dunkel, ...
    'DisplayName', ['Kern R=' num2str(R_klein) 'm bei ' num2str(Ip_high) ' A']);

% --- Plotten: Voluminöser Kern (Rot) ---
% 1000 A
plot(D_vec_gross, Phi_gross_low * 1e6, 'LineWidth', 2, 'Color', c_rot_hell, ...
    'DisplayName', ['Kern R=' num2str(R_gross) 'm bei ' num2str(Ip_low) ' A']);

% 2000 A
plot(D_vec_gross, Phi_gross_high * 1e6, 'LineWidth', 2, 'Color', c_rot_dunkel, ...
    'DisplayName', ['Kern R=' num2str(R_gross) 'm bei ' num2str(Ip_high) ' A']);


% --- Asymptoten (Physische Grenzen) ---
% Diese Linien nicht in die Legende aufnehmen ('HandleVisibility', 'off')
xline(R_klein, ':', 'Color', c_blau_dunkel, 'LineWidth', 1, 'HandleVisibility', 'off');
xline(R_gross, ':', 'Color', c_rot_dunkel, 'LineWidth', 1, 'HandleVisibility', 'off');

hold off;
grid on;

%% 5. Styling (Schwarz auf Weiß)
title('Einfluss von Kerngröße und Stromstärke auf den Streufluss', 'Color', 'k');
subtitle(['Vergleich bei ' num2str(Ip_low) ' A und ' num2str(Ip_high) ' A'], 'Color', 'k');

xlabel('Phasenabstand D [m]', 'Color', 'k');
ylabel('Magnetischer Fluss \Phi [\muWb]', 'Color', 'k');

% Achsen-Design für helle Umgebung
set(gca, 'Color', 'w');
set(gca, 'XColor', 'k');
set(gca, 'YColor', 'k');
set(gca, 'GridColor', 'k', 'GridAlpha', 0.2);
set(gca, 'FontSize', 12);

% Legende optimiert
lgd = legend('show', 'Location', 'northeast');
set(lgd, 'TextColor', 'k');
set(lgd, 'Color', 'w');
set(lgd, 'EdgeColor', 'k');
title(lgd, 'Konfiguration', 'Color', 'k');