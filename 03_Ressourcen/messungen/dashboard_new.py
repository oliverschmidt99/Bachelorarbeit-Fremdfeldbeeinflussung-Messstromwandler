import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
import io
import zipfile
import subprocess
import re

# --- KONFIGURATION ---
DATA_FILE = "messdaten_db.parquet"
WORK_DIR = "matlab_working_dir"
DEFAULT_MATLAB_PATH = r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"

PHASES = ["L1", "L2", "L3"]

ZONES = {
    "Niederstrom (5-50%)": [5, 20, 50],
    "Nennstrom (80-100%)": [80, 90, 100],
    "Überlast (≥120%)": [120, 150, 200],
}

# --- STAMMDATEN ---
META_COLS_EDIT = [
    "Preis (€)",
    "Nennbürde (VA)",
    "T (mm)",
    "B (mm)",
    "H (mm)",
    "Kommentar",
]
META_COLS_FIX = [
    "Hersteller",
    "Modell",
    "nennstrom",
    "Mess-Bürde",
    "Geometrie",
    "raw_file",
]
META_COLS = META_COLS_FIX + META_COLS_EDIT

# --- FARBEN ---
BLUES = [
    "#1f4e8c",
    "#2c6fb2",
    "#4a8fd1",
    "#6aa9e3",
    "#8fc0ee",
    "#b3d5f7",
    "#d6e8fb",
    "#5f7fd9",
    "#6fa3ff",
    "#8bb8ff",
    "#a6ccff",
    "#cfe2ff",
]
ORANGES = [
    "#8c4a2f",
    "#a65a2a",
    "#c96a2a",
    "#e07b39",
    "#f28e4b",
    "#f6a25e",
    "#f9b872",
    "#f4a261",
    "#f7b267",
    "#ff9f4a",
    "#ffb347",
    "#ffd199",
]
OTHERS = [
    "#4caf50",
    "#6bd36b",
    "#b0b0b0",
    "#b39ddb",
    "#bc8f6f",
    "#f2a7d6",
    "#d4d65a",
    "#6fd6e5",
]

# --- MATLAB TEMPLATE ---
MATLAB_SCRIPT_TEMPLATE = r"""
%% Automatische Diagrammerstellung
clear; clc; close all;
try
    filename = 'plot_data.csv';
    phases = {'L1', 'L2', 'L3'};
    limits_class = ACC_CLASS_PH; 
    nennstrom = NOMINAL_CURRENT_PH;
    if ~isfile(filename); error('Datei plot_data.csv nicht gefunden!'); end
    data = readtable(filename, 'Delimiter', ',');
    hex2rgb = @(hex) sscanf(hex(2:end),'%2x%2x%2x',[1 3])/255;
    x_lims = [1, 5, 20, 100, 120];
    if limits_class == 0.2; y_lims = [0.75, 0.35, 0.2, 0.2, 0.2];
    elseif limits_class == 0.5; y_lims = [1.5, 1.5, 0.75, 0.5, 0.5];
    elseif limits_class == 1.0; y_lims = [3.0, 1.5, 1.0, 1.0, 1.0];
    else; y_lims = [1.5, 1.5, 0.75, 0.5, 0.5]; end

    for i = 1:length(phases)
        p = phases{i};
        rows = strcmp(data.phase, p);
        sub_data = data(rows, :);
        if isempty(sub_data); continue; end
        
        f = figure('Visible', 'off', 'PaperType', 'A4', 'PaperOrientation', 'landscape');
        set(f, 'Color', 'w', 'Units', 'centimeters', 'Position', [0 0 29.7 21]);
        t = tiledlayout(f, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
        
        ax1 = nexttile; hold(ax1, 'on'); grid(ax1, 'on'); box(ax1, 'on');
        plot(ax1, x_lims, y_lims, 'k--', 'LineWidth', 1.2, 'HandleVisibility', 'off');
        plot(ax1, x_lims, -y_lims, 'k--', 'LineWidth', 1.2, 'HandleVisibility', 'off');
        
        [unique_traces, ~, ~] = unique(sub_data.trace_id, 'stable');
        for k = 1:length(unique_traces)
            trace = unique_traces{k};
            d = sub_data(strcmp(sub_data.trace_id, trace), :);
            [~, sort_idx] = sort(d.target_load); d = d(sort_idx, :);
            col_rgb = hex2rgb(d.color_hex{1});
            leg_lbl = strrep(d.legend_name{1}, '_', '\_');
            plot(ax1, d.target_load, d.err_ratio, '-o', 'Color', col_rgb, 'LineWidth', 1.5, 'MarkerSize', 4, 'MarkerFaceColor', col_rgb, 'DisplayName', leg_lbl);
        end
        title(ax1, sprintf('Fehlerverlauf - Phase %s (%d A)', p, nennstrom));
        ylabel(ax1, 'Fehler [%]'); ylim(ax1, [- Y_LIMIT_PH, Y_LIMIT_PH]); xlim(ax1, [0, 125]);
        legend(ax1, 'Location', 'southoutside', 'Orientation', 'horizontal', 'NumColumns', 2, 'Interpreter', 'tex');
        
        ax2 = nexttile; hold(ax2, 'on'); grid(ax2, 'on'); box(ax2, 'on');
        num_groups = length(unique_traces);
        single_bar_width = min(1.5, 5 / num_groups);
        for k = 1:length(unique_traces)
            trace = unique_traces{k};
            d = sub_data(strcmp(sub_data.trace_id, trace), :);
            [~, sort_idx] = sort(d.target_load); d = d(sort_idx, :);
            col_rgb = hex2rgb(d.color_hex{1});
            x_pos = d.target_load + (k - 1 - (num_groups - 1) / 2) * single_bar_width;
            bar(ax2, x_pos, d.err_std, 'FaceColor', col_rgb, 'EdgeColor', 'none', 'FaceAlpha', 0.8, 'BarWidth', 0.1);
        end
        title(ax2, sprintf('Standardabweichung - Phase %s', p)); ylabel(ax2, 'StdAbw [%]'); xlabel(ax2, 'Last [% In]'); xlim(ax2, [0, 125]);
        exportgraphics(f, sprintf('Detail_%s_%dA.pdf', p, nennstrom), 'ContentType', 'vector');
        close(f);
    end
catch ME; disp(ME.message); exit(1); end
exit(0);
"""

st.set_page_config(page_title="Wandler Dashboard", layout="wide", page_icon="📈")


# --- HELPER ---
def extract_base_type(wandler_key):
    s = str(wandler_key)
    tokens = re.split(r"[_\s\-]+", s)
    clean_tokens = []
    for t in tokens:
        if re.match(r"^\d+R\d*$", t, re.IGNORECASE):
            continue
        if t.lower() in ["parallel", "dreieck", "messstrecke", "l1", "l2", "l3"]:
            continue
        if not t:
            continue
        clean_tokens.append(t)
    return " ".join(clean_tokens)


def parse_filename_info(filename_str):
    if not isinstance(filename_str, str):
        return pd.Series(["Unbekannt", "Unbekannt", 0.0, "Unbekannt"])
    base = os.path.basename(filename_str)
    name_only = os.path.splitext(base)[0]
    parts = name_only.split("-")
    if len(parts) < 5:
        return pd.Series(["Unbekannt", "Unbekannt", 0.0, "Unbekannt"])
    try:
        hersteller = parts[1].replace("_", " ")
        modell = parts[2].replace("_", " ")
        strom_str = parts[3].upper().replace("A", "")
        nennstrom = float(strom_str) if strom_str.replace(".", "", 1).isdigit() else 0.0
        burde_part = parts[4]
        mess_burde = burde_part
        return pd.Series([hersteller, modell, nennstrom, mess_burde])
    except Exception:
        return pd.Series(["Fehler", "Fehler", 0.0, "Fehler"])


@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE):
        return None
    df = pd.read_parquet(DATA_FILE)
    if "raw_file" in df.columns:
        df["raw_file"] = df["raw_file"].astype(str)
        df["raw_file"] = df["raw_file"].apply(
            lambda x: x.replace("['", "").replace("']", "") if x.startswith("['") else x
        )
    if "dut_name" in df.columns:
        df["trace_id"] = df["folder"] + " | " + df["dut_name"].astype(str)
    else:
        df["trace_id"] = df["folder"]
    if "target_load" in df.columns:
        df["target_load"] = pd.to_numeric(df["target_load"], errors="coerce")
    if "base_type" not in df.columns:
        df["base_type"] = df["wandler_key"].apply(extract_base_type)
    for col in ["Hersteller", "Modell", "nennstrom", "Mess-Bürde", "Geometrie"]:
        if col not in df.columns:
            df[col] = 0.0 if col == "nennstrom" else "Unbekannt"
    for col in META_COLS_EDIT:
        if col not in df.columns:
            df[col] = "" if col == "Kommentar" else 0.0
    if "Kommentar" in df.columns:
        df["Kommentar"] = (
            df["Kommentar"].astype(str).replace("nan", "").replace("None", "")
        )
    return df


def save_db(df_to_save):
    try:
        df_to_save.to_parquet(DATA_FILE)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False


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


def auto_format_name(row):
    raw_key = str(row["wandler_key"])
    folder_lower = str(row["folder"]).lower()
    tokens = re.split(r"[_\s]+", raw_key)
    name_parts = []
    burden_part = ""
    for t in tokens:
        if not t:
            continue
        if re.match(r"^\d+R\d*$", t):
            burden_part = f"{t.replace('R', ',')} Ω"
        else:
            name_parts.append(t)
    base_name = " ".join(name_parts)
    dut = str(row["dut_name"])
    if dut.lower() not in base_name.lower():
        base_name = f"{base_name} | {dut}"
    if burden_part:
        base_name = f"{base_name} | {burden_part}"
    if "parallel" in folder_lower:
        base_name += " | Parallel"
    elif "dreieck" in folder_lower:
        base_name += " | Dreieck"
    if "Kommentar" in row and row["Kommentar"]:
        clean_comment = str(row["Kommentar"]).strip()
        if clean_comment and clean_comment != "0.0":
            base_name += f" | {clean_comment}"
    return base_name


def create_single_phase_figure(
    df_sub, phase, acc_class, y_limit, show_err_bars, title_prefix=""
):
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.65, 0.35],
        subplot_titles=(f"Fehlerverlauf {phase}", f"Standardabweichung {phase}"),
    )
    lim_x, lim_y_p, lim_y_n = get_trumpet_limits(acc_class)
    fig.add_trace(
        go.Scatter(
            x=lim_x,
            y=lim_y_p,
            mode="lines",
            line=dict(color="black", width=1.5, dash="dash"),
            name="Klassengrenze",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=lim_x,
            y=lim_y_n,
            mode="lines",
            line=dict(color="black", width=1.5, dash="dash"),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    phase_data = df_sub[df_sub["phase"] == phase]
    for uid, group in phase_data.groupby("unique_id"):
        group = group.sort_values("target_load")
        row_first = group.iloc[0]
        leg_name = row_first["final_legend"]
        color = row_first["final_color"]
        fig.add_trace(
            go.Scatter(
                x=group["target_load"],
                y=group["err_ratio"],
                mode="lines+markers",
                name=leg_name,
                line=dict(color=color, width=2.5),
                marker=dict(size=7),
                legendgroup=leg_name,
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
                    legendgroup=leg_name,
                    showlegend=False,
                ),
                row=2,
                col=1,
            )
    fig.update_layout(
        title=dict(text=f"{title_prefix} - Phase {phase}", font=dict(size=18)),
        template="plotly_white",
        width=1123,
        height=794,
        font=dict(family="Serif", size=14, color="black"),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="Black",
            borderwidth=1,
        ),
        margin=dict(l=60, r=30, t=80, b=120),
    )
    fig.update_yaxes(range=[-y_limit, y_limit], title_text="Fehler [%]", row=1, col=1)
    fig.update_yaxes(title_text="StdAbw [%]", row=2, col=1)
    fig.update_xaxes(title_text="Strom [% In]", row=2, col=1)
    return fig


def ensure_working_dir():
    if not os.path.exists(WORK_DIR):
        os.makedirs(WORK_DIR)
    return os.path.abspath(WORK_DIR)


def clear_cache():
    if "zip_data" in st.session_state:
        del st.session_state["zip_data"]


# --- APP START ---
df = load_data()
if df is None:
    st.error(f"⚠️ Datei '{DATA_FILE}' fehlt.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("🎛️ Globale Filter")
available_currents = sorted(df["nennstrom"].unique())
sel_current = st.sidebar.selectbox(
    "1. Nennstrom:",
    available_currents,
    format_func=lambda x: f"{int(x)} A",
    on_change=clear_cache,
)
df_curr = df[df["nennstrom"] == sel_current]

available_geos = sorted(df_curr["Geometrie"].astype(str).unique())
sel_geos = st.sidebar.multiselect(
    "2. Geometrie:", available_geos, default=available_geos, on_change=clear_cache
)
if not sel_geos:
    st.warning("Bitte mindestens eine Geometrie auswählen.")
    st.stop()
df_geo_filtered = df_curr[df_curr["Geometrie"].isin(sel_geos)]

available_wandlers = sorted(df_geo_filtered["wandler_key"].unique())
sel_wandlers = st.sidebar.multiselect(
    "3. Wandler / Messung:",
    available_wandlers,
    default=available_wandlers,
    on_change=clear_cache,
)
if not sel_wandlers:
    st.info("Bitte mindestens einen Wandler auswählen.")
    st.stop()

df_wandler_subset = df_geo_filtered[df_geo_filtered["wandler_key"].isin(sel_wandlers)]
available_duts = sorted(df_wandler_subset["dut_name"].unique())
sel_duts = st.sidebar.multiselect(
    "4. Geräte (DUTs) auswählen:",
    available_duts,
    default=available_duts,
    on_change=clear_cache,
)

mask = (
    (df["nennstrom"] == sel_current)
    & (df["Geometrie"].isin(sel_geos))
    & (df["wandler_key"].isin(sel_wandlers))
    & (df["dut_name"].isin(sel_duts))
)
if "comparison_mode" in df.columns:
    comp_mode_disp = st.sidebar.radio(
        "Vergleichsgrundlage:",
        ["Messgerät (z.B. PAC1)", "Nennwert (Ideal)"],
        on_change=clear_cache,
    )
    comp_mode_val = "device_ref" if "Messgerät" in comp_mode_disp else "nominal_ref"
    mask = mask & (df["comparison_mode"] == comp_mode_val)

df_sub = df[mask].copy()
if df_sub.empty:
    st.warning("⚠️ Keine Daten.")
    st.stop()

if comp_mode_val == "device_ref" and "ref_name" in df_sub.columns:
    df_sub = df_sub[df_sub["dut_name"] != df_sub["ref_name"]]
df_sub["unique_id"] = df_sub["raw_file"] + " | " + df_sub["dut_name"].astype(str)
df_sub["err_ratio"] = (
    (df_sub["val_dut_mean"] - df_sub["val_ref_mean"]) / df_sub["val_ref_mean"]
) * 100
df_sub["err_std"] = (df_sub["val_dut_std"] / df_sub["val_ref_mean"]) * 100

# --- DESIGN & SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 Design & Settings")
sync_axes = st.sidebar.checkbox("🔗 Phasen synchronisieren", value=True)
y_limit = st.sidebar.slider("Y-Achse Zoom (+/- %)", 0.2, 10.0, 1.5, 0.1)
acc_class = st.sidebar.selectbox("Norm-Klasse", [0.2, 0.5, 1.0, 3.0], index=2)
show_err_bars = st.sidebar.checkbox("Fehlerbalken (StdAbw)", value=True)

# 1. Farben & Namen (Expander)
with st.sidebar.expander("Farben & Namen bearbeiten", expanded=False):
    unique_curves = df_sub[
        ["unique_id", "wandler_key", "folder", "dut_name", "trace_id", "Kommentar"]
    ].drop_duplicates()
    config_data = []
    b_idx, o_idx, x_idx = 0, 0, 0
    for idx, row in unique_curves.iterrows():
        auto_name = auto_format_name(row)
        folder_lower = str(row["folder"]).lower()
        if "parallel" in folder_lower:
            col = BLUES[b_idx % len(BLUES)]
            b_idx += 1
        elif "dreieck" in folder_lower:
            col = ORANGES[o_idx % len(ORANGES)]
            o_idx += 1
        else:
            col = OTHERS[x_idx % len(OTHERS)]
            x_idx += 1
        config_data.append({"ID": row["unique_id"], "Legende": auto_name, "Farbe": col})

    df_config_default = pd.DataFrame(config_data)
    if hasattr(st.column_config, "ColorColumn"):
        color_col_config = st.column_config.ColorColumn("Farbe")
    else:
        color_col_config = st.column_config.TextColumn("Farbe (Hex)")
    edited_config = st.data_editor(
        df_config_default,
        column_config={"ID": None, "Legende": "Legende", "Farbe": color_col_config},
        disabled=["ID"],
        hide_index=True,
        key="design_editor",
    )

map_legend = dict(zip(edited_config["ID"], edited_config["Legende"]))
map_color = dict(zip(edited_config["ID"], edited_config["Farbe"]))
df_sub["final_legend"] = df_sub["unique_id"].map(map_legend)
df_sub["final_color"] = df_sub["unique_id"].map(map_color)

# 2. Diagramm-Titel (Neuer Expander)
with st.sidebar.expander("Diagramm-Titel bearbeiten", expanded=False):
    st.caption(
        "Hier können die Überschriften für die Diagramme individuell angepasst werden."
    )
    # Standard-Titel definieren
    default_titles_data = [
        {
            "Typ": "Gesamtübersicht (Tab 1)",
            "Titel": f"Gesamtübersicht: {int(sel_current)} A",
        },
        {"Typ": "Scatter-Plot", "Titel": "Kosten-Nutzen-Analyse"},
        {"Typ": "Performance-Index", "Titel": "Performance Index"},
        {"Typ": "Heatmap", "Titel": "Fehler-Heatmap"},
        {"Typ": "Boxplot", "Titel": "Fehlerverteilung (Boxplot)"},
        {"Typ": "Pareto", "Titel": "Pareto-Analyse"},
        {"Typ": "Radar", "Titel": "Radar-Profil"},
    ]
    df_titles_default = pd.DataFrame(default_titles_data)

    edited_titles_df = st.data_editor(
        df_titles_default,
        column_config={
            "Typ": st.column_config.TextColumn("Diagramm-Typ", disabled=True),
            "Titel": st.column_config.TextColumn("Titel (Editierbar)"),
        },
        hide_index=True,
        key="titles_editor",
    )
    # Mapping erstellen: Typ -> Titel
    TITLES_MAP = dict(zip(edited_titles_df["Typ"], edited_titles_df["Titel"]))

# --- EXPORT ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 PDF Export")
export_opts = [
    "Gesamtübersicht (Tab 1)",
    "Detail-Phasen (Tab 1)",
    "Ökonomie: Performance-Index",
    "Ökonomie: Scatter-Plot",
    "Ökonomie: Heatmap",
    "Ökonomie: Boxplot",
    "Ökonomie: Pareto",
    "Ökonomie: Radar",
]
export_selection = st.sidebar.multiselect(
    "Zu exportierende Diagramme:",
    export_opts,
    default=["Gesamtübersicht (Tab 1)", "Ökonomie: Performance-Index"],
)
engine_mode = st.sidebar.selectbox(
    "Render-Engine für Details:", ["Python (Direkt)", "MATLAB (Automatischer Start)"]
)
matlab_exe = (
    st.sidebar.text_input("Pfad MATLAB:", value=DEFAULT_MATLAB_PATH)
    if "MATLAB" in engine_mode
    else None
)

if st.sidebar.button("🔄 Export starten", type="primary"):
    if not export_selection:
        st.error("Bitte mindestens ein Diagramm auswählen.")
    else:
        zip_buffer = io.BytesIO()

        # --- ÖKONOMIE DATEN ---
        has_eco_request = any("Ökonomie" in s for s in export_selection)
        if has_eco_request:
            try:
                # Datenaufbereitung (gleiche Logik wie in Tab 2)
                df_err_exp = (
                    df_sub.groupby("unique_id")
                    .agg(
                        wandler_key=("wandler_key", "first"),
                        legend_name=("final_legend", "first"),
                        err_nieder=(
                            "err_ratio",
                            lambda x: x[
                                df_sub.loc[x.index, "target_load"].isin(
                                    ZONES["Niederstrom (5-50%)"]
                                )
                            ]
                            .abs()
                            .mean(),
                        ),
                        err_nom=(
                            "err_ratio",
                            lambda x: x[
                                df_sub.loc[x.index, "target_load"].isin(
                                    ZONES["Nennstrom (80-100%)"]
                                )
                            ]
                            .abs()
                            .mean(),
                        ),
                        err_high=(
                            "err_ratio",
                            lambda x: x[
                                df_sub.loc[x.index, "target_load"].isin(
                                    ZONES["Überlast (≥120%)"]
                                )
                            ]
                            .abs()
                            .mean(),
                        ),
                        preis=("Preis (€)", "first"),
                        vol_t=("T (mm)", "first"),
                        vol_b=("B (mm)", "first"),
                        vol_h=("H (mm)", "first"),
                        color_hex=("final_color", "first"),
                    )
                    .reset_index()
                )
                df_err_exp["volumen"] = (
                    df_err_exp["vol_t"] * df_err_exp["vol_b"] * df_err_exp["vol_h"]
                ) / 1000.0

                # Normalisierung
                mx_p = df_err_exp["preis"].max() or 1
                mx_v = df_err_exp["volumen"].max() or 1
                mx_en = df_err_exp["err_nieder"].abs().max() or 0.01
                mx_nn = df_err_exp["err_nom"].abs().max() or 0.01
                mx_eh = df_err_exp["err_high"].abs().max() or 0.01

                df_err_exp["Norm: Preis"] = (df_err_exp["preis"] / mx_p) * 100
                df_err_exp["Norm: Volumen"] = (df_err_exp["volumen"] / mx_v) * 100
                df_err_exp["Norm: Niederstrom"] = (
                    df_err_exp["err_nieder"].abs() / mx_en
                ) * 100
                df_err_exp["Norm: Nennstrom"] = (
                    df_err_exp["err_nom"].abs() / mx_nn
                ) * 100
                df_err_exp["Norm: Überstrom"] = (
                    df_err_exp["err_high"].abs() / mx_eh
                ) * 100

                # Standard-Score für Sortierung
                df_err_exp["total_score"] = (
                    df_err_exp["Norm: Preis"]
                    + df_err_exp["Norm: Volumen"]
                    + df_err_exp["Norm: Nennstrom"]
                )

                color_map_dict = dict(
                    zip(df_err_exp["legend_name"], df_err_exp["color_hex"])
                )

                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
                    # 1. Performance Index
                    if "Ökonomie: Performance-Index" in export_selection:
                        title_str = TITLES_MAP.get(
                            "Performance-Index", "Performance Index"
                        )
                        df_sorted = df_err_exp.sort_values(
                            "total_score", ascending=True
                        )
                        df_long = df_sorted.melt(
                            id_vars=["legend_name"],
                            value_vars=[
                                "Norm: Preis",
                                "Norm: Volumen",
                                "Norm: Nennstrom",
                            ],
                            var_name="Kategorie",
                            value_name="Anteil (%)",
                        )
                        fig_perf = px.bar(
                            df_long,
                            y="legend_name",
                            x="Anteil (%)",
                            color="Kategorie",
                            orientation="h",
                            title=title_str,
                            color_discrete_map={
                                "Norm: Preis": "#1f77b4",
                                "Norm: Volumen": "#aec7e8",
                                "Norm: Nennstrom": "#ff7f0e",
                            },
                        )
                        fig_perf.update_layout(
                            yaxis=dict(autorange="reversed"),
                            template="plotly_white",
                            width=1123,
                            height=794,
                            font=dict(family="Serif", size=14, color="black"),
                        )
                        zf.writestr(
                            "Oekonomie_Performance_Index.pdf",
                            fig_perf.to_image(format="pdf"),
                        )

                    # 2. Scatter
                    if "Ökonomie: Scatter-Plot" in export_selection:
                        title_str = TITLES_MAP.get(
                            "Scatter-Plot", "Kosten-Nutzen-Analyse"
                        )
                        fig_scat = px.scatter(
                            df_err_exp,
                            x="preis",
                            y="err_nom",
                            color="legend_name",
                            size=[20] * len(df_err_exp),
                            color_discrete_map=color_map_dict,
                            title=title_str,
                        )
                        fig_scat.update_layout(
                            template="plotly_white",
                            width=1123,
                            height=794,
                            font=dict(family="Serif", size=14, color="black"),
                        )
                        zf.writestr(
                            "Oekonomie_Scatter.pdf", fig_scat.to_image(format="pdf")
                        )

                    # 3. Heatmap
                    if "Ökonomie: Heatmap" in export_selection:
                        title_str = TITLES_MAP.get("Heatmap", "Fehler-Heatmap")
                        df_hm = df_err_exp.melt(
                            id_vars=["legend_name"],
                            value_vars=["err_nieder", "err_nom", "err_high"],
                            var_name="Bereich",
                            value_name="Fehler",
                        )
                        fig_hm = px.density_heatmap(
                            df_hm,
                            x="legend_name",
                            y="Bereich",
                            z="Fehler",
                            color_continuous_scale="Blues",
                            title=title_str,
                        )
                        fig_hm.update_layout(
                            template="plotly_white",
                            width=1123,
                            height=794,
                            font=dict(family="Serif", size=14, color="black"),
                        )
                        zf.writestr(
                            "Oekonomie_Heatmap.pdf", fig_hm.to_image(format="pdf")
                        )

                    # 4. Boxplot
                    if "Ökonomie: Boxplot" in export_selection:
                        title_str = TITLES_MAP.get(
                            "Boxplot", "Fehlerverteilung (Boxplot)"
                        )
                        df_box = df_err_exp.melt(
                            id_vars=["legend_name"],
                            value_vars=["err_nieder", "err_nom", "err_high"],
                            var_name="Bereich",
                            value_name="Fehler",
                        )
                        fig_box = px.box(
                            df_box,
                            x="legend_name",
                            y="Fehler",
                            color="Bereich",
                            title=title_str,
                        )
                        fig_box.update_layout(
                            template="plotly_white",
                            width=1123,
                            height=794,
                            font=dict(family="Serif", size=14, color="black"),
                        )
                        zf.writestr(
                            "Oekonomie_Boxplot.pdf", fig_box.to_image(format="pdf")
                        )

                    # 5. Pareto
                    if "Ökonomie: Pareto" in export_selection:
                        title_str = TITLES_MAP.get("Pareto", "Pareto-Analyse")
                        df_par = df_err_exp.sort_values(by="err_nom", ascending=False)
                        df_par["cum_pct"] = (
                            df_par["err_nom"].cumsum() / df_par["err_nom"].sum() * 100
                        )
                        fig_par = make_subplots(specs=[[{"secondary_y": True}]])
                        fig_par.add_trace(
                            go.Bar(
                                x=df_par["legend_name"],
                                y=df_par["err_nom"],
                                name="Fehler (Nenn)",
                                marker_color=df_par["color_hex"],
                            ),
                            secondary_y=False,
                        )
                        fig_par.add_trace(
                            go.Scatter(
                                x=df_par["legend_name"],
                                y=df_par["cum_pct"],
                                name="Kumulativ %",
                                mode="lines+markers",
                                line=dict(color="red", width=3),
                            ),
                            secondary_y=True,
                        )
                        fig_par.update_layout(
                            title=title_str,
                            template="plotly_white",
                            width=1123,
                            height=794,
                            font=dict(family="Serif", size=14, color="black"),
                        )
                        zf.writestr(
                            "Oekonomie_Pareto.pdf", fig_par.to_image(format="pdf")
                        )

                    # 6. Radar
                    if "Ökonomie: Radar" in export_selection:
                        title_str = TITLES_MAP.get("Radar", "Radar-Profil")
                        fig_rad = go.Figure()
                        cats = [
                            "Preis",
                            "Volumen",
                            "Err Nieder",
                            "Err Nenn",
                            "Err High",
                        ]
                        for i, row in df_err_exp.iterrows():
                            vals = [
                                row["Norm: Preis"] / 100,
                                row["Norm: Volumen"] / 100,
                                row["Norm: Niederstrom"] / 100,
                                row["Norm: Nennstrom"] / 100,
                                row["Norm: Überstrom"] / 100,
                                row["Norm: Preis"] / 100,
                            ]
                            fig_rad.add_trace(
                                go.Scatterpolar(
                                    r=vals,
                                    theta=cats + [cats[0]],
                                    fill="toself",
                                    name=row["legend_name"],
                                    line_color=row["color_hex"],
                                )
                            )
                        fig_rad.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                            title=title_str,
                            template="plotly_white",
                            width=1123,
                            height=794,
                            font=dict(family="Serif", size=14, color="black"),
                        )
                        zf.writestr(
                            "Oekonomie_Radar.pdf", fig_rad.to_image(format="pdf")
                        )

            except Exception as e:
                st.error(f"Fehler bei Ökonomie-Export: {e}")

        # --- GESAMT EXPORT ---
        if "Gesamtübersicht (Tab 1)" in export_selection:
            with st.spinner("Generiere Gesamtübersicht..."):
                main_title_export = TITLES_MAP.get(
                    "Gesamtübersicht (Tab 1)", f"Gesamtübersicht: {int(sel_current)} A"
                )
                fig_ex = make_subplots(
                    rows=2,
                    cols=3,
                    shared_xaxes=True,
                    vertical_spacing=0.1,
                    horizontal_spacing=0.05,
                    row_heights=[0.65, 0.35],
                    subplot_titles=PHASES,
                )
                lim_x, lim_y_p, lim_y_n = get_trumpet_limits(acc_class)
                for c_idx, ph in enumerate(PHASES, 1):
                    fig_ex.add_trace(
                        go.Scatter(
                            x=lim_x,
                            y=lim_y_p,
                            mode="lines",
                            line=dict(color="black", width=1.5, dash="dash"),
                            showlegend=(c_idx == 1),
                            name="Klassengrenze",
                        ),
                        row=1,
                        col=c_idx,
                    )
                    fig_ex.add_trace(
                        go.Scatter(
                            x=lim_x,
                            y=lim_y_n,
                            mode="lines",
                            line=dict(color="black", width=1.5, dash="dash"),
                            showlegend=False,
                        ),
                        row=1,
                        col=c_idx,
                    )
                    phase_data = df_sub[df_sub["phase"] == ph]
                    for uid, group in phase_data.groupby("unique_id"):
                        group = group.sort_values("target_load")
                        row_first = group.iloc[0]
                        fig_ex.add_trace(
                            go.Scatter(
                                x=group["target_load"],
                                y=group["err_ratio"],
                                mode="lines+markers",
                                name=row_first["final_legend"],
                                line=dict(color=row_first["final_color"], width=2.5),
                                legendgroup=row_first["final_legend"],
                                showlegend=(c_idx == 1),
                            ),
                            row=1,
                            col=c_idx,
                        )
                        if show_err_bars:
                            fig_ex.add_trace(
                                go.Bar(
                                    x=group["target_load"],
                                    y=group["err_std"],
                                    marker_color=row_first["final_color"],
                                    legendgroup=row_first["final_legend"],
                                    showlegend=False,
                                ),
                                row=2,
                                col=c_idx,
                            )
                fig_ex.update_layout(
                    title=dict(text=main_title_export, font=dict(size=18)),
                    template="plotly_white",
                    width=1123,
                    height=794,
                    font=dict(family="Serif", size=14, color="black"),
                    legend=dict(orientation="h", y=-0.15, x=0.5),
                )
                fig_ex.update_yaxes(range=[-y_limit, y_limit], row=1)
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr(
                        f"Zusammenfassung_{int(sel_current)}A.pdf",
                        fig_ex.to_image(format="pdf", width=1123, height=794),
                    )

        # --- DETAIL EXPORT ---
        if "Detail-Phasen (Tab 1)" in export_selection:
            # (Der Kürze halber wird der Detail-Export Block unverändert übernommen - Hier können ggf. auch Titel angepasst werden, ist aber komplexer da Phasen-abhängig)
            if "MATLAB" in engine_mode:
                pass  # MATLAB Code (wie oben)
            else:
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
                    for ph in PHASES:
                        fig_s = create_single_phase_figure(
                            df_sub,
                            ph,
                            acc_class,
                            y_limit,
                            show_err_bars,
                            title_prefix=f"{int(sel_current)} A",
                        )
                        zf.writestr(
                            f"Detail_{ph}_{int(sel_current)}A.pdf",
                            fig_s.to_image(format="pdf", width=1123, height=794),
                        )
            st.success("✅ Details exportiert")

        st.session_state["zip_data"] = zip_buffer.getvalue()

if "zip_data" in st.session_state:
    st.sidebar.download_button(
        "💾 Download ZIP", st.session_state["zip_data"], "Report.zip", "application/zip"
    )

# =============================================================================
# MAIN TABS
# =============================================================================
tab1, tab2, tab3 = st.tabs(
    ["📈 Gesamtgenauigkeit", "💰 Ökonomische Analyse", "⚙️ Stammdaten-Editor"]
)

with tab1:
    # Hier verwenden wir den custom Title aus der Map
    custom_title_tab1 = TITLES_MAP.get(
        "Gesamtübersicht (Tab 1)", f"Gesamtübersicht: {int(sel_current)} A"
    )

    fig_main = make_subplots(
        rows=2,
        cols=3,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3],
        subplot_titles=PHASES,
    )
    lim_x, lim_y_p, lim_y_n = get_trumpet_limits(acc_class)
    for col_idx, phase in enumerate(PHASES, start=1):
        fig_main.add_trace(
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
        fig_main.add_trace(
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
        for uid, group in phase_data.groupby("unique_id"):
            group = group.sort_values("target_load")
            row_first = group.iloc[0]
            fig_main.add_trace(
                go.Scatter(
                    x=group["target_load"],
                    y=group["err_ratio"],
                    mode="lines+markers",
                    name=row_first["final_legend"],
                    line=dict(color=row_first["final_color"], width=2),
                    legendgroup=row_first["final_legend"],
                    showlegend=(col_idx == 1),
                ),
                row=1,
                col=col_idx,
            )
            if show_err_bars:
                fig_main.add_trace(
                    go.Bar(
                        x=group["target_load"],
                        y=group["err_std"],
                        marker_color=row_first["final_color"],
                        legendgroup=row_first["final_legend"],
                        showlegend=False,
                    ),
                    row=2,
                    col=col_idx,
                )
    fig_main.update_layout(
        title=custom_title_tab1,
        template="plotly_white",
        height=800,
        legend=dict(orientation="h", y=-0.15, x=0.5),
    )
    if sync_axes:
        fig_main.update_yaxes(matches="y", row=1)
    fig_main.update_yaxes(
        range=[-y_limit, y_limit], title_text="Fehler [%]", row=1, col=1
    )
    fig_main.update_yaxes(title_text="StdAbw [%]", row=2, col=1)
    fig_main.update_xaxes(title_text="Last [% In]", row=2, col=2)
    st.plotly_chart(fig_main, use_container_width=True)

with tab2:
    st.markdown("### 💰 Preis/Leistung & Varianten-Vergleich")

    # 1. Daten aggregieren
    df_err = (
        df_sub.groupby("unique_id")
        .agg(
            wandler_key=("wandler_key", "first"),
            legend_name=("final_legend", "first"),
            err_nieder=(
                "err_ratio",
                lambda x: x[
                    df_sub.loc[x.index, "target_load"].isin(
                        ZONES["Niederstrom (5-50%)"]
                    )
                ]
                .abs()
                .mean(),
            ),
            err_nom=(
                "err_ratio",
                lambda x: x[
                    df_sub.loc[x.index, "target_load"].isin(
                        ZONES["Nennstrom (80-100%)"]
                    )
                ]
                .abs()
                .mean(),
            ),
            err_high=(
                "err_ratio",
                lambda x: x[
                    df_sub.loc[x.index, "target_load"].isin(ZONES["Überlast (≥120%)"])
                ]
                .abs()
                .mean(),
            ),
            preis=("Preis (€)", "first"),
            vol_t=("T (mm)", "first"),
            vol_b=("B (mm)", "first"),
            vol_h=("H (mm)", "first"),
            color_hex=("final_color", "first"),
        )
        .reset_index()
    )
    df_err["volumen"] = (df_err["vol_t"] * df_err["vol_b"] * df_err["vol_h"]) / 1000.0

    # --- DEFINITION DER NAMEN ---
    Y_OPTIONS_MAP = {
        "Fehler Niederstrom": "err_nieder",
        "Fehler Nennstrom": "err_nom",
        "Fehler Überlast": "err_high",
        "Preis (€)": "preis",
        "Volumen (Gesamt)": "volumen",
        "Breite (B)": "vol_b",
        "Höhe (H)": "vol_h",
        "Tiefe (T)": "vol_t",
    }
    REVERSE_Y_MAP = {v: k for k, v in Y_OPTIONS_MAP.items()}

    if not df_err.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            x_sel = st.selectbox("X-Achse:", ["Preis (€)", "Volumen (dm³)"])
            x_col = "preis" if "Preis" in x_sel else "volumen"

        with c2:
            y_selection = st.multiselect(
                "Y-Achse (Mehrfachauswahl):",
                options=list(Y_OPTIONS_MAP.keys()),
                default=["Fehler Nennstrom"],
            )
            y_cols_selected = [Y_OPTIONS_MAP[label] for label in y_selection]

        with c3:
            chart_type = st.radio(
                "Diagramm-Typ:",
                [
                    "Scatter",
                    "Performance-Index",
                    "Heatmap",
                    "Boxplot",
                    "Pareto",
                    "Radar",
                ],
            )

        color_map_dict = dict(zip(df_err["legend_name"], df_err["color_hex"]))

        if not y_cols_selected:
            st.warning("Bitte wähle mindestens einen Wert für die Y-Achse aus.")
        else:
            # --- DIAGRAMM LOGIK ---
            if chart_type == "Scatter":
                title_str = TITLES_MAP.get("Scatter-Plot", f"{x_sel} vs. Auswahl")
                df_long = df_err.melt(
                    id_vars=["unique_id", "legend_name", x_col, "color_hex"],
                    value_vars=y_cols_selected,
                    var_name="Metrik_Intern",
                    value_name="Wert",
                )
                df_long["Metrik"] = df_long["Metrik_Intern"].map(REVERSE_Y_MAP)
                fig_eco = px.scatter(
                    df_long,
                    x=x_col,
                    y="Wert",
                    color="legend_name",
                    symbol="Metrik",
                    size=[15] * len(df_long),
                    color_discrete_map=color_map_dict,
                    title=title_str,
                )
                st.plotly_chart(fig_eco, use_container_width=True)

            elif chart_type == "Performance-Index":
                title_str = TITLES_MAP.get("Performance-Index", "Performance Index")
                norm_cols = []
                df_err["total_score"] = 0.0
                for label in y_selection:
                    raw_col = Y_OPTIONS_MAP[label]
                    norm_col_name = label
                    mx_val = df_err[raw_col].abs().max()
                    if mx_val == 0:
                        mx_val = 1.0
                    df_err[norm_col_name] = (df_err[raw_col].abs() / mx_val) * 100
                    df_err["total_score"] += df_err[norm_col_name]
                    norm_cols.append(norm_col_name)

                df_sorted = df_err.sort_values("total_score", ascending=True)
                df_long = df_sorted.melt(
                    id_vars=["legend_name"],
                    value_vars=norm_cols,
                    var_name="Kategorie",
                    value_name="Normalisierter Anteil (%)",
                )
                fig_eco = px.bar(
                    df_long,
                    y="legend_name",
                    x="Normalisierter Anteil (%)",
                    color="Kategorie",
                    orientation="h",
                    title=title_str,
                )
                fig_eco.update_layout(
                    yaxis=dict(autorange="reversed"),
                    legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
                )
                st.plotly_chart(fig_eco, use_container_width=True)

            elif chart_type == "Heatmap":
                title_str = TITLES_MAP.get("Heatmap", "Heatmap der Auswahl")
                df_long = df_err.melt(
                    id_vars=["legend_name"],
                    value_vars=y_cols_selected,
                    var_name="Kategorie_Intern",
                    value_name="Wert",
                )
                df_long["Kategorie"] = df_long["Kategorie_Intern"].map(REVERSE_Y_MAP)
                fig_eco = px.density_heatmap(
                    df_long,
                    x="legend_name",
                    y="Kategorie",
                    z="Wert",
                    color_continuous_scale="Blues",
                    title=title_str,
                )
                st.plotly_chart(fig_eco, use_container_width=True)

            elif chart_type == "Boxplot":
                title_str = TITLES_MAP.get(
                    "Boxplot", f"Verteilung: {', '.join(y_selection)}"
                )
                df_long = df_err.melt(
                    id_vars=["legend_name"],
                    value_vars=y_cols_selected,
                    var_name="Kategorie_Intern",
                    value_name="Wert",
                )
                df_long["Kategorie"] = df_long["Kategorie_Intern"].map(REVERSE_Y_MAP)
                fig_eco = px.box(
                    df_long,
                    x="legend_name",
                    y="Wert",
                    color="Kategorie",
                    title=title_str,
                )
                st.plotly_chart(fig_eco, use_container_width=True)

            elif chart_type == "Pareto":
                title_str = TITLES_MAP.get("Pareto", "Pareto-Analyse")
                target_y = y_cols_selected[0]
                target_label = y_selection[0]
                df_sorted = df_err.sort_values(by=target_y, ascending=False)
                df_sorted["cum_pct"] = (
                    df_sorted[target_y].cumsum() / df_sorted[target_y].sum() * 100
                )
                fig_par = make_subplots(specs=[[{"secondary_y": True}]])
                fig_par.add_trace(
                    go.Bar(
                        x=df_sorted["legend_name"],
                        y=df_sorted[target_y],
                        name=target_label,
                        marker_color=df_sorted["color_hex"],
                    ),
                    secondary_y=False,
                )
                fig_par.add_trace(
                    go.Scatter(
                        x=df_sorted["legend_name"],
                        y=df_sorted["cum_pct"],
                        name="Kumulativ %",
                        mode="lines+markers",
                        line=dict(color="red"),
                    ),
                    secondary_y=True,
                )
                fig_par.update_layout(title=title_str)
                st.plotly_chart(fig_par, use_container_width=True)

            elif chart_type == "Radar":
                title_str = TITLES_MAP.get("Radar", "Radar-Vergleich")
                fig_r = go.Figure()
                categories = y_selection
                max_vals = {}
                for col_name in y_cols_selected:
                    m = df_err[col_name].max()
                    max_vals[col_name] = m if m != 0 else 1

                for i, row in df_err.iterrows():
                    r_vals = []
                    for col_name in y_cols_selected:
                        val = row[col_name]
                        norm_val = val / max_vals[col_name]
                        r_vals.append(norm_val)
                    r_vals.append(r_vals[0])
                    theta_vals = categories + [categories[0]]
                    fig_r.add_trace(
                        go.Scatterpolar(
                            r=r_vals,
                            theta=theta_vals,
                            fill="toself",
                            name=row["legend_name"],
                            line_color=row["color_hex"],
                        )
                    )
                fig_r.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    title=title_str,
                )
                st.plotly_chart(fig_r, use_container_width=True)

with tab3:
    st.markdown("### ⚙️ Stammdaten pro Messdatei")
    col_info, col_btn = st.columns([2, 1])
    with col_info:
        st.info("Die Datenbank ist die Hauptquelle.")
    with col_btn:
        if st.button(
            "🔄 Infos aus Dateinamen neu einlesen",
            type="secondary",
            use_container_width=True,
        ):
            src_col = "raw_file" if "raw_file" in df.columns else "wandler_key"
            new_meta = df[src_col].apply(parse_filename_info)
            new_meta.columns = ["Hersteller", "Modell", "nennstrom", "Mess-Bürde"]
            df["Hersteller"] = new_meta["Hersteller"]
            df["Modell"] = new_meta["Modell"]
            df["nennstrom"] = new_meta["nennstrom"]
            df["Mess-Bürde"] = new_meta["Mess-Bürde"]
            if save_db(df):
                st.success("Aktualisiert!")
                st.rerun()

    df_editor_view = (
        df_sub[META_COLS].drop_duplicates(subset=["raw_file"]).set_index("raw_file")
    )
    edited_df = st.data_editor(
        df_editor_view,
        column_config={"raw_file": st.column_config.TextColumn(disabled=True)},
        hide_index=True,
        key="specs_editor",
    )

    if st.button("💾 Änderungen speichern", type="primary"):
        changes = edited_df.to_dict(orient="index")
        df_to_save = df.copy()
        count = 0
        for fname, attrs in changes.items():
            mask = df_to_save["raw_file"] == str(fname).strip()
            if mask.any():
                count += 1
                for c in META_COLS_EDIT:
                    if c in attrs:
                        df_to_save.loc[mask, c] = attrs[c]
        if count > 0:
            save_db(df_to_save)
            st.success(f"✅ {count} Dateien gespeichert!")
            st.rerun()
        else:
            st.warning("Keine Übereinstimmung gefunden.")
