"""Génère des données FICTIVES pour tester. Remplacez data/data.csv par votre export Power BI."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
gouvs = ["ARIANA","BEJA","BEN AROUS","BIZERTE","GABES","GAFSA","JENDOUBA","KAIROUAN","KASSERINE","KEBELI",
         "KEF","MAHDIA","MANNOUBA","MEDNINE","MONASTIR","NABEUL","SFAX","SIDI BOUZID","SILIANA","SOUSSE",
         "TATAOUINE","TOZEUR","TUNIS","ZAGHOUAN"]
progs = ["Convention","Convention Sol","Entreprise","Grand compte","Grand public","Internet Conve","Internet Entreprise","Internet GP","Internet Grand"]
lignes = ["ADSL","DATA","Autres","FIX BOX","CLE 3G","FLYBOX","FWA 5G","M2M","Mobile"]
types = ["HYBRIDE","POSTPAYE","PREPAYE"]
mois = pd.date_range("2025-08-01", "2026-08-01", freq="MS")
rows = []
for g in gouvs:
    combos = {(rng.choice(progs), rng.choice(lignes), rng.choice(types)) for _ in range(30)}
    for p, l, t in combos:
        base0 = rng.integers(200, 3000)
        for i, d in enumerate(mois):
            base = int(base0 * (1 + 0.01 * i) * rng.uniform(0.95, 1.05))
            churn = int(base * rng.uniform(0.15, 0.30))
            arpu = rng.uniform(5, 15)
            rows.append((d, g, p, l, t, base, churn, round(base * arpu, 2)))
pd.DataFrame(rows, columns=["date","gouvernorat","programme","ligne_produit","type_offre","base_actif","churn","rev_actif"]) \
  .to_csv("data/data.csv", index=False)
print("data/data.csv créé")
