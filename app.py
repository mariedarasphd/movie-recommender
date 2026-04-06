# app.py – Movie Recommender (with efficient-apriori rules)

# -------------------------------------------------
# Imports
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
# Logo handling
# -------------------------------------------------
logo_path = pathlib.Path(__file__).parent / "logo.png"
if logo_path.is_file():
    st.sidebar.image(str(logo_path), width=120)
else:
    st.sidebar.warning(
        "⚠️ `logo.png` not found – please add it next to `app.py` "
        "(or update `logo_path` accordingly)."
    )

# -------------------------------------------------
# Page configuration
# -------------------------------------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
)

# -------------------------------------------------
# 1️⃣ Load data (cached)
# -------------------------------------------------
@st.cache_data
def load_movies():
    movies = pd.read_csv("movies.csv")
    movie_dict = movies.set_index("movieId")["title"].to_dict()
    return movies, movie_dict

movies, movie_dict = load_movies()

# -------------------------------------------------
# 2️⃣ Sidebar inputs
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
# 3️⃣ Load pre-computed efficient-apriori rules
# -------------------------------------------------
with open("rules.pkl", "rb") as f:
    rules = pickle.load(f)

# -------------------------------------------------
# 4️⃣ Build recommendation table (convert Rule objects to DataFrame-friendly format)
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
                "Confidence": round(rule.confidence, 2),
                "Lift": round(rule.lift, 2)
            })
    except Exception:
        continue

rec_df = pd.DataFrame(recommendations)

# -------------------------------------------------
# 5️⃣ Filter by search term & confidence
# -------------------------------------------------
if search_movie:
    rec_df = rec_df[
        rec_df["If you like"].str.contains(search_movie, case=False, na=False)
        | rec_df["You might like"].str.contains(search_movie, case=False, na=False)
    ]
rec_df = rec_df[rec_df["Confidence"] >= min_confidence]

# -------------------------------------------------
# 6️⃣ Main title & subtitle
# -------------------------------------------------
st.title("🎬 Movie Recommender + Association Rules")
st.markdown(
    """
    A lightweight demo that shows **frequent item‑sets** from classic movies
    (1930‑1969) and suggests movies that often appear together in user histories.
    """
)

# -------------------------------------------------
# 7️⃣ Show filtered recommendations
# -------------------------------------------------
st.subheader(
    f"Recommendations for: {search_movie if search_movie else 'All Movies'}"
)

# -------------------------------------------------
# 8️⃣ Centered Ag‑Grid table
# -------------------------------------------------
if not rec_df.empty:
    gb = GridOptionsBuilder.from_dataframe(rec_df)
    gb.configure_default_column(editable=False, sortable=True, filter=True)
    grid_options = gb.build()
    AgGrid(rec_df, gridOptions=grid_options, fit_columns_on_grid_load=True)
else:
    st.info("No recommendations match the current filters.")ers. Try adjusting confidence or search term.")
