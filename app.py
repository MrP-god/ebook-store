#imports
from flask import Flask, render_template, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from sqlalchemy.ext.mutable import MutableList
from flask_migrate import Migrate
from datetime import datetime
import os
from functools import wraps
import stripe



#MY APP

#setup
app = Flask(__name__) #this creates the app
Scss(app=app)
app.secret_key = os.environ.get("SECRET_KEY") or "fallback-dev-key"
stripe.api_key = os.environ.get("STRIPE_KEY") 





app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db" #this link the db
app.config["SQLALCHEMY_TRACk_MODIFICATION"] = False #this is for production
db = SQLAlchemy(app=app)
migrate = Migrate(app=app, db=db)

#==================MODELS========================================================================

#==================Item
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float(precision=2))
    created = db.Column(db.DateTime, default=datetime.now())
    #cover
    #book pdf

    def __repr__(self):
        return f"Task {self.id}"
    
    def __init__(self, title, description, price):
        self.title = title
        self.description = description
        self.price = price

#================= User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    passwordHash  = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    cartItems = db.Column(MutableList.as_mutable(JSON), default=list)

    def __init__(self, username, email, password):
        self.setPassword(password=password)
        self.username = username
        self.email = email
        self.role = "user" # explicit save the role

    def setPassword(self, password):
        self.passwordHash = generate_password_hash(password=password)

    def checkPassword(self, password):
        return check_password_hash(self.passwordHash, password=password)
    
    def addCartItem(self, itemID):
        if self.cartItems is None:
            self.cartItems = []
        if itemID not in self.cartItems:
            self.cartItems.append(itemID)
        # else: do nothing if already in cart
        return self
    
    def removeCartItem(self, itemID):
        if self.cartItems and itemID in self.cartItems:
            self.cartItems.remove(itemID)
        return self




with app.app_context(): # this is for producation if not goes into main (creates the db in the  db)
    db.create_all()


#================================ROUTES STORE==========================================================



#routes
@app.route("/") #this is a decoretor that transform the index function in a route (url)
def index():

    items = Item.query.order_by(Item.created).all()
    return render_template("index.html", items=items)


#login
@app.route("/login", methods=["POST", "GET"])
def login():
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.checkPassword(password):
            session["username"] = username
            session["userType"] = user.role
            return redirect(url_for("index"))
        else: 
            return render_template("login.html", error="username or password incorect")
    else:

        return render_template("login.html", error="")

#register
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        # Check for existing username or email
        userEmail = User.query.filter_by(email=email).first()
        userUsername = User.query.filter_by(username=username).first()

        if userEmail:
            return render_template("register.html", error="Email already registered, please login!")
        if userUsername:
            return render_template("register.html", error="Username already taken!")

        newUser = User(username=username, email=email, password=password)
        try:
            db.session.add(newUser)
            db.session.commit()
            session["username"] = username
            return redirect("/")
        except Exception as e:
            print(f"Registration error: {e}")  # For debugging
            return render_template("register.html", error="Registration failed. Please try again.")
    else:
        return render_template("register.html")
            


#logout
@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username", None)
    return redirect("/")


#ebook-single-page
@app.route("/book-page/<int:id>", methods=["GET"])
def bookPage(id:int):
    item = Item.query.get_or_404(id)
    return render_template("book-page.html", item=item)


#================================ROUTES CHECKOUT==========================================================

@app.route("/checkout/<int:id>", methods=["GET", "POST"])
def checkout(id:int):

    if not "username" in session:
        return redirect(url_for("bookPage", id=id))
    else:   
        item = Item.query.get_or_404(id)
        stripeSession = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": item.title,
                        "description": item.description,
                    },
                    "unit_amount": int(item.price * 100), #in cents
                },
                "quantity": 1,
            }],
            success_url=url_for("index" , _external=True), 
            cancel_url=url_for("bookPage", id=id, _external=True)
        )
        return redirect(stripeSession.url)







#================================ROUTES ADMIN==========================================================


def adminRequired(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # logic 
        if "username" not in session or session.get('userType') != "admin":
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper




@app.route("/admin", methods=['POST','GET'])
@adminRequired
def admin():
    # business logic
    ## add item logic 
    if request.method == "POST": 
        itemTitle = request.form["title"]
        itemDescription = request.form["description"]
        itemPrice = request.form["price"]
        newItem = Item(title=itemTitle, description=itemDescription, price=itemPrice)

        
        try:
            db.session.add(newItem) #add row in session
            db.session.commit()     #add all the row added in db
            #this is like git, where we stage the changes and then commit them to finalize
            return redirect("/admin")
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: {e}"
        #this adds item to DB

    elif request.method == "GET":
        items = Item.query.order_by(Item.created).all()
        return render_template("admin.html", items=items)
    #if the request is get then  from the db querry all the tasks oredred by creation time



@app.route("/delete/<int:id>")
@adminRequired
def delete(id:int):
    deleteItem = Item.query.get_or_404(id)
    #this gets the itme to delete by id
    try:
        db.session.delete(deleteItem) # session makes a connection to the DB
        db.session.commit() # then we enter in the session/connection and commit it
        return redirect("/admin")
    except Exception as e:
        return f"Error: {e}"


@app.route("/update/<int:id>", methods=["GET", "POST"])
@adminRequired
def update(id:int):
    item = Item.query.get_or_404(id)

    if request.method == "POST":
        item.title = request.form["title"]
        item.description = request.form["description"]
        item.price = request.form["price"]
        try:
            db.session.commit()
            return redirect("/admin")
        except Exception as e:
            return f"Error: {e}"
    else:
        return render_template('edit.html', item=item)

#=======================================ROUTES CART===================================================

#cart
@app.route("/cart", methods=["GET"])
def cart():
    if not "username" in session:
        return render_template("login.html")
    else:
        user = User.query.filter_by(username=session["username"]).first()
        booksIDs = user.cartItems #this is an array of numbers
        items = Item.query.filter(Item.id.in_(booksIDs)).all()
        return render_template("cart.html", items=items)
    

@app.route("/add-cart/<int:id>", methods=["POST" ,"GET"])
def addItemCart(id:int):
    if not "username" in session:
        return redirect(url_for("bookPage", id=id))
    else:
        # here i add the id to the model
        userCart = User.query.filter_by(username=session["username"]).first()
        userCart.addCartItem(id)
        db.session.commit()
        return redirect(url_for("index"))
    
@app.route("/remove-cart-item/<int:id>", methods=["POST", "GET"])
def remoteItemCart(id:int):
    user = User.query.filter_by(username=session["username"]).first()
    user.removeCartItem(id)
    db.session.commit()
    return redirect(url_for("cart"))



























# main
if __name__ == "__main__":  
    # with app.app_context(): #this here is for dev
    #     db.create_all()      

    app.run(debug=True)