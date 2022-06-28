#from crypt import methods
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

#User login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login to view this page","danger")
            return redirect(url_for("login"))

    return decorated_function

#users register form
class RegisterForm(Form):
    name  = StringField("Name Surname", validators=[validators.length(min = 4, max = 30)])
    username  = StringField("User Name", validators=[validators.length(min = 5, max = 35)])
    email  = StringField("Email Adress", validators=[validators.Email(message="Please enter a valid email address")])
    password = PasswordField("Password:", validators=[
        validators.DataRequired(message="please enter password"),
        validators.EqualTo(fieldname="confirm", message="Wrong password")
    ])

    confirm = PasswordField("Confirm your password")

class LoginForm(Form):
    username = StringField("Username")
    password = PasswordField("Password")

app = Flask(__name__)
app.secret_key = "blog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blogpage"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/")
def index():

    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

#article page
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sql = "SELECT * FROM articles"

    result = cursor.execute(sql)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")


@app.route("/dashboard")
@login_required
def dashboard():

    cursor = mysql.connection.cursor()

    sql = "SELECT * FROM articles WHERE author = %s"

    result = cursor.execute(sql,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)

    else:

        return render_template("dashboard.html")

#register

@app.route("/register", methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sqlsearch = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sqlsearch,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("You have successfully registered","success")

        return redirect(url_for("login"))
    else:

        return render_template("register.html", form = form)

#login
@app.route("/login", methods = ["GET","POST"])
def login():

    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        login_sql = "SELECT * FROM users WHERE username = %s"

        result = cursor.execute(login_sql, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Login Successfully","success")

                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))

            else:
                flash("Wrong password","danger")

                return redirect(url_for("login"))
        else:
            flash("Wrong username or password","danger")

            return redirect(url_for("login"))

    return render_template("login.html", form = form)

#Detail page

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sql = "SELECT * FROM articles WHERE id = %s"

    result = cursor.execute(sql,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article = article)
    else:
        return render_template("article.html")

#logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


#@app.route("/article/<string:id>")

#def detail(id):
#    return "Article Id:" + id

#add article
@app.route("/addarticle", methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sql = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sql,(title,session["username"],content))

        mysql.connection.commit()
        cursor.close()

        flash("Article successfully added","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form = form)

#profile
@app.route("/profile", methods = ["GET","POST"])
@login_required
def profile():
 
    return render_template("profile.html")


#delete article
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sql = "SELECT * FROM articles WHERE author = %s and id = %s"

    result = cursor.execute(sql,(session["username"],id))

    if result > 0:
        sql2 = "DELETE FROM articles WHERE id = %s"

        cursor.execute(sql2, (id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("There is no such article or you have not permission","danger")
        return redirect(url_for("index"))

#update article
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sql = "SELECT * FROM articles WHERE id = %s AND author = %s"

        result = cursor.execute(sql,(id,session["username"]))

        if result == 0:
            flash("There is no such article or you dont have permission","danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)
    else:
        #POST REQUEST
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data
        
        sql2 = "UPDATE articles SET title = %s, content = %s WHERE id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sql2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Article updated successfully","success")

        return redirect(url_for("dashboard"))

#create article
class ArticleForm(Form):
    title = StringField("Article Title", validators=[validators.length(min = 5, max = 100)])
    content = TextAreaField("Article Content", validators=[validators.length(min = 10)])

#search url
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))

    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sql = "SELECT * FROM articles WHERE title like '%" + keyword + "%' "

        result = cursor.execute(sql)

        if result == 0:
            flash("No article found matching the search term","warning")
            return redirect(url_for("articles"))

        else:
            articles = cursor.fetchall()

            return render_template("articles.html", articles = articles)

if __name__ == "__main__":

    app.run(debug=True, port = "7000")