# app.py – Movie Recommender (Tiffany‑blue theme, dict-style pickle)
# Updated with error handling and safe lookups

# -------------------------------------------------
# Imports
# -------------------------------------------------
import os
import pathlib
import pickle
import sys

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# -------------------------------------------------
# Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
)

# -------------------------------------------------
# Custom CSS – Tiffany‑blue theme
# -------------------------------------------------
CUSTOM_CSS = """
<style>
body {
    background-color: #0ABAB5;
    color: #ffffff;
}

section[data-testid="stSidebar"],
div[data-testid="stBlockContainer"] {
    background-color: #0ABAB5;
    border-radius: 8px;
}

h1, h2, h3, h4, h5, h6 {
    color: #006D71;
}

a {
    color: #ffffff;
    text-decoration: underline;
}

/* Ensure text is visible */
.stMarkdown, .stDataFrame, .stTable {
    color: #ffffff !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------------------------
# Helper: Get absolute paths
# -------------------------------------------------
def get_file_path(filename):
    """Returns the absolute path to a file in the same directory as this script."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

# -------------------------------------------------
# Logo
# -------------------------------------------------
logo_path = get_file_path("logo.png")
if os.path.isfile(logo_path):
    st.sidebar.image(logo_path, width=120)
else:
    st.sidebar.warning(
        "⚠️ `logo.png` not found – please add it next to `app.py`"
    )

# -------------------------------------------------
# Load movie data
# -------------------------------------------------
movies_path = get_file_path("movies.csv")

try:
    movies = pd.read_csv(movies_path)
    
    # Validate columns
    if "movieId" not in movies.columns or "title" not in movies.columns:
        st.error("❌ Error: 'movies.csv' must contain 'movieId' and 'title' columns.")
        st.stop()

    movie_dict = movies.set_index("movieId")["title"].to_dict()
    
except FileNotFoundError:
    st.error(f"❌ Error: Could not find 'movies.csv' at {movies_path}.")
    st.stop()
except Exception as e:
    st.error(f"❌ Error loading movies.csv: {e}")
    st.stop()

# -------------------------------------------------
# Sidebar filters
# -------------------------------------------------
st.sidebar.header("🔧 Filters")
min_confidence = st.sidebar.slider(
    "Minimum confidence for recommendations",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.01,
)
search_movie = st.sidebar.text_input("Search for a movie", "")

# -------------------------------------------------
# Load rules pickle (dict-style)
# -------------------------------------------------
rules_path = get_file_path("rules.pkl")
rules = []

try:
    with open(rules_path, "rb") as f:
        rules = pickle.load(f)
        
    if not isinstance(rules, list):
        st.error("❌ Error: The loaded
