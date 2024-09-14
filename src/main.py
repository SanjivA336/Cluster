from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models import Users, UserData, Groups, GroupMembers, Purchases, Settlements, Benefactors
from sqlalchemy import or_
from . import db

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/home')
@login_required
def home():
    name = Users.query.filter_by(id=current_user.id).first().name
    return render_template('main/home.html', path=request.path, name=name)

@main.route('/groups')
@login_required
def groups():
    groups = GroupMembers.query.filter_by(user_id=current_user.id).all()
    return render_template('main/groups.html', path=request.path, groups=groups)