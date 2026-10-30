import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ORANGE = "#E8703A"
st.set_page_config(page_title="GeoPulse", page_icon="📡", layout="wide")

st.markdown(
    "<div style='background:#000;padding:14px 20px;border-bottom:4px solid #E8703A'>"
    "<h2 style='color:#fff;margin:0'>GeoPulse | Telecom Geomarketing Intelligence</h2>"
    "<span style='color:#fff'>Transformer les données géographiques en décisions commerciales intelligentes.</span></div>",
    unsafe_allow_html=True,
)

@st.cache_data
def load():
    return pd.read_csv("data/data.csv", parse_dates=["date"])

df = load()

# ---------- Filtres (équivalent des segments Power BI) ----------
with st.sidebar:
    st.header("Filtres")
    sel = {}
    for col, label in [("gouvernorat", "Localisation"), ("programme", "Programme"),
                       ("ligne_produit", "Ligne de produit"), ("type_offre", "Type d'offre")]:
        sel[col] = st.multiselect(label, sorted(df[col].unique()))
    n_mois = st.slider("Nombre de mois affichés", 3, 13, 3)

f = df
for col, vals in sel.items():
    if vals:
        f = f[f[col].isin(vals)]

m = f.groupby("date")[["base_actif", "churn", "rev_actif"]].sum().sort_index()
m["arpu"] = m["rev_actif"] / m["base_actif"]

def human(x):
    a = abs(x)
    if a >= 1e6: return f"{x/1e6:.1f}M"
    if a >= 1e3: return f"{x/1e3:.1f}K"
    return f"{x:.1f}"

def block(col, title, container):
    s = m[col]
    last = s.index.max()
    cur = s[last]
    prev = s.get(last - pd.DateOffset(months=1))
    yago = s.get(last - pd.DateOffset(years=1))
    with container:
        st.subheader(f"{title} · évolution mensuelle")
        c1, c2 = st.columns([3, 1])
        view = s.tail(n_mois)
        fig = go.Figure(go.Bar(x=view.index.strftime("%b %Y"), y=view.values,
                               marker_color=ORANGE, text=[human(v) for v in view.values],
                               textposition="outside"))
        fig.update_layout(height=300, margin=dict(t=20, b=10, l=10, r=10), yaxis_visible=False)
        c1.plotly_chart(fig, use_container_width=True)
        with c2:
            if prev is not None:
                c2.metric("MoM", human(cur - prev), f"{(cur/prev-1)*100:+.1f} %",
                          delta_color="inverse" if col == "churn" else "normal")
            if yago is not None:
                c2.metric("YoY", human(cur - yago), f"{(cur/yago-1)*100:+.1f} %",
                          delta_color="inverse" if col == "churn" else "normal")

if m.empty:
    st.warning("Aucune donnée pour cette sélection.")
else:
    a, b = st.columns(2)
    block("base_actif", "Base active", a)
    block("churn", "Churn", b)
    c, d = st.columns(2)
    block("rev_actif", "Revenu actif", c)
    block("arpu", "ARPU", d)
