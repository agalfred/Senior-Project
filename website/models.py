from .import db 
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):##usermixin makes it easier for user login
    id = db.Column(db.Integer, primary_key=True)##unique key
    email = db.Column(db.String(320), unique=True)##cant have the same email
    telnum = db.Column(db.String(10),unique=True)##cant have the same telephone number
    s_id = db.Column(db.String(9),unique=True)
    fname = db.Column(db.String(26))
    lname = db.Column(db.String(50))
    password = db.Column(db.String(15))
    sf = db.Column(db.String(7))
    ## PP: zip = db.Column(db.String(5))
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    borroweditems= db.relationship('Borroweditem', backref='user',passive_deletes=True)##reference all borroweditems##relationship with db
    creators= db.relationship('Inventory', backref='user',passive_deletes=True)##reference all borroweditems##relationship with db
    access= db.relationship('AccessRequest', backref='user',passive_deletes=True)

class Borroweditem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id= db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    date_borrowed = db.Column(db.DateTime(timezone=True), default=func.now())
    reason = db.Column(db.String(200))
    borrower = db.Column(db.Integer, db.ForeignKey('user.s_id', ondelete="CASCADE"),nullable=False) ##foreign key relationship

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer(), unique=True)
    product_name = db.Column(db.String(26))
    date_added = db.Column(db.DateTime(timezone=True), default=func.now())
    desc=db.Column(db.String(200))
    i_loc=db.Column(db.String(200))
    quantity= db.Column(db.Integer)
    group= db.Column(db.String(26))
    subgroup=db.Column(db.String(26))
    Creator = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"),nullable=False) ##foreign key relationship //id of who added it.

class AccessRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester = db.Column(db.String(320), db.ForeignKey('user.s_id', ondelete="CASCADE"),nullable=False)
    fname = db.Column(db.String(26))
    lname = db.Column(db.String(50))
    date_requested = db.Column(db.DateTime(timezone=True), default=func.now())
