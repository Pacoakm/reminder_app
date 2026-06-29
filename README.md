# Reminder App

A multi-user, full-stack task / reminder web app built with **Python**, **Streamlit**, and **MySQL**, accompanied by a small **Flask** REST API for the same data layer. Originally developed as an HKDSE ICT School-based Assessment.

## Features

- 👤 Multi-user registration and login (session cookie signed with JWT / HS256)
- 🔐 Password-protected authentication via `streamlit-authenticator` with a 30-day cookie
- ✅ Tasks: create, read, update (inline via `st.data_editor`), delete completed in bulk
- 📂 Per-user task categories (each user has their own category set, no cross-user leakage)
- 📅 Per-task `add_date` / `due_date`, validation that `due_date ≥ add_date`
- 📝 Title + description, edit-in-place inside the data grid
- 🙍 Profile picture upload (saved under `uploads/<username>/icon.png`)
- 🔁 Logout invalidates the cookie and clears server-side `logged_in` flag
- 💾 Persistence in a MySQL database accessed through `mysql-connector-python`
- 🌐 Parallel **Flask + Flask-CORS** REST API (`api.py`) that exposes the same operations as JSON endpoints

## Architecture

```
reminder_app/
├── auth.py                  # Streamlit login page (entry point)
├── backend.py               # All DB access + auth helpers + JWT/cookie helpers
├── api.py                   # Flask REST API exposing the same operations
├── pages/
│   ├── register.py          # Registration form
│   ├── list_task.py         # Main app: My Tasks / Category / User Info tabs
│   └── upload.py            # Profile-picture upload
├── test.py                  # one-liner sanity test (get_cid call)
├── test2.py                 # MySQL SSL connection test
├── test.txt                 # empty placeholder
├── .env.example             # (see below — not in repo, .env is git-ignored)
└── .gitignore               # ignores .env, env/, __pycache__, uploads/
```

Three layers:

1. **Streamlit frontend** (`auth.py`, `pages/*`) — calls into `backend`.
2. **Application / data layer** (`backend.py`) — Python functions, one DB connection per call.
3. **MySQL** — three relational tables: `user`, `category`, `tasks`.

The Flask layer (`api.py`) is an independent alternate entry point and does not import `backend.py` — it duplicates the same query helpers.

## Database schema

The app expects a MySQL database with three tables. Suggested DDL:

```sql
CREATE TABLE user (
    uid           INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(64)  NOT NULL UNIQUE,
    name          VARCHAR(128) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password      VARCHAR(255) NOT NULL,
    join_date     DATETIME     NOT NULL,
    logged_in     TINYINT(1)   NOT NULL DEFAULT 0,
    icon_path     VARCHAR(255) NULL
);

CREATE TABLE category (
    cid   INT AUTO_INCREMENT PRIMARY KEY,
    cname VARCHAR(64)  NOT NULL,
    uid   INT          NOT NULL,
    UNIQUE KEY uniq_user_cat (uid, cname),
    FOREIGN KEY (uid) REFERENCES user(uid) ON DELETE CASCADE
);

CREATE TABLE tasks (
    tid         INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    completed   TINYINT(1)   NOT NULL DEFAULT 0,
    adddate     DATE         NOT NULL,
    duedate     DATE         NULL,
    cid         INT          NULL,
    description TEXT         NULL,
    uid         INT          NOT NULL,
    FOREIGN KEY (uid) REFERENCES user(uid)   ON DELETE CASCADE,
    FOREIGN KEY (cid) REFERENCES category(cid) ON DELETE SET NULL
);
```

The schema is in 3NF, with foreign keys for referential integrity.

## Installation

```bash
git clone https://github.com/Pacoakm/reminder_app.git
cd reminder_app
python -m venv env
source env/bin/activate          # Windows: env\Scripts\activate
pip install streamlit \
            streamlit-authenticator \
            mysql-connector-python \
            pandas \
            python-dotenv \
            streamlit-cookies-controller \
            PyJWT \
            flask \
            flask-cors
```

(`test2.py` additionally references `bcrypt`, and `pages/register.py` references `requests` and `hashlib` — both are in the stdlib / commonly installed.)

> There is no `requirements.txt` in the repo, so copy the command above into one and `pip install -r requirements.txt` going forward.

## Configuration

Create a `.env` file in the project root (this path is git-ignored):

```dotenv
DB_HOST=127.0.0.1
DB_USERNAME=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=reminder
COOKIE_KEY=replace-with-a-long-random-secret-used-for-cookie-signing
```

`COOKIE_KEY` is consumed twice:

- in `backend.init_authenticator()` — the `streamlit-authenticator` cookie key (HMAC over the session cookie, 30-day expiry).
- in `backend.current_state()` — the `jwt.decode(...)` key for the same `sessionid` cookie.

Pick a long random string (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).

The Flask API in `api.py` reads the **same** `.env` variables to connect to MySQL.

## Running the Streamlit app

```bash
streamlit run auth.py
```

The login page opens at `http://localhost:8501`. After signing in you are routed to `/list_task` (the main My Tasks / Category / User Info dashboard).

| URL | Purpose |
|---|---|
| `http://localhost:8501/` | Login |
| `http://localhost:8501/register` | New account |
| `http://localhost:8501/list_task` | Task dashboard (needs login) |
| `http://localhost:8501/upload` | Profile-picture upload (needs login) |

## Running the Flask API (optional)

```bash
python api.py
```

REST endpoints (all return JSON). Default port is `5000`:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/login` | Body `{username, password}` — JSON login |
| `POST` | `/add_task` | Create a task |
| `GET`  | `/get_tasks/<username>` | List a user's tasks |
| `GET`  | `/get_all_category/<username>` | List a user's categories |
| `GET`  | `/get_category/<cid>` | Resolve category name from id |
| `GET`  | `/get_cid/<username>/<cname>` | Resolve category id from name |
| `GET`  | `/get_uid/<username>` | Resolve user id from username |
| `GET`  | `/get_user_by_username/<username>` | Full user record |
| `POST` | `/update_user_password` | Body `{username, new_password}` |
| `POST` | `/update_logged_in` | Mark user as logged in |
| `POST` | `/update_logged_out` | Mark user as logged out |
| `POST` | `/update_task` | Body `{task_id, column, new_value}` |
| `DELETE` | `/delete_completed/<username>` | Bulk-delete completed tasks |

## Security & known issues (read before deploying)

The codebase is a working SBA project; for production use the following should be tightened:

1. **Passwords are stored in plain SHA-256** (`pages/register.py` `hash_password`). There is no salt and no work factor. Use `bcrypt` / `argon2` instead — `api.py` already imports `bcrypt` for the `/login` check but is not wired into registration.
2. **SQL injection risk in `backend.py`.** `add_user`, `add_task`, `add_category`, `get_tasks`, `get_all_category`, `get_category`, `get_cid`, `delete_completed`, `delete_category`, `update_task` use f-string interpolation. The `api.py` copy uses parameterized queries — keep `backend.py` aligned with that style.
3. **`streamlit-authenticator` API drift.** `auth.py` does `name, authentication_status, username = authenticator.login()`, which is the pre-0.3 tuple-returning signature. On modern `streamlit-authenticator` (≥ 0.3.x) `login()` returns `None` and pushes the values into `st.session_state`. Pin the package or migrate to the new API.
4. **CAPTCHA is a stub.** `pages/register.py` defines `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` placeholders but never validates a Cloudflare Turnstile token. Wire it up to `https://challenges.cloudflare.com/turnstile/v0/siteverify` if you want bot protection.
5. **Login page has no input sanitisation.** `username = st.text_input(...)` is passed straight into SQL — see point 2.

## Tests in the repo

- `test.py` — quick smoke test that calls `get_cid("Work", "john_doe")`.
- `test2.py` — connects to MySQL with SSL (`ssl_cert`, `ssl_ca`, `ssl_key` paths hardcoded to `/home/pacoakm/...`; adjust before running).

Neither is wired into a CI system.

## Possible next steps

- Add `requirements.txt` + `pip install -r` instructions in CI
- Replace SHA-256 with bcrypt / argon2 and add a salt column
- Parameterise all queries in `backend.py`
- Wire Turnstile (or hCaptcha) verification into registration
- Add `streamlit run api.py`-style integration tests against a Dockerised MySQL
- Schedule recurring reminders (the `add_date`/`due_date` columns exist but no notification path is implemented yet)
