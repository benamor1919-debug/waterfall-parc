import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ORANGE = "#E8703A"
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
VALS = ["base_actif", "churn", "rev_actif", "ga_30", "react_30"]
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
st.markdown(
    "<div style='background:#000;padding:14px 20px;border-bottom:4px solid #E8703A'>"
    "<h2 style='color:#fff;margin:0'>GeoPulse | Telecom Geomarketing Intelligence</h2>"
    "<span style='color:#fff'>Transformer les données géographiques en décisions commerciales intelligentes.</span></div>",
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
    fig = go.Figure(go.Bar(x=[fm(d) for d in s.index], y=s.values, marker_color=ORANGE,
                           text=[human(v) for v in s.values], textposition="outside"))
    fig.update_layout(height=300, margin=dict(t=20, b=10, l=10, r=10), yaxis_visible=False)
    return fig


def hbar(s, height, colors=None):
    fig = go.Figure(go.Bar(x=s.values, y=s.index, orientation="h", marker_color=colors or ORANGE,
                           text=[human(v) for v in s.values], textposition="outside"))
    fig.update_layout(height=height, margin=dict(t=10, b=10, l=10, r=40), xaxis_visible=False)
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
        xs, bases, heights, colors, texts = [f"Parc<br>{fm(d_from)}"], [0], [start], ["#F4C84B"], [space(start)]
        level = start
        for name, v, color in steps:
            new = level + v
            xs.append(f"{name}<br>{fm(d_to)}")
            bases.append(min(level, new))
            heights.append(abs(v))
            colors.append(color)
            texts.append(f"{'+' if v >= 0 else '-'}{human(abs(v))}")
            level = new
        xs.append(f"Parc<br>{fm(d_to)}")
        bases.append(0); heights.append(end); colors.append("#F4C84B"); texts.append(space(end))
        fig = go.Figure(go.Bar(x=xs, y=heights, base=bases, marker_color=colors, text=texts,
                               textposition=["inside"] + ["outside"] * 4 + ["inside"]))
        filt = " - ".join(" + ".join(v) for v in sel.values() if v)
        diff = end - start
        fig.update_layout(title=f"Waterfall Parc MoM {fm(d_from)} → {fm(d_to)}" + (f" | {filt}" if filt else ""),
                          height=520, showlegend=False, yaxis_visible=False, margin=dict(t=60, b=20))
        fig.add_annotation(x=xs[3], y=start * 0.5, showarrow=False, font=dict(size=18, color="#27AE60" if diff >= 0 else "#E74C3C"),
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

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown(f"**{title} · carte de Tunisie** ({fm(mois_sel)})")
        mp = pd.DataFrame({"valeur": r}).join(pd.DataFrame(COORD, index=["lat", "lon"]).T).dropna(subset=["lat", "lon"])
        mp = mp.rename_axis("gouvernorat").reset_index()
        mp["taille"] = mp["valeur"].clip(lower=0).fillna(0) + 1e-9
        mp["valeur_txt"] = mp["valeur"].map(human)
        fig = px.scatter_map(mp, lat="lat", lon="lon", size="taille", hover_name="gouvernorat",
                             hover_data={"valeur_txt": True, "lat": False, "lon": False, "taille": False},
                             size_max=35, zoom=5.2, center={"lat": 34.0, "lon": 9.5},
                             map_style="open-street-map", height=520, color_discrete_sequence=["#1E90FF"])
        fig.update_traces(marker=dict(opacity=0.7))
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True, key=f"map_{col}")
    with c2:
        st.markdown(f"**{title} · évolution mensuelle**")
        st.plotly_chart(evo_chart(s), use_container_width=True, key=f"evo_{col}")

    d1, d2 = st.columns(2)
    with d1:
        st.markdown(f"**Classement des régions · {title}**")
        rk = r.dropna().sort_values()
        st.plotly_chart(hbar(rk, 640), use_container_width=True, key=f"rank_{col}")
    with d2:
        st.markdown(f"**Régions · MoM ({fm(prev_d)} → {fm(mois_sel)})**")
        mom = (r - rp).dropna().sort_values()
        good, bad = ("#E74C3C", "#2ECC71") if col == "churn" else ("#2ECC71", "#E74C3C")
        st.plotly_chart(hbar(mom, 640, [good if v >= 0 else bad for v in mom.values]),
                        use_container_width=True, key=f"mom_{col}")


for tab, col in zip(tabs[2:], ["base_actif", "churn", "rev_actif", "arpu"]):
    with tab:
        detail(col)
