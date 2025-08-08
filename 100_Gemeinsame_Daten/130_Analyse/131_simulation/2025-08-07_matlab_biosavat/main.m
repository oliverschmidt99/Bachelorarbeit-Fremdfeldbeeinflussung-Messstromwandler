% =========================================================================
% MATLAB-Skript zur Berechnung des magnetischen Feldes (B-Feld)
% von bis zu drei parallelen, geraden Leitern.
%
% Die Leiter verlaufen parallel zur z-Achse.
% Das Skript verwendet das Superpositionsprinzip und die Formel für
% einen unendlich langen, geraden Leiter.
%
% Dieses Skript wurde aktualisiert, um die Hilfsfunktionen
% printfENG, convertENG und saveMyPlot zu verwenden.
% =========================================================================

%% Skript initialisieren
clear;         % Löscht alle Variablen aus dem Workspace
clc;           % Löscht den Text im Command Window
close all;     % Schließt alle offenen Abbildungen

%% 1. Konstanten definieren
% -------------------------------------------------------------------------
mu0 = 4*pi*1e-7; % Magnetische Feldkonstante [Vs/Am]

%% 2. Eingabeparameter definieren
% -------------------------------------------------------------------------
% Definiere den Punkt P, an dem das Feld berechnet werden soll
P = [2, 4, -7]; % Format: [x, y, z] in Metern

% Definiere die Leiter. Jeder Leiter ist eine Zeile in der Matrix.
% Format: [x_Position, y_Position, Strom_I]
conductors = [
    0,  0,  2000;  % Leiter 1: Position (0,0), Strom +2000 A
    7,  0,  2000;  % Leiter 2: Position (7,0), Strom +2000 A
    2, -5, -1500;  % Leiter 3: Position (2,-5), Strom -1500 A (Gegenrichtung)
];

%% 3. Berechnung des Magnetfeldes
% -------------------------------------------------------------------------
B_total = [0, 0, 0]; % Initialisierung des Gesamt-Magnetfelds

% Temporäre Speicherung der einzelnen B-Felder für die Visualisierung
B_individual = zeros(size(conductors, 1), 3);

for i = 1:size(conductors, 1)
    L_pos = [conductors(i, 1), conductors(i, 2)];
    I = conductors(i, 3);
    
    r_rel = [P(1) - L_pos(1), P(2) - L_pos(2)];
    x_rel = r_rel(1);
    y_rel = r_rel(2);
    
    rho_squared = x_rel^2 + y_rel^2;
    
    if rho_squared == 0
        fprintf('Warnung: Punkt P liegt direkt auf Leiter %d. Feld ist unendlich und wird übersprungen.\n\n', i);
        B_conductor = [0, 0, 0];
    else
        faktor = (mu0 * I) / (2 * pi * rho_squared);
        B_conductor = faktor * [-y_rel, x_rel, 0];
    end
    
    B_individual(i, :) = B_conductor; % Speichere das Feld dieses Leiters
    B_total = B_total + B_conductor; % Addiere zum Gesamtfeld
end

%% 4. Berechnung des Betrags (Stärke) des Feldes
% -------------------------------------------------------------------------
B_magnitude = norm(B_total);

%% 5. Ergebnisse im Command Window ausgeben
% -------------------------------------------------------------------------
fprintf('==================== ERGEBNISSE ====================\n');
fprintf('Berechnung des B-Feldes am Punkt P(%g, %g, %g)\n\n', P(1), P(2), P(3));

fprintf('Verwendete Leiter:\n');
for i = 1:size(conductors, 1)
    fprintf('  Leiter %d: Position (%g, %g), Strom = %g A\n', i, conductors(i,1), conductors(i,2), conductors(i,3));
end
fprintf('\n');

% Ausgabe mit der benutzerdefinierten printfENG Funktion
fprintf('Gesamt-Magnetfeldvektor (B_ges):\n');
fprintf('  Bx = '); printfENG(B_total(1), '', 'T');
fprintf('  By = '); printfENG(B_total(2), '', 'T');
fprintf('  Bz = '); printfENG(B_total(3), '', 'T');
fprintf('\n');

fprintf('Stärke (Betrag) des Magnetfeldes |B_ges|:\n');
fprintf('  |B| = '); printfENG(B_magnitude, 'mu', 'T');
fprintf('====================================================\n');


%% 6. Grafische Darstellung des Ergebnisses (Optional)
% -------------------------------------------------------------------------
fig = figure('Name', 'Magnetfeld-Visualisierung', 'NumberTitle', 'off');
hold on;
grid on;
axis equal;
title(sprintf('B-Feld-Superposition am Punkt P(%g, %g)', P(1), P(2)));
xlabel('x-Position [m]');
ylabel('y-Position [m]');

% Zeichne die Leiter
for i = 1:size(conductors, 1)
    strom = conductors(i, 3);
    if strom > 0
        % Strom fließt aus der Ebene heraus (Punkt)
        plot(conductors(i, 1), conductors(i, 2), 'o', 'MarkerSize', 10, 'MarkerFaceColor', 'r', 'DisplayName', sprintf('Leiter %d (+I)', i));
    else
        % Strom fließt in die Ebene hinein (Kreuz)
        plot(conductors(i, 1), conductors(i, 2), 'x', 'MarkerSize', 10, 'MarkerFaceColor', 'b', 'LineWidth', 2, 'DisplayName', sprintf('Leiter %d (-I)', i));
    end
end

% Zeichne den Punkt P
plot(P(1), P(2), 'k*', 'MarkerSize', 8, 'DisplayName', 'Punkt P');

% Zeichne die einzelnen Feldvektoren skaliert, damit sie sichtbar sind
% Skalierungsfaktor für bessere Sichtbarkeit der Pfeile
max_magnitude = max(vecnorm(B_individual, 2, 2));
if max_magnitude == 0; max_magnitude = 1; end; % Verhindert Division durch Null
scale_factor = 2 / max_magnitude; % Passe den Faktor je nach Bedarf an

farben = ['g', 'm', 'c']; % Farben für die einzelnen Vektoren
for i = 1:size(B_individual, 1)
    quiver(P(1), P(2), B_individual(i,1)*scale_factor, B_individual(i,2)*scale_factor, 0, ...
        'Color', farben(i), 'LineWidth', 1.5, 'DisplayName', sprintf('B%d (skaliert)', i));
end

% Zeichne den resultierenden Gesamtvektor
quiver(P(1), P(2), B_total(1)*scale_factor, B_total(2)*scale_factor, 0, 'k', 'LineWidth', 2.5, 'DisplayName', 'B_{ges} (skaliert)');

legend('Location', 'bestoutside');
hold off;

%% 7. Speichern der Abbildung mit saveMyPlot
% -------------------------------------------------------------------------
% Erstellt einen Unterordner 'plots' und speichert die Grafik als PDF
saveMyPlot('B-Feld_Visualisierung.pdf', 'plots', fig);