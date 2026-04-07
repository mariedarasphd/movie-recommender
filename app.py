# app.py – Movie Recommender (Tiffany-blue theme, dict-style pickle)
# Updated with debugging and fallback display

# -------------------------------------------------
# Imports
# -------------------------------------------------
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

.stMarkdown, .stDataFrame, .stTable {
    color: #ffffff !important;
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
    st.sidebar.warning("logo.png not found - please add it next to app.py")

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
    st.sidebar.success("Loaded " + str(len(movie_dict)) + " movies")
    
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
    "Minimum confidence for recommendations",
    min_value=0.0,
    max_value=1.0,
    value=0.1,  # Changed from 0.5 to 0.1 to show more results
    step=0.01,
)
search_movie = st.sidebar.text_input("Search for a movie", "")

# Debug: Show confidence distribution
st.sidebar.markdown("---")
st.sidebar.markdown("**Debug Info:**")

# -------------------------------------------------
# Load rules pickle (dict-style)
# -------------------------------------------------
rules_path = get_file_path("rules.pkl")
rules = []

try:
    with open(rules_path, "rb") as f:
        rules = pickle.load(f)
        
    if not isinstance(rules, list):
        st.error("Error: The loaded pickle file is not a list of rules.")
        st.stop()
    
    st.sidebar.success("Loaded " + str(len(rules)) + " rules")
        
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
        lhs_titles = [movie_dict.get(j, "Unknown Movie (" + str(j) + ")") for j in rule["lhs"]]
        rhs_titles = [movie_dict.get(j, "Unknown Movie (" + str(j) + ")") for j in rule["rhs"]]
        
        recommendations.append({
            "If you like": ", ".join(lhs_titles),
            "You might like": ", ".join(rhs_titles),
            "Confidence": round(rule["confidence"], 4),
            "Lift": round(rule.get("lift", 0), 4),
        })
    except KeyError as e:
        errors_found = True
    except Exception as e:
        errors_found = True

rec_df = pd.DataFrame(recommendations)

# Debug: Show confidence stats
if not rec_df.empty:
    st.sidebar.markdown("Min confidence: " + str(round(rec_df["Confidence"].min(), 4)))
    st.sidebar.markdown("Max confidence: " + str(round(rec_df["Confidence"].max(), 4)))
    st.sidebar.markdown("Avg confidence: " + str(round(rec_df["Confidence"].mean(), 4)))

# -------------------------------------------------
# Apply search and confidence filters
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
st.markdown(
    "Explore classic movie pairings (1930-1969). See what other users often watched together"
)

if errors_found:
    st.info("Some rules were skipped due to missing movie IDs.")

# Debug: Show filter results
st.sidebar.markdown("---")
st.sidebar.markdown("**Results:**")
st.sidebar.markdown("Total rules: " + str(original_count))
st.sidebar.markdown("After filtering: " + str(filtered_count))

# -------------------------------------------------
# Show table
# -------------------------------------------------
st.subheader("Recommendations for: " + (search_movie if search_movie else "All Movies"))

if not rec_df.empty:
    try:
        # First try AgGrid
        gb = GridOptionsBuilder.from_dataframe(rec_df)
        gb.configure_default_column(editable=False, sortable=True, filter=True)
        gb.configure_column("Confidence", type=["numericColumn", "numberColumnFilter"])
        
        grid_options = gb.build()
        AgGrid(
            rec_df, 
            gridOptions=grid_options, 
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
            height=400
        )
    except Exception as e:
        # Fallback to standard dataframe if AgGrid fails
        st.warning("AgGrid failed, showing standard table:")
        st.dataframe(rec_df, height=400)
else:
    st.warning("No recommendations match the current filters.")
    st.info("Try lowering the minimum confidence slider or clearing the search box.")
    
    # Show sample of raw data for debugging
    if not recommendations:
        st.error("No recommendations were generated. Check if rules.pkl loaded correctly.")
    else:
        st.markdown("**Sample of unfiltered data (first 5 rows):**")
        st.dataframe(pd.DataFrame(recommendations).head())
