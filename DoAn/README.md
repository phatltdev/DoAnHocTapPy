# DoAn - Patient Management Web Application

This is a simple, single-page web application for managing patients, their test forms, and test details. It is built with a Python Flask backend, SQLAlchemy for ORM, a CockroachDB database, and a frontend using HTML, Bootstrap 5, and jQuery.

## Core Technologies

- **Backend:** Python 3.10+, Flask
- **Database:** CockroachDB with SQLAlchemy
- **Frontend:** HTML, Bootstrap 5, jQuery
- **API:** RESTful JSON API with a generic structure for CRUD operations.

## Project Structure

```
DoAn/
├── app.py              # Main Flask application, API endpoints, and database models
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Single-page frontend HTML
├── static/
│   └── js/
│       └── app.js        # Frontend jQuery and AJAX logic
└── README.md           # This file
```

## Setup and Installation

Follow these steps to get the project running on your local machine.

### 1. Prerequisites

- **Python 3.10 or newer:** Make sure Python is installed and accessible from your command line.
- **CockroachDB:** Install CockroachDB on your machine. You can find instructions at the [official CockroachDB documentation](https://www.cockroachlabs.com/docs/stable/install-cockroachdb.html).

### 2. Database Setup (CockroachDB)

1.  Start a local, insecure CockroachDB node:
    ```sh
    cockroach start-single-node --insecure --listen-addr=localhost:26257 --http-addr=localhost:8081 --store=cockroach-data

    ```

2.  In a new terminal, open the CockroachDB SQL shell:
    ```sh
    cockroach sql --insecure
    ```

3.  Create the database required for the application by running the following SQL command:
    ```sql
    CREATE DATABASE doan_db;
    ```

4.  **(Optional) For authenticated connections:** If you plan to use a specific user and password (as shown in "Option 2" in `app.py`), create a user and grant it privileges:
    ```sql
    CREATE USER your_user WITH PASSWORD 'your_password';
    GRANT ALL ON DATABASE doan_db TO your_user;
    ```
    You will then need to update the `SQLALCHEMY_DATABASE_URI` in `app.py` with these credentials.

### 3. Install Dependencies

1.  Open a terminal or command prompt and navigate to the root directory of the `DoAn` project.
2.  Create and activate a virtual environment (recommended):

    ```sh
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install the required Python packages using `pip`:

    ```sh
    pip install -r requirements.txt
    ```
    *Note: Make sure `sqlalchemy-cockroachdb` and `psycopg2-binary` are included in your `requirements.txt` or install them manually (`pip install sqlalchemy-cockroachdb psycopg2-binary`).*

### 4. Running the Application

1.  With your terminal still in the project's root directory, run the Flask application:

    ```sh
    python app.py
    ```

2.  The application will start the development server. When it runs for the first time, it will automatically create all the necessary tables (`patient`, `test_form`, `test_detail`) in the `doan_db` database.
3.  You should see output indicating that the server is running and listening for requests, typically at `http://127.0.0.1:5000/`.

### 5. Access the Application

1.  Open your web browser.
2.  Navigate to the following URL:

    [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

You can now use the web interface to perform all CRUD operations on patients, view their associated test forms, and drill down to the test details.
