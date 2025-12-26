# app.py – Movie Recommender (styled like SMB demo)
# -------------------------------------------------

import streamlit as st
import pandas as pd
import pathlib
import pickle

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# -------------------------------------------------
# 0️⃣  Custom CSS + logo (Tiffany‑blue background)
# -------------------------------------------------
# ------------------------------------------------------------------
# 0️⃣  Theme & logo (Tiffany‑blue)
# ------------------------------------------------------------------
CUSTOM_CSS = """
<style>
/* Whole‑page background */
body {
    background-color: #0ABAB5;      /* Tiffany blue */
    color: #ffffff;                 /* White text */
    background-color: #0ABAB5;   /* Tiffany blue */
    color: #ffffff;              /* White text */
}
[data-testid="stSidebar"] {

/* Sidebar – works on older and newer Streamlit releases */
section[data-testid="stSidebar"],
.css-1d391kg {               /* fallback selector for newer builds */
    background-color: #0ABAB5;
}
section[data-testid="stHeader"] {

/* Header bar */
section[data-testid="stHeader"],
.css-1v0mbdj {               /* fallback selector for newer builds */
    background-color: #0ABAB5;
}

/* Footer (if you ever add one) */
footer {
    background-color: #0ABAB5;
}

/* Reduce default padding around the main block */
.block-container {
    padding-top: 0rem;
    padding-bottom: 0rem;
}

/* Optional: style a logo image you might embed elsewhere */
.logo-img {
    max-height: 60px;
    margin-right: 12px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------------------------
# 0️⃣‑B  Show the logo (sidebar)
# -------------------------------------------------
# ----- logo -------------------------------------------------
logo_path = pathlib.Path(__file__).parent / "logo.png"
st.sidebar.image(str(logo_path), width=120)

# -------------------------------------------------
# 0️⃣‑C  Optional debug info (remove if not needed)
# -------------------------------------------------
# st.subheader("🔎 Debug info (remove later)")
# cwd = pathlib.Path.cwd()
# st.write(f"**Current working directory:** `{cwd}`")
# st.write("**Files in repo root:**",
#          sorted([p.name for p in cwd.iterdir() if p.is_file()]))
if logo_path.is_file():
    # Streamlit can display a pathlib.Path directly
    st.sidebar.image(str(logo_path), width=120)
else:
    st.sidebar.warning(
        "⚠️ `logo.png` not found – please add it next to `app.py` "
        "(or update `logo_path` accordingly)."
    )

# -------------------------------------------------
# ------------------------------------------------------------------
# Page configuration
# -------------------------------------------------
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
    layout="wide",
)

# -------------------------------------------------
# ------------------------------------------------------------------
# 1️⃣  Load data (cached)
# -------------------------------------------------
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    """Read the CSV files, merge, clean and return transactions + title map."""
    """
    Load movies & ratings, keep only the “Golden Age” (1930‑1969),
    filter out Disney/children titles, and return:
        • a list of transactions (list of movieIds per user)
        • a dict mapping movieId → title
    """
    # ------------------------------------------------------------------
    # Load raw CSVs (they must sit in the same folder as this script)
    # ------------------------------------------------------------------
    movies = pd.read_csv("movies.csv")
    ratings = pd.read_csv("ratings.csv")

    # Merge and extract year
    # ------------------------------------------------------------------
    # Merge and extract year from the title column
    # ------------------------------------------------------------------
    df = pd.merge(movies, ratings, on="movieId", how="outer")
    df[["Movie", "Year"]] = df["title"].str.extract(r"(.+?)\s*$$(\d{4})$$")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df_clean = df.dropna(subset=["userId", "rating", "Year"])

    # Focus on the “Golden Age” (1930‑1969) and filter out Disney/children movies
    # ------------------------------------------------------------------
    # Keep only classic movies (1930‑1969) and drop Disney/children titles
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
    filtered = golden_age[
        golden_age["movieId"].isin(top_movies)
    ]
    filtered = golden_age[golden_age["movieId"].isin(top_movies)]

    # Remove Disney and obvious children/family movies
    filtered = filtered[~filtered["Movie"].str.contains("Disney", na=False)]
    filtered = filtered[
        ~filtered["genres"].str.contains("Childre|Family", na=False)
    ]

    # Build the list‑of‑transactions format expected by the Apriori model
    transactions = filtered.groupby("userId")["movieId"].apply(list).tolist()
    # ------------------------------------------------------------------
    # Build the transaction list expected by the Apriori model
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
# 2️⃣  Sidebar inputs
# -------------------------------------------------
# ------------------------------------------------------------------
# 2️⃣  Sidebar controls
# ------------------------------------------------------------------
st.sidebar.header("🔧 Filters")
min_confidence = st.sidebar.slider(
    "Minimum confidence for recommendations",
@@ -115,15 +147,15 @@ def load_data():
)
search_movie = st.sidebar.text_input("Search for a movie", "")

# -------------------------------------------------
# ------------------------------------------------------------------
# 3️⃣  Load pre‑computed Apriori rules
# -------------------------------------------------
# ------------------------------------------------------------------
with open("rules.pkl", "rb") as f:
    rules = pickle.load(f)

# -------------------------------------------------
# 4️⃣  Build recommendation table
# -------------------------------------------------
# ------------------------------------------------------------------
# 4️⃣  Build the recommendation DataFrame
# ------------------------------------------------------------------
recommendations = []
for rule in rules:
    lhs_titles = [movie_dict[i] for i in rule.lhs]
@@ -138,37 +170,35 @@ def load_data():
    )
rec_df = pd.DataFrame(recommendations)

# -------------------------------------------------
# 5️⃣  Filter by search term & confidence
# -------------------------------------------------
# ------------------------------------------------------------------
# 5️⃣  Apply search‑term & confidence filters
# ------------------------------------------------------------------
if search_movie:
    rec_df = rec_df[
        rec_df["If you like"].str.contains(search_movie, case=False, na=False)
        | rec_df["You might like"].str.contains(search_movie, case=False, na=False)
    ]
rec_df = rec_df[rec_df["Confidence"] >= min_confidence]

# -------------------------------------------------
# 6️⃣  Main title & subtitle
# -------------------------------------------------
# ------------------------------------------------------------------
# 6️⃣  Main title & description
# ------------------------------------------------------------------
st.title("🎬 Movie Recommender + Association Rules")
st.markdown(
    """
    A lightweight demo that shows **frequent item‑sets** from classic movies
    (1930‑1969) and suggests movies that often appear together in user histories.
    (1930‑1969) and suggests movies that often appear together in user
    histories.
    """
)

# -------------------------------------------------
# 7️⃣  Show filtered recommendations
# -------------------------------------------------
st.subheader(
    f"Recommendations for: {search_movie if search_movie else 'All Movies'}"
)

# -------------------------------------------------
# 8️⃣  Centered Ag‑Grid table (styled like SMB demo)
# -------------------------------------------------
# ------------------------------------------------------------------
# 7️⃣  Centered Ag‑Grid table (styled like the SMB demo)
# ------------------------------------------------------------------
st.markdown(
    """
    <style>
@@ -213,9 +243,9 @@ def load_data():
    )
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# 9️⃣  Optional download of the full rule set
# -------------------------------------------------
# ------------------------------------------------------------------
# 8️⃣  Download button for the filtered recommendations
# ------------------------------------------------------------------
csv_bytes = rec_df.to_csv(index=False).encode()
st.download_button(
    label="💾 Download recommendations (CSV)",
