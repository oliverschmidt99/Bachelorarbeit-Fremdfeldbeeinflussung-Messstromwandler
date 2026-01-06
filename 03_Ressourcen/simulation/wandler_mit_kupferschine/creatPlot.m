% 1. Fläche definieren
A_mm2 = 10 * 30;       % Fläche in mm^2 (300 mm^2)
A_m2 = A_mm2 * 1e-6;   % Umrechnung in m^2 für die Formel (Phi = B * A)

% 2. Dateien einlesen
% MATLABs 'load' Befehl ignoriert Zeilen mit %, das passt also perfekt für deine Dateien
data_sym = load('wandler.sym.0.txt');
data_unsym = load('wandler.unsym.0.txt');

% 3. Spalten zuweisen (Spalte 1: Länge, Spalte 2: B-Feld)
len_sym = data_sym(:, 1);
B_sym = data_sym(:, 2);

len_unsym = data_unsym(:, 1);
B_unsym = data_unsym(:, 2);

% 4. Magnetischen Fluss berechnen (Phi = B * A)
Phi_sym = B_sym * A_m2;
Phi_unsym = B_unsym * A_m2;

% 5. Plotten
figure;
plot(len_sym, Phi_sym * 1e6, 'LineWidth', 1.5, 'DisplayName', 'Symmetrisch'); 
hold on;
plot(len_unsym, Phi_unsym * 1e6, 'LineWidth', 1.5, 'DisplayName', 'Unsymmetrisch');

% Beschriftung
xlabel('Länge [mm]');
ylabel('Magnetischer Fluss \Phi [\muWb]'); % Anzeige in Mikro-Weber
title('Verlauf des magnetischen Flusses');
legend show;
grid on;