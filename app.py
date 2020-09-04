import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from ipstack import GeoLookup

from helpers import sorry, login_required

# Configure application
app = Flask(__name__)


# templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache_control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def about():
    # Return Welcome page
    return render_template("about.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """ Show the search page """

    # Query database for current user hobbies
    hobbies = db.execute("SELECT * FROM hobby WHERE user_id = :user", {"user":session["user_id"]}).fetchall()

    # Query database for current user
    current = db.execute("SELECT row_to_json(row(country,city)) FROM users WHERE id = :user", {"user":session["user_id"]}).fetchone()

    # Set a variable for user country
    country = current[0]["f1"]

    # Set a variable for current user city
    city = current[0]["f2"]

    # User reached the page via POST
    if request.method == "POST":

        # Set variable for the selected hobby in the form
        z = request.form.get("hobby")

        # Query database for everyone who has same hobby at the same location except current user
        match = db.execute("SELECT * FROM users INNER JOIN hobby ON hobby.user_id = users.id WHERE users.id != :user AND country = :country AND city = :city AND hobby = :z ORDER BY name ASC", {"user":session["user_id"], "z":z, "country":country, "city":city}).fetchall()
        # Return filterd page showing every match as per the selected hobby
        return render_template("filterd.html", z=z, hobbies=hobbies, match=match, city=city, country=country)

    # User reached the age via GET
    else:

        # Query database for everyone who has all same current user hobbies at the same location except current user
        record = db.execute("SELECT * FROM users INNER JOIN hobby ON users.id = hobby.user_id WHERE users.id != :user AND country = :country AND city = :city AND hobby IN (SELECT hobby FROM hobby WHERE hobby.user_id = :user) ORDER BY name ASC", {"user":session["user_id"], "country":country, "city":city}).fetchall()
        # Return search page
        return render_template("search.html", hobbies=hobbies, record=record, city=city, country=country)


@app.route("/profile")
@login_required
def profile():
    # Show the profile page

    # Query database to check the user information
    hobbies = db.execute("SELECT * FROM hobby WHERE user_id = :userid", {"userid":session["user_id"]}).fetchall()
    # Show profile page with all user information
    return render_template("profile.html", hobbies=hobbies)


@app.route("/hobbies", methods=["GET", "POST"])
@login_required
def hobbies():
    # Hobbies page where user can add hobbies

    # Show user list of all hobbies
    hobbies = db.execute("SELECT * FROM hobbies ORDER BY name ASC").fetchall()

    # User reached the page via POST
    if request.method == "POST":

        # Add the chosen hobby to database
        db.execute("INSERT INTO hobby (hobby, user_id) VALUES (:hobby, :user)", {"hobby":request.form.get("hobby"), "user":session["user_id"]})
        db.commit() 

        # Return to profile page
        return redirect("/profile")

    # User readched the page via GET
    else:

        # Return hobbies page to add new hobby
        return render_template("hobbies.html", hobbies=hobbies)


@app.route("/register", methods=["GET", "POST"])
def register():
    # Show the register page

    # Query database for list of all hobbies
    hobbies = db.execute("SELECT * FROM hobbies ORDER BY name ASC").fetchall()

    # user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure name was provided
        if not request.form.get("username"):
            return sorry("must provide a name")

        # Ensure password was provided
        elif not request.form.get("password"):
            return sorry("must provide a password")

        # Ensure password was confirmed
        elif request.form.get("password") != request.form.get("confirm"):
            return sorry("passwords do not match")

        # Ensure year of birth was provided
        elif not request.form.get("year"):
            return sorry("Please enter your birth year")

        # Ensure hobby was provided
        elif not request.form.get("hobby"):
            return sorry("Please select a hobby")

        # Ensure App was provided
        elif not request.form.get("app"):
            return sorry("Please provide an App")

        # Ensure link was provided
        elif not request.form.get("link"):
            return sorry("Please provide a link to your account in the app")

        # Query database for same username
        rows = db.execute("SELECT * FROM users WHERE name = :username", {"username":request.form.get("username")}).fetchall()

        # Ensure the user does not already exist
        if len(rows) != 0:
            return sorry("username already exists")

        # hash the password before saving it i the database
        hashed = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # checking the current year
        currentyear = datetime.utcnow().year

        # Calculating user age
        age = int(currentyear) - int(request.form.get("year"))

        # Getting name from the form
        name = request.form.get("username")

        # get client IP address
        ip = request.form.get('ip')

        # connect to the API
        geo_lookup = GeoLookup(os.getenv("API_KEY"))
        
        # get the location details
        location = geo_lookup.get_location(ip)

        # Get user city 
        city = location['city']

        # Get user country 
        country = location['country_name']

        # Getting app from the form
        app = request.form.get("app")

        # Getting hobby from the form
        h = request.form.get("hobby")

        # Getting link from the form
        link = request.form.get("link")

        # Adding user information useres table
        db.execute("INSERT INTO users (name, hash, age, country, city, app, link) VALUES (:name, :hashed, :age, :country, :city, :app, :link)", {"name":name, "hashed":hashed, "age":age, "country":country, "city":city, "app":app, "link":link})
        db.commit() 

        # Query database for assigned user id
        row = db.execute("SELECT id FROM users WHERE name = :name", {"name":name}).fetchone()

        # Adding user hobby to hobby table
        db.execute("INSERT INTO hobby (hobby, user_id) VALUES (:hobby, :user)", {"hobby":h, "user":row[0]})
        db.commit() 

        # Remember which user has logged in
        session["user_id"] = row[0]

        # Riderict to search page
        return redirect("/search")

    # user reached route via GET
    else:

        # showing register page and providing lists of countries, cities and hobbies
        return render_template("register.html", hobbies=hobbies)


@app.route("/login", methods=["GET", "POST"])
def login():

    #forget any "user_id"
    session.clear()

    #User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # get client IP address
        ip = request.form.get('ip')

        # connect to the API
        geo_lookup = GeoLookup(os.getenv("API_KEY"))

        # get the location details
        location = geo_lookup.get_location(ip)

        # Get user city 
        city = location['city']

        # Get user country 
        country = location['country_name']

        # Ensure username was submitted
        if not request.form.get("username"):
            return sorry("Please enter your name")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return sorry("Please enter password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE name = :username", {"username":request.form.get("username")}).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return sorry("invalide username or/and password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Update user location with current data
        db.execute("UPDATE users SET country = :country, city = :city WHERE id = :user", {"country":country, "city":city, "user":session["user_id"]})
        db.commit() 

        # Redirect user to search page
        return redirect("/search")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    #forget any "user_id"
    session.clear()

    #rediredt user to login page
    return redirect("/login")


def errorhandler(e):
    # Handle error
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return sorry(e.name)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.run()