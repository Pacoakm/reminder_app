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
pip install -r requirements.txt
```

The requirements file pins `streamlit-authenticator>=0.3.3` and includes `bcrypt`.

If you prefer to install by hand, the dependencies are:

`streamlit`, `streamlit-authenticator>=0.3.3`, `mysql-connector-python`, `pandas`, `python-dotenv`, `streamlit-cookies-controller`, `PyJWT`, `bcrypt`, `flask`, `flask-cors`.

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

The codebase is an SBA project. The most pressing security items have been fixed; the remaining list is for future hardening before any real deployment.

**Fixed in the current revision:**

- ✅ **Passwords** are hashed with bcrypt (`bcrypt.hashpw(..., bcrypt.gensalt())`) in both `pages/register.py` and the inline `change_pw` dialog inside `pages/list_task.py`. The previous plain SHA-256 (no salt) was equivalent to plaintext.
- ✅ **SQL queries in `backend.py`** are now parameterised (`%s` placeholders) for `add_user`, `add_task`, `add_category`, `get_tasks`, `get_all_category`, `get_category`, `get_cid`, `delete_completed`, `delete_category`, `update_task` — matching the style already used in `api.py`.
- ✅ **`streamlit-authenticator`** is migrated to the 0.3+ session-state API. `auth.py` no longer unpacks `name, authentication_status, username`; it reads them from `st.session_state`. Pinned in `requirements.txt` as `streamlit-authenticator>=0.3.3`.

**Remaining / future work:**

1. **Legacy password migration.** Existing users in the `user` table still have SHA-256 hashes; they can't log in with bcrypt. Add a one-shot migration script (verify a legacy hash against the password, then `update_user_password` with bcrypt) or wipe the table and re-seed.
2. **CAPTCHA.** Removed the unused Turnstile placeholder keys from `pages/register.py`. If you want bot protection, wire up Cloudflare Turnstile (or hCaptcha) by calling `https://challenges.cloudflare.com/turnstile/v0/siteverify` with `secret` + `response` (the user's submitted token) inside the `register()` form.
3. **Existing user `password` column size.** VARCHAR(255) comfortably fits a bcrypt hash, but the migration comment in point 1 should sanity-check it.
4. **`api.py /login` only does byte-equality.** It compares `password.encode('utf-8') == user['password'].encode('utf-8')` and does not use `bcrypt.checkpw`. Replace with `bcrypt.checkpw(password.encode(), user['password'].encode())` to actually verify the bcrypt hash.
5. **No CSRF / rate-limiting** on the Flask endpoints. Add Flask-Limiter + CSRF protection before exposing `/login` and `/update_user_password` publicly.
6. **No authorisation checks in `api.py`.** `/get_tasks/<username>`, `/delete_completed/<username>` etc. accept any username — a caller only needs to know the username to read or wipe that user's tasks. Either require a Bearer token / signed cookie to match the username, or change the routes to take a JWT.

## Tests in the repo

- `test.py` — quick smoke test that calls `get_cid("Work", "john_doe")`.
- `test2.py` — connects to MySQL with SSL (`ssl_cert`, `ssl_ca`, `ssl_key` paths hardcoded to `/home/pacoakm/...`; adjust before running).

Neither is wired into a CI system.

## Possible next steps

- Backfill bcrypt for any existing user rows (see **Legacy password migration** above)
- Wire Turnstile (or hCaptcha) verification into registration
- Replace `api.py /login`'s byte-equality check with `bcrypt.checkpw` and add per-user authorisation on the other Flask routes
- Add Flask-Limiter and a smoke-test workflow (`docker compose up mysql`, then hit the endpoints) in CI
- Schedule recurring reminders (the `add_date` / `due_date` columns exist but no notification path is implemented yet)
- Replace the raw `pytesseract`-style password rule with a sensible `password_strength` estimator (e.g. zxcvbn)
