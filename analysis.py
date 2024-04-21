# coding=utf-8
""" """
# Copyright 2023, Swiss Statistical Design & Innovation Sàrl

import pandas as pd

from plotly import graph_objects as go
import streamlit as st
from streamlit_searchbox import st_searchbox

st.set_page_config(
    page_title="Villes dangereuses en France",
)

st.title("Analyse de la dangerosité des villes en France")

st.markdown("""
Le site **ville-data.com** a proposé un classement des villes les plus dangereuses en France. Le classement est disponible à l'adresse suivante: https://ville-data.com/delinquance/classement-des-villes-les-plus-dangereuses-de-france. Cependant, ce **classement a fait polémique sur les réseaux sociaux**. 
Étant donné que les données sont disponibles, nous vous proposons d'explorer vous-mêmes ces données pour vous faire votre propre opinion.
            
Lien pour le téléchargement des données: https://www.data.gouv.fr/fr/datasets/bases-statistiques-communale-departementale-et-regionale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales/
""")

st.divider()
            
st.header('Choix des paramètres')

@st.cache_data
def load_data():

    df = pd.DataFrame()

    for i in range(2016, 2024):
        tmp = pd.read_csv(f'data/data_{i}.csv')

        df = pd.concat([df, tmp])

    return df

df = load_data()

years = df['Annee'].unique()

year_chosen = st.selectbox(
    "Quelle année souhaitez-vous explorer?",
    years[::-1],
    label_visibility='visible',
)

categories = df['Categorie'].unique()

categories_chosen = st.multiselect(
    "Quelle catégories souhaitez-vous sélectionner?",
    categories,
    categories,
    label_visibility='visible',
)

min_size_city = st.number_input(
    "Quelle est la taille minimale de la ville?",
    min_value=0,
    value=0,
    step=1000,
    format='%d',
)

showing = st.selectbox(
    "Voulez-vous voir les taux les plus hauts ou les plus bas?",
    ['plus hauts', 'plus bas'],
    label_visibility='visible',
)

how_many = st.number_input(
    "Combien de villes voulez-vous voir?",
    min_value=1,
    value=10,
    step=1,
    max_value=50,
    format='%d',
)

st.divider()


st.header(f'Classement des villes avec taux de criminalité les {showing}')

def filter_data(df, year, categories, min_size_city):
    df_filtered = df[(df['Annee'] == year) & (df['Population'] >= min_size_city) & (df['Categorie'].isin(categories))]

    return df_filtered

df_filtered = filter_data(df, year_chosen, categories_chosen, min_size_city)

def get_ranking(df, showing):
    df_ranking = df.groupby('Commune').agg({'Faits': 'sum', 'Population': 'mean'})

    df_ranking['Taux pour mille'] = df_ranking['Faits'] / df_ranking['Population'] * 1000

    if showing == 'plus hauts':
        ascending = False
    else:
        ascending = True

    df_ranking.sort_values(by='Taux pour mille', ascending=ascending, inplace=True)
    df_ranking['Rang'] = df_ranking['Taux pour mille'].rank(ascending=ascending, method='min')

    return df_ranking

df_ranking = get_ranking(df_filtered, showing)

ranks = ""

for i in range(how_many):
    ranks += f"{int(df_ranking.iloc[i]['Rang'])}. **{df_ranking.index[i]}** - {int(df_ranking.iloc[i]['Faits']):d} faits pour {int(df_ranking.iloc[i]['Population']):d} habitants ({df_ranking.iloc[i]['Taux pour mille']:.2f}‰)\n"

st.write(ranks)

with st.expander("Voir la liste complète"):
    st.dataframe(df_ranking, use_container_width=True)

list_cities = df_ranking.index.tolist()

cities_chosen = st.multiselect(
    "Vous cherchez des villes en particulier?",
    list_cities,
    [],
    label_visibility='visible',
)

if len(cities_chosen) > 0:

    for city in cities_chosen:

        nbr_inhab = " " if min_size_city == 0 else f", de plus de {min_size_city} habitants, "

        str_res = f"**{city}** est la {int(df_ranking.loc[city]['Rang']):d}e / {len(df_ranking)} ville{nbr_inhab}avec le plus {'haut' if showing == 'plus hauts' else 'bas'} taux de criminalité en France en {year_chosen} avec {int(df_ranking.loc[city]['Faits']):d} faits pour {int(df_ranking.loc[city]['Population']):d} habitants ({df_ranking.loc[city]['Taux pour mille']:.2f}‰)."
        st.write(str_res)

st.divider()

st.header('Évolution au cours du temps')

list_cities_evo = df['Commune'].unique()

cities_chosen_evo = st.multiselect(
    "Choississez les villes pour lesquelles vous voulez voir l'évolution",
    list_cities_evo,
    [],
    label_visibility='visible',
)

categories_chosen_evo = st.multiselect(
    "Quelle catégories souhaitez-vous sélectionner?",
    categories,
    categories,
    label_visibility='visible',
    key='categories_evo',
)

def filter_data_evo(df, cities, categories):
    df_filtered = df[(df['Commune'].isin(cities)) & (df['Categorie'].isin(categories))]

    df_filtered = df_filtered.groupby(['Commune', 'Annee']).agg({'Faits': 'sum', 'Population': 'mean'}).reset_index()

    df_filtered['Taux pour mille'] = df_filtered['Faits'] / df_filtered['Population'] * 1000

    return df_filtered

df_filtered_evo = filter_data_evo(df, cities_chosen_evo, categories_chosen_evo)

fig = go.Figure()

for city in cities_chosen_evo:
    df_city = df_filtered_evo[df_filtered_evo['Commune'] == city]

    fig.add_trace(go.Scatter(
        x=df_city['Annee'],
        y=df_city['Taux pour mille'],
        mode='lines+markers',
        name=city,
    ))

fig.update_layout(
    title=f"Évolution du taux de criminalité pour {', '.join(cities_chosen_evo)}",
    xaxis_title='Année',
    yaxis_title='Taux pour mille',
)

st.plotly_chart(fig)