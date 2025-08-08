% =========================================================================
% MATLAB-Skript: Simulation eines 3-Leiter-Systems (OOP-Ansatz für Wandler)
% =========================================================================
clear; clc; close all;
addpath('classes');

%% 1. Parameter & Konstanten
I_peak = 4000; f = 50; omega = 2*pi*f;
phase_angle_deg = 30; t = phase_angle_deg / (360 * f);

%% 2. Leiter und Wandler erstellen und zuweisen (NEUE, EINFACHE METHODE)

% Leiter erstellen
L1 = Leiter([-0.150, 0], 0);
L2 = Leiter([0,      0], -2*pi/3);
L3 = Leiter([0.150,  0], 2*pi/3);

% Den Leitern direkt ihre Wandler hinzufügen:
L1 = L1.addWandler(4000, 5, Buerde=2.0, Kernflaeche=300);
L2 = L2.addWandler(4000, 5, Buerde=2.0, Kernflaeche=300);
L3 = L3.addWandler(4000, 5, Buerde=2.0, Kernflaeche=300);

leiterArray = [L1, L2, L3];

%% 3. Systemzustand aktualisieren und analysieren
fprintf('Analyse bei Phasenwinkel: %d°\n', phase_angle_deg);
fprintf('--------------------------------------------------\n');

for i = 1:length(leiterArray)
    % Strom aktualisieren
    leiterArray(i) = leiterArray(i).updateCurrent(I_peak, omega, t);
    fprintf('Leiter L%d: Momentanstrom = %6.1f A\n', i, leiterArray(i).Momentanstrom);
    
    % Prüfen, ob dieser Leiter einen Wandler hat
    if ~isempty(leiterArray(i).Wandler)
        % Analyse-Methode des Wandler-Objekts aufrufen
        results = leiterArray(i).Wandler.analyse(I_peak, f);
        
        % Ergebnisse ausgeben
        fprintf('  > Wandler-Analyse (%s):\n', leiterArray(i).Wandler.RatioStr);
        fprintf('    Sekundärstrom (RMS): %.3f A\n', results.I_sek_rms);
        fprintf('    Benötigtes B-Feld:   %.3f T\n', results.B_peak_benoetigt);
        if results.isSaturated
            fprintf('    Status: ⚠️ SÄTTIGUNG\n');
        else
            fprintf('    Status: ✅ OK\n');
        end
    end
end
fprintf('--------------------------------------------------\n\n');

%% 4. B-Feld Berechnung & Visualisierung

% Gitter erstellen (ausreichend groß für alle drei Leiter)
[X, Y] = meshgrid(-0.3:0.02:0.3, -0.2:0.02:0.2); 

% Felder initialisieren
Bx_total = zeros(size(X));
By_total = zeros(size(Y));

% Felder aller Leiter überlagern (Superpositionsprinzip)
for i = 1:length(leiterArray)
    [Bx, By] = leiterArray(i).calculateField(X, Y);
    Bx_total = Bx_total + Bx;
    By_total = By_total + By;
end

% Plot-Daten vorbereiten
B_mag = sqrt(Bx_total.^2 + By_total.^2);
B_log_mag = log10(B_mag + eps); 
u = Bx_total ./ B_mag; 
v = By_total ./ B_mag;

% Plot erstellen und Handle (Adresse) der Figur speichern
fig = figure('Name', '3-Leiter-System (Interaktiv)', 'Color', 'w');

% Die berechneten Daten in der Figur speichern, damit der Data Cursor sie finden kann
set(fig, 'UserData', {X, Y, Bx_total, By_total});
hold on;

% Hintergrund (Feldstärke) & Vektorfeld (Richtung) zeichnen
pcolor(X*1000, Y*1000, B_log_mag);
shading interp; 
colormap(flipud(jet));
quiver(X*1000, Y*1000, u, v, 0.5, 'k');

% Visualisierung von Leitern und dem Wandlerkern
for i = 1:length(leiterArray)
    pos = leiterArray(i).Position * 1000;
    strom = leiterArray(i).Momentanstrom;
    
    % Zeichne den Wandlerkern nur für den mittleren Leiter (Index 2)
    if i == 2 % core_conductor_index
        viscircles(pos, 15, 'Color', [0.5 0.5 0.5], 'LineWidth', 1);
        viscircles(pos, 30, 'Color', [0.5 0.5 0.5], 'LineWidth', 1);
    end
    
    % Zeichne das Leitersymbol (⊙ oder ⊗)
    if strom >= 0
        symbol = '⊙'; textColor = 'white'; edgeColor = 'black';
    else
        symbol = '⊗'; textColor = 'black'; edgeColor = 'white';
    end
    plot(pos(1), pos(2), 'o', 'MarkerSize', 14, 'MarkerFaceColor', edgeColor, 'MarkerEdgeColor', 'k');
    text(pos(1), pos(2), symbol, 'FontSize', 14, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Color', textColor);
end

% Achsen und Beschriftungen formatieren
hold off; 
axis equal; 
grid off; 
box on;   
xlim([-320, 320]); 
ylim([-220, 220]);
title(sprintf('Feld des 3-Leiter-Systems bei %d°', phase_angle_deg), 'FontSize', 14);
xlabel('x-Position [mm]', 'FontSize', 12);
ylabel('y-Position [mm]', 'FontSize', 12);

% Farbleiste zur Interpretation der Feldstärke hinzufügen
c = colorbar;
ylabel(c, 'log_{10}(|B_{total}|) [T]', 'FontSize', 12, 'Rotation', -90, 'VerticalAlignment', 'bottom');

%% 5. Interaktiven Data Cursor einrichten
dcm_obj = datacursormode(fig);
set(dcm_obj, 'UpdateFcn', @b_field_cursor_update, 'Enable', 'on');