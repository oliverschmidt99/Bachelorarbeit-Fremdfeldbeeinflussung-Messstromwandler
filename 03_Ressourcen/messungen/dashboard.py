import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import io
import zipfile
import tempfile

# --- MATLAB ENGINE IMPORT VERSUCH ---
try:
    import matlab.engine

    MATLAB_AVAILABLE = True
except ImportError:
    MATLAB_AVAILABLE = False

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

# Blau (Parallel)
BLUES = [
    "#042a5c",
    "#084594",
    "#2171b5",
    "#4292c6",
    "#6baed6",
    "#9ecae1",
    "#c6dbef",
    "#000080",
    "#0000cd",
    "#4169e1",
    "#1e90ff",
    "#87cefa",
]
# Orange (Dreieck)
ORANGES = [
    "#4a1700",
    "#662506",
    "#993404",
    "#cc4c02",
    "#ec7014",
    "#fe9929",
    "#fec44f",
    "#d95f0e",
    "#f16913",
    "#ff7f0e",
    "#ffa500",
    "#ffbb78",
]
# Andere
OTHERS = [
    "#006400",
    "#2ca02c",
    "#7f7f7f",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#bcbd22",
    "#17becf",
]

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


def hex_to_rgb_matlab(hex_color):
    """Wandelt Hex '#RRGGBB' in MATLAB RGB [0-1, 0-1, 0-1] um"""
    hex_color = hex_color.lstrip("#")
    return [int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]


def create_single_phase_figure(
    df_sub, phase, acc_class, y_limit, color_map, show_err_bars, title_prefix=""
):
    """Erstellt Figur für Einzel-Export (Python/Kaleido)"""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3],
        subplot_titles=(f"Fehlerverlauf {phase}", f"Standardabweichung {phase}"),
    )

    lim_x, lim_y_p, lim_y_n = get_trumpet_limits(acc_class)

    # Trompete
    fig.add_trace(
        go.Scatter(
            x=lim_x,
            y=lim_y_p,
            mode="lines",
            line=dict(color="black", width=1, dash="dash"),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=lim_x,
            y=lim_y_n,
            mode="lines",
            line=dict(color="black", width=1, dash="dash"),
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    # Daten
    phase_data = df_sub[df_sub["phase"] == phase]

    # Sortieren
    grouped = []
    for name, group in phase_data.groupby(["wandler_key", "trace_id"]):
        sort_key = group.iloc[0]["trace_id"]
        if group.iloc[0]["dut_name"] in group.iloc[0]["wandler_key"]:
            legend_name = group.iloc[0]["wandler_key"]
        else:
            legend_name = (
                f"{group.iloc[0]['wandler_key']} | {group.iloc[0]['dut_name']}"
            )
        grouped.append((sort_key, legend_name, group, name))

    grouped.sort(key=lambda x: x[0])

    for _, legend_name, group, name_tuple in grouped:
        group = group.sort_values("target_load")
        full_key_for_color = f"{name_tuple[0]} - {name_tuple[1]}"
        color = color_map.get(full_key_for_color, "black")

        fig.add_trace(
            go.Scatter(
                x=group["target_load"],
                y=group["err_ratio"],
                mode="lines+markers",
                name=legend_name,
                line=dict(color=color, width=2),
                marker=dict(size=6),
                legendgroup=legend_name,
                showlegend=True,
            ),
            row=1,
            col=1,
        )

        if show_err_bars:
            fig.add_trace(
                go.Bar(
                    x=group["target_load"],
                    y=group["err_std"],
                    marker_color=color,
                    legendgroup=legend_name,
                    showlegend=False,
                ),
                row=2,
                col=1,
            )

    fig.update_layout(
        title=f"{title_prefix} - Phase {phase}",
        template="plotly_white",
        height=800,
        width=1100,
        margin=dict(t=80, b=100),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
    )
    fig.update_yaxes(range=[-y_limit, y_limit], title_text="Fehler [%]", row=1, col=1)
    fig.update_yaxes(title_text="StdAbw [%]", row=2, col=1)
    fig.update_xaxes(title_text="Last [% I_Nenn]", row=2, col=1)

    return fig


def generate_matlab_pdf(
    eng, df_sub, phase, acc_class, y_limit, color_map, title_prefix, temp_dir
):
    """
    Steuert MATLAB fern, um ein Diagramm zu erstellen.
    """
    lim_x, lim_y_p, lim_y_n = get_trumpet_limits(acc_class)

    # MATLAB Figure erstellen (unsichtbar)
    eng.eval(
        "f = figure('Visible', 'off', 'PaperType', 'A4', 'PaperOrientation', 'landscape');",
        nargout=0,
    )
    eng.eval("t = tiledlayout(2,1, 'TileSpacing', 'compact');", nargout=0)

    # --- PLOT 1: Fehler ---
    eng.eval("nexttile;", nargout=0)
    eng.eval("hold on;", nargout=0)
    eng.eval("grid on;", nargout=0)

    # Trompete
    eng.plot(
        matlab.double(lim_x),
        matlab.double(lim_y_p),
        "k--",
        "LineWidth",
        1.0,
        "HandleVisibility",
        "off",
        nargout=0,
    )
    eng.plot(
        matlab.double(lim_x),
        matlab.double(lim_y_n),
        "k--",
        "LineWidth",
        1.0,
        "HandleVisibility",
        "off",
        nargout=0,
    )

    # Daten vorbereiten
    phase_data = df_sub[df_sub["phase"] == phase]
    grouped = []
    for name, group in phase_data.groupby(["wandler_key", "trace_id"]):
        sort_key = group.iloc[0]["trace_id"]
        if group.iloc[0]["dut_name"] in group.iloc[0]["wandler_key"]:
            legend_name = group.iloc[0]["wandler_key"]
        else:
            legend_name = (
                f"{group.iloc[0]['wandler_key']} | {group.iloc[0]['dut_name']}"
            )
        grouped.append((sort_key, legend_name, group, name))
    grouped.sort(key=lambda x: x[0])

    for _, legend_name, group, name_tuple in grouped:
        group = group.sort_values("target_load")
        full_key_for_color = f"{name_tuple[0]} - {name_tuple[1]}"
        hex_col = color_map.get(full_key_for_color, "#000000")
        mat_col = hex_to_rgb_matlab(hex_col)

        x_val = group["target_load"].tolist()
        y_val = group["err_ratio"].tolist()

        # Plot Linie
        eng.plot(
            matlab.double(x_val),
            matlab.double(y_val),
            "-o",
            "Color",
            matlab.double(mat_col),
            "LineWidth",
            1.5,
            "DisplayName",
            legend_name,
            "MarkerSize",
            4,
            nargout=0,
        )

    eng.title(f"{title_prefix} - Phase {phase}", nargout=0)
    eng.ylabel("Fehler [%]", nargout=0)
    eng.ylim(matlab.double([-y_limit, y_limit]), nargout=0)
    # Legende
    eng.eval(
        "lgd = legend('Location', 'southoutside', 'Orientation', 'horizontal');",
        nargout=0,
    )
    eng.eval("lgd.NumColumns = 3;", nargout=0)

    # --- PLOT 2: StdAbw ---
    eng.eval("nexttile;", nargout=0)
    eng.eval("hold on;", nargout=0)
    eng.eval("grid on;", nargout=0)

    for _, legend_name, group, name_tuple in grouped:
        group = group.sort_values("target_load")
        full_key_for_color = f"{name_tuple[0]} - {name_tuple[1]}"
        hex_col = color_map.get(full_key_for_color, "#000000")
        mat_col = hex_to_rgb_matlab(hex_col)

        x_val = group["target_load"].tolist()
        y_std = group["err_std"].tolist()

        # Bar Chart tricksen mit 'bar'
        eng.bar(
            matlab.double(x_val),
            matlab.double(y_std),
            "FaceColor",
            matlab.double(mat_col),
            "EdgeColor",
            "none",
            "FaceAlpha",
            0.6,
            "DisplayName",
            legend_name,
            "BarWidth",
            1,
            nargout=0,
        )

    eng.ylabel("StdAbw [%]", nargout=0)
    eng.xlabel("Last [% I_Nenn]", nargout=0)

    # Speichern
    filename = f"Detail_{phase}_MATLAB.pdf"
    full_path = os.path.join(temp_dir, filename)
    eng.eval(f"exportgraphics(f, '{full_path}', 'ContentType', 'vector');", nargout=0)
    eng.eval("close(f);", nargout=0)

    return full_path


def clear_cache():
    if "zip_data" in st.session_state:
        del st.session_state["zip_data"]


# --- APP START ---
df = load_data()
if df is None:
    st.error(f"⚠️ Datei '{DATA_FILE}' fehlt. Bitte erst `precalc.py` ausführen.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("🎛️ Filter & Settings")

sync_axes = st.sidebar.checkbox(
    "🔗 Phasen synchronisieren", value=True, on_change=clear_cache
)
y_limit = st.sidebar.slider(
    "Y-Achse Zoom (+/- %)", 0.2, 5.0, 1.5, 0.1, on_change=clear_cache
)
acc_class = st.sidebar.selectbox(
    "Norm-Klasse", [0.2, 0.5, 1.0, 3.0], index=1, on_change=clear_cache
)
show_err_bars = st.sidebar.checkbox(
    "Fehlerbalken (StdAbw)", value=True, on_change=clear_cache
)

st.sidebar.markdown("---")

if "comparison_mode" in df.columns:
    comp_mode_disp = st.sidebar.radio(
        "Vergleichsgrundlage:",
        ["Messgerät (z.B. PAC1)", "Nennwert (Ideal)"],
        on_change=clear_cache,
    )
    comp_mode_val = "device_ref" if "Messgerät" in comp_mode_disp else "nominal_ref"
else:
    st.sidebar.warning("Datenbank veraltet.")
    comp_mode_val = None

st.sidebar.markdown("---")

available_currents = sorted(df["nennstrom"].unique())
sel_current = st.sidebar.selectbox(
    "1. Nennstrom:",
    available_currents,
    format_func=lambda x: f"{int(x)} A",
    on_change=clear_cache,
)

df_curr = df[df["nennstrom"] == sel_current]
available_wandlers = sorted(df_curr["wandler_key"].unique())
sel_wandlers = st.sidebar.multiselect(
    "2. Wandler / Messung:",
    available_wandlers,
    default=available_wandlers,
    on_change=clear_cache,
)

if not sel_wandlers:
    st.info("Bitte mindestens einen Wandler auswählen.")
    st.stop()

df_wandler_subset = df_curr[df_curr["wandler_key"].isin(sel_wandlers)]
available_duts = sorted(df_wandler_subset["dut_name"].unique())
sel_duts = st.sidebar.multiselect(
    "3. Geräte (DUTs) auswählen:",
    available_duts,
    default=available_duts,
    on_change=clear_cache,
)

if not sel_duts:
    st.stop()

# --- DATEN FILTERN ---
mask = (
    (df["nennstrom"] == sel_current)
    & (df["wandler_key"].isin(sel_wandlers))
    & (df["dut_name"].isin(sel_duts))
)
if comp_mode_val:
    mask = mask & (df["comparison_mode"] == comp_mode_val)

df_sub = df[mask].copy()

if comp_mode_val == "device_ref" and "ref_name" in df_sub.columns:
    df_sub = df_sub[df_sub["dut_name"] != df_sub["ref_name"]]

if df_sub.empty:
    st.warning("Keine Daten.")
    st.stop()

df_sub["err_ratio"] = (
    (df_sub["val_dut_mean"] - df_sub["val_ref_mean"]) / df_sub["val_ref_mean"]
) * 100
df_sub["err_std"] = (df_sub["val_dut_std"] / df_sub["val_ref_mean"]) * 100

# --- FARBEN ---
unique_keys = df_sub[["wandler_key", "trace_id"]].drop_duplicates()
unique_keys["folder_helper"] = unique_keys["trace_id"].apply(
    lambda x: x.split(" | ")[0]
)
unique_keys = unique_keys.sort_values(["folder_helper", "wandler_key"])

color_map = {}
b_idx, o_idx, x_idx = 0, 0, 0

for idx, row in unique_keys.iterrows():
    full_key = f"{row['wandler_key']} - {row['trace_id']}"
    folder_lower = row["trace_id"].lower()
    if "parallel" in folder_lower:
        col = BLUES[b_idx % len(BLUES)]
        b_idx += 1
    elif "dreieck" in folder_lower:
        col = ORANGES[o_idx % len(ORANGES)]
        o_idx += 1
    else:
        col = OTHERS[x_idx % len(OTHERS)]
        x_idx += 1
    color_map[full_key] = col

# --- SCREEN PLOT ---
ref_name_disp = "Einspeisung"
if not df_sub.empty and "ref_name" in df_sub.columns:
    ref_name_disp = (
        df_sub.iloc[0]["ref_name"] if comp_mode_val == "device_ref" else "Nennwert"
    )
main_title = f"{int(sel_current)} A | Ref: {ref_name_disp}"

fig = make_subplots(
    rows=2,
    cols=3,
    shared_xaxes=True,
    vertical_spacing=0.08,
    row_heights=[0.7, 0.3],
    subplot_titles=PHASES,
)
lim_x, lim_y_p, lim_y_n = get_trumpet_limits(acc_class)

for col_idx, phase in enumerate(PHASES, start=1):
    fig.add_trace(
        go.Scatter(
            x=lim_x,
            y=lim_y_p,
            mode="lines",
            line=dict(color="black", width=1, dash="dash"),
            showlegend=False,
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
            showlegend=False,
        ),
        row=1,
        col=col_idx,
    )

    phase_data = df_sub[df_sub["phase"] == phase]
    grouped_phase = []
    for name, group in phase_data.groupby(["wandler_key", "trace_id"]):
        grouped_phase.append((group.iloc[0]["trace_id"], name, group))
    grouped_phase.sort(key=lambda x: x[0])

    for _, name_tuple, group in grouped_phase:
        if group.iloc[0]["dut_name"] in group.iloc[0]["wandler_key"]:
            legend_name = group.iloc[0]["wandler_key"]
        else:
            legend_name = (
                f"{group.iloc[0]['wandler_key']} | {group.iloc[0]['dut_name']}"
            )

        group = group.sort_values("target_load")
        color = color_map.get(f"{name_tuple[0]} - {name_tuple[1]}", "black")
        show_leg = col_idx == 1

        fig.add_trace(
            go.Scatter(
                x=group["target_load"],
                y=group["err_ratio"],
                mode="lines+markers",
                name=legend_name,
                line=dict(color=color, width=2),
                legendgroup=legend_name,
                showlegend=show_leg,
            ),
            row=1,
            col=col_idx,
        )
        if show_err_bars:
            fig.add_trace(
                go.Bar(
                    x=group["target_load"],
                    y=group["err_std"],
                    marker_color=color,
                    legendgroup=legend_name,
                    showlegend=False,
                ),
                row=2,
                col=col_idx,
            )

fig.update_layout(
    title=f"Gesamtübersicht: {main_title}",
    template="plotly_white",
    height=800,
    margin=dict(t=80, b=100),
    legend=dict(orientation="h", y=-0.15, x=0.5),
)
if sync_axes:
    fig.update_yaxes(matches="y", row=1)
fig.update_yaxes(range=[-y_limit, y_limit], title_text="Fehler [%]", row=1, col=1)
if not sync_axes:
    fig.update_yaxes(range=[-y_limit, y_limit], row=1, col=2)
    fig.update_yaxes(range=[-y_limit, y_limit], row=1, col=3)
fig.update_yaxes(title_text="StdAbw [%]", row=2, col=1)
fig.update_xaxes(title_text="Last [% I_Nenn]", row=2, col=2)
st.plotly_chart(fig, use_container_width=True)

# --- EXPORT LOGIK ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 PDF Export")

# Engine Auswahl
engine_options = ["Python (Standard)"]
if MATLAB_AVAILABLE:
    engine_options.append("MATLAB (High-Quality)")

engine_mode = st.sidebar.selectbox("Render-Engine:", engine_options, index=0)

if st.sidebar.button("🔄 PDFs jetzt generieren", type="primary"):
    zip_buffer = io.BytesIO()

    # --- MATLAB MODUS ---
    if "MATLAB" in engine_mode:
        with st.spinner("Starte MATLAB Engine... (Dies dauert beim ersten Mal länger)"):
            try:
                eng = matlab.engine.start_matlab()
                with tempfile.TemporaryDirectory() as temp_dir:
                    with zipfile.ZipFile(
                        zip_buffer, "a", zipfile.ZIP_DEFLATED, False
                    ) as zip_file:

                        # Einzelne Phasen via MATLAB rendern
                        for phase in PHASES:
                            pdf_path = generate_matlab_pdf(
                                eng,
                                df_sub,
                                phase,
                                acc_class,
                                y_limit,
                                color_map,
                                main_title,
                                temp_dir,
                            )
                            zip_file.write(
                                pdf_path,
                                f"Detail_{phase}_{int(sel_current)}A_MATLAB.pdf",
                            )

                    st.success("✅ MATLAB-Diagramme generiert!")
                eng.quit()
            except Exception as e:
                st.error(f"Fehler mit MATLAB: {e}")
                st.stop()

    # --- PYTHON MODUS ---
    else:
        with st.spinner("Erstelle Diagramme mit Python..."):
            with zipfile.ZipFile(
                zip_buffer, "a", zipfile.ZIP_DEFLATED, False
            ) as zip_file:
                # 1. Zusammenfassung (Screenshot Main Fig)
                img_bytes = fig.to_image(format="pdf", width=1169, height=827)
                zip_file.writestr(f"Zusammenfassung_{int(sel_current)}A.pdf", img_bytes)
                # 2. Einzelne Phasen
                for phase in PHASES:
                    fig_single = create_single_phase_figure(
                        df_sub,
                        phase,
                        acc_class,
                        y_limit,
                        color_map,
                        show_err_bars,
                        title_prefix=main_title,
                    )
                    img_bytes_single = fig_single.to_image(
                        format="pdf", width=1169, height=827
                    )
                    zip_file.writestr(
                        f"Detail_{phase}_{int(sel_current)}A.pdf", img_bytes_single
                    )
            st.success("✅ Fertig!")

    st.session_state["zip_data"] = zip_buffer.getvalue()

if "zip_data" in st.session_state:
    suffix = "MATLAB" if "MATLAB" in engine_mode else "Python"
    st.sidebar.download_button(
        label=f"💾 ZIP herunterladen ({suffix})",
        data=st.session_state["zip_data"],
        file_name=f"Report_{int(sel_current)}A_{suffix}.zip",
        mime="application/zip",
    )
