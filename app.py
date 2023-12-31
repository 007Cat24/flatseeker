import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from login_helper import login_required, apology, check_password

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///flatseeker.db")


# TEMPORARY
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show main page"""

    # Query database for friend requests:
    friend_requests = db.execute(
        "SELECT * FROM friends WHERE confirmed = 'False' AND user2_id = ?",
        session["user_id"],
    )
    for friend in friend_requests:
        rows = db.execute("SELECT username FROM users WHERE id = ?", friend["user1_id"])
        friend["user1_name"] = rows[0]["username"]
    return render_template(
        "index.html", friend_requests=friend_requests, user_id=session["user_id"]
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_flat():
    """Allow user to add flats"""

    if request.method == "POST":
        # Make sure that all fields are filled out
        title = request.form.get("title")
        link = request.form.get("link")
        rooms = request.form.get("rooms")
        price = request.form.get("price")
        location = request.form.get("location")
        comments = request.form.get("comments")

        if not title or not link or not rooms or not price:
            return apology("Please fill out all required fields before submitting!")

        # Validate numeric inputs
        if rooms.isnumeric() and int(rooms) >= 1:
            rooms = int(rooms)
        else:
            return apology("Please only enter numbers in the room field")

        if price.isnumeric() and int(price) > 0:
            price = int(price)
        else:
            return apology("Please only enter numbers in the price field")

        # Add flat to database
        db.execute(
            "INSERT INTO flats (title, link, rooms, price, added_by, location, comments) VALUES(?, ?, ?, ?, ?, ?, ?)",
            title,
            link,
            rooms,
            price,
            session["user_id"],
            location,
            comments,
        )
        flash("Flat added successfully")
        return redirect("/view")
    else:
        return render_template("add.html")


@app.route("/addfriend", methods=["GET", "POST"])
@login_required
def add_friend():
    """Allow user to add friends"""

    if request.method == "POST":
        # Make sure that all fields are filled out
        friend = request.form.get("friend")
        print(friend)
        # Prevent users from adding themselves
        if session["username"] == friend:
            return apology("You can't add yourself!")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", friend)

        # Ensure username exists and password is correct
        if len(rows) != 1:
            flash("Username not found")
            return redirect("/addfriend")

        # Check if friend request already exists:
        friend_requests = db.execute(
            "SELECT * FROM friends WHERE confirmed = 'False' AND user1_id = ? AND user2_id = ?",
            session["user_id"],
            rows[0]["id"],
        )
        print(friend_requests)
        if len(friend_requests) == 1:
            flash("Friend request already sent")
            return redirect("/")

        # Accept friend if request already exists, ignore otherwise:
        friend_requests = db.execute(
            "SELECT * FROM friends WHERE confirmed = 'False' AND user2_id = ? AND user1_id = ?",
            session["user_id"],
            rows[0]["id"],
        )
        if len(friend_requests) == 1:
            ignore = request.form.get("ignore")
            if ignore == "False":
                db.execute(
                    "UPDATE friends SET confirmed = 'True' WHERE user2_id = ? AND user1_id = ?",
                    session["user_id"],
                    rows[0]["id"],
                )
                flash("Friend request accepted")
                return redirect("/")
            elif ignore == "True":
                db.execute(
                    "DELETE FROM friends WHERE user2_id = ? AND user1_id = ?",
                    session["user_id"],
                    rows[0]["id"],
                )
                flash("Friend request ignored")
                return redirect("/")
            else:
                return apology("Server error")

        # Delete friend
        confirmed_friends = db.execute(
            "SELECT * FROM friends WHERE confirmed = 'True' AND user2_id = ? AND user1_id = ?",
            session["user_id"],
            rows[0]["id"],
        )
        ignore = request.form.get("ignore")
        if ignore == "True":
            db.execute(
                "DELETE FROM friends WHERE user2_id = ? AND user1_id = ?",
                session["user_id"],
                rows[0]["id"],
            )
            flash("Friend deleted")
            return redirect("/")

        # Add friend request to database
        db.execute(
            "INSERT INTO friends (user1_id, user2_id, confirmed) VALUES(?, ?, ?)",
            session["user_id"],
            rows[0]["id"],
            "False",
        )
        flash("Friend request sent!")
        return redirect("/")
    else:
        return render_template("addfriend.html")

@app.route("/comment", methods=["POST"])
@login_required
def comment():
    """Allow user to comment"""
    flat_id = request.form.get("flat_id")
    type = request.form.get("type")
    if not flat_id or not type:
        return apology("Please use the form to submit comments")
    flats = db.execute("SELECT * FROM flats WHERE id = ?", flat_id)
    for flat in flats:
        friend1 = db.execute("SELECT user1_id FROM friends WHERE user2_id = ? AND confirmed='True'", flat["added_by"])
        friend2 = db.execute("SELECT user2_id FROM friends WHERE user1_id = ? AND confirmed='True'", flat["added_by"])

        # Source for following line: https://stackoverflow.com/questions/3897499/check-if-value-already-exists-within-list-of-dictionaries-in-python
        if any(entry['user1_id'] == session["user_id"] for entry in friend1) or any(entry['user2_id'] == session["user_id"] for entry in friend2) or session["user_id"] == flat["added_by"]:
            if type == "ADD":
                db.execute("INSERT INTO comments (flat_id, user_id, text) VALUES(?, ?, ?)", flat_id, session["user_id"], request.form.get("comment"))
            elif type == "DELETE":
                comment_id = request.form.get("comment_id")
                db.execute("DELETE FROM comments WHERE id = ?", comment_id)
            return redirect("/flat?id=" + flat_id)
        else:
            return apology("Unauthorised")

@app.route("/changepwd", methods=["GET", "POST"])
@login_required
def changepwd():
    """Allow user to change password"""

    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm = request.form.get("confirmation")
        # Make sure all fields are filled out and the user made no typos
        if not old_password or not new_password or not confirm:
            return apology("Please fill out all fields!")
        if new_password != confirm:
            return apology("Passwords don't match")
        if not check_password(new_password):
            flash("Password doesn't meet requirements")
            return redirect("/register")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Check if password is correct
        if not check_password_hash(rows[0]["hash"], old_password):
            return apology("invalid password", 403)
        # Update password
        db.execute(
            "UPDATE users SET hash = ? WHERE id = ?",
            generate_password_hash(new_password),
            session["user_id"],
        )

        return redirect("/")
    else:
        # Show registration form
        return render_template("changepwd.html")


@app.route("/friends")
@login_required
def friends():
    """Show list of friends"""

    # Query database for friends:
    friends = db.execute(
        "SELECT * FROM friends WHERE confirmed = 'True' AND user2_id = ? OR user1_id = ?",
        session["user_id"],
        session["user_id"],
    )
    for friend in friends:
        if friend["user1_id"] != session["user_id"]:
            rows = db.execute(
                "SELECT username FROM users WHERE id = ?", friend["user1_id"]
            )
            friend["user1_name"] = rows[0]["username"]
        else:
            rows = db.execute(
                "SELECT username FROM users WHERE id = ?", friend["user2_id"]
            )
            friend["user1_name"] = rows[0]["username"]
    return render_template("friends.html", friends=friends)


@app.route("/view")
@login_required
def viewallflats():
    """Show list of all flats"""
    flats = db.execute("SELECT * FROM flats ORDER BY timestamp DESC")
    valid_flats = []
    for flat in flats:
        friend1 = db.execute("SELECT user1_id FROM friends WHERE user2_id = ? AND confirmed='True'", flat["added_by"])
        friend2 = db.execute("SELECT user2_id FROM friends WHERE user1_id = ? AND confirmed='True'", flat["added_by"])

        # Source for following line: https://stackoverflow.com/questions/3897499/check-if-value-already-exists-within-list-of-dictionaries-in-python
        if any(entry['user1_id'] == session["user_id"] for entry in friend1) or any(entry['user2_id'] == session["user_id"] for entry in friend2) or session["user_id"] == flat["added_by"]:
            valid_flats.append(flat)
    flats = valid_flats
    return render_template("view.html", flats=flats)


@app.route("/flat")
@login_required
def viewflat():
    """Show individual flat"""
    flat_id = request.args.get("id")
    if flat_id:
        flat = db.execute("SELECT * FROM flats WHERE id = ?", flat_id)
        if len(flat) == 1:
            flat = flat[0]
            rows = db.execute(
                "SELECT username FROM users WHERE id = ?", flat["added_by"]
            )
            flat["username"] = rows[0]["username"]
            friend1 = db.execute("SELECT user1_id FROM friends WHERE user2_id = ? AND confirmed='True'", flat["added_by"])
            friend2 = db.execute("SELECT user2_id FROM friends WHERE user1_id = ? AND confirmed='True'", flat["added_by"])

            # Source for following line: https://stackoverflow.com/questions/3897499/check-if-value-already-exists-within-list-of-dictionaries-in-python
            if any(entry['user1_id'] == session["user_id"] for entry in friend1) or any(entry['user2_id'] == session["user_id"] for entry in friend2) or session["user_id"] == flat["added_by"]:
                comments = db.execute("SELECT * FROM comments WHERE flat_id = ?", flat_id)
                for comment in comments:
                    rows = db.execute("SELECT username FROM users WHERE id = ?", comment["user_id"])
                    comment["username"] = rows[0]["username"]
                return render_template("flat.html", flat=flat, comments=comments, session=session)
            else:
                return apology("Unauthorised")

        else:
            return apology("Flat not found")
    else:
        return apology("Invalid input")


@app.route("/delete")
@login_required
def deleteflat():
    """Delete flat"""
    flat_id = request.args.get("id")
    if flat_id:
        flat = db.execute("SELECT * FROM flats WHERE id = ?", flat_id)
        if len(flat) == 1:
            flat = flat[0]
            # Make sure users can only delete their own flat
            if flat["added_by"] == session["user_id"]:
                db.execute("DELETE FROM flats WHERE id = ?", flat_id)
                flash("Flat deleted")
                return redirect("/view")
            else:
                return apology("Unauthorised")
        else:
            return apology("Flat not found")
    else:
        return apology("Invalid input")


@app.route("/edit", methods=["GET", "POST"])
@login_required
def editflat():
    """Edit flat"""
    flat_id = request.args.get("id")
    if flat_id:
        flat = db.execute("SELECT * FROM flats WHERE id = ?", flat_id)
        if len(flat) == 1:
            flat = flat[0]
            # Make sure users can only edit their own flat
            if flat["added_by"] == session["user_id"]:
                # Serve form with edit fields
                if request.method == "GET":
                    return render_template("edit.html", flat=flat)
                # TODO: Save changes
                if request.method == "POST":

                    # Make sure that all fields are filled out
                    title = request.form.get("title")
                    link = request.form.get("link")
                    rooms = request.form.get("rooms")
                    price = request.form.get("price")
                    location = request.form.get("location")
                    comments = request.form.get("comments")

                    if not title or not link or not rooms or not price:
                        return apology("Please fill out all required fields before submitting!")

                    # Validate numeric inputs
                    if rooms.isnumeric() and int(rooms) >= 1:
                        rooms = int(rooms)
                    else:
                        return apology("Please only enter numbers in the room field")

                    if price.isnumeric() and int(price) > 0:
                        price = int(price)
                    else:
                        return apology("Please only enter numbers in the price field")

                    db.execute(
                        "UPDATE flats SET title = ?, link = ?, rooms = ?, price = ?, location = ?, comments = ? WHERE id = ?",
                        title,
                        link,
                        rooms,
                        price,
                        location,
                        comments,
                        flat_id
                        )
                    flash("Flat edited successfully")
                    return redirect("/view")
            else:
                return apology("Unauthorised")
        else:
            return apology("Flat not found")
    else:
        return apology("Invalid input")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        email = request.form.get("email")

        # Make sure all fields are filled out
        if not username:
            return apology("Username blank")

        if not password or not confirm:
            return apology("Fill out both password fields")

        if password != confirm:
            return apology("Passwords don't match")

        if not check_password(password):
            flash("Password doesn't meet requirements")
            return redirect("/register")

        # Make sure username is unique
        username_exists = db.execute("SELECT * FROM users WHERE username = ?", username)
        if username_exists:
            return apology("Username already exists")

        # Register user
        db.execute(
            "INSERT INTO users (username, hash, email) VALUES(?, ?, ?)",
            username,
            generate_password_hash(password),
            email,
        )
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/profile")
@login_required
def profile():
    """Show profile"""
    flat_count = db.execute("SELECT COUNT(*) FROM flats WHERE added_by = ?", session["user_id"])
    flat_count = flat_count[0]['COUNT(*)']
    # Query database for friends:
    friend_count = db.execute(
        "SELECT COUNT(*) FROM friends WHERE confirmed = 'True' AND user2_id = ? OR user1_id = ?",
        session["user_id"],
        session["user_id"],
    )
    friend_count = friend_count[0]['COUNT(*)']
    print(friend_count)
    if friend_count == 1:
        friend_count = "1 friend"
    else:
        friend_count = f"{friend_count} friends"
    if flat_count == 1:
        flat_count = "1 flat"
    else:
        flat_count = f"{flat_count} flats"
    return render_template("profile.html", flat_count=flat_count, friend_count=friend_count)

@app.route("/changeusername", methods=["GET", "POST"])
@login_required
def change_username():
    """Change username"""
    if request.method == "GET":
        return render_template("username.html")
    elif request.method == "POST":
        new_username = request.form.get("new_username")

        if not new_username:
            return apology("Please enter a username")

        rows = db.execute("SELECT * FROM users WHERE username = ?", new_username)
        if len(rows) == 0:
            db.execute("UPDATE users SET username = ? WHERE id = ?", new_username, session["user_id"])
            session["username"] = new_username
            flash("Username changed successfully")
        else:
            return apology("Username not available")

        return redirect("/profile")