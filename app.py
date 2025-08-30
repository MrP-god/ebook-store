#imports
from flask import Flask, render_template, redirect, request, session
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime



#MY APP

#setup
app = Flask(__name__) #this creates the app
Scss(app=app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACk_MODIFICATION"] = False
db = SQLAlchemy(app=app)


#models Data Class ~ row of data
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

with app.app_context():
    db.create_all()


#================================ROUTES STORE==========================================================



#routes
@app.route("/") #this is a decoretor that transform the index function in a route (url)
def index():
    items = Item.query.order_by(Item.created).all()
    return render_template("index.html", items=items)







#================================ROUTES ADMIN==========================================================


@app.route("/admin", methods=['POST','GET'])
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

#==========================================================================================




# main
if __name__ == "__main__":        

    app.run(debug=True)