import base64
import json
import os
from string import Template

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

ORANGE = "#E8703A"
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
VALS = ["base_actif", "churn", "rev_actif", "ga_30", "react_30"]

# =====================================================================
#                 PARAMÈTRES D'AFFICHAGE  (modifie ici)
# =====================================================================
APP_VERSION = "v16"        # affichée en bas de la barre latérale : sert à vérifier que le bon code est en ligne

# --- Chiffres des graphiques (taille en px) ---
NUM_BOLD = True            # True = chiffres en gras, False = normal
NUM_COLOR = "#000000"      # couleur des chiffres
FS_WATERFALL = 24          # chiffres du waterfall
FS_WATERFALL_DELTA = 28    # grand "Δ" au centre du waterfall
FS_WATERFALL_AXIS = 20     # libellés sous le waterfall (Parc, GA, React...)
FS_EVO = 22                # chiffres des graphes d'évolution mensuelle
FS_EVO_AXIS = 22           # libellés des mois sous les graphes d'évolution
FS_HBAR = 26               # chiffres au bout des barres (classements régions / MoM / YoY)
HBAR_ROW_HEIGHT = 40       # hauteur d'une ligne (px)
FS_HBAR_AXIS = 20          # noms des régions
AXIS_BOLD = True           # True = libellés des axes en gras
AXIS_COLOR = "#000000"     # couleur des libellés des axes
HBAR_PAD_NEG = 0.5         # espace à gauche pour les valeurs négatives
HBAR_PAD_POS = 0.3         # espace à droite pour les valeurs positives
FS_MAP_HOVER = 16          # texte de l'infobulle de la carte
HBAR_DIM_OPACITY = 0.30    # opacité des barres NON sélectionnées quand un gouvernorat est filtré

# --- Barre latérale (filtres) ---
SB_BG = "#E4E7EC"
SB_PADDING = 24
SB_TITLE_SIZE = 36
SB_LABEL_SIZE = 22
SB_VALUE_SIZE = 20
SB_TAG_SIZE = 18
SB_OPTION_SIZE = 20
SB_FIELD_HEIGHT = 60

# --- Onglets ---
TAB_FONT_SIZE = 24
TAB_HEIGHT = 66
TAB_PADDING_X = 34
TAB_GAP = 12
TAB_BG = "#F3F4F6"
TAB_TEXT = "#374151"
TAB_ACTIVE_BG = ORANGE
TAB_ACTIVE_TEXT = "#FFFFFF"

# --- Carte de Tunisie ---
MAP_STYLE = "open-street-map"   # "open-street-map" ou "carto-positron" (plus épuré)
MAP_CLICK_FILTER = True        # True = un clic sur une bulle filtre TOUS les graphiques (comme Power BI)
MAP_ZOOM_ON_SELECT = True      # True = la carte zoome sur le gouvernorat cliqué
MAP_HEIGHT = 650
MAP_TEXT_SIZE = 16             # taille des chiffres sur la carte (vue d'ensemble)
MAP_TEXT_SIZE_ZOOM = 22        # taille des chiffres quand un gouvernorat est sélectionné
MAP_LABEL_MIN_RATIO = 0.0      # 0 = tous les chiffres affichés ; 0.05 = cache les bulles < 5 % de la plus grande (vue d'ensemble)
MAP_BUBBLE_MAX = 60            # diamètre max des bulles (px)
MAP_BUBBLE_MIN = 34            # diamètre min des bulles (px) : assez grand pour contenir le chiffre
MAP_HALO_PX = 10               # épaisseur du contour noir autour des bulles sélectionnées
MAP_HALO_COLOR = "#111827"
MAP_COLOR_LOW = "#FDBA74"
MAP_COLOR_HIGH = "#C2410C"
MAP_ZOOM_DEFAULT = 5.5
MAP_ZOOM_MAX = 10
MAP_PAD_DEG = 1.0

# --- Look général de la page ---
PAGE_BG = "#F1F3F6"
CARD_BG = "#FFFFFF"
CARD_RADIUS = 16
CARD_SHADOW = "0 4px 14px rgba(0,0,0,0.10)"
SUBTITLE_SIZE = 28
CHART_TITLE_SIZE = 20
METRIC_LABEL_SIZE = 18
METRIC_VALUE_SIZE = 34
VUE_COLS = [5, 2]
METRIC_DELTA_SIZE = 16
# =====================================================================

COORD = {  # latitude, longitude des gouvernorats
    "ARIANA": (36.8665, 10.1647), "BEJA": (36.7256, 9.1817), "BEN AROUS": (36.7531, 10.2189),
    "BIZERTE": (37.2744, 9.8739), "GABES": (33.8815, 10.0982), "GAFSA": (34.4250, 8.7842),
    "JENDOUBA": (36.5011, 8.7803), "KAIROUANE": (35.6781, 10.0963), "KASERINE": (35.1676, 8.8365),
    "KEBELI": (33.7044, 8.9690), "KEF": (36.1675, 8.7049), "MAHDIA": (35.5047, 11.0622),
    "MANNOUBA": (36.8101, 10.0956), "MEDNINE": (33.3549, 10.5055), "MONASTIR": (35.7643, 10.8113),
    "NABEUL": (36.4561, 10.7376), "SFAX": (34.7406, 10.7603), "SIDI BOUZID": (35.0382, 9.4849),
    "SILIANA": (36.0849, 9.3708), "SOUSSE": (35.8256, 10.6084), "TATAOUINE": (32.9297, 10.4518),
    "TOZEUR": (33.9197, 8.1335), "TUNIS": (36.8065, 10.1815), "ZAGHOUAN": (36.4029, 10.1429),
}

st.set_page_config(page_title="GeoPulse", page_icon="📡", layout="wide")

# ---- Style (barre latérale + onglets) : tout est piloté par les paramètres ci-dessus ----
_NOT_TAG = ':not([data-baseweb="tag"]):not([data-baseweb="tag"] *)'
_CSS = Template("""
/* ===== Page ===== */
.stApp { background-color: ${PAGE_BG}; }
[data-testid="stHeader"] { background: transparent; }
.stApp h3 {
    font-size: ${SUBTITLE_SIZE}px !important; font-weight: 800 !important; color: #111 !important;
    border-left: 7px solid ${ORANGE}; padding-left: 12px !important; margin-top: 10px;
}
.stApp h4 { font-weight: 800 !important; color: #111 !important; }
[data-testid="stMain"] [data-testid="stMarkdownContainer"] strong { font-size: ${CHART_TITLE_SIZE}px; color: #111; }
[data-testid="stMain"] [data-testid="stWidgetLabel"] p { font-size: 18px !important; font-weight: 700 !important; color: #111 !important; }
[data-testid="stMain"] [data-baseweb="select"] * { font-size: 18px !important; font-weight: 700 !important; }

/* ===== Cartes : graphiques et indicateurs ===== */
[data-testid="stPlotlyChart"] {
    background: ${CARD_BG}; border-radius: ${CARD_RADIUS}px; box-shadow: ${CARD_SHADOW}; padding: 10px; margin-bottom: 10px;
}
[data-testid="stMetric"] {
    background: ${CARD_BG}; border-radius: ${CARD_RADIUS}px; box-shadow: ${CARD_SHADOW};
    padding: 14px 12px 14px 16px; border-left: 7px solid ${ORANGE}; margin-bottom: 10px;
}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * { font-size: ${METRIC_LABEL_SIZE}px !important; font-weight: 700 !important; color: #4B5563 !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    font-size: ${METRIC_VALUE_SIZE}px !important; font-weight: 800 !important; color: #000 !important;
    overflow: visible !important; text-overflow: clip !important; white-space: nowrap !important;
}
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * { font-size: ${METRIC_DELTA_SIZE}px !important; font-weight: 700 !important; }

/* ===== Barre latérale ===== */
[data-testid="stSidebar"] { background-color: ${SB_BG}; box-shadow: 2px 0 10px rgba(0,0,0,0.08); }
[data-testid="stSidebarUserContent"] { padding-left: ${SB_PADDING}px !important; padding-right: ${SB_PADDING}px !important; }
[data-testid="stSidebar"] h2 {
    font-size: ${SB_TITLE_SIZE}px !important; font-weight: 800 !important; color: #000 !important;
    border-bottom: 4px solid ${ORANGE}; padding-bottom: 8px !important; display: inline-block;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label p {
    font-size: ${SB_LABEL_SIZE}px !important; font-weight: 800 !important; color: #000 !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] *,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] *,
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [role="combobox"],
[data-testid="stSidebar"] input {
    font-size: ${SB_VALUE_SIZE}px !important; font-weight: 700 !important;
}
[data-testid="stSidebar"] input::placeholder { color: #374151 !important; opacity: 1 !important; font-weight: 700 !important; font-size: ${SB_VALUE_SIZE}px !important; }
[data-testid="stSidebar"] [data-baseweb="select"] div${_NOT_TAG} { min-height: ${SB_FIELD_HEIGHT}px; }
[data-testid="stSidebar"] [data-baseweb="select"] { background-color: #FFFFFF; border-radius: 10px; box-shadow: 0 0 0 2px #9AA3AF; }
[data-testid="stSidebar"] [data-baseweb="tag"],
[data-testid="stSidebar"] [data-baseweb="tag"] * { font-size: ${SB_TAG_SIZE}px !important; font-weight: 700 !important; min-height: 0 !important; }
[data-baseweb="popover"] li, [data-baseweb="popover"] li *,
[role="listbox"] *, [role="option"], [role="option"] *,
[data-testid="stSelectboxVirtualDropdown"] * {
    font-size: ${SB_OPTION_SIZE}px !important; font-weight: 600 !important;
}

/* ===== Onglets ===== */
[role="tablist"], [data-baseweb="tab-list"] { gap: ${TAB_GAP}px !important; border-bottom: 3px solid ${TAB_ACTIVE_BG} !important; padding-top: 8px; }
[role="tab"], [data-baseweb="tab"], [data-testid="stTab"] {
    height: ${TAB_HEIGHT}px !important; padding: 0 ${TAB_PADDING_X}px !important; background-color: ${TAB_BG} !important;
    border-radius: 12px 12px 0 0 !important; transition: all 0.2s ease;
}
[role="tab"], [role="tab"] *, [data-baseweb="tab"] *, [data-testid="stTab"] * {
    font-size: ${TAB_FONT_SIZE}px !important; font-weight: 800 !important; color: ${TAB_TEXT} !important;
}
[role="tab"]:hover { background-color: #FDE5D8 !important; }
[role="tab"][aria-selected="true"] { background-color: ${TAB_ACTIVE_BG} !important; }
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] * { color: ${TAB_ACTIVE_TEXT} !important; }
[data-baseweb="tab-highlight"] { background-color: #000000 !important; height: 4px !important; }
[data-baseweb="tab-border"] { background-color: transparent !important; }
/* ===== Navigation (radio horizontal stylé comme des onglets) ===== */
.st-key-nav [role="radiogroup"] { gap: ${TAB_GAP}px !important; border-bottom: 3px solid ${TAB_ACTIVE_BG}; padding-top: 8px; flex-wrap: wrap; }
.st-key-nav label[data-baseweb="radio"] {
    height: ${TAB_HEIGHT}px; padding: 0 ${TAB_PADDING_X}px !important; margin: 0 !important; background-color: ${TAB_BG};
    border-radius: 12px 12px 0 0; align-items: center; cursor: pointer; transition: all 0.2s ease;
}
.st-key-nav label[data-baseweb="radio"] > div:first-child { display: none !important; }
.st-key-nav label[data-baseweb="radio"] p {
    font-size: ${TAB_FONT_SIZE}px !important; font-weight: 800 !important; color: ${TAB_TEXT} !important; margin: 0 !important;
}
.st-key-nav label[data-baseweb="radio"]:hover { background-color: #FDE5D8; }
.st-key-nav label[data-baseweb="radio"]:has(input:checked) { background-color: ${TAB_ACTIVE_BG}; }
.st-key-nav label[data-baseweb="radio"]:has(input:checked) p { color: ${TAB_ACTIVE_TEXT} !important; }
""")
_css_txt = _CSS.safe_substitute(globals())

# Injection 1 : balise <style> classique
st.markdown(f"<style>{_css_txt}</style>", unsafe_allow_html=True)

# Injection 2 : via JavaScript directement dans la page (contourne les filtres de Streamlit)
components.html(
    "<script>(function(){var css=" + json.dumps(_css_txt) + ";"
    "var d=window.parent.document;var e=d.getElementById('geopulse-style');"
    "if(!e){e=d.createElement('style');e.id='geopulse-style';d.head.appendChild(e);}"
    "e.textContent=css;})();</script>",
    height=0,
)


def img_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as fh:
            return base64.b64encode(fh.read()).decode()
    return None


_lg, _lo = img_b64("logo_geopulse.png"), img_b64("logo_orange.png")
_left = f"<img src='data:image/png;base64,{_lg}' style='height:84px;border-radius:50%;margin-right:18px'>" if _lg else ""
_right = f"<img src='data:image/png;base64,{_lo}' style='height:64px'>" if _lo else ""
st.markdown(
    "<div style='background:#000;padding:14px 24px;border-bottom:5px solid #E8703A;border-radius:14px;box-shadow:0 6px 18px rgba(0,0,0,0.25);margin-bottom:18px;display:flex;align-items:center;justify-content:space-between'>"
    f"<div style='display:flex;align-items:center'>{_left}<div>"
    "<h2 style='color:#fff;margin:0;padding:0'>GeoPulse | Telecom Geomarketing Intelligence</h2>"
    "<span style='color:#fff'>Transformer les données géographiques en décisions commerciales intelligentes.</span></div></div>"
    f"{_right}</div>",
    unsafe_allow_html=True,
)


def fm(d):
    d = pd.Timestamp(d)
    return f"{MOIS[d.month - 1]} {d.year}"


def human(x):
    if x is None or pd.isna(x):
        return "–"
    a = abs(x)
    if a >= 1e6:
        return f"{x / 1e6:.2f}M"
    if a >= 1e3:
        return f"{x / 1e3:.1f}K"
    return f"{x:.1f}"


def space(x):
    return f"{x:,.0f}".replace(",", " ")


def bold(t):
    return f"<b>{t}</b>" if NUM_BOLD else t


def lab(t):
    """Libellé d'axe (mois, région) : en gras si AXIS_BOLD."""
    return f"<b>{t}</b>" if AXIS_BOLD else str(t)


@st.cache_data
def load():
    return pd.read_csv("data.csv", parse_dates=["date"])


df = load()
dates = [pd.Timestamp(x) for x in sorted(df["date"].unique())]

# ---------------- Filtre "carte" (état partagé par tous les onglets) ----------------
if "geo_sel" not in st.session_state:
    st.session_state["geo_sel"] = []     # gouvernorats cliqués sur la carte
if "mapver" not in st.session_state:
    st.session_state["mapver"] = 0       # change à chaque clic => les cartes sont recréées proprement


def set_geo(names):
    st.session_state["geo_sel"] = list(names)
    st.session_state["mapver"] += 1


# ---------------- Filtres (équivalent des segments Power BI) ----------------
with st.sidebar:
    st.header("Filtres")
    sel = {}
    for col, label in [("gouvernorat", "Localisation"), ("programme", "Programme"),
                       ("ligne_produit", "Ligne de produit"), ("type_offre", "Type d'offre")]:
        sel[col] = st.multiselect(label, sorted(df[col].unique()))
    mois_sel = st.selectbox("Mois des KPI et de la carte", dates, index=len(dates) - 1, format_func=fm)
    multi_click = st.toggle("Sélection multiple sur la carte", value=False,
                            help="Activé : chaque clic ajoute/retire un gouvernorat. Désactivé : un clic remplace la sélection.")
    st.caption(f"Version du code : {APP_VERSION}")

# f_base = filtres de la barre latérale uniquement (sert à la carte et aux classements régionaux)
f_base = df
for col, vals in sel.items():
    if vals:
        f_base = f_base[f_base[col].isin(vals)]
if f_base.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()

# f = f_base + gouvernorats cliqués sur la carte (sert aux KPI, évolutions, waterfall)
_ok = set(f_base["gouvernorat"].unique())
geo_sel = [g for g in st.session_state["geo_sel"] if g in _ok]
if geo_sel != st.session_state["geo_sel"]:
    st.session_state["geo_sel"] = geo_sel
f = f_base[f_base["gouvernorat"].isin(geo_sel)] if geo_sel else f_base
if f.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()


def agg(d, by):
    g = d.groupby(by)[VALS].sum()
    g["arpu"] = g["rev_actif"] / g["base_actif"].where(g["base_actif"] > 0)
    return g


m = agg(f, "date").sort_index()
prev_d = mois_sel - pd.DateOffset(months=1)
yago_d = mois_sel - pd.DateOffset(years=1)


def show_delta(container, label, cur, ref, col):
    if cur is None or ref is None or pd.isna(cur) or pd.isna(ref) or ref == 0:
        return
    container.metric(label, human(cur - ref), f"{(cur / ref - 1) * 100:+.1f} %",
                     delta_color="inverse" if col == "churn" else "normal")


def evo_chart(s):
    fig = go.Figure(go.Bar(
        x=[lab(fm(d)) for d in s.index], y=s.values, marker_color=ORANGE,
        text=[bold(human(v)) for v in s.values], textposition="outside",
        textfont=dict(size=FS_EVO, color=NUM_COLOR), outsidetextfont=dict(size=FS_EVO, color=NUM_COLOR),
        cliponaxis=False, constraintext="none"))
    fig.update_layout(height=360, margin=dict(t=60, b=10, l=10, r=10), yaxis_visible=False, bargap=0.35,
                      xaxis=dict(tickfont=dict(size=FS_EVO_AXIS, color=AXIS_COLOR), showgrid=False))
    return fig


def hbar(s, height, colors=None, selected=()):
    """Barres horizontales. Si des gouvernorats sont sélectionnés sur la carte, les autres sont atténués."""
    base_colors = list(colors) if colors is not None else [ORANGE] * len(s)
    opac = [1.0 if (not selected or n in selected) else HBAR_DIM_OPACITY for n in s.index]
    fig = go.Figure(go.Bar(
        x=s.values, y=[lab(n) for n in s.index], orientation="h",
        marker=dict(color=base_colors, opacity=opac),
        text=[bold(human(v)) for v in s.values], textposition="outside",
        textfont=dict(size=FS_HBAR, color=NUM_COLOR), outsidetextfont=dict(size=FS_HBAR, color=NUM_COLOR),
        cliponaxis=False, constraintext="none"))
    # marge dans l'axe pour que les valeurs (surtout négatives) ne passent pas sous les noms de régions
    vmin, vmax = float(min(np.nanmin(s.values), 0)), float(max(np.nanmax(s.values), 0))
    span = (vmax - vmin) or 1.0
    xr = [vmin - (HBAR_PAD_NEG * span if vmin < 0 else 0), vmax + HBAR_PAD_POS * span]
    fig.update_layout(height=max(height, HBAR_ROW_HEIGHT * len(s) + 50), margin=dict(t=30, b=10, l=10, r=20), bargap=0.25,
                      xaxis=dict(visible=False, range=xr),
                      yaxis=dict(tickfont=dict(size=FS_HBAR_AXIS, color=AXIS_COLOR), automargin=True, showgrid=False))
    return fig


TITRES = {"base_actif": "Base active", "churn": "Churn", "rev_actif": "Revenu actif", "arpu": "ARPU"}

# ---------------- Bandeau "filtre carte actif" (visible sur tous les onglets) ----------------
if geo_sel:
    cA, cB = st.columns([6, 1])
    cA.info(f"🎯 Filtre carte actif : **{', '.join(geo_sel)}** — KPI, évolutions et waterfall sont filtrés. "
            "Les classements régionaux restent complets (sélection en surbrillance).")
    cB.button("✖ Effacer", key="clear_geo", on_click=set_geo, args=([],))

PAGES = ["VUE 360", "Waterfall", "Base active", "Churn", "Revenu actif", "ARPU"]
# st.radio garde la page active après un st.rerun() (contrairement à st.tabs qui revenait sur VUE 360)
with st.container(key="nav"):
    page = st.radio("Page", PAGES, horizontal=True, key="page", label_visibility="collapsed")

# ---------------- VUE 360 ----------------
if page == "VUE 360":
    cols = st.columns(2)
    for i, col in enumerate(["base_actif", "churn", "rev_actif", "arpu"]):
        with cols[i % 2]:
            st.subheader(f"{TITRES[col]} · évolution mensuelle")
            c1, c2 = st.columns(VUE_COLS)
            c1.plotly_chart(evo_chart(m[col]), use_container_width=True, key=f"vue_{col}")
            cur = m[col].get(mois_sel)
            show_delta(c2, "MoM", cur, m[col].get(prev_d), col)
            show_delta(c2, "YoY", cur, m[col].get(yago_d), col)

# ---------------- Waterfall ----------------
if page == "Waterfall":
    c1, c2 = st.columns(2)
    d_from = c1.selectbox("Mois de départ", dates, index=max(len(dates) - 2, 0), format_func=fm, key="wf_from")
    d_to = c2.selectbox("Mois d'arrivée", dates, index=len(dates) - 1, format_func=fm, key="wf_to")
    if d_from not in m.index or d_to not in m.index:
        st.info("Pas de données pour ces mois.")
    else:
        a, b = m.loc[d_from], m.loc[d_to]
        start, end = a["base_actif"], b["base_actif"]
        ga, react, churn = b["ga_30"], b["react_30"], b["churn"]
        autres = end - start - ga - react + churn
        steps = [("GA", ga, "#2ECC71"), ("React", react, "#3498DB"), ("Churn", -churn, "#E74C3C"), ("Autres", autres, "#95A5A6")]
        xs, bases, heights, colors, texts = [lab(f"Parc<br>{fm(d_from)}")], [0], [start], ["#F4C84B"], [bold(space(start))]
        level = start
        for name, v, color in steps:
            new = level + v
            xs.append(lab(f"{name}<br>{fm(d_to)}"))
            bases.append(min(level, new))
            heights.append(abs(v))
            colors.append(color)
            texts.append(bold(f"{'+' if v >= 0 else '-'}{human(abs(v))}"))
            level = new
        xs.append(lab(f"Parc<br>{fm(d_to)}"))
        bases.append(0); heights.append(end); colors.append("#F4C84B"); texts.append(bold(space(end)))
        fig = go.Figure(go.Bar(x=xs, y=heights, base=bases, marker_color=colors, text=texts,
                               textposition=["inside"] + ["outside"] * 4 + ["inside"],
                               textfont=dict(size=FS_WATERFALL, color=NUM_COLOR),
                               insidetextfont=dict(size=FS_WATERFALL + 2, color=NUM_COLOR),
                               outsidetextfont=dict(size=FS_WATERFALL, color=NUM_COLOR),
                               cliponaxis=False, constraintext="none"))
        filt_parts = [v for v in sel.values() if v] + ([geo_sel] if geo_sel else [])
        filt = " - ".join(" + ".join(v) for v in filt_parts)
        diff = end - start
        fig.update_layout(title=f"Waterfall Parc MoM {fm(d_from)} → {fm(d_to)}" + (f" | {filt}" if filt else ""),
                          height=560, showlegend=False, yaxis_visible=False, margin=dict(t=90, b=20), bargap=0.3, title_font=dict(size=22),
                          xaxis=dict(tickfont=dict(size=FS_WATERFALL_AXIS, color=AXIS_COLOR), showgrid=False))
        fig.add_annotation(x=xs[3], y=start * 0.5, showarrow=False,
                           font=dict(size=FS_WATERFALL_DELTA, color="#27AE60" if diff >= 0 else "#E74C3C"),
                           text=f"<b>Δ {space(diff)} ({diff / start * 100:+.2f}%)</b>")
        st.plotly_chart(fig, use_container_width=True, key="waterfall")

        # Analyse hors effet calendrier : chaque mois ramené à une base de 30 jours
        def n30(row, d, c):
            return row[c] * 30 / pd.Timestamp(d).days_in_month
        st.markdown("#### Analyse hors effet calendrier (base 30j)")
        parts = []
        for c, nom, up_color, down_color in [("ga_30", "GA", "green", "red"), ("react_30", "React", "blue", "blue"), ("churn", "Churn", "red", "green")]:
            dv = n30(b, d_to, c) - n30(a, d_from, c)
            parts.append(f":{up_color if dv >= 0 else down_color}[**{'↑ Hausse' if dv >= 0 else '↓ Baisse'} de {nom} : {space(abs(dv))}**]")
        st.markdown(f"[{fm(d_to)}] " + "  ·  ".join(parts))


def map_view(names):
    """Centre et zoom de la carte : s'adapte aux gouvernorats sélectionnés."""
    pts = [COORD[n] for n in names if n in COORD]
    if not pts:
        return {"lat": 33.9, "lon": 9.5}, MAP_ZOOM_DEFAULT
    lats, lons = [p[0] for p in pts], [p[1] for p in pts]
    center = {"lat": (min(lats) + max(lats)) / 2, "lon": (min(lons) + max(lons)) / 2}
    span = max(max(lons) - min(lons), (max(lats) - min(lats)) * 1.3) + MAP_PAD_DEG
    zoom = float(np.clip(np.log2(560 / span), MAP_ZOOM_DEFAULT, MAP_ZOOM_MAX))
    return center, zoom


def build_map(mp, title, zoomed, focus, selected):
    """3 couches : contour des bulles sélectionnées / bulles colorées / chiffres centrés dans les bulles.
    Les chiffres sont dans une couche séparée, centrés : ils ne sont plus décalés par la taille des bulles,
    donc l'affichage est identique dans tous les onglets (ARPU, Churn, Revenu, Base active)."""
    vals = mp["valeur"].clip(lower=0).fillna(0)
    vmax = float(vals.max()) or 1.0
    diam = np.maximum(MAP_BUBBLE_MIN, MAP_BUBBLE_MAX * np.sqrt(vals / vmax))

    txt = mp["valeur_txt"]
    label = (mp["gouvernorat"] + " : " + txt) if zoomed else txt
    if not zoomed and MAP_LABEL_MIN_RATIO > 0:
        label = label.where(vals >= MAP_LABEL_MIN_RATIO * vmax, "")

    cd = mp[["valeur_txt", "gouvernorat"]].values
    hov = "<b>%{customdata[1]}</b><br>" + title + " : <b>%{customdata[0]}</b><extra></extra>"
    is_sel = mp["gouvernorat"].isin(selected).values

    fig = go.Figure()
    # couche 0 : contour noir autour des gouvernorats sélectionnés
    fig.add_trace(go.Scattermap(
        lat=mp["lat"][is_sel].tolist(), lon=mp["lon"][is_sel].tolist(), mode="markers",
        marker=dict(size=(diam[is_sel] + MAP_HALO_PX).tolist(), color=MAP_HALO_COLOR, opacity=1),
        hoverinfo="skip", showlegend=False))
    # couche 1 : bulles
    fig.add_trace(go.Scattermap(
        lat=mp["lat"].tolist(), lon=mp["lon"].tolist(), mode="markers",
        marker=dict(size=diam.tolist(), color=mp["valeur"].tolist(),
                    colorscale=[[0, MAP_COLOR_LOW], [1, MAP_COLOR_HIGH]],
                    cmin=float(mp["valeur"].min()), cmax=float(mp["valeur"].max()),
                    opacity=0.85, showscale=False),
        customdata=cd, hovertemplate=hov, showlegend=False))
    # couche 2 : chiffres centrés
    fig.add_trace(go.Scattermap(
        lat=mp["lat"].tolist(), lon=mp["lon"].tolist(), mode="text",
        text=label.tolist(), textposition="middle center",
        textfont=dict(size=MAP_TEXT_SIZE_ZOOM if zoomed else MAP_TEXT_SIZE, color="#000000"),
        customdata=cd, hovertemplate=hov, showlegend=False))

    center, zoom = map_view(focus)
    fig.update_layout(map=dict(style=MAP_STYLE, center=center, zoom=zoom), height=MAP_HEIGHT,
                      margin=dict(t=0, b=0, l=0, r=0), hoverlabel=dict(font_size=FS_MAP_HOVER),
                      showlegend=False, clickmode="event+select")
    return fig


def clicked_names(pts, mp):
    """Noms des gouvernorats cliqués (lus dans customdata, sinon via l'index du point)."""
    out = []
    names = set(mp["gouvernorat"])
    for p in pts:
        name = None
        cd = p.get("customdata")
        if cd is not None and len(cd) > 1 and cd[1] in names:
            name = cd[1]
        elif p.get("curve_number") in (1, 2):
            idx = p.get("point_index", p.get("point_number"))
            if idx is not None and 0 <= idx < len(mp):
                name = mp.iloc[idx]["gouvernorat"]
        if name and name not in out:
            out.append(name)
    return out


# ---------------- Pages détail : Base active / Churn / Revenu actif / ARPU ----------------
def detail(col):
    title = TITRES[col]
    s = m[col]
    cur = s.get(mois_sel)
    if cur is None or pd.isna(cur):
        st.info("Pas de données pour le mois sélectionné.")
        return
    k = st.columns(4)
    k[0].metric(f"{title} · {fm(mois_sel)}", human(cur))
    show_delta(k[1], "MoM", cur, s.get(prev_d), col)
    show_delta(k[2], "YoY", cur, s.get(yago_d), col)

    reg_k = agg(f[f["date"] == mois_sel], "gouvernorat")          # filtré par la carte
    if "NON RENSEIGNÉ" in reg_k.index:
        k[3].metric("Dont localisation non renseignée", human(reg_k.loc["NON RENSEIGNÉ", col]))

    # Données régionales : toujours TOUS les gouvernorats (sidebar seulement), la sélection est mise en surbrillance
    reg = agg(f_base[f_base["date"] == mois_sel], "gouvernorat")
    reg_prev = agg(f_base[f_base["date"] == prev_d], "gouvernorat")
    reg_yago = agg(f_base[f_base["date"] == yago_d], "gouvernorat")
    r = reg[col].drop("NON RENSEIGNÉ", errors="ignore")
    if r.dropna().empty:
        st.info("Pas de données régionales pour ce mois.")
        return
    rp = reg_prev[col].reindex(r.index)
    ry = reg_yago[col].reindex(r.index)

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(f"**{title} · carte de Tunisie** ({fm(mois_sel)})")
        mp = pd.DataFrame({"valeur": r}).join(pd.DataFrame(COORD, index=["lat", "lon"]).T).dropna(subset=["lat", "lon"])
        mp = mp.rename_axis("gouvernorat").reset_index()
        mp["valeur_txt"] = mp["valeur"].map(human)
        names = list(mp["gouvernorat"])

        geo_in = [g for g in geo_sel if g in names]
        chosen = [g for g in sel.get("gouvernorat", []) if g in names]
        focus = geo_in if (geo_in and MAP_ZOOM_ON_SELECT) else chosen
        zoomed = len(focus) > 0

        fig = build_map(mp, title, zoomed, focus, geo_in)
        ver = st.session_state["mapver"]
        pts = []
        if MAP_CLICK_FILTER:
            try:
                ev = st.plotly_chart(fig, use_container_width=True, key=f"map_{col}_{ver}",
                                     on_select="rerun", selection_mode="points")
                pts = ev["selection"]["points"]
            except Exception:  # ancienne version de Streamlit : pas de clic, on affiche simplement la carte
                st.plotly_chart(fig, use_container_width=True, key=f"map_{col}_{ver}_ro")
                pts = []
        else:
            st.plotly_chart(fig, use_container_width=True, key=f"map_{col}_{ver}_ro")

        clicked = clicked_names(pts, mp)
        sigk = f"mapsig_{col}_{ver}"
        if clicked and st.session_state.get(sigk) != tuple(clicked):
            st.session_state[sigk] = tuple(clicked)
            if multi_click:      # chaque clic ajoute / retire un gouvernorat
                new = [g for g in geo_sel if g not in clicked] + [g for g in clicked if g not in geo_sel]
            else:                # un clic remplace la sélection ; re-cliquer le même gouvernorat l'efface
                new = [] if set(clicked) == set(geo_sel) else clicked
            set_geo(new)
            st.rerun()
        st.caption("💡 Clique sur une bulle pour filtrer tous les graphiques · re-clique pour annuler · "
                   "outil lasso/rectangle de la carte pour en choisir plusieurs.")
    with c2:
        suffix = f" — {', '.join(geo_sel)}" if geo_sel else ""
        st.markdown(f"**{title} · évolution mensuelle**{suffix}")
        st.plotly_chart(evo_chart(s), use_container_width=True, key=f"evo_{col}")

    sel_set = set(geo_sel)
    d1, d2, d3 = st.columns(3)
    good, bad = ("#E74C3C", "#2ECC71") if col == "churn" else ("#2ECC71", "#E74C3C")
    with d1:
        st.markdown(f"**Classement des régions · {title}**")
        rk = r.dropna().sort_values()
        st.plotly_chart(hbar(rk, 720, selected=sel_set), use_container_width=True, key=f"rank_{col}")
    with d2:
        st.markdown(f"**Régions · MoM** ({fm(prev_d)} → {fm(mois_sel)})")
        mom = (r - rp).dropna().sort_values()
        if mom.empty:
            st.info("Pas de données pour le mois précédent.")
        else:
            st.plotly_chart(hbar(mom, 720, [good if v >= 0 else bad for v in mom.values], sel_set),
                            use_container_width=True, key=f"mom_{col}")
    with d3:
        st.markdown(f"**Régions · YoY** ({fm(yago_d)} → {fm(mois_sel)})")
        yoy = (r - ry).dropna().sort_values()
        if yoy.empty:
            st.info("Pas de données pour le même mois de l'année précédente.")
        else:
            st.plotly_chart(hbar(yoy, 720, [good if v >= 0 else bad for v in yoy.values], sel_set),
                            use_container_width=True, key=f"yoy_{col}")


_DETAIL = {"Base active": "base_actif", "Churn": "churn", "Revenu actif": "rev_actif", "ARPU": "arpu"}
if page in _DETAIL:
    detail(_DETAIL[page])
