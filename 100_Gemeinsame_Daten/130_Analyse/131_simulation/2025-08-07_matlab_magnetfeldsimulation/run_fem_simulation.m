% =========================================================================
% MATLAB-Skript: FEM-Simulation eines Leiters mit Wandlerkern
% Finale, universelle Version, kompatibel mit sehr alten MATLABs
% Benötigt die Partial Differential Equation Toolbox(TM)
% =========================================================================

clear;
clc;
close all;

fprintf('Starte FEM-Simulation...\n');

%% 1. Geometrie-Definition (Rechteckiger Kern)
% Alle Dimensionen sind in Metern

% Außenmaße der Simulations-"Luftbox"
air_w = 0.2; % Breite
air_h = 0.15; % Höhe

% Außenmaße des Kerns
core_outer_w = 0.12;
core_outer_h = 0.08;

% Innenmaße des Kerns (Fenster)
core_inner_w = 0.06;
core_inner_h = 0.04;

% Maße des "Leiter"-Bereichs (die Wicklung L1)
conductor_w = 0.05;
conductor_h = 0.03;

% Definiere die 4 Rechtecke im decsg-Format
% Format: [3; 4; x-coords; y-coords]
R1 = [3; 4; -air_w / 2; air_w / 2; air_w / 2; -air_w / 2; -air_h / 2; -air_h / 2; air_h / 2; air_h / 2];
R2 = [3; 4; -core_outer_w / 2; core_outer_w / 2; core_outer_w / 2; -core_outer_w / 2; -core_outer_h / 2; -core_outer_h / 2; core_outer_h / 2; core_outer_h / 2];
R3 = [3; 4; -core_inner_w / 2; core_inner_w / 2; core_inner_w / 2; -core_inner_w / 2; -core_inner_h / 2; -core_inner_h / 2; core_inner_h / 2; core_inner_h / 2];
R4 = [3; 4; -conductor_w / 2; conductor_w / 2; conductor_w / 2; -conductor_w / 2; -conductor_h / 2; -conductor_h / 2; conductor_h / 2; conductor_h / 2];

% Füge sie zu einer einzigen Geometrie-Matrix zusammen
geom_matrix = [R1, R2, R3, R4];

% Definiere die booleschen Operationen
% (Luft - äußerer Kern) + (äußerer Kern - innerer Kern) + Leiter
sf = '(R1-R2)+(R2-R3)+R4';

% Erstelle die Namens-Matrix
ns = char('R1', 'R2', 'R3', 'R4')';

% Wandle diese Beschreibung in das finale Geometrie-Format um
geom = decsg(geom_matrix, sf, ns);

%% 2. Allgemeines PDE-Modell erstellen
model = createpde(1);
geometryFromEdges(model, geom);

%% 3. Physikalische Koeffizienten definieren
mu_0 = 4*pi*1e-7;
mu_r_core = 2500;
I = 200;

% KORREKTUR HIER: Berechne die Fläche des rechteckigen Leiters
conductor_area = conductor_w * conductor_h;
Jz = I / conductor_area; % Stromdichte J in z-Richtung

c_air = 1/mu_0;
c_core = 1/(mu_r_core * mu_0);
c_conductor = 1/mu_0;
a = 0;
f_conductor = Jz;

% Wende die Koeffizienten auf die jeweiligen Bereiche (Faces) an
specifyCoefficients(model, 'm', 0, 'd', 0, 'c', c_air,       'a', a, 'f', 0, 'Face', 1);
specifyCoefficients(model, 'm', 0, 'd', 0, 'c', c_core,      'a', a, 'f', 0, 'Face', 2);
specifyCoefficients(model, 'm', 0, 'd', 0, 'c', c_conductor, 'a', a, 'f', f_conductor, 'Face', 3);

%% 4. Randbedingungen festlegen
applyBoundaryCondition(model, 'dirichlet', 'Edge', 1:4, 'u', 0);

%% 5. Netz erstellen und Simulation lösen
fprintf('Erstelle das Berechnungsnetz...\n');
generateMesh(model, 'Hmax', 0.003);

fprintf('Löse die FEM-Simulation (das kann einen Moment dauern)...\n');
results = solvepde(model);
fprintf('Lösung fertig!\n');

%% 6. Ergebnisse visualisieren
fprintf('Visualisiere die Ergebnisse...\n');

% --- Manuelle Berechnung von B aus dem Potential A_z (u) ---
p = model.Mesh.Nodes;
t = model.Mesh.Elements;
u = results.NodalSolution;
[gradx_tri, grady_tri] = pdegrad(p, t, u);
Bx_tri = grady_tri;
By_tri = -gradx_tri;
B_norm_tri = sqrt(Bx_tri .^ 2 + By_tri .^ 2);
B_norm_nodes = pdeprtni(p, t, B_norm_tri);
Bx_nodes = pdeprtni(p, t, Bx_tri);
By_nodes = pdeprtni(p, t, By_tri);

% --- Plot erstellen ---
figure('Name', 'FEM-Simulationsergebnis (Finale Version)', 'Color', 'w');

% Plotte die magnetische Flussdichte B als farbige Kontur
pdeplot(model, 'XYData', B_norm_nodes, 'Contour', 'on', 'ColorMap', 'jet');
hold on;

% Plotte die magnetischen Feldlinien als Pfeile
% FINALE KORREKTUR: Horizontale Verkettung [Bx, By] statt [Bx; By]
pdeplot(model, 'FlowData', [Bx_nodes, By_nodes], 'FlowStyle', 'arrow');

% Plot-Formatierung
title('Ergebnis: Magnetische Flussdichte (B) in [T]');
xlabel('x-Position [m]');
ylabel('y-Position [m]');
axis equal;
colorbar;
hold off;

%% 7. Spezifische Ergebnisse auswerten
% Finde alle Knotenpunkte, die zur Geometrie des Kerns (Face 2) gehören
core_nodes = findNodes(model.Mesh, 'region', 'Face', 2);

% Extrahiere die B-Feld-Werte an genau diesen Knotenpunkten
B_values_in_core = B_norm_nodes(core_nodes);

% Berechne die Durchschnitts- und Maximalwerte
B_avg_core = mean(B_values_in_core);
B_max_core = max(B_values_in_core);

% Gib die Ergebnisse im Befehlsfenster aus
fprintf('\n--- Analyse des B-Feldes im Kern (Face 2) ---\n');
fprintf('Durchschnittliche Flussdichte: %.4f T\n', B_avg_core);
fprintf('Maximale Flussdichte:          %.4f T\n', B_max_core);
fprintf('-------------------------------------------\n');
