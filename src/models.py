from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):  # Records of all users
    id = db.Column(db.Integer, primary_key=True)  # user_id
    email = db.Column(db.String(100), unique=True, index=True)  # Indexed for fast lookup
    password_hash = db.Column(db.String(1000))
    name = db.Column(db.String(100))
    admin = db.Column(db.Boolean, default=False)
    total_debt = db.Column(db.Float, default=0)

    groups_owned = db.relationship('Groups', backref='owner', lazy=True, cascade="all, delete-orphan")
    group_members = db.relationship('GroupMembers', backref='user', lazy=True)

class Group(db.Model):  # Records of all groups
    id = db.Column(db.Integer, primary_key=True)  # group_id
    name = db.Column(db.String(100), index=True)  # Indexed for fast lookup
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # owner's user_id
    num_participants = db.Column(db.Integer, default=0)
    creation_date = db.Column(db.Date)
    currency = db.Column(db.String(10), default="USD")
    last_updated = db.Column(db.Date)
    joinCode = db.Column(db.String(100))

    members = db.relationship('GroupMembers', backref='group', lazy=True, cascade="all, delete-orphan")
    purchases = db.relationship('Purchases', backref='group', lazy=True, cascade="all, delete-orphan")
    settlements = db.relationship('Settlements', backref='group', lazy=True, cascade="all, delete-orphan")

class GroupMember(db.Model):  # Records of all members in a group
    id = db.Column(db.Integer, primary_key=True)  # member_id
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)  # group_id
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # member's user_id
    debt = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=True)

    purchases = db.relationship('Purchases', backref='member', lazy=True, cascade="all, delete-orphan")
    settlements = db.relationship('Settlements', backref='member', lazy=True, cascade="all, delete-orphan")
    benefactors = db.relationship('Benefactors', backref='member', lazy=True, cascade="all, delete-orphan")

class Purchase(db.Model):  # Records of all purchases made in a group
    id = db.Column(db.Integer, primary_key=True)  # purchase_id
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)  # group_id
    buyer_id = db.Column(db.Integer, db.ForeignKey('group_members.id'), nullable=False)  # buyer's member_id
    item = db.Column(db.String(100))
    cost = db.Column(db.Float)
    num_benefactors = db.Column(db.Integer, default=0)
    date = db.Column(db.Date)
    self_purchase = db.Column(db.Boolean, default=False)

    benefactors = db.relationship('Benefactors', backref='purchase', lazy=True, cascade="all, delete-orphan")

class Settlement(db.Model):  # All transactions where a user pays another user
    id = db.Column(db.Integer, primary_key=True)  # settlement_id
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)  # group_id
    sender_id = db.Column(db.Integer, db.ForeignKey('group_members.id'), nullable=False)  # sender's member_id
    receiver_id = db.Column(db.Integer, db.ForeignKey('group_members.id'), nullable=False)  # receiver's member_id
    amount = db.Column(db.Float)
    date = db.Column(db.Date)

class Benefactor(db.Model):  # Anyone who benefits from a purchase, including the buyer
    id = db.Column(db.Integer, primary_key=True)  # benefactor_id
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)  # purchase_id
    member_id = db.Column(db.Integer, db.ForeignKey('group_members.id'), nullable=False)  # benefactor's member_id
    amount = db.Column(db.Float)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
