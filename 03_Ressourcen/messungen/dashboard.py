import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- KONFIGURATION ---
DATA_FILE = "messdaten_db.parquet"

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

st.set_page_config(page_title="Wandler Dashboard", layout="wide", page_icon="📈")

# --- CSS ---
st.markdown(
    """
<style>
    @media print {
        .stSidebar, header, footer, .stButton { display: none !important; }
        .block-container { padding: 0 !important; }
    }
    .block-container { padding-top: 1rem; }
</style>
""",
    unsafe_allow_html=True,
)


# --- FUNKTIONEN ---
@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    df = pd.read_parquet(DATA_FILE)

    # Trace ID erstellen
    if "dut_name" in df.columns:
        df["trace_id"] = df["folder"] + " | " + df["dut_name"].astype(str)
    else:
        df["trace_id"] = df["folder"]

    return df


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


# --- APP ---
df = load_data()
if df is None:
    st.error(f"⚠️ Datei '{DATA_FILE}' fehlt. Bitte erst `precalc.py` ausführen.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("🎛️ Filter & Settings")

# Settings
y_limit = st.sidebar.slider("Y-Achse Zoom (+/- %)", 0.2, 5.0, 1.5, 0.1)
acc_class = st.sidebar.selectbox("Norm-Klasse", [0.2, 0.5, 1.0, 3.0], index=1)
show_err_bars = st.sidebar.checkbox("Fehlerbalken (StdAbw)", value=True)

st.sidebar.markdown("---")

# --- NEU: VERGLEICHSMODUS ---
# Wir prüfen, ob die Spalte existiert (Kompatibilität mit alten DBs)
if "comparison_mode" in df.columns:
    comp_mode_disp = st.sidebar.radio(
        "Vergleichsgrundlage:", ["Messgerät (z.B. PAC1)", "Nennwert (Ideal)"]
    )
    # Mapping auf Datenbank-Werte
    comp_mode_val = "device_ref" if "Messgerät" in comp_mode_disp else "nominal_ref"
else:
    st.sidebar.warning("Datenbank veraltet. Bitte `precalc.py` neu ausführen.")
    comp_mode_val = None

st.sidebar.markdown("---")

# 1. Nennstrom
available_currents = sorted(df["nennstrom"].unique())
sel_current = st.sidebar.selectbox(
    "1. Nennstrom:", available_currents, format_func=lambda x: f"{int(x)} A"
)

# 2. Wandler
df_curr = df[df["nennstrom"] == sel_current]
available_wandlers = sorted(df_curr["wandler_key"].unique())
sel_wandlers = st.sidebar.multiselect(
    "2. Wandler / Messung:", available_wandlers, default=available_wandlers
)

if not sel_wandlers:
    st.info("Bitte mindestens einen Wandler auswählen.")
    st.stop()

# --- DATEN FILTERN ---
mask = (df["nennstrom"] == sel_current) & (df["wandler_key"].isin(sel_wandlers))

# Filter nach Modus (falls vorhanden)
if comp_mode_val:
    mask = mask & (df["comparison_mode"] == comp_mode_val)

df_sub = df[mask].copy()

if df_sub.empty:
    st.warning("Keine Daten für diese Auswahl (evtl. `precalc.py` neu starten?).")
    st.stop()

# Berechnungen
df_sub["err_ratio"] = (
    (df_sub["val_dut_mean"] - df_sub["val_ref_mean"]) / df_sub["val_ref_mean"]
) * 100
df_sub["err_std"] = (df_sub["val_dut_std"] / df_sub["val_ref_mean"]) * 100

# Farben zuweisen
unique_keys = df_sub[["wandler_key", "trace_id"]].drop_duplicates()
color_map = {}
for idx, row in unique_keys.iterrows():
    name = f"{row['wandler_key']} - {row['trace_id']}"
    color_map[name] = COLOR_PALETTE[idx % len(COLOR_PALETTE)]

# --- PLOT ---
fig = make_subplots(
    rows=2,
    cols=3,
    shared_xaxes=True,
    vertical_spacing=0.08,
    row_heights=[0.7, 0.3],
    subplot_titles=("Phase L1", "Phase L2", "Phase L3"),
)

lim_x, lim_y_p, lim_y_n = get_trumpet_limits(acc_class)

for col_idx, phase in enumerate(PHASES, start=1):
    # 1. Trompete (Norm)
    fig.add_trace(
        go.Scatter(
            x=lim_x,
            y=lim_y_p,
            mode="lines",
            line=dict(color="black", width=1, dash="dash"),
            hoverinfo="skip",
        ),
        row=1,
        col=col_idx,
    )
    fig.add_trace(
        go.Scatter(
            x=lim_x,
            y=lim_y_n,
            mode="lines",
            line=dict(color="black", width=1, dash="dash"),
            hoverinfo="skip",
        ),
        row=1,
        col=col_idx,
    )

    # 2. Daten
    phase_data = df_sub[df_sub["phase"] == phase]

    # Gruppieren pro Trace
    for name, group in phase_data.groupby(["wandler_key", "trace_id"]):
        full_name = f"{name[0]} - {name[1]}"
        group = group.sort_values("target_load")

        color = color_map.get(full_name, "black")

        # Nur beim mittleren Plot die Legende anzeigen (Cleaner)
        show_leg = col_idx == 1

        # Linie Oben (Fehler)
        fig.add_trace(
            go.Scatter(
                x=group["target_load"],
                y=group["err_ratio"],
                mode="lines+markers",
                name=full_name,
                line=dict(color=color, width=2),
                marker=dict(size=6),
                legendgroup=full_name,
                showlegend=show_leg,
                hovertemplate="<b>%{text}</b><br>Last: %{x}%<br>Fehler: %{y:.3f}%<extra></extra>",
                text=[full_name] * len(group),
            ),
            row=1,
            col=col_idx,
        )

        # Balken Unten (StdAbw)
        if show_err_bars:
            fig.add_trace(
                go.Bar(
                    x=group["target_load"],
                    y=group["err_std"],
                    marker_color=color,
                    legendgroup=full_name,
                    showlegend=False,
                    hovertemplate="Std: %{y:.4f}%<extra></extra>",
                ),
                row=2,
                col=col_idx,
            )

# Info für Titel
ref_info = (
    "Referenz: Einspeisung"
    if comp_mode_val == "device_ref"
    else "Referenz: Nennwert (Ideal)"
)

fig.update_layout(
    title=f"Genauigkeitsanalyse {int(sel_current)} A (Klasse {acc_class}) | {ref_info}",
    template="plotly_white",
    height=800,
    margin=dict(t=80, b=100),
    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
)

fig.update_yaxes(range=[-y_limit, y_limit], title_text="Fehler [%]", row=1, col=1)
fig.update_yaxes(title_text="StdAbw [%]", row=2, col=1)
fig.update_xaxes(title_text="Last [% I_Nenn]", row=2, col=2)

st.plotly_chart(fig, use_container_width=True)
