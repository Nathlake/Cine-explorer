import numpy as np
import pandas as pd
import requests
import json
from st_click_detector import click_detector
import streamlit as st

def load_movie_data(json_file):
    with open(json_file, "r", encoding="utf-8") as file:
        return json.load(file)

movie_data = load_movie_data("movie_data_with_videos.json")

def trouver_id(film_id: int, movie_data: list=movie_data):
    """
    Rechercher un film dans la liste des films par son ID.
    """
    for film in movie_data:
        if film.get("id") == film_id:
            return film
    return None

def get_clicked(movie_data: list, film_title: str, idx: int, categorie: str, annee: int = None, key_: bool = False):
    """
    Gère le clic sur un film pour une liste de films avec filtrage possible par année, par genre.
    """

    # Filtrage par année si une année est spécifiée
    if annee:
        movie_data = [film for film in movie_data if film.get("year") == annee]

    # Trouver le film par son index
    film = trouver_id(idx, movie_data)
    if not film:
        print(f"Aucun film trouvé pour l'ID : {idx}")
        return None, False
    
    film_id = film.get("id", None)
    film_title = film.get("title", "Titre inconnu")
    poster_path = film.get('poster_path', None)

    # image manquante
    if poster_path:
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
    else:
        print(f"Image manquante pour le film : {film_title}")
        poster_url = "https://via.placeholder.com/150x225.png?text=Image+Manquante&bg=transparent"

    # Clé unique sur 'id'
    unique_key = f"film_{categorie}_{film_id}_{idx}"

    content = f"""
    <div style="
        text-align: center; 
        cursor: pointer; 
        display: inline-flex;  
        flex-direction: column;  
        justify-content: flex-start;  
        align-items: center;  
        margin: 8px 0 0 0; /* Ajout d'une marge en haut */
        padding: 0; 
        background-color: transparent;
        border-radius: 15px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
        width: calc(100% - 16px);
        overflow: hidden;
        line-height: 0;
        position: relative;
    ">
        <a id="{unique_key}" href="#" style="
            display: block; 
            background-color: transparent; 
            line-height: 0;
            width: 100%; 
            padding: 0; 
            margin: 0;
            overflow: hidden;
        ">
            <img src="{poster_url}" 
                 style="
                    width: 100%; 
                    height: 100%; /* Permet à l'image de remplir tout le conteneur */
                    border-radius: 15px;
                    object-fit: cover; /* Cela permet de rogner l'image pour qu'elle remplisse le conteneur sans déformer */
                    vertical-align: bottom;
                    margin: 0;
                    padding: 0;
                    display: block;
                    overflow: hidden; /* Assure qu'il n'y a pas de débordement */
                 "/>
        </a>
        <div style="
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 5px;
        ">
            <p style="
                color: white; 
                font-size: 14px; 
                font-weight: bold; 
                margin: 0; 
                padding: 0;
                line-height: 1.2;  
                text-align: center;
            ">        
        </div>
    </div>
    """

    return idx, click_detector(content, key=unique_key)


def get_actor_clicked(actors_data: list, actor_names_list: list, nb: int, key_: bool = False):
    """
    Gère le clic sur un acteur pour une liste d'acteurs donnée.
    
    Arguments:
        actors_data (list): Liste des détails des acteurs.
        actor_names_list (list): Liste des noms des acteurs.
        nb (int): Index de l'acteur actuel dans la liste.
        key_ (bool): Active une clé unique pour le détecteur de clic.

    Returns:
        tuple: Index de l'acteur et état du clic.
    """
    if nb >= len(actor_names_list):
        return None, None

    # Recherche de l'acteur par nom
    actor_name = actor_names_list[nb]
    actor = next((a for a in actors_data if a["name"] == actor_name), None)
    if not actor:
        return None, None

    # Récupération des détails de l'acteur
    index = actors_data.index(actor)
    image_link = f"https://image.tmdb.org/t/p/w500{actor.get('profile_path', '')}"
    name_actor = actor["name"]

    # Récupérer la filmographie de l'acteur
    films = get_actor_films(actor_name, actors_data)

    # Affichage de l'image de l'acteur dans Streamlit avec un bouton pour chaque acteur
    col = st.columns(1)  # Utilisation de colonnes pour un meilleur alignement
    with col[0]:
        st.markdown(f"<h4>{name_actor}</h4>", unsafe_allow_html=True)
        actor_image = st.image(image_link, caption=name_actor, width=150)

        # Afficher la filmographie de l'acteur
        if films:
            st.markdown("<h5>Films :</h5>", unsafe_allow_html=True)
            for film in films:
                st.markdown(f"- {film}")

        # Créer un bouton pour chaque acteur
        if st.button(f"Voir les détails de {name_actor}", key=f"actor_{nb}_{key_}"):
            st.session_state.selected_person = actor_name  # Mémoriser l'acteur sélectionné
            st.session_state.page = "actor_details"  # Définir la page comme celle de l'acteur
            st.experimental_rerun()  # Rediriger vers la page des détails de l'acteur

    return index, True  # Retourne l'index et indique qu'un clic a eu lieu

def get_actor_films(actor_name, actors_data):
    """
    Récupère la filmographie d'un acteur à partir des données d'acteurs.
    
    Arguments:
        actor_name (str): Le nom de l'acteur.
        actors_data (list): Liste des données des acteurs.

    Returns:
        list: Liste des titres de films dans lesquels l'acteur a joué.
    """
    films = []
    for row in actors_data:
        # Recherche de l'acteur dans les colonnes des acteurs
        for i in range(1, 4):
            actor_key = f"actor_{i}"
            if row.get(actor_key) == actor_name:
                film_id = row["tconst"]
                film_title = row.get("title", "Titre inconnu")  # Récupérer le titre du film
                films.append(film_title)
    return films

def display_banner():
    # Vérifier si la page actuelle n'est pas "personnage"
    if st.session_state.page != "personnage":
        st.markdown(
            """
            <div style="background-color: #000; color: #fff; padding: 10px; text-align: center; font-size: 20px;">
                À la recherche du film parfait ? Laissez-nous vous guider ! 🍿
            </div>
            """,
            unsafe_allow_html=True
        )

