from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models import Users, UserData, Groups, GroupMembers, Purchases, Settlements, Benefactors
from sqlalchemy import or_
from . import db
import string
import random
import datetime

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
    peronas = GroupMembers.query.filter_by(user_id=current_user.id).all()
    groups = []
    for persona in peronas:
        group = Groups.query.filter_by(id=persona.group_id).first()
        groups.append(group)
    
    groups.sort(key=lambda x: x.last_updated, reverse=True)
    
    return render_template('main/groups.html', path=request.path, groups=groups)

@main.route('/create')
@login_required
def create():
    return redirect(url_for('main.groups'))

@main.route('/create', methods=['POST'])
@login_required
def create_post():
    name = request.form.get('groupName')
    #currency = request.form.get('currency')
        
    group = Groups.query.filter_by(name=name, owner_id=current_user.id).first()
    
    if group:
        flash('You already own a group by this name.')
        return redirect(url_for('main.groups'))
        
    new_group = Groups(name=name, owner_id=current_user.id, creation_date=datetime.date.today(), last_updated=datetime.date.today())
    
    db.session.add(new_group)
    db.session.commit()
    
    group = Groups.query.filter_by(name=name, owner_id=current_user.id).first()
    
    new_member = GroupMembers(group_id=group.id, user_id=current_user.id)
    group.num_participants = 1
    
    db.session.add(new_member)
    db.session.commit()
    
    return redirect(url_for('main.groups'))


@main.route('/join')
@login_required
def join():
    return redirect(url_for('main.groups'))

@main.route('/join', methods=['POST'])
@login_required
def join_post():
    joinCode = request.form.get('joinCode')
    
    group = Groups.query.filter_by(id=joinCode).first()
    persona = GroupMembers.query.filter_by(group_id=joinCode, user_id=current_user.id).first()
    
    if group is None:
        flash('That group does not exist.')
        return redirect(url_for('main.groups'))
    if persona:
        flash('You are already a member of this group.')
        return redirect(url_for('main.groups'))
        
    new_member = GroupMembers(group_id=group.id, user_id=current_user.id)
    
    db.session.add(new_member)
    group.num_participants += 1
    db.session.commit()
    
    return redirect(url_for('main.groups'))

@main.route('/group/<int:group_id>')
@login_required
def group(group_id):
    group = Groups.query.filter_by(id=group_id).first()
    memberLinks = GroupMembers.query.filter_by(group_id=group_id).all()[:11]
    members = []
    for memberLink in memberLinks:
        member = Users.query.filter_by(id=memberLink.user_id).first()
        members.append(member)
    
    members.sort(key=lambda x: x.name, reverse=False)
    
    userLookup = {member.id: member.name for member in members}
    
    purchases = Purchases.query.filter_by(group_id=group_id).all()[:10]
    settlements = Settlements.query.filter_by(group_id=group_id).all()[:10]
    
    # Format the date to exclude the year
    for purchase in purchases:
        purchase.date = purchase.date.strftime("%m/%d")  # Format as MM/DD
        
        # Format the date to exclude the year
    for settlement in settlements:
        settlement.date = settlement.date.strftime("%m/%d")  # Format as MM/DD
        
    purchases.sort(key=lambda x: x.date, reverse=True)
    settlements.sort(key=lambda x: x.date, reverse=True)
    
    return render_template('main/group.html', path=request.path, user=current_user, group=group, members=members, purchases=purchases, userLookup=userLookup)

@main.route('/group/<int:group_id>/recordPurchase', methods=['POST'])
@login_required
def recordPurchase_post(group_id):
    buyer_id = request.form.get('buyer')
    item = request.form.get('item')
    cost = request.form.get('cost')
    benefactors = request.form.getlist('benefactors')
    everyone = request.form.get('everyone')
    
    self_purchase = current_user.id in benefactors
    
    group = Groups.query.filter_by(id=group_id).first()

    if(everyone):
        benefactorLinks = GroupMembers.query.filter_by(group_id=group_id).all()
        self_purchase = True
        benefactors = []
        for benefactorLink in benefactorLinks:
            benefactor = Users.query.filter_by(id=benefactorLink.user_id).first()
            benefactors.append(benefactor.id)
    numBenefactors = len(benefactors)
        
    new_purchase = Purchases(group_id=group_id, buyer_id=buyer_id, item=item, cost=cost, num_benefactors=numBenefactors, date=datetime.date.today(), self_purchase=self_purchase)
    
    db.session.add(new_purchase)
    db.session.commit()
    
    purchase = Purchases.query.filter_by(group_id=group_id, buyer_id=buyer_id, item=item, cost=cost, num_benefactors=numBenefactors, date=datetime.date.today(), self_purchase=self_purchase).first()
    
    for benefactor in benefactors:
        if(benefactor != int(buyer_id)):
            new_benefactor = Benefactors(purchase_id=purchase.id, user_id=benefactor, amount=int(cost)/numBenefactors)
            db.session.add(new_benefactor)
            db.session.commit()
    
    return redirect(url_for('main.group', group_id=group_id))
    