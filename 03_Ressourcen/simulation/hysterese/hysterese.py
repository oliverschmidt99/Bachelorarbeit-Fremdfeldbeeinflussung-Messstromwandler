import numpy as np
import matplotlib.pyplot as plt

def draw_hysteresis():
    # Daten generieren
    h = np.linspace(-3, 3, 500)
    
    # Hysterese Parameter
    width = 0.8
    scale = 2.0
    
    # Kurvenberechnung
    b_upper = np.tanh(h + width) * scale
    b_lower = np.tanh(h - width) * scale
    
    # Neukurve
    h_neu = np.linspace(0, 3, 250)
    b_neu = np.tanh(h_neu) * scale

    # Plot initialisieren
    fig, ax = plt.subplots(figsize=(12, 10))

    # ACHSEN KONFIGURATION
    # 'data', 0 zwingt die Achsen exakt auf die mathematische Null-Linie
    ax.spines['left'].set_position(('data', 0))
    ax.spines['bottom'].set_position(('data', 0))
    
    # Rahmen entfernen
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    
    # Achsenbeschriftung
    ax.set_xlabel('Feldstärke H', loc='right', fontsize=16, fontweight='bold')
    ax.set_ylabel('Flussdichte B', loc='top', fontsize=16, rotation=0, fontweight='bold')
    ax.xaxis.set_label_coords(1.0, 0.48)
    ax.yaxis.set_label_coords(0.55, 1.0)

    # LINIENPLOT
    linewidth_curve = 4
    ax.plot(h, b_upper, color='green', linewidth=linewidth_curve, label='Rücklauf')
    ax.plot(h, b_lower, color='green', linewidth=linewidth_curve, label='Hinlauf')
    ax.plot(h_neu, b_neu, color='blue', linestyle='--', linewidth=linewidth_curve, label='Neukurve')

    # Endpunkte verbinden
    ax.plot([h[0], h[0]], [b_upper[0], b_lower[0]], color='green', linewidth=linewidth_curve)
    ax.plot([h[-1], h[-1]], [b_upper[-1], b_lower[-1]], color='green', linewidth=linewidth_curve)

    # Wichtige Werte berechnen
    br_val = np.tanh(0 + width) * scale  # Schnittpunkt Y-Achse
    hc_val = -width                      # Schnittpunkt X-Achse (negativ)

    # PUNKTE MARKIEREN (Farben angepasst)
    
    # Y-Achse Punkte (Remanenz) -> Orange
    ax.scatter([0], [br_val], color='orange', s=100, zorder=10)
    ax.scatter([0], [-br_val], color='orange', s=100, zorder=10)
    
    # X-Achse Punkte (Koerzitivfeldstärke) -> Cyan
    ax.scatter([hc_val], [0], color='cyan', s=100, zorder=10)
    ax.scatter([-hc_val], [0], color='cyan', s=100, zorder=10)

    # PFEILE AUF KURVEN
    arrow_props = dict(arrowstyle='-|>', color='green', lw=4, mutation_scale=30)
    arrow_props_blue = dict(arrowstyle='-|>', color='blue', lw=4, mutation_scale=30)

    # Pfeil Hinlauf (unten)
    idx_l = 100
    ax.annotate('', xy=(h[idx_l], b_lower[idx_l]), xytext=(h[idx_l-10], b_lower[idx_l-10]), arrowprops=arrow_props)
    
    # Pfeil Rücklauf (oben)
    idx_u = 400
    ax.annotate('', xy=(h[idx_u], b_upper[idx_u]), xytext=(h[idx_u+10], b_upper[idx_u+10]), arrowprops=arrow_props)

    # Pfeil Neukurve
    idx_n = 150
    ax.annotate('', xy=(h_neu[idx_n], b_neu[idx_n]), xytext=(h_neu[idx_n-5], b_neu[idx_n-5]), arrowprops=arrow_props_blue)

    # BESCHRIFTUNGEN & MASSLINIEN

    # 1. Remanenz (Br) - Maßlinie
    ax.annotate('', xy=(hc_val, 0), xytext=(hc_val, br_val),
                arrowprops=dict(arrowstyle='<->', color='gray', lw=2))
    ax.text(hc_val-0.2, br_val/2, r'Remanenz $B_r$', fontsize=14, fontweight='bold', ha='right', va='center')
    # Hilfslinie
    ax.plot([0, hc_val], [br_val, br_val], color='gray', linestyle=':', linewidth=1)

    # 2. Koerzitivfeldstärke (Hc) - Maßlinie
    ax.annotate('', xy=(0, -0.3), xytext=(hc_val, -0.3),
                arrowprops=dict(arrowstyle='<->', color='gray', lw=2))
    ax.text(hc_val/2, -0.6, 'Koerzitiv\nfeldstärke', fontsize=14, fontweight='bold', ha='center', va='top')
    ax.text(hc_val/2, -0.15, r'$H_c$', fontsize=14, fontweight='bold', color='gray', ha='center')
    # Hilfslinie
    ax.plot([hc_val, hc_val], [0, -0.3], color='gray', linestyle=':', linewidth=1)

    # Weitere Beschriftungen
    ax.text(1.5, scale + 0.2, 'magnetische\nSättigung', fontsize=14, fontweight='bold')
    ax.text(-2.8, -scale - 0.5, 'magnetische\nSättigung', fontsize=14, fontweight='bold')

    ax.text(0.8, 0.5, 'Neukurve', color='black', fontsize=14, fontweight='bold')

    ax.text(1.8, -1.0, r'$\frac{\Delta B}{\Delta H} = \mu_r$', fontsize=18, fontweight='bold')
    

    # Layout
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-3.2, 3.5)
    ax.set_ylim(-2.8, 2.8)

    plt.savefig('hysterese_kurve_final_colors.pdf', bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    draw_hysteresis()