import os
import requests
import ast

from flask import Flask, session, request, render_template, redirect, url_for, jsonify, abort
from flask_session import Session
from flask_bcrypt import Bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
bcrypt = Bcrypt(app)
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.secret_key = "donottrytocrackthisotherwiseappwillbedoomed"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("""postgres://vrpczrevrbswwe:005db2ea1d556db71d62f85fc8336d09b7fe02d3a2271810367eaf58233c2274@ec2-3-231-16-122.compute-1.amazonaws.com:5432/dfu0mnudct28i2
""")
db = scoped_session(sessionmaker(bind=engine))


# Index page route
@app.route("/")
def index():
    return render_template("index.html")

#login page route
@app.route("/login")
def login():  
    if 'email' in session:
        return redirect( url_for('loggedin'))
    else:
         return render_template("login.html")
        
#Register page route
@app.route("/register")
def register():
    return render_template("register.html")

#Registeration form submit route
@app.route("/signup", methods=["POST"])
def signup():
    email = request.form.get("regmail")
    password = request.form.get("regpass")
    bpass = bcrypt.generate_password_hash(password).decode('utf-8')
    db.execute("INSERT INTO users(email, password) VALUES(:email, :password)", {"email":email, "password": bpass})
    db.commit()
    return redirect(url_for('login'))

#login form submit route
@app.route("/loggedin", methods=["GET", "POST"])
def loggedin():
    if request.method == "POST": 
            mail = request.form.get("logmail")
            password = request.form.get("logpass")
            data = db.execute("SELECT * FROM users WHERE email=:email", {"email": mail}).fetchone()
            if data is None:
                return render_template("error.html", message="No user found with requested email address")
            else:
                if(bcrypt.check_password_hash(data.password, password)):
                    session['email'] = mail
                    mail = None
                    return render_template("success.html", email=session['email'])
                else:
                    return render_template("error.html", message="Password Incorrect")
    elif 'email' in session:
        return render_template("loginerror.html", message="User already logged in another window, automatically logging out in 5 seconds!!")
    else:
        return render_template("error.html", message="Unexpected error")
        
    #logout route
@app.route("/logout")
def logout():
    if 'email' in session:
        session.pop('email', None)
        return render_template("logout.html")
    else:
        return render_template("loginerror.html", message="User already logged out")

@app.route('/revbook')
def revbooks():
    if 'email' in session:
        return render_template("searchbook.html", email=session['email'])
    else:
        return redirect(url_for('logout'))

@app.route('/success')
def success():
    if 'email' in session:
        return render_template("success.html", email=session['email'])
    else:
        return redirect(url_for('logout'))

#review book route
@app.route('/revbook/<code>')
def revbook(code):
    if 'email' in session:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "7vrOEt7H1rStfNPUIqRlCg", "isbns": code})
        check = db.execute("SELECT review FROM review WHERE isbn = :isbn AND email = :email", {"isbn": code, "email": session['email']}).fetchall()
        dt = db.execute("SELECT email, review, rating FROM review WHERE isbn = :isbn", {"isbn": code}).fetchall()
        dm = db.execute("SELECT * FROM project1 WHERE isbn = :isbn", {"isbn": code}).fetchone()
        if check:
            msg = "You already have reviewed this book!"
            return render_template("error2.html", email=session['email'], message=msg)
        else:
            if res.status_code == 200:
                return render_template("review.html", email=session['email'], isbn=code, data = res.json(), book=dm, reviews=dt, message="No reviews found")
            else: 
                return render_template("error2.html", message="Book not found!")
    else:
        return redirect(url_for('logout'))

@app.route('/bookpg/<code>')
def bookpg(code):
    if 'email' in session:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "7vrOEt7H1rStfNPUIqRlCg", "isbns": code})
        dt = db.execute("SELECT email, review, rating FROM review WHERE isbn = :isbn", {"isbn": code}).fetchall()
        dm = db.execute("SELECT * FROM project1 WHERE isbn = :isbn", {"isbn": code}).fetchone()
        return render_template("infobook.html", email=session['email'], data=res.json(), book=dm, reviews=dt)
    else:
        return redirect(url_for('logout'))

@app.route("/searchbook")
def searchbook():
    if 'email' in session:
        return render_template("searchbook.html", email=session['email'])
    else:
        return redirect(url_for('logout'))

@app.route("/findbook", methods=["GET", "POST"])
def findbook():
    if 'email' in session:
        name1 = request.form.get('book')
        name = name1.title()
        named = "%"+str(name)+"%"
        filter_by = request.form.get('filter')
        if filter_by == 'title':
            data = db.execute("SELECT isbn, title, author, year FROM project1 WHERE title = :bookname OR title LIKE :name", {"bookname": name, "name":named}).fetchall()
        elif filter_by == 'author':
            data = db.execute("SELECT isbn, title, author, year FROM project1 WHERE author = :authname OR author LIKE :name", {"authname": name, "name":named}).fetchall()
        elif filter_by == 'isbn':
            data = db.execute("SELECT isbn, title, author, year FROM project1 WHERE isbn = :isbn OR isbn LIKE :name", {"isbn": name, "name":named}).fetchall()
        elif filter_by == 'none':
            return render_template('error2.html', message="No filter found!", email=session['email'])
        db.commit()
        return render_template("displaybook.html", email=session['email'], filter_by=filter_by ,data=data)
    else:
        return redirect(url_for('logout'))

@app.route("/saverev", methods=["GET", "POST"])
def saverev():
    if 'email' in session:
        mail = request.form.get('email')
        code = request.form.get('bname')
        revuser = request.form.get('user-review')
        rating = request.form.get('rating')
        try:
            db.execute("INSERT INTO review(email, isbn, review, rating) VALUES(:email, :isbn, :review, :rating)", {"email": mail, "isbn": code, "review": revuser, "rating": rating})
            db.commit()
        except: 
            return render_template("error2.html", message="Failed to add response", email=session['email'])    
        else:
            return render_template("success.html", email=session['email'])
    else:
        return redirect(url_for('logout'))

@app.route("/api")
def appi():
    return render_template("data.html")

@app.route("/api/<isbn>")
def api(isbn):
    dt = db.execute("SELECT * FROM project1 WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "7vrOEt7H1rStfNPUIqRlCg", "isbns": isbn})
    if res.status_code != 200:
        abort(404, description="Book not found! Check ISBN code.")
    else:
        obget=res.json()
        v1 = obget['books'][0]['reviews_count']
        v2 = obget['books'][0]['average_rating']
        return jsonify({
            "title" : dt.title,
            "author" : dt.author,
            "year" : dt.year,
            "isbn" : dt.isbn,
            "review_count" : v1,
            "average_score" : v2
        })