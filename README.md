# Country Currency & Exchange API

This is a RESTful API built with Python, FastAPI, and MySQL. It fetches country data from external sources, computes estimated GDP, and caches the results in a local database, providing a full set of CRUD operations to access the data.

This project also includes a feature to generate a dynamic summary image of the cached data.

---

## Features

* Fetches data from `restcountries.com` and `open.er-api.com`.
* Caches all data in a MySQL database.
* Calculates an `estimated_gdp` for each country.
* Generates a `summary.png` image with key stats on data refresh.
* Provides filtering by region and currency.
* Provides sorting by name, population, and GDP.
* Automatic API documentation via Swagger UI (`/docs`) and ReDoc (`/redoc`).

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/countries/refresh` | Fetches fresh data from external APIs, updates the DB, and generates the summary image. |
| `GET` | `/countries` | Gets a list of all countries. Supports filtering and sorting. |
| `GET` | `/countries/{name}` | Gets a single country by its name (case-insensitive). |
| `DELETE` | `/countries/{name}` | Deletes a single country record by its name. |
| `GET` | `/status` | Shows the total number of cached countries and the last refresh timestamp. |
| `GET` | `/countries/image` | Serves the generated `summary.png` file. |

### Filtering & Sorting

The `GET /countries` endpoint supports the following query parameters:

* **`region`**: Filters by region (e.g., `?region=Africa`).
* **`currency`**: Filters by currency code (e.g., `?currency=NGN`).
* **`sort`**: Sorts the results. Options are:
    * `name_asc` (default)
    * `name_desc`
    * `population_asc`
    * `population_desc`
    * `gdp_asc`
    * `gdp_desc`

---

## Setup and Installation

### 1. Prerequisites

* Python 3.9+
* A running MySQL Server

### 2. Clone the Repository

```
git clone https://github.com/your-username/watermelon.git
cd country-api
```

### 3. Set Up Virtual Environment

It's highly recommended to use a virtual environment.

Windows:
```
python -m venv venv
.\venv\Scripts\activate
```

macOS / Linux:
```
python3 -m venv venv
source venv/bin/activate
```
### 4. Install Dependencies
Install all required packages from requirements.txt. 

```
pip install -r requirements.txt
```

### 5. Set Up Environment Variables
This project requires a .env file for configuration.

Create a file named .env in the project root.

Add your MySQL database URL:

Ini, TOML

# .env
DATABASE_URL="mysql+pymysql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME"
Example:

Ini, TOML

DATABASE_URL="mysql+pymysql://root:my_secret_password@localhost:3306/country_db"
Important: Make sure you have created the database (e.g., country_db) in MySQL before running the app.

SQL

CREATE DATABASE country_db;
How to Run
With your virtual environment active and .env file in place, run the app using uvicorn:

```
uvicorn main:app --reload
The API will be live at http://127.0.0.1:8000
```