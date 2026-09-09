"""
models.py
---------
Database schema for the F1 Management System.

6 Entities: User, Team, Driver, Car, Race, RaceResult
Each entity includes all 5 basic SQL attribute types so the schema
satisfies the DBMS project requirement:

    Integer  -> primary keys / foreign keys / whole-number stats
    String   -> names / text fields / password hashes / user roles
    Float    -> decimal / numeric measurements
    Date     -> calendar dates
    Boolean  -> true/false flags

Relationships:
    Team        1 --- * Driver
    Team        1 --- * Car
    Driver      1 --- * RaceResult
    Race        1 --- * RaceResult
"""

from datetime import date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """System users with role-based permissions (Admin, Editor, Viewer)."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)                      # Integer
    username = db.Column(db.String(80), unique=True, nullable=False)      # String
    password_hash = db.Column(db.String(255), nullable=False)         # String
    role = db.Column(db.String(20), nullable=False, default="Viewer")  # String: Admin, Editor, Viewer

    def set_password(self, password):
        """Hashes the user password using Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies the hashed password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Team(db.Model):
    """A Formula 1 constructor / team."""
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)                      # Integer
    name = db.Column(db.String(100), nullable=False)                   # String
    budget_million = db.Column(db.Float, nullable=False)               # Float
    founded_date = db.Column(db.Date, nullable=False)                  # Date
    is_active = db.Column(db.Boolean, default=True)                    # Boolean
    country = db.Column(db.String(100), nullable=False)
                       # Boolean
   
    
    

    # One team has many drivers and many cars
    drivers = db.relationship("Driver", backref="team", cascade="all, delete-orphan")
    cars = db.relationship("Car", backref="team", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Team {self.name}>"


class Driver(db.Model):
    """A driver contracted to a team."""
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)                      # Integer
    name = db.Column(db.String(100), nullable=False)                   # String
    career_points = db.Column(db.Float, default=0.0)                   # Float
    date_of_birth = db.Column(db.Date, nullable=False)                 # Date
    is_active = db.Column(db.Boolean, default=True)    
                    # Boolean
    
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)

    results = db.relationship("RaceResult", backref="driver", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Driver {self.name}>"


class Car(db.Model):
    """A chassis / car built by a team."""
    __tablename__ = "cars"

    id = db.Column(db.Integer, primary_key=True)                      # Integer
    chassis_name = db.Column(db.String(100), nullable=False)           # String
    top_speed_kmh = db.Column(db.Float, nullable=False)                # Float
    build_date = db.Column(db.Date, nullable=False)                   # Date
    is_race_ready = db.Column(db.Boolean, default=True)                # Boolean
    car = db.Column(db.String(100), nullable=False)                    # String

    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)

    def __repr__(self):
        return f"<Car {self.chassis_name}>"


class Race(db.Model):
    """A Grand Prix event on the calendar."""
    __tablename__ = "races"

    id = db.Column(db.Integer, primary_key=True)                      # Integer
    grand_prix_name = db.Column(db.String(100), nullable=False)        # String
    circuit_length_km = db.Column(db.Float, nullable=False)            # Float
    race_date = db.Column(db.Date, nullable=False)                     # Date
    is_completed = db.Column(db.Boolean, default=False)                # Boolean
    is_comp = db.Column(db.Boolean, default=False)

    results = db.relationship("RaceResult", backref="race", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Race {self.grand_prix_name}>"


class RaceResult(db.Model):
    """The result of one driver in one race (junction entity)."""
    __tablename__ = "race_results"

    id = db.Column(db.Integer, primary_key=True)                      # Integer
    finishing_position = db.Column(db.Integer, nullable=False)         # Integer
    points_scored = db.Column(db.Float, default=0.0)                   # Float
    recorded_on = db.Column(db.Date, default=date.today)               # Date
    fastest_lap = db.Column(db.Boolean, default=False)                 # Boolean

    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    race_id = db.Column(db.Integer, db.ForeignKey("races.id"), nullable=False)

    def __repr__(self):
        return f"<Result {self.driver_id} @ {self.race_id}>"