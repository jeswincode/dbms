from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import inspect, func
from flask_migrate import Migrate
from models import db, User, Team, Driver, Car, Race, RaceResult

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///f1_management.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "f1-dbms-project-secret-key"
app.config["TEMPLATES_AUTO_RELOAD"] = True

db.init_app(app)
migrate = Migrate(app, db, render_as_batch=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

MODEL_REGISTRY = {
    "teams": Team,
    "drivers": Driver,
    "cars": Car,
    "races": Race,
    "results": RaceResult
}

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("login"))
            if current_user.role not in roles:
                flash("Permission denied: You do not have access to perform this action.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def cast_value(column, value):
    if value is None or value == "":
        return None
    col_type = type(column.type).__name__
    if col_type == 'Date':
        return datetime.strptime(value, "%Y-%m-%d").date()
    if col_type == 'Boolean':
        return str(value).lower() in ['true', 'on', '1', 'yes']
    if col_type in ['Float', 'Numeric']:
        return float(value)
    if col_type == 'Integer':
        return int(value)
    return value

def get_related_data(model):
    related_data = {}
    for col in inspect(model).c:
        if col.foreign_keys:
            fk = list(col.foreign_keys)[0]
            target_table = fk.column.table.name
            for entity_model in MODEL_REGISTRY.values():
                if entity_model.__tablename__ == target_table:
                    related_data[col.name] = entity_model.query.all()
                    break
    return related_data

def get_model_relationships(model):
    mapper = inspect(model)
    relationships = {}
    for rel in mapper.relationships:
        target_model = rel.mapper.class_
        registry_key = next((k for k, v in MODEL_REGISTRY.items() if v == target_model), None)
        if registry_key:
            relationships[rel.key] = {
                "target_key": registry_key,
                "target_model": target_model,
                "relationship_obj": rel
            }
    return relationships

def get_average_races_per_driver():
    driver_race_counts = (
        db.session.query(
            Driver.id,
            func.count(func.distinct(RaceResult.race_id)).label("race_count")
        )
        .outerjoin(RaceResult, RaceResult.driver_id == Driver.id)
        .group_by(Driver.id)
        .subquery()
    )
    average = db.session.query(func.avg(driver_race_counts.c.race_count)).scalar()
    return round(float(average), 2) if average is not None else 0.0

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/admin/users", methods=["GET", "POST"])
@login_required
@role_required("Admin")
def manage_users():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
        else:
            new_user = User(username=username, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash(f"User '{username}' created with role '{role}'.", "success")
            return redirect(url_for("manage_users"))
    users = User.query.all()
    return render_template("manage_users.html", users=users)

@app.route("/")
@login_required
def index():
    stats = {name.capitalize(): model.query.count() for name, model in MODEL_REGISTRY.items()}
    stats["Average races per driver"] = get_average_races_per_driver()
    return render_template("index.html", stats=stats, entities=MODEL_REGISTRY.keys())

@app.route("/<string:entity>")
@login_required
def list_records(entity):
    if entity not in MODEL_REGISTRY:
        abort(404)
    model = MODEL_REGISTRY[entity]
    records = model.query.all()
    columns = inspect(model).c
    return render_template("generic_list.html", entity=entity, records=records, columns=columns)

@app.route("/<string:entity>/add", methods=["GET", "POST"])
@login_required
@role_required("Admin", "Editor")
def add_record(entity):
    if entity not in MODEL_REGISTRY:
        abort(404)
    model = MODEL_REGISTRY[entity]
    columns = inspect(model).c
    if request.method == "POST":
        new_record = model()
        for col in columns:
            if col.name in request.form and not col.primary_key:
                val = cast_value(col, request.form.get(col.name))
                setattr(new_record, col.name, val)
        for col in columns:
            if type(col.type).__name__ == 'Boolean' and col.name not in request.form:
                setattr(new_record, col.name, False)
        db.session.add(new_record)
        db.session.commit()
        flash(f"Record successfully added to {entity}.", "success")
        return redirect(url_for("list_records", entity=entity))
    related_data = get_related_data(model)
    return render_template("generic_form.html", entity=entity, columns=columns, record=None, related_data=related_data)

@app.route("/<string:entity>/edit/<int:record_id>", methods=["GET", "POST"])
@login_required
@role_required("Admin", "Editor")
def edit_record(entity, record_id):
    if entity not in MODEL_REGISTRY:
        abort(404)
    model = MODEL_REGISTRY[entity]
    columns = inspect(model).c
    record = model.query.get_or_404(record_id)
    if request.method == "POST":
        for col in columns:
            if col.name in request.form and not col.primary_key:
                val = cast_value(col, request.form.get(col.name))
                setattr(record, col.name, val)
        for col in columns:
            if type(col.type).__name__ == 'Boolean' and col.name not in request.form:
                setattr(record, col.name, False)
        db.session.commit()
        flash("Record updated successfully.", "success")
        return redirect(url_for("list_records", entity=entity))
    related_data = get_related_data(model)
    return render_template("generic_form.html", entity=entity, columns=columns, record=record, related_data=related_data)

@app.route("/<string:entity>/delete/<int:record_id>", methods=["POST"])
@login_required
@role_required("Admin")
def delete_record(entity, record_id):
    if entity not in MODEL_REGISTRY:
        abort(404)
    model = MODEL_REGISTRY[entity]
    record = model.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash(f"Record deleted from {entity}.", "info")
    return redirect(url_for("list_records", entity=entity))

@app.route("/joins")
@app.route("/joins/<string:primary_entity>")
@login_required
def dynamic_join_view(primary_entity=None):
    if not primary_entity:
        primary_entity = list(MODEL_REGISTRY.keys())[0]
    if primary_entity not in MODEL_REGISTRY:
        abort(404)
    base_model = MODEL_REGISTRY[primary_entity]
    relationships = get_model_relationships(base_model)
    selected_join_keys = request.args.getlist("joins")
    query = db.session.query(base_model)
    active_relationships = []
    for rel_key, rel_info in relationships.items():
        if rel_key in selected_join_keys:
            query = query.outerjoin(getattr(base_model, rel_key))
            active_relationships.append(rel_key)
    results = query.all()
    headers = [f"{base_model.__name__}: {c.name}" for c in inspect(base_model).c]
    for rel_key in active_relationships:
        rel_model = relationships[rel_key]["target_model"]
        headers.extend([f"{rel_model.__name__}: {c.name}" for c in inspect(rel_model).c])
    rows = []
    for record in results:
        row_values = [getattr(record, c.name) for c in inspect(base_model).c]
        for rel_key in active_relationships:
            related_obj = getattr(record, rel_key)
            rel_model = relationships[rel_key]["target_model"]
            if related_obj:
                row_values.extend([getattr(related_obj, c.name) for c in inspect(rel_model).c])
            else:
                row_values.extend([None] * len(inspect(rel_model).c))
        rows.append(row_values)
    return render_template("dynamic_join.html", entities=MODEL_REGISTRY.keys(), primary_entity=primary_entity, relationships=relationships, selected_join_keys=active_relationships, headers=headers, rows=rows)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", role="Admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin / admin123")
    app.run(debug=True)