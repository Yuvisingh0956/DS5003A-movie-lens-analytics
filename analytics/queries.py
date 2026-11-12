
# ============================================================
# MOVIELENS ANALYTICS - SEVEN PROJECT QUERIES
# Database: PostgreSQL
# ============================================================


# ------------------------------------------------------------
# QUESTION A
# Top 5 genome tags by relevance for a selected movie
# Parameter: movie_id
# ------------------------------------------------------------

Q1_TOP_TAGS_FOR_MOVIE = """
SELECT
    m.movie_id,
    m.title,
    gt.tag_name,
    gs.relevance
FROM genome_scores gs
JOIN genome_tags gt
    ON gs.tag_id = gt.tag_id
JOIN movies m
    ON gs.movie_id = m.movie_id
WHERE m.movie_id = :movie_id
ORDER BY gs.relevance DESC
LIMIT 5;
"""


# ------------------------------------------------------------
# QUESTION B1
# Overall top 10 movies by average rating
# ------------------------------------------------------------

Q2_OVERALL_TOP_MOVIES = """
SELECT
    m.movie_id,
    m.title,
    ROUND(AVG(r.rating), 3) AS average_rating,
    COUNT(r.rating) AS rating_count
FROM movies m
JOIN ratings r
    ON m.movie_id = r.movie_id
GROUP BY m.movie_id, m.title
ORDER BY average_rating DESC, rating_count DESC
LIMIT 10;
"""


# ------------------------------------------------------------
# QUESTION B2
# Year-wise top 10 movies by average rating
# ------------------------------------------------------------

Q2_YEARWISE_TOP_MOVIES = """
WITH movie_ratings AS (
    SELECT
        m.movie_id,
        m.title,
        m.release_year,
        ROUND(AVG(r.rating), 3) AS average_rating,
        COUNT(r.rating) AS rating_count
    FROM movies m
    JOIN ratings r
        ON m.movie_id = r.movie_id
    WHERE m.release_year IS NOT NULL
    GROUP BY
        m.movie_id,
        m.title,
        m.release_year
),
ranked_movies AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY release_year
            ORDER BY average_rating DESC, rating_count DESC
        ) AS movie_rank
    FROM movie_ratings
)
SELECT
    release_year,
    movie_id,
    title,
    average_rating,
    rating_count,
    movie_rank
FROM ranked_movies
WHERE movie_rank <= 10
ORDER BY release_year, movie_rank;
"""


# ------------------------------------------------------------
# QUESTION C
# Most popular user-generated tags for each genre
# Top 10 tags per genre
# ------------------------------------------------------------

Q3_POPULAR_TAGS_BY_GENRE = """
WITH genre_tag_counts AS (
    SELECT
        g.genre_name,
        ut.tag,
        COUNT(*) AS tag_count
    FROM user_tags ut
    JOIN movie_genres mg
        ON ut.movie_id = mg.movie_id
    JOIN genres g
        ON mg.genre_id = g.genre_id
    GROUP BY
        g.genre_name,
        ut.tag
),
ranked_tags AS (
    SELECT
        genre_name,
        tag,
        tag_count,
        ROW_NUMBER() OVER (
            PARTITION BY genre_name
            ORDER BY tag_count DESC, tag
        ) AS tag_rank
    FROM genre_tag_counts
)
SELECT
    genre_name,
    tag,
    tag_count,
    tag_rank
FROM ranked_tags
WHERE tag_rank <= 10
ORDER BY genre_name, tag_rank;
"""


# ------------------------------------------------------------
# QUESTION D
# Distribution of user ratings for a selected movie
# Parameter: movie_id
# ------------------------------------------------------------

Q4_MOVIE_RATING_DISTRIBUTION = """
SELECT
    rating,
    COUNT(*) AS number_of_users
FROM ratings
WHERE movie_id = :movie_id
GROUP BY rating
ORDER BY rating;
"""


# ------------------------------------------------------------
# QUESTION E
# Distribution of total ratings received by movies
# ------------------------------------------------------------

Q5_RATING_COUNT_DISTRIBUTION = """
WITH movie_rating_counts AS (
    SELECT
        m.movie_id,
        COUNT(r.rating) AS total_ratings
    FROM movies m
    LEFT JOIN ratings r
        ON m.movie_id = r.movie_id
    GROUP BY m.movie_id
),
rating_buckets AS (
    SELECT
        CASE
            WHEN total_ratings = 0 THEN '0'
            WHEN total_ratings BETWEEN 1 AND 5 THEN '1-5'
            WHEN total_ratings BETWEEN 6 AND 10 THEN '6-10'
            WHEN total_ratings BETWEEN 11 AND 50 THEN '11-50'
            WHEN total_ratings BETWEEN 51 AND 100 THEN '51-100'
            WHEN total_ratings BETWEEN 101 AND 500 THEN '101-500'
            WHEN total_ratings BETWEEN 501 AND 1000 THEN '501-1000'
            ELSE '1001+'
        END AS rating_range,
        CASE
            WHEN total_ratings = 0 THEN 1
            WHEN total_ratings BETWEEN 1 AND 5 THEN 2
            WHEN total_ratings BETWEEN 6 AND 10 THEN 3
            WHEN total_ratings BETWEEN 11 AND 50 THEN 4
            WHEN total_ratings BETWEEN 51 AND 100 THEN 5
            WHEN total_ratings BETWEEN 101 AND 500 THEN 6
            WHEN total_ratings BETWEEN 501 AND 1000 THEN 7
            ELSE 8
        END AS sort_order
    FROM movie_rating_counts
)
SELECT
    rating_range,
    COUNT(*) AS number_of_movies
FROM rating_buckets
GROUP BY rating_range, sort_order
ORDER BY sort_order;
"""


# ------------------------------------------------------------
# QUESTION F
# Genre with the highest number of movie releases in a year
# Parameter: year
# ------------------------------------------------------------

Q6_TOP_GENRE_BY_YEAR = """
WITH genre_release_counts AS (
    SELECT
        g.genre_name,
        COUNT(DISTINCT m.movie_id) AS movie_count
    FROM movies m
    JOIN movie_genres mg
        ON m.movie_id = mg.movie_id
    JOIN genres g
        ON mg.genre_id = g.genre_id
    WHERE m.release_year = :year
    GROUP BY g.genre_name
),
ranked_genres AS (
    SELECT
        genre_name,
        movie_count,
        RANK() OVER (
            ORDER BY movie_count DESC
        ) AS genre_rank
    FROM genre_release_counts
)
SELECT
    genre_name,
    movie_count
FROM ranked_genres
WHERE genre_rank = 1
ORDER BY genre_name;
"""


# ------------------------------------------------------------
# QUESTION G
# Genre-wise coverage of movies
# ------------------------------------------------------------

Q7_GENRE_WISE_COVERAGE = """
WITH total_movies AS (
    SELECT COUNT(*) AS total
    FROM movies
),
genre_counts AS (
    SELECT
        g.genre_name,
        COUNT(DISTINCT mg.movie_id) AS movie_count
    FROM genres g
    LEFT JOIN movie_genres mg
        ON g.genre_id = mg.genre_id
    GROUP BY g.genre_name
)
SELECT
    gc.genre_name,
    gc.movie_count,
    tm.total AS total_movies,
    ROUND(
        gc.movie_count * 100.0 / NULLIF(tm.total, 0),
        2
    ) AS coverage_percentage
FROM genre_counts gc
CROSS JOIN total_movies tm
ORDER BY gc.movie_count DESC, gc.genre_name;
"""
