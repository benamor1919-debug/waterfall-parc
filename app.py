import base64
import os
from string import Template

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ORANGE = "#E8703A"
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
VALS = ["base_actif", "churn", "rev_actif", "ga_30", "react_30"]

# =====================================================================
#                 PARAMÈTRES D'AFFICHAGE  (modifie ici)
# =====================================================================
# --- Chiffres des graphiques (taille en px) ---
NUM_BOLD = True            # True = chiffres en gras, False = normal
NUM_COLOR = "#000000"      # couleur des chiffres
FS_WATERFALL = 24          # chiffres du waterfall
FS_WATERFALL_DELTA = 28    # grand "Δ" au centre du waterfall
FS_WATERFALL_AXIS = 18     # libellés sous le waterfall (Parc, GA, React...)
FS_EVO = 22                # chiffres des graphes d'évolution mensuelle (VUE 360, Base active, Churn, Revenu, ARPU)
FS_EVO_AXIS = 18           # libellés des mois sous ces graphes
FS_HBAR = 20               # chiffres des classements régions / MoM / YoY
FS_HBAR_AXIS = 17          # noms des régions
FS_MAP_HOVER = 16          # texte de l'infobulle de la carte

# --- Barre latérale (filtres) ---
SB_BG = "#E4E7EC"          # couleur de fond de la barre
SB_PADDING = 24            # marge gauche/droite (px)
SB_TITLE_SIZE = 36         # titre "Filtres"
SB_LABEL_SIZE = 22         # Localisation, Programme, Ligne de produit...
SB_VALUE_SIZE = 20         # contenu des champs (Choose options, août 2026...)
SB_TAG_SIZE = 18           # valeurs sélectionnées (ex. ARIANA)
SB_OPTION_SIZE = 20        # liste déroulante des options
SB_FIELD_HEIGHT = 60       # hauteur des champs

# --- Onglets (VUE 360, Waterfall, Base active...) ---
TAB_FONT_SIZE = 24         # taille du texte
TAB_HEIGHT = 66            # hauteur
TAB_PADDING_X = 34         # espace horizontal dans chaque onglet
TAB_GAP = 12               # espace entre les onglets
TAB_BG = "#F3F4F6"         # fond des onglets
TAB_TEXT = "#374151"       # texte des onglets
TAB_ACTIVE_BG = ORANGE     # fond de l'onglet actif
TAB_ACTIVE_TEXT = "#FFFFFF"  # texte de l'onglet actif
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
/* ===== Barre latérale ===== */
[data-testid="stSidebar"] { background-color: ${SB_BG}; }
[data-testid="stSidebarUserContent"] { padding-left: ${SB_PADDING}px !important; padding-right: ${SB_PADDING}px !important; }
[data-testid="stSidebar"] h2 { font-size: ${SB_TITLE_SIZE}px !important; font-weight: 800 !important; color: #000 !important; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label p {
    font-size: ${SB_LABEL_SIZE}px !important; font-weight: 800 !important; color: #000 !important;
}

/* Contenu des champs (Choose options, août 2026, ...) */
[data-testid="stSidebar"] [data-testid="stSelectbox"] *,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] *,
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [role="combobox"],
[data-testid="stSidebar"] input {
    font-size: ${SB_VALUE_SIZE}px !important; font-weight: 700 !important;
}
[data-testid="stSidebar"] input::placeholder { color: #374151 !important; opacity: 1 !important; font-weight: 700 !important; font-size: ${SB_VALUE_SIZE}px !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] div${_NOT_TAG},
[data-testid="stSidebar"] [data-testid="stMultiSelect"] div${_NOT_TAG},
[data-testid="stSidebar"] [data-baseweb="select"] div${_NOT_TAG} { min-height: ${SB_FIELD_HEIGHT}px; }
[data-testid="stSidebar"] [data-baseweb="select"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] { background-color: #FFFFFF; border-radius: 8px; box-shadow: 0 0 0 2px #9AA3AF; }

/* Valeurs sélectionnées (ex. ARIANA) */
[data-testid="stSidebar"] [data-baseweb="tag"],
[data-testid="stSidebar"] [data-baseweb="tag"] * { font-size: ${SB_TAG_SIZE}px !important; font-weight: 700 !important; min-height: 0 !important; }

/* Liste déroulante des options (affichée hors de la barre latérale) */
[data-baseweb="popover"] li, [data-baseweb="popover"] li *,
[role="listbox"] *, [role="option"], [role="option"] *,
[data-testid="stSelectboxVirtualDropdown"] * {
    font-size: ${SB_OPTION_SIZE}px !important; font-weight: 600 !important;
}

/* ===== Onglets ===== */
[role="tablist"], [data-baseweb="tab-list"] { gap: ${TAB_GAP}px !important; border-bottom: 3px solid ${TAB_ACTIVE_BG} !important; padding-top: 8px; }
button[role="tab"], button[data-baseweb="tab"], button[data-testid="stTab"] {
    height: ${TAB_HEIGHT}px !important; padding: 0 ${TAB_PADDING_X}px !important; background-color: ${TAB_BG} !important;
    border-radius: 12px 12px 0 0 !important; transition: all 0.2s ease;
}
button[role="tab"], button[role="tab"] *, button[data-baseweb="tab"] *, button[data-testid="stTab"] * {
    font-size: ${TAB_FONT_SIZE}px !important; font-weight: 800 !important; color: ${TAB_TEXT} !important;
}
button[role="tab"]:hover { background-color: #FDE5D8 !important; }
button[role="tab"][aria-selected="true"] { background-color: ${TAB_ACTIVE_BG} !important; }
button[role="tab"][aria-selected="true"], button[role="tab"][aria-selected="true"] * { color: ${TAB_ACTIVE_TEXT} !important; }
[data-baseweb="tab-highlight"] { background-color: #000000 !important; height: 4px !important; }
[data-baseweb="tab-border"] { background-color: transparent !important; }
""")
_css_txt = _CSS.safe_substitute(globals())

# Injection 1 : balise <style> classique
st.markdown(f"<style>{_css_txt}</style>", unsafe_allow_html=True)

# Injection 2 : via JavaScript directement dans la page (contourne les filtres de Streamlit)
import json
import streamlit.components.v1 as components
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
    "<div style='background:#000;padding:12px 20px;border-bottom:4px solid #E8703A;display:flex;align-items:center;justify-content:space-between'>"
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


@st.cache_data
def load():
    return pd.read_csv("data.csv", parse_dates=["date"])


df = load()
dates = [pd.Timestamp(x) for x in sorted(df["date"].unique())]

# ---------------- Filtres (équivalent des segments Power BI) ----------------
with st.sidebar:
    st.header("Filtres")
    sel = {}
    for col, label in [("gouvernorat", "Localisation"), ("programme", "Programme"),
                       ("ligne_produit", "Ligne de produit"), ("type_offre", "Type d'offre")]:
        sel[col] = st.multiselect(label, sorted(df[col].unique()))
    mois_sel = st.selectbox("Mois des KPI et de la carte", dates, index=len(dates) - 1, format_func=fm)

f = df
for col, vals in sel.items():
    if vals:
        f = f[f[col].isin(vals)]
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
        x=[fm(d) for d in s.index], y=s.values, marker_color=ORANGE,
        text=[bold(human(v)) for v in s.values], textposition="outside",
        textfont=dict(size=FS_EVO, color=NUM_COLOR), outsidetextfont=dict(size=FS_EVO, color=NUM_COLOR),
        cliponaxis=False))
    fig.update_layout(height=360, margin=dict(t=60, b=10, l=10, r=10), yaxis_visible=False,
                      xaxis=dict(tickfont=dict(size=FS_EVO_AXIS)))
    return fig


def hbar(s, height, colors=None):
    fig = go.Figure(go.Bar(
        x=s.values, y=s.index, orientation="h", marker_color=colors or ORANGE,
        text=[bold(human(v)) for v in s.values], textposition="outside",
        textfont=dict(size=FS_HBAR, color=NUM_COLOR), outsidetextfont=dict(size=FS_HBAR, color=NUM_COLOR),
        cliponaxis=False))
    fig.update_layout(height=height, margin=dict(t=30, b=10, l=70, r=90), xaxis_visible=False,
                      yaxis=dict(tickfont=dict(size=FS_HBAR_AXIS), automargin=True))
    return fig


TITRES = {"base_actif": "Base active", "churn": "Churn", "rev_actif": "Revenu actif", "arpu": "ARPU"}

tabs = st.tabs(["VUE 360", "Waterfall", "Base active", "Churn", "Revenu actif", "ARPU"])

# ---------------- VUE 360 ----------------
with tabs[0]:
    cols = st.columns(2)
    for i, col in enumerate(["base_actif", "churn", "rev_actif", "arpu"]):
        with cols[i % 2]:
            st.subheader(f"{TITRES[col]} · évolution mensuelle")
            c1, c2 = st.columns([3, 1])
            c1.plotly_chart(evo_chart(m[col]), use_container_width=True, key=f"vue_{col}")
            cur = m[col].get(mois_sel)
            show_delta(c2, "MoM", cur, m[col].get(prev_d), col)
            show_delta(c2, "YoY", cur, m[col].get(yago_d), col)

# ---------------- Waterfall ----------------
with tabs[1]:
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
        xs, bases, heights, colors, texts = [f"Parc<br>{fm(d_from)}"], [0], [start], ["#F4C84B"], [bold(space(start))]
        level = start
        for name, v, color in steps:
            new = level + v
            xs.append(f"{name}<br>{fm(d_to)}")
            bases.append(min(level, new))
            heights.append(abs(v))
            colors.append(color)
            texts.append(bold(f"{'+' if v >= 0 else '-'}{human(abs(v))}"))
            level = new
        xs.append(f"Parc<br>{fm(d_to)}")
        bases.append(0); heights.append(end); colors.append("#F4C84B"); texts.append(bold(space(end)))
        fig = go.Figure(go.Bar(x=xs, y=heights, base=bases, marker_color=colors, text=texts,
                               textposition=["inside"] + ["outside"] * 4 + ["inside"],
                               textfont=dict(size=FS_WATERFALL, color=NUM_COLOR),
                               insidetextfont=dict(size=FS_WATERFALL + 2, color=NUM_COLOR),
                               outsidetextfont=dict(size=FS_WATERFALL, color=NUM_COLOR),
                               cliponaxis=False))
        filt = " - ".join(" + ".join(v) for v in sel.values() if v)
        diff = end - start
        fig.update_layout(title=f"Waterfall Parc MoM {fm(d_from)} → {fm(d_to)}" + (f" | {filt}" if filt else ""),
                          height=560, showlegend=False, yaxis_visible=False, margin=dict(t=90, b=20),
                          xaxis=dict(tickfont=dict(size=FS_WATERFALL_AXIS)))
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

    reg = agg(f[f["date"] == mois_sel], "gouvernorat")
    if "NON RENSEIGNÉ" in reg.index:
        k[3].metric("Dont localisation non renseignée", human(reg.loc["NON RENSEIGNÉ", col]))
    reg_prev = agg(f[f["date"] == prev_d], "gouvernorat")
    r = reg[col].drop("NON RENSEIGNÉ", errors="ignore")
    rp = reg_prev[col].reindex(r.index)
    reg_yago = agg(f[f["date"] == yago_d], "gouvernorat")
    ry = reg_yago[col].reindex(r.index)

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(f"**{title} · carte de Tunisie** ({fm(mois_sel)})")
        mp = pd.DataFrame({"valeur": r}).join(pd.DataFrame(COORD, index=["lat", "lon"]).T).dropna(subset=["lat", "lon"])
        mp = mp.rename_axis("gouvernorat").reset_index()
        mp["taille"] = mp["valeur"].clip(lower=0).fillna(0) + 1e-9
        mp["valeur_txt"] = mp["valeur"].map(human)
        fig = px.scatter_map(mp, lat="lat", lon="lon", size="taille", hover_name="gouvernorat",
                             hover_data={"valeur_txt": True, "lat": False, "lon": False, "taille": False},
                             size_max=35, zoom=5.5, center={"lat": 33.9, "lon": 9.5},
                             map_style="open-street-map", height=600, color_discrete_sequence=["#1E90FF"])
        fig.update_traces(marker=dict(opacity=0.7))
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), hoverlabel=dict(font_size=FS_MAP_HOVER))
        st.plotly_chart(fig, use_container_width=True, key=f"map_{col}")
    with c2:
        st.markdown(f"**{title} · évolution mensuelle**")
        st.plotly_chart(evo_chart(s), use_container_width=True, key=f"evo_{col}")

    d1, d2, d3 = st.columns(3)
    good, bad = ("#E74C3C", "#2ECC71") if col == "churn" else ("#2ECC71", "#E74C3C")
    with d1:
        st.markdown(f"**Classement des régions · {title}**")
        rk = r.dropna().sort_values()
        st.plotly_chart(hbar(rk, 720), use_container_width=True, key=f"rank_{col}")
    with d2:
        st.markdown(f"**Régions · MoM** ({fm(prev_d)} → {fm(mois_sel)})")
        mom = (r - rp).dropna().sort_values()
        st.plotly_chart(hbar(mom, 720, [good if v >= 0 else bad for v in mom.values]),
                        use_container_width=True, key=f"mom_{col}")
    with d3:
        st.markdown(f"**Régions · YoY** ({fm(yago_d)} → {fm(mois_sel)})")
        yoy = (r - ry).dropna().sort_values()
        if yoy.empty:
            st.info("Pas de données pour le même mois de l'année précédente.")
        else:
            st.plotly_chart(hbar(yoy, 720, [good if v >= 0 else bad for v in yoy.values]),
                            use_container_width=True, key=f"yoy_{col}")


for tab, col in zip(tabs[2:], ["base_actif", "churn", "rev_actif", "arpu"]):
    with tab:
        detail(col)
