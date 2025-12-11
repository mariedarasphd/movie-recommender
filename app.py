# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import pickle

# --------------------------
# Page Config
# --------------------------
st.set_page_config(
    page_title="Golden Age Movie Recommender",
    layout="wide"
)

# --------------------------
# Tiffany Blue Theme
# --------------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #E0F7FA;
        color: #0ABAB5;
    }
    h1, h2, h3, h4 {
        color: #0ABAB5;
    }
    .stButton>button {
        background-color: #0ABAB5;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------------
# Centered Logo
# --------------------------
st.image("mariedaraslogo.png", width=200)
st.title("🎬 Golden Age Movie Recommender")

# --------------------------
# Load Data from repo
# --------------------------
@st.cache_data
def load_data():
    movies = pd.read_csv("movies.csv")
    ratings = pd.read_csv("ratings.csv")

    df = pd.merge(movies, ratings, on='movieId', how='outer')
    df[['Movie', 'Year']] = df['title'].str.extract(r'(.+?)\s*\((\d{4})\)')
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df_clean = df.dropna(subset=['userId','rating','Year'])

    golden_age = df_clean[(df_clean['Year'] >= 1930) & (df_clean['Year'] <= 1969)]

    top_movies = golden_age['movieId'].value_counts().nlargest(500).index
    filtered_data = golden_age[golden_age['movieId'].isin(top_movies)]

    filtered_data = filtered_data[~filtered_data['Movie'].str.contains('Disney', na=False)]
    filtered_data = filtered_data[~filtered_data['genres'].str.contains("Childre|Family", na=False)]

    transactions = filtered_data.groupby('userId')['movieId'].apply(list).tolist()
    movie_dict = movies.set_index('movieId')['title'].to_dict()

    return transactions, movie_dict

transactions, movie_dict = load_data()

# --------------------------
# Sidebar Inputs
# --------------------------
min_confidence = st.sidebar.slider("Minimum confidence for recommendations", 0.5, 1.0, 0.7, 0.05)
search_movie = st.sidebar.text_input("Search for a movie", "")

# --------------------------
# Load precomputed Apriori rules
# --------------------------
with open("rules.pkl", "rb") as f:
    rules = pickle.load(f)

# --------------------------
# Build Recommendation Table
# --------------------------
recommendations = []
for rule in rules:
    lhs_titles = [movie_dict[i] for i in rule.lhs]
    rhs_titles = [movie_dict[i] for i in rule.rhs]
    recommendations.append({
        "If you like": ", ".join(lhs_titles),
        "You might like": ", ".join(rhs_titles),
        "Confidence": round(rule.confidence, 2),
        "Lift": round(rule.lift, 2)
    })

rec_df = pd.DataFrame(recommendations)

# --------------------------
# Filter by search and confidence
# --------------------------
if search_movie:
    rec_df = rec_df[
        (rec_df["If you like"].str.contains(search_movie, case=False, na=False)) |
        (rec_df["You might like"].str.contains(search_movie, case=False, na=False))
    ]

rec_df = rec_df[rec_df["Confidence"] >= min_confidence]

st.subheader(f"Recommendations for: {search_movie if search_movie else 'All Movies'}")

# --------------------------
# Streamlit-AgGrid Table
# --------------------------
st.markdown(
    """
    <style>
    .centered-table {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 30px;
        margin-bottom: 50px;
    }
    .centered-table .ag-theme-material {
        width: 90%;
        max-width: 1200px;
        border: 2px solid #0ABAB5;
        border-radius: 10px;
        padding: 10px;
        background-color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if rec_df.empty:
    st.warning("No recommendations found for this selection.")
else:
    gb = GridOptionsBuilder.from_dataframe(rec_df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_default_column(editable=False, filter=True, sortable=True)
    gridOptions = gb.build()

    st.markdown("<div class='centered-table'>", unsafe_allow_html=True)
    AgGrid(
        rec_df,
        gridOptions=gridOptions,
        enable_enterprise_modules=False,
        theme='material',
        height=700,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True
    )
    st.markdown("</div>", unsafe_allow_html=True)
