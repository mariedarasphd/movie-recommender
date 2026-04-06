# app.py – Movie Recommender (Tiffany-blue theme)
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
body { background-color: #0ABAB5; color: #ffffff; }
section[data-testid="stSidebar"], div[data-testid="stBlockContainer"] { background-color: #0ABAB5; border-radius: 8px; }
h1, h2, h3, h4, h5, h6 { color: #006D71; }
a { color: #ffffff; text-decoration: underline; }
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
    st.sidebar.warning("⚠️ `logo.png` not found – please add it next to `app.py`")

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
)

# -------------------------------------------------
# Load movie CSVs
# -------------------------------------------------
@st.cache_data
def load_movies():
    movies = pd.read_csv("movies.csv")
    movie_dict = movies.set_index("movieId")["title"].to_dict()
    return movies, movie_dict

movies, movie_dict = load_movies()

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
# Load rules from pickle
# -------------------------------------------------
with open("rules.pkl", "rb") as f:
    rules = pickle.load(f)

# -------------------------------------------------
# Build recommendations DataFrame
# -------------------------------------------------
recommendations = []
for rule in rules:
    lhs_titles = [movie_dict.get(i, f"Unknown ({i})") for i in rule["lhs"]]
    rhs_titles = [movie_dict.get(i, f"Unknown ({i})") for i in rule["rhs"]]
    recommendations.append({
        "If you like": ", ".join(lhs_titles),
        "You might like": ", ".join(rhs_titles),
        "Confidence": rule.get("confidence", 0),
        "Lift": rule.get("lift", 0)
    })

rec_df = pd.DataFrame(recommendations)

# -------------------------------------------------
# Apply filters
# -------------------------------------------------
if search_movie:
    rec_df = rec_df[
        rec_df["If you like"].str.contains(search_movie, case=False, na=False)
        | rec_df["You might like"].str.contains(search_movie, case=False, na=False)
    ]
rec_df = rec_df[rec_df["Confidence"] >= min_confidence]

# -------------------------------------------------
# Main title
# -------------------------------------------------
st.title("🎬 Movie Recommender + Association Rules")
st.markdown(
    "This demo shows frequent movie pairings from classic films (1930-1969) "
    "and suggests what movies you might like based on user histories."
)

st.subheader(f"Recommendations for: {search_movie if search_movie else 'All Movies'}")

# -------------------------------------------------
# Show table
# -------------------------------------------------
if not rec_df.empty:
    gb = GridOptionsBuilder.from_dataframe(rec_df)
    gb.configure_default_column(editable=False, sortable=True, filter=True)
    grid_options = gb.build()
    AgGrid(rec_df, gridOptions=grid_options, fit_columns_on_grid_load=True)
else:
    st.info("No recommendations match the current filters. Try adjusting confidence or search term.")
