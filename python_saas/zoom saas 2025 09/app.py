from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "My Super Secret KEY"

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)


@app.route("/")
def index():
    if "user_id" not in session:
        return render_template("index.html", logged_in=False)

    current_user = User.query.get(session["user_id"])
    return render_template("index.html", logged_in=True, current_user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect("/")
        else:
            return redirect("/login")

    return render_template("auth/login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        existing_user = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()

        if existing_user:
            flash(
                "Username or email already exists. Please choose a different username or email.",
                "danger",
            )
        else:
            hashed_password = generate_password_hash(password)

            new_user = User(username=username, password=hashed_password, email=email)
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("login"))

    return render_template("auth/register.html")


@app.route("/meeting")
def meeting():
    return render_template("meeting.html")


@app.route("/join")
def join():
    return render_template("join.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out successfully.", "success")
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
