# app.py – Movie Recommender (styled like SMB demo)

import pathlib
import pickle
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# Custom CSS – Tiffany‑blue theme
CUSTOM_CSS = """
<style>
body {background-color: #0ABAB5; color: #ffffff;}
section[data-testid="stSidebar"], div[data-testid="stBlockContainer"] {
    background-color: #0ABAB5; border-radius: 8px;
}
h1,h2,h3,h4,h5,h6 {color:#006D71;}
a {color:#ffffff; text-decoration:underline;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Logo
logo_path = pathlib.Path(__file__).parent / "logo.png"
if logo_path.is_file():
    st.sidebar.image(str(logo_path), width=120)
else:
    st.sidebar.warning("⚠️ `logo.png` not found – add it next to `app.py`.")

# Page config
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# Load data
@st.cache_data
def load_data():
    movies = pd.read_csv("movies.csv")
    ratings = pd.read_csv("ratings.csv")
    df = pd.merge(movies, ratings, on="movieId", how="inner")
    df[["Movie","Year"]] = df["title"].str.extract(r"(.+?)\s*\((\d{4})\)")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df_clean = df.dropna(subset=["userId","rating","Year"])
    golden_age = df_clean[(df_clean["Year"]>=1930)&(df_clean["Year"]<=1969)]
    top_movies = golden_age["movieId"].value_counts().nlargest(500).index
    filtered = golden_age[golden_age["movieId"].isin(top_movies)]
    filtered = filtered[~filtered["Movie"].str.contains("Disney", na=False)]
    filtered = filtered[~filtered["genres"].str.contains("Child|Family", na=False)]
    transactions = filtered.groupby("userId")["movieId"].apply(list).tolist()
    movie_dict = movies.set_index("movieId")["title"].to_dict()
    return transactions, movie_dict, set(filtered["movieId"])

transactions, movie_dict, filtered_movie_ids = load_data()

# Sidebar filters
st.sidebar.header("🔧 Filters")
min_confidence = st.sidebar.slider("Minimum confidence for recommendations", 0.0, 1.0, 0.5, 0.01)
search_movie = st.sidebar.text_input("Search for a movie", "")

# Load rules
with open("rules.pkl","rb") as f:
    rules = pickle.load(f)

# Build recommendation table (corrected)
recommendations = []
for rule in rules:
    lhs_in = [movie_dict[i] for i in rule.lhs if i in filtered_movie_ids]
    rhs_in = [movie_dict[i] for i in rule.rhs if i in filtered_movie_ids]
    if lhs_in and rhs_in:
        recommendations.append({
            "If you like": ", ".join(lhs_in),
            "You might like": ", ".join(rhs_in),
            "Confidence": rule.confidence,
        })
rec_df = pd.DataFrame(recommendations)

# Dynamic filtering
def filter_recommendations(df, search, min_conf):
    if df.empty: return df
    df_filtered = df[df["Confidence"]>=min_conf]
    if search:
        terms = search.strip().lower().split()
        mask = df_filtered.apply(lambda row: any(term in row["If you like"].lower() or term in row["You might like"].lower() for term in terms), axis=1)
        df_filtered = df_filtered[mask]
    return df_filtered

rec_df_filtered = filter_recommendations(rec_df, search_movie, min_confidence)

# Title
st.title("🎬 Movie Recommender + Association Rules")
st.markdown("Shows frequent item‑sets from classic movies (1930‑1969) and suggests movies that appear together in user histories.")
st.subheader(f"Recommendations for: {search_movie if search_movie else 'All Movies'}")

# AgGrid table
if not rec_df_filtered.empty:
    gb = GridOptionsBuilder.from_dataframe(rec_df_filtered)
    gb.configure_default_column(editable=False, sortable=True, filter=True, resizable=True)
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()
    AgGrid(rec_df_filtered, gridOptions=grid_options, enable_enterprise_modules=False, height=400, fit_columns_on_grid_load=True, allow_unsafe_jscode=True)
else:
    st.info("No recommendations match the current filters.")
