
-- =====================================================
-- MOVIELENS ANALYTICS DATABASE
-- Dataset: MovieLens ml-latest
-- =====================================================

-- 1. MOVIES
CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    release_year SMALLINT
);

-- 2. GENRES
CREATE TABLE IF NOT EXISTS genres (
    genre_id SMALLINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    genre_name VARCHAR(100) UNIQUE NOT NULL
);

-- 3. MOVIE-GENRE MAPPING
CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INTEGER NOT NULL
        REFERENCES movies(movie_id),
    genre_id SMALLINT NOT NULL
        REFERENCES genres(genre_id),

    PRIMARY KEY (movie_id, genre_id)
);

-- 4. MOVIE EXTERNAL LINKS
CREATE TABLE IF NOT EXISTS movie_links (
    movie_id INTEGER PRIMARY KEY
        REFERENCES movies(movie_id),
    imdb_id VARCHAR(20),
    tmdb_id BIGINT
);

-- 5. GENOME TAGS
CREATE TABLE IF NOT EXISTS genome_tags (
    tag_id INTEGER PRIMARY KEY,
    tag_name TEXT NOT NULL UNIQUE
);

-- 6. GENOME SCORES
CREATE TABLE IF NOT EXISTS genome_scores (
    movie_id INTEGER NOT NULL
        REFERENCES movies(movie_id),
    tag_id INTEGER NOT NULL
        REFERENCES genome_tags(tag_id),
    relevance NUMERIC(6,5) NOT NULL
        CHECK (relevance >= 0 AND relevance <= 1),

    PRIMARY KEY (movie_id, tag_id)
);

-- 7. ORIGINAL MOVIE USERS' RATINGS
CREATE TABLE IF NOT EXISTS ratings (
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL
        REFERENCES movies(movie_id),
    rating NUMERIC(2,1) NOT NULL
        CHECK (
            rating >= 0.5
            AND rating <= 5.0
            AND rating * 2 = TRUNC(rating * 2)
        ),
    rating_timestamp BIGINT NOT NULL,

    PRIMARY KEY (user_id, movie_id)
);

-- 8. USER-GENERATED TAGS
CREATE TABLE IF NOT EXISTS user_tags (
    user_tag_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL
        REFERENCES movies(movie_id),
    tag TEXT NOT NULL,
    tag_timestamp BIGINT NOT NULL
);

-- 9. APPLICATION ROLES
CREATE TABLE IF NOT EXISTS roles (
    role_id SMALLINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    role_name VARCHAR(30) UNIQUE NOT NULL
);

-- 10. APPLICATION USERS
CREATE TABLE IF NOT EXISTS app_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id SMALLINT NOT NULL
        REFERENCES roles(role_id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 11. APPLICATION USERS' OWN RATINGS
CREATE TABLE IF NOT EXISTS user_ratings (
    user_rating_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    user_id BIGINT NOT NULL
        REFERENCES app_users(user_id),
    movie_id INTEGER NOT NULL
        REFERENCES movies(movie_id),
    rating NUMERIC(2,1) NOT NULL
        CHECK (
            rating >= 0.5
            AND rating <= 5.0
            AND rating * 2 = TRUNC(rating * 2)
        ),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (user_id, movie_id)
);

-- 12. RATINGS STAGING TABLE
-- Used for bulk ingestion before validation.

CREATE UNLOGGED TABLE IF NOT EXISTS ratings_staging (
    user_id INTEGER,
    movie_id INTEGER,
    rating NUMERIC(3,1),
    rating_timestamp BIGINT
);

-- 13. DEFAULT APPLICATION ROLES

INSERT INTO roles (role_name)
VALUES ('admin'), ('user')
ON CONFLICT (role_name) DO NOTHING;
