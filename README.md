# 🎬 MovieLens Analytics Platform

A full-stack **Data Engineering project** built using Python, PostgreSQL, Streamlit, and Plotly to process, store, analyze, and visualize the MovieLens dataset.

The platform implements an end-to-end data engineering pipeline, including data profiling, validation, ETL processing, relational database management, SQL-based analytics, interactive dashboards, user authentication, role-based access control, and database-level row-level security.

**Course:** DS5003 – Data Engineering Lab  
**Institution:** IIT Palakkad  
**Dataset:** [MovieLens Latest Dataset](https://grouplens.org/datasets/movielens/)  
**Database:** PostgreSQL

---

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Project Objectives](#-project-objectives)
- [Dataset Description](#-dataset-description)
- [Technology Stack](#-technology-stack)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Data Engineering Pipeline](#-data-engineering-pipeline)
- [Database Design](#-database-design)
- [Dashboard Features](#-dashboard-features)
- [Authentication and Security](#-authentication-and-security)
- [Installation and Setup](#-installation-and-setup)
- [Running the Application](#-running-the-application)
- [Analytical Questions](#-analytical-questions)
- [Data Quality and Validation](#-data-quality-and-validation)
- [Testing](#-testing)
- [Future Improvements](#-future-improvements)
- [Dataset Attribution](#-dataset-attribution)

---

## 📖 Project Overview

MovieLens Analytics is an interactive movie analytics platform designed to demonstrate practical data engineering concepts using a large-scale real-world dataset.

The project uses the MovieLens Latest dataset, containing millions of movie ratings and user-generated tags. The raw CSV files are processed through a Python-based ETL pipeline and stored in a PostgreSQL relational database.

The stored data is accessed using SQL queries to generate analytical insights, which are presented through an interactive Streamlit dashboard.

The application also supports multiple user roles:

- **Administrator:** Can manage application users and access analytics.
- **Regular User:** Can explore analytics and submit or update personal movie ratings.

The project demonstrates the complete journey from raw data ingestion to interactive data exploration.

## 🎯 Project Objectives

The main objectives are:

1. Process large CSV datasets and organize them into relational database tables.
2. Perform data profiling, cleaning, preprocessing, and validation.
3. Design and implement a PostgreSQL database schema.
4. Develop an efficient ETL pipeline for loading large datasets.
5. Perform analytical operations using SQL.
6. Build interactive data visualizations and dashboards.
7. Implement authentication and role-based access control.
8. Restrict application users to modifying only their own submitted movie ratings.
9. Demonstrate database security through PostgreSQL row-level security.

---

## 📊 Dataset Description

The project uses the **MovieLens Latest dataset**, generated on July 20, 2023, by GroupLens Research.

### Dataset Statistics

| Dataset Component | Number of Records |
|---|---:|
| Movies | 86,537 |
| Ratings | 33,832,162 |
| User Tags | 2,328,315 |
| Genome Scores | 18,472,128 |
| Genome Tags | 1,128 |
| Distinct Rating Users | 330,975 |

### Dataset Files

The dataset contains six CSV files.

| File | Description |
|---|---|
| `movies.csv` | Movie titles, IDs, and genres |
| `ratings.csv` | User ratings for movies |
| `tags.csv` | User-generated movie tags |
| `links.csv` | IMDb and TMDb identifiers |
| `genome-tags.csv` | Movie genome tag definitions |
| `genome-scores.csv` | Relevance scores for movie genome tags |

### Important Dataset Relationships

- `movieId` connects movies, ratings, tags, links, and genome scores.
- `userId` identifies users in ratings and user-generated tags.
- `tagId` connects genome tags with genome relevance scores.

The ratings use a half-star scale ranging from 0.5 to 5.0.

**Note:** The dataset is not included in this repository because of its large size. Download it separately from the official MovieLens website.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing and application development |
| Pandas | Data profiling, cleaning, and transformation |
| NumPy | Numerical operations |
| PostgreSQL | Relational database management |
| SQLAlchemy | Database connectivity |
| Psycopg2 | PostgreSQL connectivity and bulk loading |
| Streamlit | Interactive web dashboard |
| Plotly | Interactive charts and visualizations |
| Bcrypt | Password hashing |
| Python-dotenv | Environment variable management |
| Pytest | Testing |

---

## 🏗️ System Architecture

The project follows a layered data engineering architecture.

```text
                 MOVIELENS DATASET
                        |
                        v
              Raw CSV Files (6 files)
                        |
                        v
              DATA PROFILING & VALIDATION
                        |
                        v
                 PYTHON ETL PIPELINE
                        |
                        v
                DATA TRANSFORMATION
                        |
                        v
                POSTGRESQL DATABASE
                        |
             +----------+----------+
             |                     |
             v                     v
       SQL ANALYTICS         AUTHENTICATION
             |                     |
             v                     v
       PANDAS DATAFRAMES    ROLE-BASED ACCESS
             |                     |
             +----------+----------+
                        |
                        v
                STREAMLIT DASHBOARD
                        |
                        v
                PLOTLY VISUALIZATIONS
```

### Architecture Components

**1. Data Layer**

Contains the original MovieLens CSV files.

**2. ETL Layer**

Python scripts perform data ingestion, validation, transformation, and loading into PostgreSQL.

**3. Database Layer**

PostgreSQL stores movies, genres, ratings, tags, genome scores, and application user information.

**4. Analytics Layer**

SQL queries calculate rating distributions, popular tags, genre coverage, and movie rankings.

**5. Application Layer**

Streamlit provides an interactive interface with login, role-based functionality, and analytical visualizations.

---

## 📁 Project Structure

```text
movie-lens-analytics/
│
├── data/
│   ├── raw/
│   │   ├── movies.csv
│   │   ├── ratings.csv
│   │   ├── tags.csv
│   │   ├── links.csv
│   │   ├── genome-tags.csv
│   │   └── genome-scores.csv
│   │
│   ├── processed/
│   └── rejected/
│
├── config/
│   ├── __init__.py
│   ├── database.py
│   └── settings.py
│
├── database/
│
├── etl/
│   ├── __init__.py
│   ├── profile_dataset.py
│   ├── validate_dataset.py
│   ├── load_dimensions.py
│   ├── load_genome_scores.py
│   ├── load_ratings.py
│   ├── load_user_tags.py
│   └── create_admin.py
│
├── analytics/
│   ├── __init__.py
│   └── queries.py
│
├── dashboard/
│   ├── app.py
│   └── auth.py
│
├── tests/
│
├── logs/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Data Engineering Pipeline

The ETL pipeline is responsible for processing and loading the MovieLens dataset into PostgreSQL.

### 1. Data Profiling

The profiling stage examines:

- Dataset dimensions.
- Column names and data types.
- Missing values.
- Duplicate records.
- File sizes.
- Basic dataset statistics.

### 2. Data Validation and Cleaning

The validation process checks:

- Missing and invalid values.
- Movie and user references.
- Genre validity.
- Rating ranges.
- Duplicate rating combinations.
- Genome score ranges.
- Whitespace-only user tags.

Invalid whitespace-only tags are separated into a rejected records table rather than silently discarded.

Missing TMDb IDs and missing movie release years are preserved where appropriate.

### 3. Data Loading

The ETL process uses PostgreSQL bulk loading techniques to handle large CSV files efficiently.

The loading process is organized into the following stages:

| Stage | Script | Purpose |
|---|---|---|
| 1 | `load_dimensions.py` | Load movies, genres, movie-genre relationships, links, and genome tags |
| 2 | `load_genome_scores.py` | Load genome relevance scores |
| 3 | `load_ratings.py` | Load ratings through a staging table |
| 4 | `load_user_tags.py` | Load user-generated tags and separate rejected records |

Large datasets are loaded using PostgreSQL `COPY` through Psycopg2 rather than relying on row-by-row insertion.

The ratings pipeline uses a staging table before transferring validated records into the final ratings table.

---

## 🗄️ Database Design

The project uses PostgreSQL as its primary relational database.

### Main Tables

| Table | Purpose |
|---|---|
| `movies` | Stores movie information |
| `genres` | Stores unique genre names |
| `movie_genres` | Maps movies to genres |
| `movie_links` | Stores IMDb and TMDb identifiers |
| `ratings` | Stores original MovieLens ratings |
| `user_tags` | Stores user-generated tags |
| `genome_tags` | Stores genome tag definitions |
| `genome_scores` | Stores movie-tag relevance scores |
| `app_users` | Stores application user accounts |
| `roles` | Stores administrator and user roles |
| `user_ratings` | Stores ratings submitted through the application |
| `ratings_staging` | Temporary staging table for rating ingestion |
| `user_tags_rejected` | Stores rejected user-tag records |

### Database Relationships

- One movie can have multiple ratings.
- One movie can belong to multiple genres.
- One genre can contain multiple movies.
- One movie can have multiple user-generated tags.
- One movie can have multiple genome relevance scores.
- One application user can submit ratings for multiple movies.

The `movie_genres` table implements the many-to-many relationship between movies and genres.

The `user_ratings` table is kept separate from the original MovieLens `ratings` table so application-submitted ratings do not modify the source dataset.

---

## 📈 Dashboard Features

The Streamlit dashboard provides interactive access to all seven analytical questions.

### A. Top 5 Tags by Relevance

For a selected movie, displays the five genome tags with the highest relevance scores.

**Visualization:** Horizontal bar chart.

### B. Overall and Year-wise Top 10 Movies

Identifies the top ten movies based on average user ratings.

Two views are provided:

- Overall top ten movies.
- Year-wise top ten movies based on release year.

**Visualization:** Interactive tables and bar charts.

### C. Most Popular Tags by Genre

Identifies the most frequently used user-generated tags for each genre.

Users can select a genre to explore its most popular tags.

**Visualization:** Interactive table and horizontal bar chart.

### D. Distribution of User Ratings for a Movie

Displays the distribution of ratings received by a selected movie.

Also calculates:

- Total number of ratings.
- Average movie rating.

**Visualization:** Rating distribution bar chart.

### E. Distribution of Total Ratings for Movies

Groups movies according to the number of ratings they have received.

The rating-count categories are:

- 0
- 1–5
- 6–10
- 11–50
- 51–100
- 101–500
- 501–1000
- 1001+

**Visualization:** Distribution table and bar chart.

### F. Genre with the Highest Number of Movie Releases

For a selected release year, identifies the genre with the highest number of movie releases.

Ties are preserved where applicable.

**Visualization:** Metric cards, table, and bar chart.

### G. Genre-wise Coverage of Movies

Displays the number and percentage of movies belonging to each genre.

Coverage is calculated relative to the total number of movies.

**Visualization:** Genre coverage table and horizontal bar chart.

**Note:** A movie can belong to multiple genres. Therefore, genre coverage percentages are not mutually exclusive and may sum to more than 100%.

---

## 🔐 Authentication and Security

The application implements authentication and role-based access control.

### User Roles

**Administrator**

- Login to the application.
- Access all analytical dashboard features.
- Create regular application users.
- View registered application users.
- View submitted movie ratings.

**Regular User**

- Login to the application.
- Explore all analytical dashboard features.
- Search for movies.
- Submit movie ratings.
- Update previously submitted ratings.
- Access only their own submitted ratings through the application.

### Password Security

Passwords are hashed using the Bcrypt algorithm before being stored in PostgreSQL.

Plain-text passwords are not stored in the database.

### Database Access Separation

Two PostgreSQL database connections are maintained:

| Connection | Database Account | Purpose |
|---|---|---|
| Administrative | `postgres` | ETL operations and administrative database tasks |
| Application | `movielens_app` | Streamlit dashboard and authentication |

The application account has restricted privileges:

- Read-only access to the original MovieLens data tables.
- Read access to application users and roles.
- Permission to create application users.
- SELECT, INSERT, and UPDATE access to `user_ratings`.
- No DELETE permission on `user_ratings`.

### Row-Level Security (RLS)

PostgreSQL Row-Level Security is enabled and forced on the `user_ratings` table.

The application supplies transaction-local identity settings:

- `app.user_id`
- `app.user_role`

The RLS policy allows:

- Regular users to access and modify their own submitted ratings.
- Administrators to access all submitted ratings.

The implementation was tested using two regular users and one administrator.

**Security limitation:** The application uses a shared PostgreSQL application account. The RLS policy trusts the identity supplied by the authenticated application. A person with direct access to the application database credentials could set these custom session variables themselves. Therefore, RLS provides defense in depth, but is not an independent authentication boundary against compromised application credentials.

---

## 💻 Installation and Setup

### Prerequisites

Install the following:

- Python 3.9 or later.
- PostgreSQL.
- Git.
- VS Code or another Python IDE.

### 1. Clone the Repository

```bash
git clone https://github.com/Yuvisingh0956/DS5003A-movie-lens-analytics.git
```

Navigate to the project:

```bash
cd movie-lens-analytics
```

### 2. Create a Virtual Environment

```bash
python -m venv venv_new
```

Activate it on Linux:

```bash
source venv_new/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the Dataset

Download the MovieLens Latest dataset from:

https://grouplens.org/datasets/movielens/

Extract the six CSV files into:

```text
data/raw/
```

### 5. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=movielens_db

# Administrative connection for ETL
DB_USER=postgres
DB_PASSWORD=your_admin_password

# Restricted application connection
APP_DB_USER=movielens_app
APP_DB_PASSWORD=your_application_password
```

Replace the example credentials with your local PostgreSQL credentials.

**Important:** Never commit `.env` to GitHub.

### 6. Create the PostgreSQL Database

Connect to PostgreSQL:

```bash
psql -U postgres
```

Create the database:

```sql
CREATE DATABASE movielens_db;
```

Connect to it:

```sql
\c movielens_db
```

Execute the database schema SQL scripts from the `database/` directory before running the ETL pipeline.

### 7. Run the ETL Pipeline

Run the scripts from the project root, in this order:

```bash
python -m etl.profile_dataset
```

```bash
python -m etl.validate_dataset
```

```bash
python -m etl.load_dimensions
```

```bash
python -m etl.load_genome_scores
```

```bash
python -m etl.load_ratings
```

```bash
python -m etl.load_user_tags
```

The ETL scripts use the administrative database connection.

### 8. Configure the Application Database Account

Create the restricted PostgreSQL application account and grant the permissions described in the [Authentication and Security](#-authentication-and-security) section.

Enable row-level security on `user_ratings` and configure its policy after the application code is configured.

### 9. Create an Administrator Account

Run:

```bash
python -m etl.create_admin
```

Follow the prompts to create the initial administrator account.

---

## 🚀 Running the Application

Activate the virtual environment:

```bash
source venv_new/bin/activate
```

Start Streamlit:

```bash
streamlit run dashboard/app.py
```

The dashboard will be available at the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

Log in using the administrator account created during setup.

The administrator can create regular application users through the Administrator Panel.

---

## 🧪 Data Quality and Validation

The dataset validation stage checks the integrity of the loaded data.

Some important validation results from the processed dataset include:

| Validation | Result |
|---|---|
| Movie records | 86,537 |
| Genre records | 19 |
| Movie-genre relationships | 145,228 |
| Genome tag definitions | 1,128 |
| Genome score records | 18,472,128 |
| Original ratings | 33,832,162 |
| Imported user tags | 2,328,305 |
| Rejected whitespace-only tags | 10 |
| Orphan movie references | 0 |

Additional checks include:

- Rating values are between 0.5 and 5.0.
- Ratings use valid half-star increments.
- Genome relevance values are between 0 and 1.
- Movie references are valid.
- Duplicate `(user_id, movie_id)` rating combinations are checked.
- Genome scores are complete for the movies represented in the genome dataset.

The 10 rejected user tags contained whitespace-only values. They are preserved separately in `user_tags_rejected`.

---

## 🧪 Testing

The project includes validation and functional tests for the database, ETL pipeline, analytics, and application functionality.

Important tests performed include:

### ETL Tests

- CSV profiling and validation.
- Successful bulk loading.
- Record-count verification.
- Foreign-key integrity checks.
- Duplicate rating checks.
- Rejected-tag handling.

### Analytics Tests

- Top genome tags for a selected movie.
- Overall and year-wise top movie rankings.
- Popular tags by genre.
- Movie rating distributions.
- Movie rating-count buckets.
- Highest-release genre by year.
- Genre-wise coverage.

### Authentication Tests

- Valid login.
- Invalid login.
- Password verification.
- Logout.
- Protected dashboard access.
- Administrator user creation.

### Database Security Tests

- Application account permissions.
- User-level rating visibility.
- Administrator rating visibility.
- Cross-user update restriction.
- Original MovieLens ratings remain unchanged.

---

## 🔮 Future Improvements

Potential enhancements include:

- Add automated ETL scheduling.
- Implement incremental data ingestion.
- Add database query optimization and indexing analysis.
- Add pagination for large search results.
- Introduce more advanced movie recommendation features.
- Add automated unit and integration test coverage.
- Improve application security with stronger database identity propagation.
- Deploy the dashboard to a cloud platform.
- Add CI/CD workflows using GitHub Actions.
- Add monitoring and logging for ETL execution.

---

## 📚 Dataset Attribution

This project uses the MovieLens dataset provided by GroupLens Research.

**Dataset reference:**

Harper, F. M., & Konstan, J. A. (2015). *The MovieLens Datasets: History and Context.* ACM Transactions on Interactive Intelligent Systems, 5(4).

https://doi.org/10.1145/2827872

Genome dataset reference:

Vig, J., Sen, S., & Riedl, J. (2012). *The Tag Genome: Encoding Community Knowledge to Support Novel Interaction.*

https://doi.org/10.1145/2362394.2362395

Dataset website:

https://grouplens.org/datasets/movielens/

Please refer to the official GroupLens dataset terms for redistribution and usage restrictions. The dataset is not included in this repository.

---

## 👨‍💻 Project Information

**Project:** MovieLens Analytics Platform  
**Course:** DS5003 – Data Engineering Lab  
**Institution:** IIT Palakkad

Built as an academic project to demonstrate practical concepts in data engineering, relational database design, ETL development, SQL analytics, interactive visualization, and application security.

---

⭐ If you find this project useful, feel free to explore the code and adapt the architecture for other data engineering applications.
