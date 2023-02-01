from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from passlib.hash import sha256_crypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta

app = Flask(__name__)
# needed when we are using sessions
app.config["SECRET_KEY"] = "mysecret"
# port number optional
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:0110@localhost:3306/todo_list"
db = SQLAlchemy(app)
# to use server side sessions and the data is stored in the database used above
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY"] = db
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
    days=7)  # use minutes to set session for minutes
sess = Session(app)
migrate = Migrate(app, db)


class Users(db.Model):  # Create table
    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(300), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self) -> str:  # how to print obj
        return f"{self.username}"


class Todos(db.Model):  # Create table
    id = db.Column(db.Integer, primary_key=True)  # auto increment
    username = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self) -> str:  # how to print obj
        return f"{self.id} - {self.title}"


def isLogin():
    isLogin = True
    if session.get("user") is None:
        isLogin = False
    return isLogin


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", isLogin=isLogin())


@app.route("/register", methods=["GET", "POST"])
def register():
    if isLogin():
        return redirect("/todos")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        encpassword = sha256_crypt.encrypt(password)
        user = Users(username=username, password=encpassword)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("details.html", data="register", err=False)


@app.route("/login", methods=["GET", "POST"])
def login():
    if isLogin():
        return redirect("/todos")

    loginError = False

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Users.query.filter_by(username=username).first()
        if user is not None:
            if sha256_crypt.verify(password, user.password):
                session["user"] = username
                return redirect("/todos")
        loginError = True

    return render_template("details.html", data="login", err=loginError)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("user", None)
    return redirect("/")


@app.route("/todos", methods=["GET", "POST"])
def todos():
    if not isLogin():
        return redirect("/login")

    if request.method == "POST":
        username = session["user"]
        title = request.form["title"]
        desc = request.form["desc"]
        todo = Todos(username=username, title=title, desc=desc)
        db.session.add(todo)
        db.session.commit()

    allTodo = Todos.query.filter_by(username=session["user"]).all()
    # print(allTodo)
    return render_template("todos.html", allTodo=allTodo)


@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    if not isLogin():
        return redirect("/login")

    todo = Todos.query.filter_by(id=id).first()
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        todo.title = title
        todo.desc = desc
        todo.date_added = datetime.now()
        db.session.add(todo)
        db.session.commit()
        return redirect("/todos")

    return render_template("update.html", todo=todo)


@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
    if not isLogin():
        return redirect("/login")

    todo = Todos.query.filter_by(id=id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect("/todos")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
