# F1 Fleet Control — DBMS Project

A full-stack F1 management website built with Flask, SQLAlchemy, SQLite, Flask-Login and Flask-Migrate.

## Entities & relationships

The database currently contains six entities:

- **User** — authentication and Admin / Editor / Viewer roles
- **Team** — constructor information
- **Driver** — driver information and team relationship
- **Car** — car/chassis information and team relationship
- **Race** — Grand Prix information
- **RaceResult** — junction entity connecting drivers to races and storing finishing results

Relationships:

```text
Team 1 ─── * Driver
Team 1 ─── * Car
Driver 1 ─── * RaceResult
Race 1 ─── * RaceResult
```

`RaceResult` is the source of truth for driver participation. A driver's number of races should therefore be calculated from the distinct `race_id` values in `race_results`, rather than storing a duplicated race count on `Driver`.

## Dashboard aggregates

The dashboard currently shows counts for teams, drivers, cars, races and results. The project is also structured for aggregate statistics such as **average races per driver**.

The correct SQL concept for that statistic is:

```sql
SELECT AVG(race_count)
FROM (
    SELECT driver_id, COUNT(DISTINCT race_id) AS race_count
    FROM race_results
    GROUP BY driver_id
);
```

If drivers with zero races should also count toward the average, use a `LEFT JOIN` from `drivers` to `race_results` before averaging.

## Project structure

```text
app.py                 # Flask routes, CRUD, authentication and joins
models.py              # SQLAlchemy database models
requirements.txt       # Python dependencies
migrations/            # Alembic / Flask-Migrate migrations
static/css/style.css   # Application styling
templates/             # Dashboard, authentication, CRUD and join views
```

## Setup

Create/activate a virtual environment if desired, then install dependencies:

```bash
py -m pip install -r requirements.txt
```

Run the application:

```bash
py app.py
```

Then open `http://127.0.0.1:5000`.

The SQLite database is created locally under `instance/` when the application initializes it. The database file, `.env`, Python bytecode and other generated files are intentionally ignored by Git.

## Migrations

Flask-Migrate is configured in `app.py`.

For a schema change, prefer creating a migration instead of committing the local SQLite database:

```bash
flask db migrate -m "describe the schema change"
flask db upgrade
```

Review generated migrations before applying them, especially for SQLite batch operations.

## Notes

- Keep secrets and local configuration in `.env`; do not commit them.
- Keep `instance/*.db` local. The repository should contain the schema/models and migrations, not a developer's live database.
- `debug=True` is useful during development but should be disabled before public deployment.
