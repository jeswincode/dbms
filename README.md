# F1 Fleet Control — DBMS Project

A full-stack F1 management website: Flask backend, SQLAlchemy ORM, SQLite
database, and a racing-themed front end. Five entities, full CRUD
(Create, Read, Update, Delete) on every one of them.

## Entities & schema

Each entity deliberately includes all 5 basic data types (Integer, String,
Float, Date, Boolean), plus foreign keys linking related entities:

| Entity      | Integer         | String           | Float               | Date            | Boolean         |
|-------------|------------------|-------------------|-----------------------|------------------|-------------------|
| Team        | id               | name              | budget_million        | founded_date     | is_active         |
| Driver      | id, team_id (FK) | name              | career_points         | date_of_birth    | is_active         |
| Car         | id, team_id (FK) | chassis_name      | top_speed_kmh         | build_date       | is_race_ready     |
| Race        | id               | grand_prix_name   | circuit_length_km     | race_date        | is_completed      |
| RaceResult  | id, finishing_position, driver_id (FK), race_id (FK) | — | points_scored | recorded_on | fastest_lap |

Relationships: `Team → Driver` (1‑to‑many), `Team → Car` (1‑to‑many),
`Driver → RaceResult` (1‑to‑many), `Race → RaceResult` (1‑to‑many).

## Project structure

```
f1_management/
├── app.py              # Flask routes (all CRUD logic lives here)
├── models.py            # SQLAlchemy models / schema definitions
├── seed_data.py          # Optional: populates sample rows
├── requirements.txt
├── static/
│   ├── css/style.css     # Racing-themed styling
│   └── js/script.js
└── templates/
    ├── base.html         # Shared layout, navbar, flash messages
    ├── index.html         # Dashboard
    ├── teams.html / team_form.html
    ├── drivers.html / driver_form.html
    ├── cars.html / car_form.html
    ├── races.html / race_form.html
    └── results.html / result_form.html
```

## Setup

You already have Flask and Flask-SQLAlchemy installed from earlier, but
if you're setting this up somewhere new:

```bash
py -m pip install -r requirements.txt
```

## Run it

```bash
py app.py
```

Then open **http://127.0.0.1:5000** in your browser. The database file
(`f1_management.db`) is created automatically on first run — no manual
setup required.

### Optional: add sample data

To pre-fill the site with a couple of teams, drivers, cars, races and
results (handy for demoing to your professor):

```bash
py seed_data.py
```

It checks whether the database already has data before inserting, so
it's safe to leave in your project.

## How it fits together (for making changes)

- **Add a field to an entity** → edit the model in `models.py`, delete
  `f1_management.db` (or write a migration) so it rebuilds with the new
  column, then add the corresponding `<input>` to that entity's form
  template and read it in the matching route in `app.py`.
- **Add a 6th entity** → copy the pattern used for any existing entity:
  one model class in `models.py`, one list route + two form routes
  (`add`/`edit`) + one delete route in `app.py`, one list template and
  one shared add/edit form template, and a nav link in `base.html`.
- **Styling** → all design tokens (colors, fonts) are defined once at
  the top of `static/css/style.css` under `:root`, so re-theming means
  changing a handful of hex values in one place.

## Notes

- Uses SQLite by default (zero setup). To switch to MySQL/PostgreSQL for
  a more "real" DBMS demo, just change `SQLALCHEMY_DATABASE_URI` in
  `app.py` (e.g. `mysql+pymysql://user:pass@localhost/f1db`) and install
  the matching driver.
- `debug=True` in `app.py` is convenient for development (auto-reloads
  on file changes, shows detailed errors) — turn it off before deploying
  anywhere public.
