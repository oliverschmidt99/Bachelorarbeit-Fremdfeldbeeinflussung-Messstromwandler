import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- KONFIGURATION ---
DATA_FILE = "messdaten_db.parquet"

# Benutzerdefiniertes Farbschema (Kräftige Farben für Unterscheidbarkeit)
# Blau, Orange, Grün, Rot, Lila, Braun, Pink, Grau, Gelb, Türkis
COLOR_PALETTE = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]
PHASES = ["L1", "L2", "L3"]

st.set_page_config(
    page_title="Wandler Vergleich (Statisch)", layout="wide", page_icon="🖨️"
)

# --- CSS FÜR PDF DRUCK ---
# Versteckt Streamlit-Elemente beim Drucken (STRG+P) und macht den Hintergrund weiß
st.markdown(
    """
<style>
    @media print {
        .stSidebar, header, footer, .stButton { display: none !important; }
        .block-container { padding: 0 !important; }
        div[data-testid="stVerticalBlock"] { gap: 0 !important; }
    }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
</style>
""",
    unsafe_allow_html=True,
)


# --- FUNKTIONEN ---
@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    return pd.read_parquet(DATA_FILE)


def get_trumpet_limits(class_val):
    x = [1, 5, 20, 100, 120]
    if class_val == 0.2:
        y = [0.75, 0.35, 0.2, 0.2, 0.2]
    elif class_val == 0.5:
        y = [1.5, 1.5, 0.75, 0.5, 0.5]
    elif class_val == 1.0:
        y = [3.0, 1.5, 1.0, 1.0, 1.0]
    elif class_val == 3.0:
        y = [None, 3.0, 3.0, 3.0, 3.0]
    else:
        y = [1.5, 1.5, 0.75, 0.5, 0.5]
    y_neg = [-v if v is not None else None for v in y]
    return x, y, y_neg


# --- APP START ---
df = load_data()
if df is None:
    st.error("⚠️ Datei 'messdaten_db.parquet' fehlt. Bitte erst `precalc.py` ausführen.")
    st.stop()

# --- SIDEBAR EINSTELLUNGEN ---
st.sidebar.header("🎛️ Einstellungen")

# 1. Y-Achsen Limit (Statisch)
y_limit = st.sidebar.slider("Y-Achse Skalierung (+/- %)", 0.5, 5.0, 2.0, 0.1)

# 2. Genauigkeitsklasse
acc_class = st.sidebar.selectbox("Norm-Grenzen (Klasse)", [0.2, 0.5, 1.0, 3.0], index=1)

# 3. Wandler Auswahl (Multi-Select!)
st.sidebar.subheader("Vergleichsobjekte")
all_wandlers = sorted(df["wandler_key"].unique())
# Standardmäßig den ersten auswählen
sel_wandlers = st.sidebar.multiselect(
    "Wandler auswählen:", all_wandlers, default=all_wandlers[:1]
)

# 4. Positionen (Filtert basierend auf Wandler-Auswahl)
if sel_wandlers:
    relevant_pos = sorted(df[df["wandler_key"].isin(sel_wandlers)]["folder"].unique())
    sel_pos = st.sidebar.multiselect(
        "Positionen filtern:", relevant_pos, default=relevant_pos
    )
else:
    sel_pos = []

if not sel_wandlers or not sel_pos:
    st.info("Bitte wähle mindestens einen Wandler und eine Position.")
    st.stop()

# --- DATEN FILTERN & AUFBEREITEN ---
mask = (df["wandler_key"].isin(sel_wandlers)) & (df["folder"].isin(sel_pos))
df_sub = df[mask].copy()

if df_sub.empty:
    st.warning("Keine Daten für diese Kombination.")
    st.stop()

# Berechnungen (Absolut -> Prozent)
i_ideal = (df_sub["target_load"] / 100.0) * df_sub["nennstrom"]

# 1. DUT vs REF
df_sub["err_1"] = (
    (df_sub["val_dut_mean"] - df_sub["val_ref_mean"]) / df_sub["val_ref_mean"]
) * 100
df_sub["std_1"] = (df_sub["val_dut_std"] / df_sub["val_ref_mean"]) * 100

# 2. DUT vs SOLL
df_sub["err_2"] = ((df_sub["val_dut_mean"] - i_ideal) / i_ideal) * 100
df_sub["std_2"] = (df_sub["val_dut_std"] / i_ideal) * 100

# 3. REF vs SOLL
df_sub["err_3"] = ((df_sub["val_ref_mean"] - i_ideal) / i_ideal) * 100
df_sub["std_3"] = (df_sub["val_ref_std"] / i_ideal) * 100

# --- FARBEN ZUWEISEN ---
# Wir weisen jeder Kombination aus (Wandler + Position) eine feste Farbe zu
unique_traces = df_sub[["wandler_key", "folder"]].drop_duplicates()
trace_colors = {}
for idx, row in unique_traces.iterrows():
    key = f"{row['wandler_key']} | {row['folder']}"
    # Farbe aus Palette wählen (Modulo falls mehr Traces als Farben)
    trace_colors[key] = COLOR_PALETTE[len(trace_colors) % len(COLOR_PALETTE)]

# --- PLOTLY FIGUR ERSTELLEN ---
fig = make_subplots(
    rows=3,
    cols=3,
    shared_xaxes=True,
    shared_yaxes=True,
    vertical_spacing=0.08,
    horizontal_spacing=0.03,
    subplot_titles=(
        "<b>L1</b>: Prüfling vs. Quelle",
        "<b>L2</b>: Prüfling vs. Quelle",
        "<b>L3</b>: Prüfling vs. Quelle",
        "<b>L1</b>: Prüfling vs. Soll",
        "<b>L2</b>: Prüfling vs. Soll",
        "<b>L3</b>: Prüfling vs. Soll",
        "<b>L1</b>: Quelle vs. Soll",
        "<b>L2</b>: Quelle vs. Soll",
        "<b>L3</b>: Quelle vs. Soll",
    ),
)

lim_x, lim_y_p, lim_y_n = get_trumpet_limits(acc_class)
row_map = {1: ("err_1", "std_1"), 2: ("err_2", "std_2"), 3: ("err_3", "std_3")}

for row in [1, 2, 3]:
    err_col, std_col = row_map[row]

    for col, phase in enumerate(PHASES, start=1):
        # 1. DIN Grenzen (Hintergrund)
        fig.add_trace(
            go.Scatter(
                x=lim_x,
                y=lim_y_p,
                mode="lines",
                line=dict(color="black", width=1, dash="dash"),
                showlegend=False,
                hoverinfo="skip",
            ),
            row=row,
            col=col,
        )
        fig.add_trace(
            go.Scatter(
                x=lim_x,
                y=lim_y_n,
                mode="lines",
                line=dict(color="black", width=1, dash="dash"),
                showlegend=False,
                hoverinfo="skip",
            ),
            row=row,
            col=col,
        )

        # 2. Datenlinien zeichnen
        # Wir iterieren über die vorab definierten Traces, damit die Farben konsistent bleiben
        for trace_name, color in trace_colors.items():
            # Trace Name splitten um zu filtern
            w_key, fold = trace_name.split(" | ")

            # Daten für diesen speziellen Plot (Wandler + Position + Phase)
            mask = (
                (df_sub["wandler_key"] == w_key)
                & (df_sub["folder"] == fold)
                & (df_sub["phase"] == phase)
            )
            data = df_sub[mask].sort_values("target_load")

            if data.empty:
                continue

            # Legende nur im ersten Subplot anzeigen (oben links)
            show_leg = row == 1 and col == 1

            # Name für die Legende (kürzen wenn möglich)
            legend_name = trace_name

            fig.add_trace(
                go.Scatter(
                    x=data["target_load"],
                    y=data[err_col],
                    error_y=dict(
                        type="data",
                        array=data[std_col],
                        visible=True,
                        thickness=1.5,
                        width=4,
                    ),
                    mode="lines+markers",
                    line=dict(color=color, width=2),
                    marker=dict(size=6, symbol="circle"),
                    name=legend_name,
                    legendgroup=trace_name,  # Verbindet alle Linien dieses Wandlers über alle Plots
                    showlegend=show_leg,
                    hovertemplate=f"<b>{legend_name}</b><br>Last: %{{x}}%<br>Fehler: %{{y:.3f}}%<br>Std: %{{error_y.array:.3f}}%<extra></extra>",
                ),
                row=row,
                col=col,
            )

# --- LAYOUT FINESSE (Statisch & Sauber) ---
fig.update_layout(
    title_text="Vergleichsanalyse der Messgenauigkeit",
    template="plotly_white",
    height=1000,  # Groß genug für A4
    margin=dict(l=50, r=50, t=100, b=50),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="Black",
        borderwidth=1,
    ),
)

# Achsen fixieren (KEIN SCROLLEN)
fig.update_xaxes(
    range=[0, 125], fixedrange=True, showgrid=True, gridwidth=1, gridcolor="lightgrey"
)
fig.update_yaxes(
    range=[-y_limit, y_limit],
    fixedrange=True,
    showgrid=True,
    gridwidth=1,
    gridcolor="lightgrey",
)

# Achsenbeschriftungen
fig.update_yaxes(title_text="Fehler [%]", row=2, col=1)
fig.update_xaxes(title_text="Last [% I_nenn]", row=3, col=2)

# PDF Download Button Config
config = {
    "toImageButtonOptions": {
        "format": "pdf",  # PDF Export
        "filename": "Wandler_Vergleich",
        "height": 1123,  # A4 Höhe (px bei 96dpi ca, hier hochskaliert für Qualität)
        "width": 1587,  # A4 Breite
        "scale": 2,  # Hohe Qualität
    },
    "displayModeBar": True,
    "scrollZoom": False,  # Mausrad deaktivieren
    "displaylogo": False,
}

st.plotly_chart(fig, use_container_width=True, config=config)

st.markdown(
    """
---
**Anleitung zum Drucken:**
1. Klicke auf das **Kamera-Symbol** oben rechts im Diagramm, um genau diese Ansicht als **PDF** herunterzuladen.
2. Wähle links verschiedene Wandler aus, um sie direkt zu vergleichen (unterschiedliche Farben).
"""
)
