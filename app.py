# -------------------------------------------------
# app.py – Movie Recommender (styled like SMB demo)
# -------------------------------------------------

import pathlib
import pickle

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# ------------------------------------------------------------------
# 0️⃣  Theme & logo (Tiffany‑blue)
# ------------------------------------------------------------------
CUSTOM_CSS = """
<style>
/* Whole‑page background */
body {
    background-color: #0ABAB5;   /* Tiffany blue */
    color: #ffffff;              /* White text */
}

/* Sidebar – works on older and newer Streamlit releases */
section[data-testid="stSidebar"],
.css-1d391kg {               /* fallback selector for newer builds */
    background-color: #0ABAB5;
}

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

# ----- logo -------------------------------------------------
logo_path = pathlib.Path(__file__).parent / "logo.png"
if logo_path.is_file():
    # Streamlit can display a pathlib.Path directly
    st.sidebar.image(str(logo_path), width=120)
else:
    st.sidebar.warning(
        "⚠️ `logo.png` not found – please add it next to `app.py` "
        "(or update `logo_path` accordingly)."
    )

# ------------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
)

# ------------------------------------------------------------------
# 1️⃣  Load data (cached)
# ------------------------------------------------------------------
@st.cache_data
def load_data():
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

    # ------------------------------------------------------------------
    # Merge and extract year from the title column
    # ------------------------------------------------------------------
    df = pd.merge(movies, ratings, on="movieId", how="outer")
    df[["Movie", "Year"]] = df["title"].str.extract(r"(.+?)\s*$$(\d{4})$$")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df_clean = df.dropna(subset=["userId", "rating", "Year"])

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
    filtered = golden_age[golden_age["movieId"].isin(top_movies)]

    # Remove Disney and obvious children/family movies
    filtered = filtered[~filtered["Movie"].str.contains("Disney", na=False)]
    filtered = filtered[
        ~filtered["genres"].str.contains("Childre|Family", na=False)
    ]

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

# ------------------------------------------------------------------
# 2️⃣  Sidebar controls
# ------------------------------------------------------------------
st.sidebar.header("🔧 Filters")
min_confidence = st.sidebar.slider(
    "Minimum confidence for recommendations",
    min_value=0.5,
    max_value=1.0,
    value=0.7,
    step=0.05,
)
search_movie = st.sidebar.text_input("Search for a movie", "")

# ------------------------------------------------------------------
# 3️⃣  Load pre‑computed Apriori rules
# ------------------------------------------------------------------
with open("rules.pkl", "rb") as f:
    rules = pickle.load(f)

# ------------------------------------------------------------------
# 4️⃣  Build the recommendation DataFrame
# ------------------------------------------------------------------
recommendations = []
for rule in rules:
    lhs_titles = [movie_dict[i] for i in rule.lhs]
    rhs_titles = [movie_dict[i] for i in rule.rhs]
    recommendations.append(
        {
            "If you like": ", ".join(lhs_titles),
            "You might like": ", ".join(rhs_titles),
            "Confidence": round(rule.confidence, 2),
            "Lift": round(rule.lift, 2),
        }
    )
rec_df = pd.DataFrame(recommendations)

# ------------------------------------------------------------------
# 5️⃣  Apply search‑term & confidence filters
# ------------------------------------------------------------------
if search_movie:
    rec_df = rec_df[
        rec_df["If you like"].str.contains(search_movie, case=False, na=False)
        | rec_df["You might like"].str.contains(search_movie, case=False, na=False)
    ]
rec_df = rec_df[rec_df["Confidence"] >= min_confidence]

# ------------------------------------------------------------------
# 6️⃣  Main title & description
# ------------------------------------------------------------------
st.title("🎬 Movie Recommender + Association Rules")
st.markdown(
    """
    A lightweight demo that shows **frequent item‑sets** from classic movies
    (1930‑1969) and suggests movies that often appear together in user
    histories.
    """
)

st.subheader(
    f"Recommendations for: {search_movie if search_movie else 'All Movies'}"
)

# ------------------------------------------------------------------
# 7️⃣  Centered Ag‑Grid table (styled like the SMB demo)
# ------------------------------------------------------------------
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
    unsafe_allow_html=True,
)

if rec_df.empty:
    st.warning("No recommendations found for this selection.")
else:
    gb = GridOptionsBuilder.from_dataframe(rec_df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_default_column(editable=False, filter=True, sortable=True)
    grid_options = gb.build()

    st.markdown("<div class='centered-table'>", unsafe_allow_html=True)
    AgGrid(
        rec_df,
        gridOptions=grid_options,
        enable_enterprise_modules=False,
        theme="material",
        height=700,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# 8️⃣  Download button for the filtered recommendations
# ------------------------------------------------------------------
csv_bytes = rec_df.to_csv(index=False).encode()
st.download_button(
    label="💾 Download recommendations (CSV)",
    data=csv_bytes,
    file_name="movie_recommendations.csv",
    mime="text/csv",
)
