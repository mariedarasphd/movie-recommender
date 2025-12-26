# app.py – Movie Recommender (styled like SMB demo)

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
/* Whole‑page background */
body {
    background-color: #0ABAB5;   /* Tiffany‑blue */
    color: #ffffff;             /* light text for contrast */
}

/* Streamlit containers (cards, sidebars, etc.) */
section[data-testid="stSidebar"],
div[data-testid="stBlockContainer"] {
    background-color: #0ABAB5;
    border-radius: 8px;
}

/* Headings – a slightly darker shade for readability */
h1, h2, h3, h4, h5, h6 {
    color: #006D71;   /* darker teal */
}

/* Links */
a {
    color: #ffffff;
    text-decoration: underline;
}
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
    layout="wide",          # only one layout argument
)

# -------------------------------------------------
# 1️⃣ Load data (cached)
# -------------------------------------------------
@st.cache_data
def load_data():
    """
    Read the CSV files, merge, clean and return:
    - a list of transactions (list of movieIds per user)
    - a dict mapping movieId → title
    """
    # ------------------------------------------------------------------
    # Load raw CSVs (they must sit in the same folder as this script)
    # ------------------------------------------------------------------
    movies = pd.read_csv("movies.csv")
    ratings = pd.read_csv("ratings.csv")

    # ------------------------------------------------------------------
    # Merge and extract year from the title column
    # ------------------------------------------------------------------
    df = pd.merge(movies, ratings, on="movieId", how="outer")
    # Expected title format: "Movie Name (1995)"
    df[["Movie", "Year"]] = df["title"].str.extract(r"(.+?)\s*$$(\d{4})$$")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df_clean = df.dropna(subset=["userId", "rating", "Year"])

    # ------------------------------------------------------------------
    # Keep only the “Golden Age” (1930‑1969) and filter out Disney/children titles
    # ------------------------------------------------------------------
    golden_age = df_clean[
        (df_clean["Year"] >= 1930) & (df_clean["Year"] <= 1969)
    ]

    # Keep the 500 most‑watched movies in that period
    top_movies = (
        golden_age["movieId"]
        .value_counts()
        .nlargest(500)
        .index
    )
    filtered = golden_age[golden_age["movieId"].isin(top_movies)]

    # Remove Disney and obvious children/family movies
    filtered = filtered[~filtered["Movie"].str.contains("Disney", na=False)]
    filtered = filtered[
        ~filtered["genres"].str.contains("Child|Family", na=False)
    ]

    # ------------------------------------------------------------------
    # Build the list‑of‑transactions format expected by the Apriori model
    # ------------------------------------------------------------------
    transactions = (
        filtered.groupby("userId")["movieId"]
        .apply(list)
        .tolist()
    )
    movie_dict = movies.set_index("movieId")["title"].to_dict()

    return transactions, movie_dict


transactions, movie_dict = load_data()

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
# 3️⃣ Load pre‑computed Apriori rules
# -------------------------------------------------
with open("rules.pkl", "rb") as f:
    rules = pickle.load(f)

# -------------------------------------------------
# 4️⃣ Build recommendation table
# -------------------------------------------------
recommendations = []
for rule in rules:
    lhs_titles = [movie_dict[i] for i in rule.lhs]
    rhs_titles = [movie_dict[i] for i in rule.rhs]
    recommendations.append(
        {
            "If you like": ", ".join(lhs_titles),
            "You might like": ", ".join(rhs_titles),
            "Confidence": rule.confidence,
        }
    )
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
# 8️⃣ Centered Ag‑Grid table (styled like SMB demo)
# -------------------------------------------------
if not rec_df.empty:
    gb = GridOptionsBuilder.from_dataframe(rec_df)
    gb.configure_default_column(editable=False, sortable=True, filter=True)
    grid_options = gb.build()
    AgGrid(rec_df, gridOptions=grid_options, fit_columns_on_grid_load=True)
else:
    st.info("No recommendations match the current filters.")
