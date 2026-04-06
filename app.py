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
<style>
/* Whole‑page background */
body {
    background-color: #0ABAB5;
    color: #ffffff;
}

/* Streamlit containers (cards, sidebars, etc.) */
section[data-testid="stSidebar"],
div[data-testid="stBlockContainer"] {
    background-color: #0ABAB5;
    border-radius: 8px;
}

/* Headings – a slightly darker shade for readability */
h1, h2, h3, h4, h5, h6 {
    color: #006D71;
}

/* Links */
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
def load_data():
    movies = pd.read_csv("movies.csv")
    ratings = pd.read_csv("ratings.csv")

    # Merge and extract year from the title column
    df = pd.merge(movies, ratings, on="movieId", how="outer")
    # Correct regex for extracting year
    df[["Movie", "Year"]] = df["title"].str.extract(r"(.+?)\s*\((\d{4})\)")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df_clean = df.dropna(subset=["userId", "rating", "Year"])

    # Golden Age filter
    golden_age = df_clean[(df_clean["Year"] >= 1930) & (df_clean["Year"] <= 1969)]

    # Top 500 most-watched
    top_movies = golden_age["movieId"].value_counts().nlargest(500).index
    filtered = golden_age[golden_age["movieId"].isin(top_movies)]

    # Remove Disney / children/family
    filtered = filtered[~filtered["Movie"].str.contains("Disney", na=False)]
    filtered = filtered[~filtered["genres"].str.contains("Child|Family", na=False)]

    transactions = filtered.groupby("userId")["movieId"].apply(list).tolist()
    movie_dict = movies.set_index("movieId")["title"].to_dict()
    filtered_movie_ids = set(filtered["movieId"])

    return transactions, movie_dict, filtered_movie_ids

transactions, movie_dict, filtered_movie_ids = load_data()

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
# 4️⃣ Build recommendation table (filtered correctly)
# -------------------------------------------------
recommendations = []
for rule in rules:
    lhs_in = [movie_dict[i] for i in rule.lhs if i in filtered_movie_ids]
    rhs_in = [movie_dict[i] for i in rule.rhs if i in filtered_movie_ids]
    if lhs_in and rhs_in:  # include rule if at least one movie on each side exists
        recommendations.append({
            "If you like": ", ".join(lhs_in),
            "You might like": ", ".join(rhs_in),
            "Confidence": rule.confidence,
        })
rec_df = pd.DataFrame(recommendations)

# -------------------------------------------------
# 5️⃣ Filter by search term & confidence
# -------------------------------------------------
def filter_recommendations(df, search, min_conf):
    if df.empty:
        return df
    df_filtered = df[df["Confidence"] >= min_conf]
    if search:
        search_terms = search.strip().lower().split()
        mask = df_filtered.apply(
            lambda row: any(
                term in row["If you like"].lower() or term in row["You might like"].lower()
                for term in search_terms
            ),
            axis=1
        )
        df_filtered = df_filtered[mask]
    return df_filtered

rec_df_filtered = filter_recommendations(rec_df, search_movie, min_confidence)

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
st.subheader(
    f"Recommendations for: {search_movie if search_movie else 'All Movies'}"
)

# -------------------------------------------------
# 7️⃣ Centered Ag‑Grid table (interactive)
# -------------------------------------------------
if not rec_df_filtered.empty:
    gb = GridOptionsBuilder.from_dataframe(rec_df_filtered)
    gb.configure_default_column(editable=False, sortable=True, filter=True, resizable=True)
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()
    AgGrid(
        rec_df_filtered,
        gridOptions=grid_options,
        enable_enterprise_modules=False,
        height=400,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True
    )
else:
    st.info("No recommendations match the current filters.")
