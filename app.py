# -------------------------------------------------
# app.py – Movie Recommender (styled like SMB demo)
# -------------------------------------------------

import streamlit as st
import pandas as pd
import pathlib
import pickle
from st_aggrid import AgGrid, GridOptionsBuilder

# -------------------------------------------------
# 0️⃣  Custom CSS + logo (Tiffany‑blue background)
# -------------------------------------------------
CUSTOM_CSS = """
body {
    background-color: #0ABAB5;      /* Tiffany blue */
    color: #ffffff;                 /* White text */
}
[data-testid="stSidebar"] {
    background-color: #0ABAB5;
}
section[data-testid="stHeader"] {
    background-color: #0ABAB5;
}
footer {
    background-color: #0ABAB5;
}
.block-container {
    padding-top: 0rem;
    padding-bottom: 0rem;
}
.logo-img {
    max-height: 60px;
    margin-right: 12px;
}
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------------------------
# 0️⃣‑B  Show the logo (sidebar)
# -------------------------------------------------
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

# -------------------------------------------------
# Page configuration
# -------------------------------------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# -------------------------------------------------
# 1️⃣  Load data (cached)
# -------------------------------------------------
@st.cache_data
def load_data():
    """Read the CSV files, merge, clean and return transactions + title map."""
    movies = pd.read_csv("movies.csv")
    ratings = pd.read_csv("ratings.csv")

    # Merge and extract year
    df = pd.merge(movies, ratings, on="movieId", how="outer")
    df[["Movie", "Year"]] = df["title"].str.extract(r"(.+?)\s*$$(\d{4})$$")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df_clean = df.dropna(subset=["userId", "rating", "Year"])

    # Focus on the “Golden Age” (1930‑1969) and filter out Disney/children movies
    golden_age = df_clean[
        (df_clean["Year"] >= 1930) & (df_clean["Year"] <= 1969)
    ]
    top_movies = (
        golden_age["movieId"]
        .value_counts()
        .nlargest(500)
        .index
    )
    filtered = golden_age[
        golden_age["movieId"].isin(top_movies)
    ]
    filtered = filtered[~filtered["Movie"].str.contains("Disney", na=False)]
    filtered = filtered[
        ~filtered["genres"].str.contains("Childre|Family", na=False)
    ]

    # Build the list‑of‑transactions format expected by the Apriori model
    transactions = filtered.groupby("userId")["movieId"].apply(list).tolist()
    movie_dict = movies.set_index("movieId")["title"].to_dict()

    return transactions, movie_dict


transactions, movie_dict = load_data()

# -------------------------------------------------
# 2️⃣  Sidebar inputs
# -------------------------------------------------
st.sidebar.header("🔧 Filters")
min_confidence = st.sidebar.slider(
    "Minimum confidence for recommendations",
    min_value=0.5,
    max_value=1.0,
    value=0.7,
    step=0.05,
)
search_movie = st.sidebar.text_input("Search for a movie", "")

# -------------------------------------------------
# 3️⃣  Load pre‑computed Apriori rules
# -------------------------------------------------
with open("rules.pkl", "rb") as f:
    rules = pickle.load(f)

# -------------------------------------------------
# 4️⃣  Build recommendation table
# -------------------------------------------------
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

# -------------------------------------------------
# 5️⃣  Filter by search term & confidence
# -------------------------------------------------
if search_movie:
    rec_df = rec_df[
        rec_df["If you like"].str.contains(search_movie, case=False, na=False)
        | rec_df["You might like"].str.contains(search_movie, case=False, na=False)
    ]
rec_df = rec_df[rec_df["Confidence"] >= min_confidence]

# -------------------------------------------------
# 6️⃣  Main title & subtitle
# -------------------------------------------------
st.title("🎬 Movie Recommender + Association Rules")
st.markdown(
    """
    A lightweight demo that shows **frequent item‑sets** from classic movies
    (1930‑1969) and suggests movies that often appear together in user histories.
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

# -------------------------------------------------
# 9️⃣  Optional download of the full rule set
# -------------------------------------------------
csv_bytes = rec_df.to_csv(index=False).encode()
st.download_button(
    label="💾 Download recommendations (CSV)",
    data=csv_bytes,
    file_name="movie_recommendations.csv",
    mime="text/csv",
)
