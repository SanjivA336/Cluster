from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .models import Users
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    return render_template('auth/login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    
    user = Users.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))
    
    login_user(user, remember=remember)
    return redirect(url_for('main.home'))

@auth.route('/signup')
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    return render_template('auth/signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    confirm = request.form.get('confirm')
    
    user = Users.query.filter_by(email=email).first()
    
    if user:
        flash('Email address already exists.')
        return redirect(url_for('auth.signup'))
    elif password != confirm:
        flash('Passwords do not match.')
        return redirect(url_for('auth.signup'))
    
    password = generate_password_hash(password, method='pbkdf2:sha256')
    
    new_user = Users(email=email, name=name, password_hash=password)
    
    db.session.add(new_user)
    db.session.commit()
    
    user = Users.query.filter_by(email=email).first()

    login_user(user, remember=False)
    return redirect(url_for('main.home'))
    
@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))