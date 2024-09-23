from flask_login import UserMixin
from . import db

class Users(UserMixin, db.Model): # Records of all users
    id = db.Column(db.Integer, primary_key=True) # user_id
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(1000))
    name = db.Column(db.String(100))
    admin = db.Column(db.Boolean, default=False)
    total_debt = db.Column(db.Float, default=0)

    
class UserData(UserMixin, db.Model): # User attributes
    id = db.Column(db.Integer, primary_key=True) # attribute_id
    user_id = db.Column(db.Integer)
    attribute_name = db.Column(db.String(100))
    attribute_value = db.Column(db.String(100))
    
class Groups(UserMixin, db.Model): # Records of all groups
    id = db.Column(db.Integer, primary_key=True) # group_id
    name = db.Column(db.String(100))
    owner_id = db.Column(db.Integer)
    num_participants = db.Column(db.Integer)
    creation_date = db.Column(db.Date)
    currency = db.Column(db.String(10), default="USD")
    last_updated = db.Column(db.Date)
    
class GroupMembers(UserMixin, db.Model): # Records of all members in a group
    id = db.Column(db.Integer, primary_key=True) # member_id
    group_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    debt = db.Column(db.Float)
    
class Purchases(UserMixin, db.Model): # Records of all purchases made in a group
    id = db.Column(db.Integer, primary_key=True) # purchase_id
    group_id = db.Column(db.Integer)
    buyer_id = db.Column(db.Integer)
    item = db.Column(db.String(100))
    cost = db.Column(db.Float)
    num_benefactors = db.Column(db.Integer)
    date = db.Column(db.Date)
    self_purchase = db.Column(db.Boolean, default=False)

    
class Settlements(UserMixin, db.Model): # All transactions where a user pays another user
    id = db.Column(db.Integer, primary_key=True) # settlement_id
    group_id = db.Column(db.Integer)
    sender_id = db.Column(db.Integer)
    reciever_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    date = db.Column(db.Date)

class Benefactors(UserMixin, db.Model): # Anyone who benefits from a purchase, including the buyer
    id = db.Column(db.Integer, primary_key=True) # benefactor_id
    purchase_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    
class JoinCode(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) #code_id
    code = db.Column(db.String(100)) 
    group_id = db.Column(db.Integer)
    creator = db.Column(db.Integer)
