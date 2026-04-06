# app.py – Movie Recommender (mlxtend Rule-compatible)

import pathlib
import pickle
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# -------------------------------------------------
# Custom CSS – Tiffany-blue theme
# -------------------------------------------------
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

# -------------------------------------------------
# Logo
# -------------------------------------------------
logo_path = pathlib.Path(__file__).parent / "logo.png"
if logo_path.is_file():
    st.sidebar.image(str(logo_path), width=120)
else:
    st.sidebar.warning("⚠️ `logo.png` not found – add it next to `app.py`.")

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# -------------------------------------------------
# Load data
# -------------------------------------------------
@st.cache_data
def load_data():
    movies = pd.read_csv("movies.csv")
    ratings = pd.read_csv("ratings.csv")

    df = pd.merge(movies, ratings, on="movieId", how="outer")
    df[["Movie", "Year"]] = df["title"].str.extract(r"(.+?)\s*\((\d{4})\)")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df_clean = df.dropna(subset=["userId", "rating", "Year"])

    golden_age = df_clean[(df_clean["Year"] >= 1930) & (df_clean["Year"] <= 1969)]
    top_movies = golden_age["movieId"].value_counts().nlargest(500).index
    filtered = golden_age[golden_age["movieId"].isin(top_movies)]

    filtered = filtered[~filtered["Movie"].str.contains("Disney", na=False)]
    filtered = filtered[~filtered["genres"].str.contains("Child|Family", na=False)]

    transactions = filtered.groupby("userId")["movieId"].apply(list).tolist()
    movie_dict = movies.set_index("movieId")["title"].to_dict()

    return transactions, movie_dict

transactions, movie_dict = load_data()

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.header("🔧 Filters")
min_confidence = st.sidebar.slider("Minimum confidence", 0.0, 1.0, 0.5, 0.01)
search_movie = st.sidebar.text_input("Search for a movie", "")

# -------------------------------------------------
# Load rules
# -------------------------------------------------
try:
    with open("rules.pkl", "rb") as f:
        rules = pickle.load(f)
except Exception as e:
    st.error(f"Failed to load rules.pkl: {e}")
    rules = []

# -------------------------------------------------
# Build recommendations (mlxtend Rule objects)
# -------------------------------------------------
recommendations = []

for rule in rules:
    try:
        lhs_titles = [movie_dict[i] for i in rule.lhs if i in movie_dict]
        rhs_titles = [movie_dict[i] for i in rule.rhs if i in movie_dict]

        if lhs_titles and rhs_titles:
            recommendations.append({
                "If you like": ", ".join(lhs_titles),
                "You might like": ", ".join(rhs_titles),
                "Confidence": rule.confidence,
            })

    except Exception as e:
        st.warning(f"Rule processing error: {e}")

rec_df = pd.DataFrame(recommendations)

# -------------------------------------------------
# Filtering
# -------------------------------------------------
def filter_recommendations(df, search, min_conf):
    if df.empty:
        return df

    df_filtered = df[df["Confidence"] >= min_conf]

    if search:
        search = search.lower()
        df_filtered = df_filtered[
            df_filtered["If you like"].str.lower().str.contains(search)
            | df_filtered["You might like"].str.lower().str.contains(search)
        ]

    return df_filtered

rec_df_filtered = filter_recommendations(rec_df, search_movie, min_confidence)

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("🎬 Movie Recommender + Association Rules")
st.markdown("Classic films (1930–1969) with association-based recommendations.")
st.subheader(f"Recommendations for: {search_movie if search_movie else 'All Movies'}")

# -------------------------------------------------
# Table
# -------------------------------------------------
if not rec_df_filtered.empty:
    gb = GridOptionsBuilder.from_dataframe(rec_df_filtered)
    gb.configure_default_column(editable=False, sortable=True, filter=True, resizable=True)
    grid_options = gb.build()

    AgGrid(
        rec_df_filtered,
        gridOptions=grid_options,
        height=400,
        fit_columns_on_grid_load=True
    )
else:
    st.info("No recommendations match the current filters.")
