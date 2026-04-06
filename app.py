# app.py — Movie Recommender (Tiffany‑blue + dict-based rules)
# -------------------------------------------------
import pathlib
import pickle
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

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
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------------------------
# Sidebar logo
# -------------------------------------------------
logo_path = pathlib.Path(__file__).parent / "logo.png"
if logo_path.is_file():
    st.sidebar.image(str(logo_path), width=120)
else:
    st.sidebar.warning(
        "⚠️ `logo.png` not found – please add it next to `app.py`."
    )

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# -------------------------------------------------
# Load movies and rules
# -------------------------------------------------
@st.cache_data
def load_data():
    movies = pd.read_csv("movies.csv")
    movie_dict = movies.set_index("movieId")["title"].to_dict()
    with open("rules_dict.pkl", "rb") as f:
        rules = pickle.load(f)
    return movie_dict, rules

movie_dict, rules = load_data()

# -------------------------------------------------
# Build recommendations DataFrame
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
# Sidebar filters
# -------------------------------------------------
st.sidebar.header("🔧 Filters")
min_confidence = st.sidebar.slider("Minimum confidence", 0.0, 1.0, 0.5, 0.01)
search_movie = st.sidebar.text_input("Search for a movie", "")

# Filter DataFrame
filtered_df = rec_df[rec_df["Confidence"] >= min_confidence]
if search_movie:
    filtered_df = filtered_df[
        filtered_df["If you like"].str.contains(search_movie, case=False, na=False) |
        filtered_df["You might like"].str.contains(search_movie, case=False, na=False)
    ]

# -------------------------------------------------
# Main content
# -------------------------------------------------
st.title("🎬 Movie Recommender – Tiffany Blue Edition")

if not filtered_df.empty:
    gb = GridOptionsBuilder.from_dataframe(filtered_df)
    gb.configure_default_column(editable=False, sortable=True, filter=True, resizable=True)
    grid_options = gb.build()
    AgGrid(filtered_df, gridOptions=grid_options, fit_columns_on_grid_load=True)
else:
    st.info("No recommendations match the current filters. Try adjusting confidence or search term.")

st.markdown("---")
st.markdown("Generated using precomputed rules pickle. 🚀")
