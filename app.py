# app.py – Movie Recommender (Tiffany-blue theme)
# Final version: Forces standard table if AgGrid fails, ensures visibility

import os
import pickle

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

# -------------------------------------------------
# Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
)

# -------------------------------------------------
# Custom CSS – Tiffany-blue theme
# -------------------------------------------------
# Force text color to be visible
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

/* Force all text in containers to be white */
div[data-testid="stVerticalBlock"] > div, 
div[data-testid="stVerticalBlock"] > div > div {
    color: #ffffff !important;
}

/* Ensure table text is white */
.css-1r6slb0, .stDataFrame, .stTable {
    color: #ffffff !important;
}

/* Ensure AgGrid text is white */
.ag-cell, .ag-header-cell {
    color: #ffffff !important;
    background-color: #0ABAB5 !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------------------------
# Helper: Get absolute paths
# -------------------------------------------------
def get_file_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

# -------------------------------------------------
# Logo
# -------------------------------------------------
logo_path = get_file_path("logo.png")
if os.path.isfile(logo_path):
    st.sidebar.image(logo_path, width=120)
else:
    st.sidebar.warning("logo.png not found")

# -------------------------------------------------
# Load movie data
# -------------------------------------------------
movies_path = get_file_path("movies.csv")

try:
    movies = pd.read_csv(movies_path)
    
    if "movieId" not in movies.columns or "title" not in movies.columns:
        st.error("Error: movies.csv must contain movieId and title columns.")
        st.stop()

    movie_dict = movies.set_index("movieId")["title"].to_dict()
    st.sidebar.success(f"Loaded {len(movie_dict)} movies")
    
except FileNotFoundError:
    st.error("Could not find movies.csv")
    st.stop()
except Exception as e:
    st.error("Error loading movies.csv: " + str(e))
    st.stop()

# -------------------------------------------------
# Sidebar filters
# -------------------------------------------------
st.sidebar.header("Filters")
min_confidence = st.sidebar.slider(
    "Minimum confidence",
    min_value=0.0,
    max_value=1.0,
    value=0.1,
    step=0.01,
)
search_movie = st.sidebar.text_input("Search for a movie", "")

# Debug Info
st.sidebar.markdown("---")
st.sidebar.markdown("**Debug Info:**")

# -------------------------------------------------
# Load rules pickle
# -------------------------------------------------
rules_path = get_file_path("rules.pkl")
rules = []

try:
    with open(rules_path, "rb") as f:
        rules = pickle.load(f)
        
    if not isinstance(rules, list):
        st.error("Error: The loaded pickle file is not a list of rules.")
        st.stop()
    
    st.sidebar.success(f"Loaded {len(rules)} rules")
        
except FileNotFoundError:
    st.error("Could not find rules.pkl")
    st.stop()
except Exception as e:
    st.error("Error loading rules.pkl: " + str(e))
    st.stop()

# -------------------------------------------------
# Build recommendation table
# -------------------------------------------------
recommendations = []
errors_found = False

for i, rule in enumerate(rules):
    try:
        # Convert IDs to Titles
        lhs_ids = rule["lhs"]
        rhs_ids = rule["rhs"]
        
        lhs_titles = [movie_dict.get(j, f"ID:{j}") for j in lhs_ids]
        rhs_titles = [movie_dict.get(j, f"ID:{j}") for j in rhs_ids]
        
        recommendations.append({
            "If you like": ", ".join(lhs_titles),
            "You might like": ", ".join(rhs_titles),
            "Confidence": round(rule["confidence"], 4),
            "Lift": round(rule.get("lift", 0), 4),
        })
    except Exception as e:
        errors_found = True

rec_df = pd.DataFrame(recommendations)

# Debug: Show stats
if not rec_df.empty:
    st.sidebar.markdown(f"Min conf: {rec_df['Confidence'].min():.2f}")
    st.sidebar.markdown(f"Max conf: {rec_df['Confidence'].max():.2f}")

# -------------------------------------------------
# Apply filters
# -------------------------------------------------
original_count = len(rec_df)

if search_movie:
    mask = (
        rec_df["If you like"].str.contains(search_movie, case=False, na=False) |
        rec_df["You might like"].str.contains(search_movie, case=False, na=False)
    )
    rec_df = rec_df[mask]

rec_df = rec_df[rec_df["Confidence"] >= min_confidence]

filtered_count = len(rec_df)

# -------------------------------------------------
# Title & description
# -------------------------------------------------
st.title("Movie Recommender + Association Rules")
st.markdown("Explore classic movie pairings (1930-1969).")

if errors_found:
    st.info("Some rules were skipped.")

# Debug: Show filter results
st.sidebar.markdown("---")
st.sidebar.markdown("**Results:**")
st.sidebar.markdown(f"Total: {original_count}")
st.sidebar.markdown(f"After filter: {filtered_count}")

# -------------------------------------------------
# Show table
# -------------------------------------------------
st.subheader(f"Recommendations ({filtered_count} found)")

if not rec_df.empty:
    # DEBUG: Show first few rows as text to verify content
    st.markdown("**Preview of data (first 3 rows):**")
    st.write(rec_df.head(3).to_string(index=False))
    
    # Try AgGrid first
    try:
        st.markdown("**Interactive Table:**")
        gb = GridOptionsBuilder.from_dataframe(rec_df)
        gb.configure_default_column(editable=False, sortable=True, filter=True)
        gb.configure_column("Confidence", type=["numericColumn", "numberColumnFilter"])
        
        grid_options = gb.build()
        
        # Force height
        AgGrid(
            rec_df, 
            gridOptions=grid_options, 
            fit_columns_on_grid_load=True,
            height=500,
            allow_unsafe_jscode=True
        )
    except Exception as e:
        st.error(f"AgGrid failed: {e}")
        st.write("Showing standard table instead:")
        st.dataframe(rec_df, height=500)
else:
    st.warning("No recommendations match the current filters.")
    st.info("Try lowering the minimum confidence slider.")
