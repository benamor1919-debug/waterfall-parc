"""Convertit l'export Excel en data/data.csv agrégé (à relancer quand l'Excel change).
Usage : python prepare_data.py Projet_Pbi_Big_data.xlsx
Règles reconstituées depuis le rapport Power BI :
  base_actif = somme(base x flag_30) | churn = somme(base x flag_churn_30) | rev_actif = somme(recharge x flag_30)
"""
import sys
import pandas as pd

src = sys.argv[1] if len(sys.argv) > 1 else "Projet_Pbi_Big_data.xlsx"
d = pd.read_excel(src)
d["localisation"] = d["localisation"].fillna("NON RENSEIGNÉ")
d["base_actif"] = d["base"] * d["flag_30"]
d["churn"] = d["base"] * d["flag_churn_30"]
d["rev_actif"] = d["recharge"] * d["flag_30"]
out = (d.groupby(["mois", "localisation", "prgname", "ligne_pdt", "type_offre"], as_index=False)
         [["base_actif", "churn", "rev_actif"]].sum()
         .rename(columns={"mois": "date", "localisation": "gouvernorat", "prgname": "programme", "ligne_pdt": "ligne_produit"}))
out.to_csv("data/data.csv", index=False)
print(len(out), "lignes -> data/data.csv")
