# Project Setup & Run

## Prerequisites

* Docker
* Git
* Python 3.x
* uv (Python package manager)
* PyCharm IDE
* VSCode IDE

## Setup Steps

1.  **Clone Repository:**
    ```bash
    git clone [your-repository-url]
    cd [your-repository-directory]
    ```

2.  **Start External Services (Docker):**
    * Ensure Docker Desktop is running.
    * Start required services:
        ```bash
        docker compose up -d postgres redis frontend
        ```

3.  **Configure Backend (Local PyCharm):**
    * Navigate to the backend directory (e.g., `cd backend` or `cd ~/sealnext/backend`).
    * **Create/Sync Virtual Env:**
        ```bash
        uv sync
        ```
    * **Open Project in PyCharm:** Open the main project folder.
    * **Set Python Interpreter:**
        * `File > Settings > Project: ... > Python Interpreter`
        * `Add Interpreter... > On Venvs tab > Existing environment`
        * Set Interpreter path to your virtual environment's Python, e.g.: `~/sealnext/backend/.venv/bin/python` (Adjust path as needed). Click `OK`.
    * **Create FastAPI Run Configuration:**
        * `Run > Edit Configurations...`
        * Click `+` > `FastAPI`.
        * **Name:** e.g., "Run Backend"
        * **Application:** Select your main file, e.g., `~/sealnext/backend/app/main.py` (Adjust path as needed).
        * **Uvicorn options:** `--reload --host 0.0.0.0`, default port is 8000 already.
        * **Environment variables:** Click the edit icon. **Manually paste** required variables (e.g., from your `.env` file). **IMPORTANT:** 
            * Use localhost instead of `postgres` or `redis` for database connection.
            * Use `VARIABLE=value` format, **without any quotes (`""`)**.
            ```
            # Example format inside the PyCharm Env Var editor:
            DATABASE_URL=postgresql://user:pass@host:port/db
            REDIS_URL=redis://host:port/0
            SECRET_KEY=yoursecret
            # ... add all others
            ```
        * Click `Apply` and `OK`.

## Running the Backend

1.  Make sure Docker services (`postgres`, `redis`, `frontend`) are running (`docker-compose ps`).
2.  In PyCharm, select the "Run Backend" configuration from the dropdown menu.
3.  Click the green **Run (▶️)** or **Debug (🐞)** button.