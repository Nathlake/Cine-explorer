import numpy as np
import pandas as pd
import requests
import json
from st_click_detector import click_detector
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder, StandardScaler
from sklearn.preprocessing import FunctionTransformer
from io import BytesIO

# Fonction pour charger les données du fichier JSON
def load_movie_data(json_file):
    with open(json_file, "r", encoding="utf-8") as file:
        return json.load(file)

# Chargement des données
movie_data = load_movie_data("movie_data_with_videos.json")


# Lien direct de téléchargement du fichier Google Drive
file_id = '1cEo3sSPwn4y3FKnEYEaPK5f2PWHTUtgX'
url = f'https://drive.google.com/uc?export=download&id={file_id}'

# Télécharger le fichier depuis Google Drive
response = requests.get(url)

# Vérifiez si la demande a réussi (code 200)
if response.status_code == 200:
    # Charger le fichier Parquet dans pandas à partir du contenu téléchargé
    data = pd.read_parquet(BytesIO(response.content))
    print(data.head())  # Affiche les premières lignes du dataframe
else:
    print(f"Erreur lors du téléchargement : {response.status_code}")

# Fonction pour rechercher un film par ID
def trouver_id(film_id: int, movie_data: list = movie_data):
    for film in movie_data:
        if film.get("id") == film_id:
            return film
    return None

# Fonction de gestion du clic sur un film

def get_clicked(movie_data: list, film_title: str, film_id: int, categorie: str, annee: int = None):
    poster_url = get_poster_url(film_id)
    
    if st.image(poster_url, use_column_width=True, caption=film_title):
        st.session_state.clicked_film = film_title
        st.session_state.clicked_film_id = film_id
        st.session_state.page = "details"
        return True
    return False


# Fonction de recherche des films par réalisateur
def films_director(name: str, data: pd.DataFrame = data) -> list:
    data = data[data['director'].str.contains(name, case=False)]
    results = data.sort_values(by=['averageRating', 'numVotes'], ascending=False).head(5)
    return results['tconst'].to_list()

# Fonction de recherche des films par acteur
def films_actor(name: str, data: pd.DataFrame = data) -> list:
    films_acteur1 = data[data['actor_1'].str.contains(name, case=False)]
    films_acteur2 = data[data['actor_2'].str.contains(name, case=False)]
    films_acteur3 = data[data['actor_3'].str.contains(name, case=False)]
    
    combined_data = pd.concat([films_acteur1, films_acteur2, films_acteur3]).drop_duplicates(subset=['title'])
    results = combined_data.sort_values(by=['averageRating', 'numVotes'], ascending=False).head(5)
    return results['tconst'].to_list()

def creer_pipeline(data):
    if 'genre_list' not in data.columns or 'list_actor' not in data.columns:
        raise ValueError("Les colonnes 'genre_list' et 'list_actor' sont nécessaires pour entraîner le pipeline.")

    df_to_fit = data[['director', 'genre_list', 'list_actor', 'numVotes', 'averageRating']]
    
    # Création du pipeline avec le préprocesseur et le KNN
    mlb_transformer = FunctionTransformer(lambda x: MultiLabelBinarizer().fit_transform(x), validate=False)
    preprocessor = ColumnTransformer(
        transformers=[
            ('réalisateur', OneHotEncoder(), ['director']),
            ('genres', mlb_transformer, 'genre_list'),
            ('acteurs', mlb_transformer, 'list_actor'),
            ('numvotes', StandardScaler(), ['numVotes']),
            ('note', 'passthrough', ['averageRating'])
        ]
    )

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('knn', NearestNeighbors(n_neighbors=5))
    ])
    
    # Créer et entraîner le pipeline
    pipeline.fit(df_to_fit)
    return pipeline


# Fonction pour rechercher les voisins d'un film
def chercher_voisins_id(id: int, pipeline: Pipeline, data: pd.DataFrame) -> list:
    data_scale = pipeline.named_steps["preprocessor"].transform(data[data['tconst'] == id].drop(columns=['tconst']))
    distances, indices = pipeline.named_steps['knn'].kneighbors(data_scale)
    voisins = data.iloc[indices[0][1:]].copy()  # Exclure le film lui-même
    voisins['Distance'] = distances[0][1:]
    return voisins['tconst'].to_list()

def display_banner():
    if st.session_state.page != "personnage":
        st.markdown(
            """
            <div style="background-color: #000; color: #fff; padding: 10px; text-align: center; font-size: 20px;">
                À la recherche du film parfait ? Laissez-nous vous guider ! 🍿
            </div>
            """,
            unsafe_allow_html=True
        )

