from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, DeleteForm, FeedbackForm
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///hashing_login"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"

app.app_context().push()
connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

@app.route("/")
def homepage():
    """homepage for user models sign in"""

    return render_template("base.html")


@app.route("/register", methods=["GET", "POST"])
def register_new_user():
    """register the new user"""

    form = RegisterForm()

    if form.validate_on_submit():
        name = form.username.data
        password = form.password.data
        email= form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(name, password, email, first_name, last_name)

        db.session.add(new_user)
        db.session.commit()

        # Like saying "Let session-username= new_user.username"
        session["username"] = new_user.username
        return redirect (f"/users/{new_user.username}")

    else:
        form.username.errors= ['Username taken. Please pick a different user name']
        return render_template('register.html', form=form)
        
@app.route("/login", methods=["GET", "POST"])
def login_user():
    """Login form to handle login."""

    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = LoginForm()

    if form.validate_on_submit():
        name = form.username.data
        password = form.password.data

        user = User.authenticate(name, password)

        if user:
            session["username"] = user.username
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ["Bad name/password"]
    
    return render_template("login.html", form=form)

@app.route("/users/<username>")
def show_user(username):
    """"Page only secret logged in users can see"""
 
    if "username" not in session or username != session['username']:
        raise Unauthorized()
    
    user = User.query.get(username)
    form = DeleteForm()
    
    return render_template("secret.html", user=user, form=form)

@app.route("/logout")
def logout_page():
    session.pop("username")

    return redirect("/")

@app.route("/users/<username>/delete", methods=["POST"])
def delete_current_user(username):
    if "username" not in session or username != session['username']:
        raise Unauthorized()
    
    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")

    return redirect("/login")

@app.route("/users/<username>/feedback/add", methods=["GET", "POST"])
def add_feedback(username):
    """User can add a feedback post"""
    if "username" not in session or username != session['username']:
        raise Unauthorized()
    
    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(title=title, content=content, feedback_username=username)

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{username}")
    else:
        return render_template("feedback_add.html", form=form)








@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Shows update for feedback entry"""
    
    feedback= Feedback.query.get(feedback_id)

    if "username" not in session or feedback.feedback_username != session['username']:
        raise Unauthorized()
    
    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.feedback_username}")
    return render_template("feedback_edit.html", form=form, feedback=feedback)

@app.route("/feedback/<feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Deletes teh feedback post"""

    feedback =Feedback.query.get(feedback_id)
    
    if "username" not in session or feedback.feedback_username != session['username']:
        raise Unauthorized()
    
    form = DeleteForm()

    if form.validate_on_submit():

        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.feedback_username}")