# app.py — Movie Recommender (Dict-based rules)
# -------------------------------------------------
# 1️⃣ Imports
# -------------------------------------------------
import pandas as pd
import pickle
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# -------------------------------------------------
# 2️⃣ Load movies and rules pickle
# -------------------------------------------------
@st.cache_data
def load_data():
    # Movies CSV (update path if needed)
    movies = pd.read_csv("movies.csv")
    movie_dict = movies.set_index("movieId")["title"].to_dict()

    # Rules pickle (dicts only)
    with open("rules_dict.pkl", "rb") as f:
        rules = pickle.load(f)

    return movie_dict, rules

movie_dict, rules = load_data()

# -------------------------------------------------
# 3️⃣ Build recommendations DataFrame
# -------------------------------------------------
recommendations = []
for rule in rules:
    lhs_titles = [movie_dict[i] for i in rule["lhs"] if i in movie_dict]
    rhs_titles = [movie_dict[i] for i in rule["rhs"] if i in movie_dict]
    recommendations.append({
        "If you like": ", ".join(lhs_titles),
        "You might like": ", ".join(rhs_titles),
        "Confidence": rule["confidence"],
        "Lift": rule["lift"]
    })

rec_df = pd.DataFrame(recommendations)

# -------------------------------------------------
# 4️⃣ Streamlit UI
# -------------------------------------------------
st.set_page_config(page_title="🎬 Movie Recommender", layout="wide")
st.title("🎬 Movie Recommender")

# Sidebar filters
st.sidebar.header("🔧 Filters")
min_confidence = st.sidebar.slider("Minimum confidence", 0.0, 1.0, 0.5, 0.01)
search_movie = st.sidebar.text_input("Search for a movie", "")

# Apply filters
filtered_df = rec_df[rec_df["Confidence"] >= min_confidence]
if search_movie:
    filtered_df = filtered_df[
        filtered_df["If you like"].str.contains(search_movie, case=False, na=False) |
        filtered_df["You might like"].str.contains(search_movie, case=False, na=False)
    ]

# Display table
if not filtered_df.empty:
    gb = GridOptionsBuilder.from_dataframe(filtered_df)
    gb.configure_default_column(editable=False, sortable=True, filter=True, resizable=True)
    grid_options = gb.build()
    AgGrid(filtered_df, gridOptions=grid_options, fit_columns_on_grid_load=True)
else:
    st.info("No recommendations match the current filters. Try adjusting confidence or search term.")

# Footer
st.markdown("---")
st.markdown("Generated using precomputed rules pickle. 🚀")
