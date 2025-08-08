function output_txt = b_field_cursor_update(obj, event_obj)
% Diese Funktion passt den Text an, der vom Data Cursor angezeigt wird.

% Abrufen der Klick-Position [x, y] in mm
pos_mm = event_obj.Position;
x_mm = pos_mm(1);
y_mm = pos_mm(2);

% Daten aus der Figure abrufen, die wir im Hauptskript gespeichert haben
fig = ancestor(event_obj.Target, 'figure');
data = get(fig, 'UserData');
[X, Y, Bx_total, By_total] = data{:};

% Umrechnung der Klick-Position von mm in Meter für die Interpolation
x_m = x_mm / 1000;
y_m = y_mm / 1000;

% 2D-Interpolation, um die Feldkomponenten am exakten Klickpunkt zu finden
Bx_clicked = interp2(X, Y, Bx_total, x_m, y_m);
By_clicked = interp2(X, Y, By_total, x_m, y_m);

% Betrag des B-Feldes berechnen
B_mag_clicked = sqrt(Bx_clicked^2 + By_clicked^2);

% Erstelle den Text, der im Tooltip angezeigt werden soll
% Die sprintf-Funktion formatiert den Text. \n sorgt für einen Zeilenumbruch.
output_txt = { ...
    sprintf('X: %.1f mm, Y: %.1f mm', x_mm, y_mm), ...
    '', ... % Eine Leerzeile für die Übersicht
    sprintf('B-Feld: %.4f mT', B_mag_clicked * 1000) ...
};

end