from flask_sqlalchemy import SQLAlchemy
from app import db, User

def convertUserToAdmin(username):
    user = User.query.filter_by(username=username).first()
    if user:
        user.role = "admin"
        db.session.commit()
        return True
    return False

