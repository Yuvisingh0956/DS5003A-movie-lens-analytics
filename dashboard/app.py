# ============================================================
# 1. SET UP PROJECT PATH FIRST
# ============================================================

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================
# 2. IMPORT LIBRARIES
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from sqlalchemy import text

# ============================================================
# 3. IMPORT PROJECT MODULES
# ============================================================

from config.database import app_engine
from dashboard.auth import (
    authenticate_user,
    create_user
)

from analytics.queries import (
    Q1_TOP_TAGS_FOR_MOVIE,
    Q2_OVERALL_TOP_MOVIES,
    Q2_YEARWISE_TOP_MOVIES,
    Q3_POPULAR_TAGS_BY_GENRE,
    Q4_MOVIE_RATING_DISTRIBUTION,
    Q5_RATING_COUNT_DISTRIBUTION,
    Q6_TOP_GENRE_BY_YEAR,
    Q7_GENRE_WISE_COVERAGE
)

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MovieLens Analytics",
    page_icon="🎬",
    layout="wide"
)


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def fetch_data(query, params=None):
    """Execute a SQL query and return a Pandas DataFrame."""
    with app_engine.connect() as connection:
        return pd.read_sql_query(
            text(query),
            connection,
            params=params or {}
        )



def fetch_user_rating(query, params, user_id, user_role):
    """Run a user_ratings query with the authenticated identity set for RLS."""
    with app_engine.begin() as connection:
        connection.execute(
            text("""
                SELECT set_config(
                    'app.user_id',
                    :user_id,
                    true
                )
            """),
            {"user_id": str(user_id)}
        )

        connection.execute(
            text("""
                SELECT set_config(
                    'app.user_role',
                    :user_role,
                    true
                )
            """),
            {"user_role": str(user_role)}
        )

        return pd.read_sql_query(
            text(query),
            connection,
            params=params
        )

   

def check_database_connection():
    """Check PostgreSQL connectivity."""
    try:
        with app_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as error:
        st.error(f"Database connection failed: {error}")
        return False


# ============================================================
# USER AUTHENTICATION AND SESSION MANAGEMENT
# ============================================================

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None


# ------------------------------------------------------------
# LOGIN SCREEN
# ------------------------------------------------------------

if not st.session_state.authenticated:

    st.title("🎬 MovieLens Analytics")
    st.subheader("Login to your account")

    st.markdown(
        "Please enter your username and password to continue."
    )

    with st.form("login_form"):

        username = st.text_input(
            "Username",
            placeholder="Enter your username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )

        login_button = st.form_submit_button(
            "Login",
            use_container_width=True
        )

        if login_button:

            if not username.strip() or not password:
                st.warning(
                    "Please enter both username and password."
                )

            else:
                user = authenticate_user(
                    username,
                    password
                )

                if user is not None:

                    st.session_state.authenticated = True
                    st.session_state.current_user = user

                    st.rerun()

                else:
                    st.error(
                        "Invalid username or password."
                    )

    st.stop()


# ------------------------------------------------------------
# LOGGED-IN USER INFORMATION
# ------------------------------------------------------------

current_user = st.session_state.current_user

st.sidebar.title("Account")

st.sidebar.write(
    f"**Username:** {current_user['username']}"
)

st.sidebar.write(
    f"**Role:** {current_user['role'].upper()}"
)

st.sidebar.divider()


# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------

if st.sidebar.button(
    "Logout",
    use_container_width=True
):

    st.session_state.authenticated = False
    st.session_state.current_user = None

    st.rerun()


# ============================================================
# APPLICATION HEADER
# ============================================================

st.title("🎬 MovieLens Analytics Dashboard")

st.markdown(
    """
    Explore movie ratings, user preferences, genres,
    and genome-based movie tags using the MovieLens dataset.
    """
)

st.divider()


# ============================================================
# DATABASE CONNECTION
# ============================================================

if not check_database_connection():
    st.stop()

st.success("Connected to PostgreSQL successfully.")



# ============================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================

current_user = st.session_state.current_user
current_user_id = current_user["user_id"]
current_user_role = current_user["role"]


# ============================================================
# ADMINISTRATOR: USER MANAGEMENT
# ============================================================

if current_user_role == "admin":

    st.sidebar.divider()
    st.sidebar.success("Administrator Access")

    st.header("Administrator Panel")
    st.subheader("Create a New User")

    with st.form("create_user_form"):

        new_username = st.text_input(
            "New username",
            max_chars=100
        )

        new_password = st.text_input(
            "Temporary password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password"
        )

        create_button = st.form_submit_button(
            "Create User",
            use_container_width=True
        )

        if create_button:

            if not new_username.strip():
                st.error("Please enter a username.")

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            else:
                success, message = create_user(
                    username=new_username,
                    password=new_password,
                    role="user"
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.divider()

    # --------------------------------------------------------
    # VIEW REGISTERED USERS
    # --------------------------------------------------------

    st.subheader("Registered Application Users")

    registered_users = fetch_data("""
        SELECT
            u.user_id,
            u.username,
            r.role_name,
            u.created_at
        FROM app_users u
        JOIN roles r
            ON u.role_id = r.role_id
        ORDER BY u.user_id
    """)

    st.dataframe(
        registered_users,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# USER AND ADMIN: SUBMIT OR UPDATE OWN MOVIE RATINGS
# ============================================================

st.divider()

st.header("My Movie Ratings")

st.write(
    "Submit a rating for a movie or update a rating "
    "you have previously submitted."
)

rating_search = st.text_input(
    "Search for a movie to rate",
    placeholder="Enter a movie title...",
    key="rating_movie_search"
)

if len(rating_search.strip()) >= 2:

    rating_movie_results = fetch_data(
        """
        SELECT movie_id, title
        FROM movies
        WHERE title ILIKE :search_text
        ORDER BY title
        LIMIT 50
        """,
        {
            "search_text": f"%{rating_search.strip()}%"
        }
    )

    if rating_movie_results.empty:
        st.warning("No matching movies found.")

    else:
        rating_movie_options = list(
            rating_movie_results.itertuples(
                index=False,
                name=None
            )
        )

        selected_rating_movie = st.selectbox(
            "Select a movie to rate",
            options=rating_movie_options,
            format_func=lambda movie: (
                f"{movie[1]} (Movie ID: {movie[0]})"
            ),
            key="rating_movie_selection"
        )

        rating_movie_id = int(selected_rating_movie[0])
        rating_movie_title = selected_rating_movie[1]

        # Retrieve only the logged-in user's rating
        existing_rating = fetch_user_rating(
            """
            SELECT rating
            FROM user_ratings
            WHERE user_id = :user_id
            AND movie_id = :movie_id
            """,
            {
                "user_id": current_user_id,
                "movie_id": rating_movie_id
            },
            current_user_id,
            current_user_role
        )

        if not existing_rating.empty:
            current_rating = float(
                existing_rating.iloc[0]["rating"]
            )

            st.info(
                f"Your current rating for "
                f"{rating_movie_title}: {current_rating:.1f}/5"
            )

            default_rating_index = (
                int(current_rating * 2) - 1
            )

        else:
            default_rating_index = 7

        rating_options = [
            value / 2 for value in range(1, 11)
        ]

        with st.form("submit_rating_form"):

            submitted_rating = st.selectbox(
                "Select your rating",
                options=rating_options,
                index=default_rating_index,
                format_func=lambda value: f"{value:.1f} / 5"
            )

            save_rating_button = st.form_submit_button(
                "Save My Rating",
                use_container_width=True
            )

            if save_rating_button:

                
                try:
                    with app_engine.begin() as connection:

                        # Set authenticated identity for RLS.
                        connection.execute(
                            text("""
                                SELECT set_config(
                                    'app.user_id',
                                    :user_id,
                                    true
                                )
                            """),
                            {"user_id": str(current_user_id)}
                        )

                        connection.execute(
                            text("""
                                SELECT set_config(
                                    'app.user_role',
                                    :user_role,
                                    true
                                )
                            """),
                            {"user_role": str(current_user_role)}
                        )

                        # User identity comes from the authenticated session.
                        connection.execute(
                            text("""
                                INSERT INTO user_ratings (
                                    user_id,
                                    movie_id,
                                    rating,
                                    updated_at
                                )
                                VALUES (
                                    :user_id,
                                    :movie_id,
                                    :rating,
                                    CURRENT_TIMESTAMP
                                )
                                ON CONFLICT (user_id, movie_id)
                                DO UPDATE SET
                                    rating = EXCLUDED.rating,
                                    updated_at = CURRENT_TIMESTAMP
                            """),
                            {
                                "user_id": current_user_id,
                                "movie_id": rating_movie_id,
                                "rating": submitted_rating
                            }
                        )

                    st.success(
                        f"Your rating of {submitted_rating:.1f}/5 "
                        f"for {rating_movie_title} was saved."
                    )

                    st.rerun()

                except Exception as error:
                    st.error(
                        f"Unable to save your rating: {error}"
                    )


elif rating_search:
    st.info("Enter at least two characters to search.")


# ============================================================
# DATABASE SUMMARY
# ============================================================

summary_query = """
SELECT
    (SELECT COUNT(*) FROM movies) AS total_movies,
    (SELECT COUNT(*) FROM ratings) AS total_ratings,
    (SELECT COUNT(DISTINCT user_id) FROM ratings) AS total_users,
    (SELECT COUNT(*) FROM genres) AS total_genres
"""

summary = fetch_data(summary_query).iloc[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Movies",
    f"{summary['total_movies']:,}"
)

col2.metric(
    "Total Ratings",
    f"{summary['total_ratings']:,}"
)

col3.metric(
    "Total Users",
    f"{summary['total_users']:,}"
)

col4.metric(
    "Total Genres",
    f"{summary['total_genres']:,}"
)

st.divider()


# ============================================================
# MOVIE SEARCH
# ============================================================

st.header("Movie Explorer")

search_text = st.text_input(
    "Search for a movie",
    value="Toy Story",
    placeholder="Enter a movie title..."
)

if len(search_text.strip()) < 2:
    st.info("Enter at least two characters to search for a movie.")
    st.stop()


movie_search_query = """
SELECT movie_id, title
FROM movies
WHERE title ILIKE :search_text
ORDER BY title
LIMIT 50
"""

movies_found = fetch_data(
    movie_search_query,
    {"search_text": f"%{search_text.strip()}%"}
)

if movies_found.empty:
    st.warning("No matching movies found.")
    st.stop()


movie_options = list(
    movies_found.itertuples(index=False, name=None)
)

selected_movie = st.selectbox(
    "Select a movie",
    options=movie_options,
    format_func=lambda movie: (
        f"{movie[1]} (Movie ID: {movie[0]})"
    )
)

selected_movie_id = selected_movie[0]
selected_movie_title = selected_movie[1]

st.caption(
    f"Selected movie: {selected_movie_title} "
    f"| Movie ID: {selected_movie_id}"
)

st.divider()


# ============================================================
# QUESTION A
# TOP 5 GENOME TAGS BY RELEVANCE
# ============================================================

st.header("A. Top 5 Tags by Relevance")

top_tags = fetch_data(
    Q1_TOP_TAGS_FOR_MOVIE,
    {"movie_id": selected_movie_id}
)

# st.subheader("Debug: Genome Relevance Data")

# st.write("Column data types:")
# st.write(top_tags.dtypes)

# st.write("Actual query results:")
# st.write(top_tags.to_dict("records"))

if top_tags.empty:
    st.warning(
        "Genome scores are not available for this movie. "
        "Only 16,376 movies in this dataset have genome scores."
    )
else:
    # Convert PostgreSQL numeric values into Pandas floats
    top_tags["relevance"] = pd.to_numeric(
        top_tags["relevance"],
        errors="coerce"
    )

    # Remove rows with invalid relevance values
    top_tags = top_tags.dropna(subset=["relevance"])

    # Display relevance scores with four decimal places
    display_tags = top_tags.copy()
    display_tags["relevance"] = display_tags["relevance"].round(4)

    st.dataframe(
        top_tags[["tag_name", "relevance"]],
        column_config={
            "tag_name": st.column_config.TextColumn(
                "Genome Tag"
            ),
            "relevance": st.column_config.NumberColumn(
                "Relevance Score",
                format="%.5f"
            )
        },
        use_container_width=True,
        hide_index=True
    )

    # Sort so the highest relevance appears at the top
    chart_tags = top_tags.sort_values(
        "relevance",
        ascending=True
    )

    fig_tags = px.bar(
        chart_tags,
        x="relevance",
        y="tag_name",
        orientation="h",
        title=f"Top Genome Tags — {selected_movie_title}",
        labels={
            "relevance": "Relevance Score",
            "tag_name": "Genome Tag"
        },
        text="relevance"
    )

    fig_tags.update_traces(
        texttemplate="%{text:.4f}",
        textposition="outside",
        cliponaxis=False
    )

    fig_tags.update_layout(
        xaxis=dict(
            title="Relevance Score",
            range=[0, 1.05],
            tickformat=".2f",
            dtick=0.1
        ),
        yaxis_title="",
        height=400,
        margin=dict(l=20, r=80, t=60, b=40)
    )

    st.plotly_chart(
        fig_tags,
        use_container_width=True
    )



# ============================================================
# QUESTION B
# OVERALL AND YEAR-WISE TOP 10 MOVIES
# ============================================================

st.divider()

st.header("B. Top 10 Movies by Average Rating")


# ------------------------------------------------------------
# Helper function to standardize query output column names
# ------------------------------------------------------------

def standardize_movie_columns(data, include_year=False):
    """Standardize column names returned by the Q2 SQL queries."""

    data = data.copy()

    column_options = {
        "title": ["title", "movie_title"],
        "average_rating": [
            "average_rating",
            "avg_rating",
            "avg"
        ],
        "rating_count": [
            "rating_count",
            "total_ratings",
            "number_of_ratings",
            "num_ratings",
            "count"
        ],
        "release_year": ["release_year", "year"]
    }

    rename_columns = {}

    for standard_name, possible_names in column_options.items():

        if standard_name == "release_year" and not include_year:
            continue

        for column in possible_names:
            if column in data.columns:
                rename_columns[column] = standard_name
                break

    data = data.rename(columns=rename_columns)

    required_columns = [
        "title",
        "average_rating",
        "rating_count"
    ]

    if include_year:
        required_columns.append("release_year")

    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        st.error(
            f"Missing expected columns: {missing_columns}. "
            f"Actual query columns: {list(data.columns)}"
        )
        st.stop()

    data["average_rating"] = pd.to_numeric(
        data["average_rating"],
        errors="coerce"
    )

    data["rating_count"] = pd.to_numeric(
        data["rating_count"],
        errors="coerce"
    )

    return data


# ------------------------------------------------------------
# B1. OVERALL TOP 10 MOVIES
# ------------------------------------------------------------

st.subheader("B1. Overall Top 10 Movies")

overall_top_movies = fetch_data(
    Q2_OVERALL_TOP_MOVIES
)

if overall_top_movies.empty:
    st.warning("No overall movie rating data available.")

else:
    overall_top_movies = standardize_movie_columns(
        overall_top_movies
    )

    overall_top_movies = overall_top_movies.dropna(
        subset=["average_rating", "rating_count"]
    )

    # Display the results
    overall_display = overall_top_movies[
        ["title", "average_rating", "rating_count"]
    ].copy()

    overall_display["average_rating"] = (
        overall_display["average_rating"].round(2)
    )

    overall_display["rating_count"] = (
        overall_display["rating_count"].astype(int)
    )

    st.dataframe(
        overall_display,
        column_config={
            "title": st.column_config.TextColumn(
                "Movie Title"
            ),
            "average_rating": st.column_config.NumberColumn(
                "Average Rating",
                format="%.2f / 5"
            ),
            "rating_count": st.column_config.NumberColumn(
                "Number of Ratings",
                format="%d"
            )
        },
        use_container_width=True,
        hide_index=True
    )

    # Average rating chart
    fig_overall = px.bar(
        overall_top_movies.sort_values(
            "average_rating",
            ascending=True
        ),
        x="average_rating",
        y="title",
        orientation="h",
        title="Overall Top 10 Movies by Average Rating",
        labels={
            "average_rating": "Average Rating",
            "title": "Movie"
        },
        text="average_rating",
        hover_data=["rating_count"]
    )

    fig_overall.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        cliponaxis=False
    )

    fig_overall.update_layout(
        xaxis=dict(
            title="Average Rating",
            range=[0, 5.5]
        ),
        yaxis_title="",
        height=500
    )

    st.plotly_chart(
        fig_overall,
        use_container_width=True
    )


st.divider()


# ------------------------------------------------------------
# B2. YEAR-WISE TOP 10 MOVIES
# ------------------------------------------------------------

st.subheader("B2. Year-wise Top 10 Movies")

yearwise_movies = fetch_data(
    Q2_YEARWISE_TOP_MOVIES
)

if yearwise_movies.empty:
    st.warning("No year-wise movie rating data available.")

else:
    yearwise_movies = standardize_movie_columns(
        yearwise_movies,
        include_year=True
    )

    yearwise_movies["release_year"] = pd.to_numeric(
        yearwise_movies["release_year"],
        errors="coerce"
    )

    yearwise_movies = yearwise_movies.dropna(
        subset=[
            "release_year",
            "average_rating",
            "rating_count"
        ]
    )

    available_years = sorted(
        yearwise_movies["release_year"]
        .astype(int)
        .unique()
        .tolist(),
        reverse=True
    )

    if not available_years:
        st.warning("No valid release years found.")

    else:
        selected_year = st.selectbox(
            "Select a release year",
            options=available_years,
            index=0
        )

        selected_year_movies = yearwise_movies[
            yearwise_movies["release_year"] == selected_year
        ].copy()

        selected_year_movies = selected_year_movies.sort_values(
            ["average_rating", "rating_count"],
            ascending=[False, False]
        ).head(10)

        st.caption(
            f"Top 10 movies released in {selected_year}"
        )

        year_display = selected_year_movies[
            ["title", "average_rating", "rating_count"]
        ].copy()

        year_display["average_rating"] = (
            year_display["average_rating"].round(2)
        )

        year_display["rating_count"] = (
            year_display["rating_count"].astype(int)
        )

        st.dataframe(
            year_display,
            column_config={
                "title": st.column_config.TextColumn(
                    "Movie Title"
                ),
                "average_rating": st.column_config.NumberColumn(
                    "Average Rating",
                    format="%.2f / 5"
                ),
                "rating_count": st.column_config.NumberColumn(
                    "Number of Ratings",
                    format="%d"
                )
            },
            use_container_width=True,
            hide_index=True
        )

        fig_yearwise = px.bar(
            selected_year_movies.sort_values(
                "average_rating",
                ascending=True
            ),
            x="average_rating",
            y="title",
            orientation="h",
            title=f"Top 10 Movies Released in {selected_year}",
            labels={
                "average_rating": "Average Rating",
                "title": "Movie"
            },
            text="average_rating",
            hover_data=["rating_count"]
        )

        fig_yearwise.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
            cliponaxis=False
        )

        fig_yearwise.update_layout(
            xaxis=dict(
                title="Average Rating",
                range=[0, 5.5]
            ),
            yaxis_title="",
            height=500
        )

        st.plotly_chart(
            fig_yearwise,
            use_container_width=True
        )



# ============================================================
# QUESTION C
# MOST POPULAR TAGS GIVEN FOR EACH GENRE
# ============================================================

st.divider()

st.header("C. Most Popular Tags by Genre")

popular_tags = fetch_data(
    Q3_POPULAR_TAGS_BY_GENRE
)

if popular_tags.empty:
    st.warning("No user tag data is available.")

else:
    # Standardize column names from the SQL query
    popular_tags = popular_tags.copy()

    column_mapping = {}

    possible_genre_columns = ["genre_name", "genre"]
    possible_tag_columns = ["tag_name", "tag"]
    possible_count_columns = [
        "tag_count",
        "number_of_tags",
        "frequency",
        "count"
    ]

    for column in possible_genre_columns:
        if column in popular_tags.columns:
            column_mapping[column] = "genre_name"
            break

    for column in possible_tag_columns:
        if column in popular_tags.columns:
            column_mapping[column] = "tag_name"
            break

    for column in possible_count_columns:
        if column in popular_tags.columns:
            column_mapping[column] = "tag_count"
            break

    popular_tags = popular_tags.rename(
        columns=column_mapping
    )

    required_columns = [
        "genre_name",
        "tag_name",
        "tag_count"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in popular_tags.columns
    ]

    if missing_columns:
        st.error(
            f"Missing columns: {missing_columns}. "
            f"Available columns: {list(popular_tags.columns)}"
        )
        st.stop()

    popular_tags["tag_count"] = pd.to_numeric(
        popular_tags["tag_count"],
        errors="coerce"
    )

    popular_tags = popular_tags.dropna(
        subset=["tag_count"]
    )

    # Get available genres
    available_genres = sorted(
        popular_tags["genre_name"].unique().tolist()
    )

    selected_genre = st.selectbox(
        "Select a genre",
        options=available_genres
    )

    # Filter tags for selected genre
    genre_tags = popular_tags[
        popular_tags["genre_name"] == selected_genre
    ].copy()

    genre_tags = genre_tags.sort_values(
        "tag_count",
        ascending=False
    ).head(10)

    st.subheader(
        f"Top 10 Most Popular Tags — {selected_genre}"
    )

    # Display table
    display_genre_tags = genre_tags[
        ["tag_name", "tag_count"]
    ].copy()

    display_genre_tags["tag_count"] = (
        display_genre_tags["tag_count"].astype(int)
    )

    st.dataframe(
        display_genre_tags,
        column_config={
            "tag_name": st.column_config.TextColumn(
                "Tag"
            ),
            "tag_count": st.column_config.NumberColumn(
                "Number of Times Used",
                format="%d"
            )
        },
        use_container_width=True,
        hide_index=True
    )

    # Display bar chart
    fig_genre_tags = px.bar(
        genre_tags.sort_values(
            "tag_count",
            ascending=True
        ),
        x="tag_count",
        y="tag_name",
        orientation="h",
        title=f"Most Popular Tags in {selected_genre}",
        labels={
            "tag_count": "Number of Tag Applications",
            "tag_name": "User Tag"
        },
        text="tag_count"
    )

    fig_genre_tags.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
        cliponaxis=False
    )

    fig_genre_tags.update_layout(
        xaxis_title="Number of Tag Applications",
        yaxis_title="",
        height=450
    )

    st.plotly_chart(
        fig_genre_tags,
        use_container_width=True
    )


# ============================================================
# QUESTION D
# DISTRIBUTION OF USER RATINGS
# ============================================================

st.header("D. Distribution of User Ratings")

rating_distribution = fetch_data(
    Q4_MOVIE_RATING_DISTRIBUTION,
    {"movie_id": selected_movie_id}
)

if rating_distribution.empty:
    st.warning("No ratings are available for this movie.")
else:
    # Ensure correct numeric data types
    rating_distribution["rating"] = pd.to_numeric(
        rating_distribution["rating"],
        errors="coerce"
    )

    rating_distribution["number_of_users"] = pd.to_numeric(
        rating_distribution["number_of_users"],
        errors="coerce"
    )

    rating_distribution = rating_distribution.dropna(
        subset=["rating", "number_of_users"]
    )

    rating_distribution = rating_distribution.sort_values("rating")

    total_movie_ratings = int(
        rating_distribution["number_of_users"].sum()
    )

    average_movie_rating = (
        rating_distribution["rating"]
        * rating_distribution["number_of_users"]
    ).sum() / total_movie_ratings

    metric1, metric2 = st.columns(2)

    metric1.metric(
        "Total User Ratings",
        f"{total_movie_ratings:,}"
    )

    metric2.metric(
        "Average Rating",
        f"{average_movie_rating:.2f} / 5"
    )

    fig_ratings = px.bar(
        rating_distribution,
        x="rating",
        y="number_of_users",
        title=f"Rating Distribution — {selected_movie_title}",
        labels={
            "rating": "User Rating",
            "number_of_users": "Number of Users"
        },
        text="number_of_users"
    )

    fig_ratings.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
        cliponaxis=False
    )

    fig_ratings.update_layout(
        xaxis=dict(
            type="category",
            title="User Rating"
        ),
        yaxis=dict(
            title="Number of Users"
        ),
        height=450
    )

    st.plotly_chart(
        fig_ratings,
        use_container_width=True
    )



# ============================================================
# QUESTION E
# DISTRIBUTION OF TOTAL RATINGS FOR MOVIES
# ============================================================

st.divider()

st.header("E. Distribution of Total Ratings for Movies")

rating_count_distribution = fetch_data(
    Q5_RATING_COUNT_DISTRIBUTION
)

if rating_count_distribution.empty:
    st.warning("No movie rating distribution data is available.")

else:
    rating_count_distribution = rating_count_distribution.copy()

    # Identify the bucket and movie-count columns
    bucket_candidates = [
        "rating_bucket",
        "rating_range",
        "bucket",
        "rating_count_bucket"
    ]

    count_candidates = [
        "movie_count",
        "number_of_movies",
        "total_movies",
        "count"
    ]

    bucket_column = next(
        (
            column for column in bucket_candidates
            if column in rating_count_distribution.columns
        ),
        None
    )

    count_column = next(
        (
            column for column in count_candidates
            if column in rating_count_distribution.columns
        ),
        None
    )

    if bucket_column is None or count_column is None:
        st.error(
            "Could not identify the expected columns in the "
            "rating distribution query. Available columns: "
            f"{list(rating_count_distribution.columns)}"
        )
        st.stop()

    # Standardize column names
    rating_count_distribution = rating_count_distribution.rename(
        columns={
            bucket_column: "rating_bucket",
            count_column: "movie_count"
        }
    )

    rating_count_distribution["movie_count"] = pd.to_numeric(
        rating_count_distribution["movie_count"],
        errors="coerce"
    )

    rating_count_distribution = rating_count_distribution.dropna(
        subset=["movie_count"]
    )

    rating_count_distribution["movie_count"] = (
        rating_count_distribution["movie_count"].astype(int)
    )

    # Ensure consistent bucket order
    bucket_order = [
        "0",
        "1-5",
        "6-10",
        "11-50",
        "51-100",
        "101-500",
        "501-1000",
        "1001+"
    ]

    rating_count_distribution["rating_bucket"] = (
        rating_count_distribution["rating_bucket"].astype(str)
    )

    rating_count_distribution["rating_bucket"] = (
        rating_count_distribution["rating_bucket"].replace(
            {"1000+": "1001+"}
        )
    )

    rating_count_distribution["rating_bucket"] = pd.Categorical(
        rating_count_distribution["rating_bucket"],
        categories=bucket_order,
        ordered=True
    )

    rating_count_distribution = (
        rating_count_distribution.sort_values("rating_bucket")
    )

    # Summary metric
    total_movies_in_distribution = int(
        rating_count_distribution["movie_count"].sum()
    )

    st.metric(
        "Total Movies Classified",
        f"{total_movies_in_distribution:,}"
    )

    # Display distribution table
    st.subheader("Movie Rating Count Distribution")

    display_distribution = rating_count_distribution.copy()

    display_distribution["rating_bucket"] = (
        display_distribution["rating_bucket"].astype(str)
    )

    st.dataframe(
        display_distribution,
        column_config={
            "rating_bucket": st.column_config.TextColumn(
                "Number of Ratings per Movie"
            ),
            "movie_count": st.column_config.NumberColumn(
                "Number of Movies",
                format="%d"
            )
        },
        use_container_width=True,
        hide_index=True
    )

    # Bar chart
    fig_rating_counts = px.bar(
        display_distribution,
        x="rating_bucket",
        y="movie_count",
        title="Distribution of Movies by Number of Ratings",
        labels={
            "rating_bucket": "Number of Ratings per Movie",
            "movie_count": "Number of Movies"
        },
        text="movie_count"
    )

    fig_rating_counts.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
        cliponaxis=False
    )

    fig_rating_counts.update_layout(
        xaxis_title="Number of Ratings per Movie",
        yaxis_title="Number of Movies",
        height=450
    )

    st.plotly_chart(
        fig_rating_counts,
        use_container_width=True
    )



# ============================================================
# QUESTION F
# GENRE WITH HIGHEST NUMBER OF MOVIE RELEASES BY YEAR
# ============================================================

st.divider()

st.header("F. Genre with the Highest Number of Movie Releases")

# Get available release years
release_years_query = """
SELECT DISTINCT release_year
FROM movies
WHERE release_year IS NOT NULL
ORDER BY release_year DESC
"""

release_years_data = fetch_data(release_years_query)

if release_years_data.empty:
    st.warning("No movie release years are available.")

else:
    available_release_years = (
        pd.to_numeric(
            release_years_data["release_year"],
            errors="coerce"
        )
        .dropna()
        .astype(int)
        .tolist()
    )

    selected_release_year = st.selectbox(
        "Select a release year to analyze",
        options=available_release_years,
        key="genre_release_year"
    )

    # Execute the genre ranking query
    top_genre_data = fetch_data(
        Q6_TOP_GENRE_BY_YEAR,
        {"year": int(selected_release_year)}
    )

    if top_genre_data.empty:
        st.warning(
            f"No genre information found for "
            f"{selected_release_year}."
        )

    else:
        top_genre_data = top_genre_data.copy()

        # Standardize column names
        rename_columns = {}

        if "genre" in top_genre_data.columns:
            rename_columns["genre"] = "genre_name"

        if "release_count" in top_genre_data.columns:
            rename_columns["release_count"] = "movie_count"

        if "number_of_movies" in top_genre_data.columns:
            rename_columns["number_of_movies"] = "movie_count"

        if "count" in top_genre_data.columns:
            rename_columns["count"] = "movie_count"

        top_genre_data = top_genre_data.rename(
            columns=rename_columns
        )

        required_columns = ["genre_name", "movie_count"]

        missing_columns = [
            column for column in required_columns
            if column not in top_genre_data.columns
        ]

        if missing_columns:
            st.error(
                f"Missing columns: {missing_columns}. "
                f"Available columns: {list(top_genre_data.columns)}"
            )
            st.stop()

        top_genre_data["movie_count"] = pd.to_numeric(
            top_genre_data["movie_count"],
            errors="coerce"
        )

        top_genre_data = top_genre_data.dropna(
            subset=["movie_count"]
        )

        # The SQL query returns the highest-ranked genre(s).
        # Preserve ties if multiple genres share first place.
        highest_count = top_genre_data["movie_count"].max()

        winning_genres = top_genre_data[
            top_genre_data["movie_count"] == highest_count
        ].copy()

        st.subheader(
            f"Top Genre for Movies Released in {selected_release_year}"
        )

        metric_columns = st.columns(len(winning_genres))

        for index, (_, genre_row) in enumerate(
            winning_genres.iterrows()
        ):
            metric_columns[index].metric(
                "Highest Release Genre",
                genre_row["genre_name"],
                f"{int(genre_row['movie_count']):,} movies"
            )

        # Display the winning genre(s)
        display_winners = winning_genres[
            ["genre_name", "movie_count"]
        ].copy()

        display_winners["movie_count"] = (
            display_winners["movie_count"].astype(int)
        )

        st.dataframe(
            display_winners,
            column_config={
                "genre_name": st.column_config.TextColumn(
                    "Genre"
                ),
                "movie_count": st.column_config.NumberColumn(
                    "Number of Movie Releases",
                    format="%d"
                )
            },
            use_container_width=True,
            hide_index=True
        )

        # Display chart
        fig_top_genre = px.bar(
            winning_genres.sort_values(
                "movie_count",
                ascending=True
            ),
            x="movie_count",
            y="genre_name",
            orientation="h",
            title=(
                f"Genre with Most Movie Releases "
                f"in {selected_release_year}"
            ),
            labels={
                "movie_count": "Number of Movie Releases",
                "genre_name": "Genre"
            },
            text="movie_count"
        )

        fig_top_genre.update_traces(
            texttemplate="%{text:,}",
            textposition="outside",
            cliponaxis=False
        )

        fig_top_genre.update_layout(
            xaxis_title="Number of Movie Releases",
            yaxis_title="",
            height=350
        )

        st.plotly_chart(
            fig_top_genre,
            use_container_width=True
        )



# ============================================================
# QUESTION G
# GENRE-WISE COVERAGE OF MOVIES
# ============================================================

st.divider()

st.header("G. Genre-wise Coverage of Movies")

genre_coverage = fetch_data(
    Q7_GENRE_WISE_COVERAGE
)

if genre_coverage.empty:
    st.warning("No genre coverage data is available.")

else:
    genre_coverage = genre_coverage.copy()

    # Standardize column names
    rename_columns = {}

    if "genre" in genre_coverage.columns:
        rename_columns["genre"] = "genre_name"

    count_candidates = [
        "movie_count",
        "number_of_movies",
        "total_movies",
        "count"
    ]

    count_column = next(
        (
            column for column in count_candidates
            if column in genre_coverage.columns
        ),
        None
    )

    if count_column is not None:
        rename_columns[count_column] = "movie_count"

    genre_coverage = genre_coverage.rename(
        columns=rename_columns
    )

    required_columns = ["genre_name", "movie_count"]

    missing_columns = [
        column for column in required_columns
        if column not in genre_coverage.columns
    ]

    if missing_columns:
        st.error(
            f"Missing columns: {missing_columns}. "
            f"Available columns: {list(genre_coverage.columns)}"
        )
        st.stop()

    # Convert movie counts into numeric values
    genre_coverage["movie_count"] = pd.to_numeric(
        genre_coverage["movie_count"],
        errors="coerce"
    )

    genre_coverage = genre_coverage.dropna(
        subset=["movie_count"]
    )

    genre_coverage["movie_count"] = (
        genre_coverage["movie_count"].astype(int)
    )

    # Calculate coverage using the total movie count
    total_movies = int(summary["total_movies"])

    genre_coverage["coverage_percentage"] = (
        genre_coverage["movie_count"] / total_movies
    ) * 100

    # Sort by number of movies
    genre_coverage = genre_coverage.sort_values(
        "movie_count",
        ascending=False
    )

    # Summary metrics
    metric1, metric2 = st.columns(2)

    metric1.metric(
        "Total Movies",
        f"{total_movies:,}"
    )

    metric2.metric(
        "Number of Genres",
        f"{genre_coverage['genre_name'].nunique():,}"
    )

    # Display genre coverage table
    st.subheader("Movie Coverage by Genre")

    display_coverage = genre_coverage[
        [
            "genre_name",
            "movie_count",
            "coverage_percentage"
        ]
    ].copy()

    st.dataframe(
        display_coverage,
        column_config={
            "genre_name": st.column_config.TextColumn(
                "Genre"
            ),
            "movie_count": st.column_config.NumberColumn(
                "Number of Movies",
                format="%d"
            ),
            "coverage_percentage": st.column_config.NumberColumn(
                "Coverage of Total Movies",
                format="%.2f%%"
            )
        },
        use_container_width=True,
        hide_index=True
    )

    # Genre-wise coverage chart
    fig_genre_coverage = px.bar(
        genre_coverage.sort_values(
            "coverage_percentage",
            ascending=True
        ),
        x="coverage_percentage",
        y="genre_name",
        orientation="h",
        title="Genre-wise Coverage of Movies",
        labels={
            "coverage_percentage": "Coverage (%)",
            "genre_name": "Genre"
        },
        text="coverage_percentage",
        hover_data=["movie_count"]
    )

    fig_genre_coverage.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        cliponaxis=False
    )

    fig_genre_coverage.update_layout(
        xaxis_title="Percentage of Total Movies (%)",
        yaxis_title="",
        height=600
    )

    st.plotly_chart(
        fig_genre_coverage,
        use_container_width=True
    )

    st.info(
        "Note: A movie can belong to multiple genres. "
        "Therefore, genre coverage percentages are not "
        "mutually exclusive and may sum to more than 100%."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MovieLens Analytics | DS5003 Data Engineering Lab"
)
