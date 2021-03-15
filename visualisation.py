# -*- coding: utf-8 -*-
"""
script pour visualiser  les données extraites à partir de l'API pushshift et enregistrées dans un csv (voir l'autre script "recup_donnees.py")
"""

import pandas
import os
import matplotlib.pyplot as plt
df = pandas.read_csv("rFrance_2010-2021.csv")
#filtre pour ne récupérer que les posts qui donnent un lien externe
df = df[df["is_self"] == False]
df = df[df["is_reddit_media_domain"] == False]
#group_by par année et par domaine principal, pour voir quel pourcentage chaque domaine représente
total_counts = df.groupby(df.date.dt.year, )["main_domain"].value_counts(normalize=True)*100

#liste des journaux ou sites qu'on veut visualiser dans un seul graph
liste_journaux = [
    # "lemonde.fr",
    "bfmtv.com",
    "lefigaro.fr",
    "liberation.fr",
    # "cnews.fr",
    #"valeursactuelles.com",
    #"mediapart.fr",
    #"marianne.net",
    #"monde-diplomatique.fr",
    #"humanite.fr",
    ]

time_series = total_counts[total_counts.index.get_level_values("main_domain").isin(liste_journaux)]
fig, ax = plt.subplots()
time_series.unstack(level=1).plot(kind='line', ax=ax)
#supprimer les fioritures du graph
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
plt.legend(title='domaine') #, bbox_to_anchor=(1.05, 1), loc='upper left')
#indiquer le chemin de son choix pour enregistrer le graph dans un fichier
plt.savefig(r'export.png')
