# app.py – Movie Recommender (Stable Native Table Version)
# Removed AgGrid to prevent crashes. Uses native st.dataframe.

import os
import pickle

import pandas as pd
import streamlit as st

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

/* Ensure table text is white */
.css-1r6slb0, .stDataFrame {
    color: #ffffff !important;
}

/* Ensure header text is readable */
.stDataFrame .dataframe {
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
    st.sidebar.warning("logo.png not found")

# -------------------------------------------------
# Load movie data
# -------------------------------------------------
movies_path = get_file_path("golden_age_movies.csv")

try:
    movies = pd.read_csv(movies_path)
    
    if "movieId" not in movies.columns or "title" not in movies.columns:
        st.error("Error: golden_age_movies.csv must contain movieId and title columns.")
        st.stop()

    movie_dict = movies.set_index("movieId")["title"].to_dict()
    st.sidebar.success(f"Loaded {len(movie_dict)} movies")
    
except FileNotFoundError:
    st.error("Could not find golden_age_movies.csv")
    st.stop()
except Exception as e:
    st.error("Error loading golden_age_movies.csv: " + str(e))
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
    
    # Filter out rules that reference removed movieIds
    valid_movie_ids = set(movie_dict.keys())
    rules = [
        rule for rule in rules
        if all(j in valid_movie_ids for j in rule["lhs"])
        and all(j in valid_movie_ids for j in rule["rhs"])
    ]
    
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
        lhs_ids = rule["lhs"]
        rhs_ids = rule["rhs"]
        
        # Convert IDs to Titles safely
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
st.markdown("Find movie recommendations based on your favorites — searchable and exportable.")

if errors_found:
    st.info("Some rules were skipped.")

# Debug: Show filter results
st.sidebar.markdown("---")
st.sidebar.markdown("**Results:**")
st.sidebar.markdown(f"Total: {original_count}")
st.sidebar.markdown(f"After filter: {filtered_count}")

# -------------------------------------------------
# Show table (Native Streamlit Table) with pagination
# -------------------------------------------------
st.subheader(f"Recommendations ({filtered_count} found)")

ROWS_PER_PAGE = 15

if not rec_df.empty:
    # Reset index for clean pagination
    rec_df = rec_df.reset_index(drop=True)
    
    total_pages = max(1, (len(rec_df) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)
    
    # Pagination controls
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("⬅️ Previous", disabled=st.session_state.get("current_page", 1) <= 1):
            st.session_state["current_page"] -= 1
    
    with col_next:
        if st.button("Next ➡️", disabled=st.session_state.get("current_page", 1) >= total_pages):
            st.session_state["current_page"] += 1
    
    with col_info:
        current_page = st.session_state.get("current_page", 1)
        if current_page > total_pages:
            current_page = 1
            st.session_state["current_page"] = 1
        st.markdown(f"**Page {current_page} of {total_pages}**")
    
    # Slice the dataframe for the current page
    start_idx = (current_page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    page_df = rec_df.iloc[start_idx:end_idx]
    
    st.dataframe(
        page_df,
        hide_index=True,
        height=500,
    )
    
    # Optional: Download button (downloads ALL filtered results, not just the page)
    csv = rec_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download All Recommendations as CSV",
        data=csv,
        file_name='movie_recommendations.csv',
        mime='text/csv',
    )
else:
    st.warning("No recommendations match the current filters.")
    st.info("Try lowering the minimum confidence slider.")
