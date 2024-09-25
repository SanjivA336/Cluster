from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models import Users, UserData, Groups, GroupMembers, Purchases, Settlements, Benefactors, JoinCodes
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

# Group Pages -----

@main.route('/groups')
@login_required
def groups():
    members = GroupMembers.query.filter_by(user_id=current_user.id, is_active=True).all()
    groups = []
    for member in members:
        group = Groups.query.filter_by(id=member.group_id).first()
        groups.append(group)
    
    groups.sort(key=lambda x: x.last_updated, reverse=True)
    
    return render_template('main/groups.html', path=request.path, groups=groups)

@main.route('/create', methods=['POST'])
@login_required
def create_post():
    name = request.form.get('groupName')     
    
    # Check if the user already owns a group by this name
    group = Groups.query.filter_by(name=name, owner_id=current_user.id).first()
    if group:
        flash('You already own a group by this name.', 'error')
        return redirect(url_for('main.groups'))
    
    # Create the group
    group = Groups(name=name, owner_id=current_user.id, creation_date=datetime.date.today(), last_updated=datetime.date.today())
    db.session.add(group)
    db.session.commit()
    
    # Add the user to the group
    new_member = GroupMembers(group_id=group.id, user_id=current_user.id, debt=0)
    group.num_participants = 1
    
    # Generate a join code
    characters = string.ascii_letters + string.digits
    joinCode = generateJoinCode().upper()
    new_joinCode = JoinCodes(group_id=group.id, code=joinCode)
    
    db.session.add(new_member)
    db.session.add(new_joinCode)
    db.session.commit()
    
    flash('Group created successfully. Your join code is ' + joinCode + '.', 'success')
    
    return redirect(url_for('main.groups'))

@main.route('/join', methods=['POST'])
@login_required
def join_post():    
    joinCode = JoinCodes.query.filter_by(code=request.form.get('joinCode').upper()).first()
    
    # Check if the join code is valid
    if joinCode is None:
        flash('That join code is invalid.', 'error')
        return redirect(url_for('main.groups'))
    
    # Check if the user is already a member of the group
    group = Groups.query.filter_by(id=joinCode.group_id).first()
    member = GroupMembers.query.filter_by(group_id=group.id, user_id=current_user.id).first()
    if member:
        flash('You are already a member of this group.', 'error')
        return redirect(url_for('main.groups'))
        
    # Add the user to the group
    new_member = GroupMembers(group_id=group.id, user_id=current_user.id, debt=0)
    db.session.add(new_member)
    group.num_participants += 1
    db.session.commit()
    
    return redirect(url_for('main.groups'))

# Individual Group Pages -----

@main.route('/group/<int:group_id>')
@login_required
def group(group_id):
    group = Groups.query.filter_by(id=group_id).first()
    
    # Check if the group exists
    if group == None:
        flash('This group does not exist.', 'error')
        return redirect(url_for('main.groups'))
    
    # Check if the user is a member of the group
    persona = GroupMembers.query.filter_by(group_id=group_id, user_id=current_user.id, is_active=True).first()
    if persona is None:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('main.groups'))
    
    
    # Get the members of the group
    members = GroupMembers.query.filter_by(group_id=group_id).all()[:11]
    users = []
    for member in members:
        user = Users.query.filter_by(id=member.user_id).first()
        users.append(user)
    
    # Sort the members by name
    userLookup = {user.id: user for user in users}
    members.sort(key=lambda x: userLookup[x.user_id].name, reverse=False)
    
    # Move owner to first position
    for i in range(len(members)):
        if members[i].user_id == group.owner_id:
            members.insert(0, members.pop(i))
            break
    
    # Get the group's purchases (Format as MM/DD)
    purchases = Purchases.query.filter_by(group_id=group_id).all()[:10]
    for purchase in purchases:
        purchase.date = purchase.date.strftime("%m/%d")
    purchases.sort(key=lambda x: x.date, reverse=True)
    
    # Get the group's settlements (Format as MM/DD)
    settlements = Settlements.query.filter_by(group_id=group_id).all()[:10]
    for settlement in settlements:
        settlement.date = settlement.date.strftime("%m/%d")
    settlements.sort(key=lambda x: x.date, reverse=True)
    
    return render_template('main/group.html', path=request.path, current_user=current_user, group=group, members=members, purchases=purchases, settlements=settlements, userLookup=userLookup)

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
    
    costPartition = int(cost)/numBenefactors
        
    new_purchase = Purchases(group_id=group_id, buyer_id=buyer_id, item=item, cost=cost, num_benefactors=numBenefactors, date=datetime.date.today(), self_purchase=self_purchase)
    buyer = GroupMembers.query.filter_by(group_id=group_id, user_id=buyer_id).first()
    if(self_purchase):
        buyer.debt -= costPartition * (numBenefactors - 1)
    else:
        buyer.debt -= float(cost)
        
    db.session.add(new_purchase)
    db.session.commit()
    
    purchase = Purchases.query.filter_by(group_id=group_id, buyer_id=buyer_id, item=item, cost=cost, num_benefactors=numBenefactors, date=datetime.date.today(), self_purchase=self_purchase).first()
    
    for benefactor in benefactors:
        if(benefactor != int(buyer_id)):
            new_benefactor = Benefactors(purchase_id=purchase.id, user_id=benefactor, amount=int(cost)/numBenefactors, group_id=group_id)
            bene_user = GroupMembers.query.filter_by(group_id=group_id, user_id=benefactor).first()
            bene_user.debt += costPartition
            db.session.add(new_benefactor)
            db.session.commit()
    
    return redirect(url_for('main.group', group_id=group_id))
    
@main.route('/group/<int:group_id>/recordSettlement', methods=['POST'])
@login_required
def recordSettlement_post(group_id):
    sender_id = request.form.get('sender')
    reciever_id = request.form.get('reciever')
    amount = request.form.get('amount')
    
    group = Groups.query.filter_by(id=group_id).first()
    
    new_settlement = Settlements(group_id=group_id, sender_id=sender_id, reciever_id=reciever_id, amount=amount, date=datetime.date.today())
    
    sender = GroupMembers.query.filter_by(group_id=group_id, user_id=sender_id).first()
    reciever = GroupMembers.query.filter_by(group_id=group_id, user_id=reciever_id).first()

    sender.debt -= float(amount)
    reciever.debt += float(amount)
    
    db.session.add(new_settlement)
    db.session.commit()
    
    return redirect(url_for('main.group', group_id=group_id))

@main.route('/group/<int:group_id>/edit', methods=['POST'])
@login_required
def groupEdit_post(group_id):
    groupName = request.form.get('groupName')
    
    group = Groups.query.filter_by(id=group_id).first()
    
    similarGroup = Groups.query.filter_by(name=groupName, owner_id=current_user.id).all()
    
    if(len(similarGroup) > 0):
        flash('You already own a group by this name.', 'error')
        return redirect(url_for('main.group', group_id=group_id))
    
    group.name = groupName
    
    db.session.commit()
    
    flash('Group name updated successfully.', 'success')
    
    return redirect(url_for('main.group', group_id=group_id))

@main.route('/group/<int:group_id>/delete', methods=['POST'])
@login_required
def groupDelete_post(group_id):
    groupName = request.form.get('groupName')
    
    group = Groups.query.filter_by(id=group_id).first()
        
    if group.owner_id != current_user.id:
        flash('You are not the owner of this group.', 'error')
        return redirect(url_for('main.group', group_id=group_id))
    elif group.name != groupName:
        flash('Group name does not match.', 'error')
        return redirect(url_for('main.group', group_id=group_id))
    
    members = GroupMembers.query.filter_by(group_id=group_id).all()
    for member in members:
        db.session.delete(member)
    
    purchases = Purchases.query.filter_by(group_id=group_id).all()
    for purchase in purchases:
        db.session.delete(purchase)
        
    settlements = Settlements.query.filter_by(group_id=group_id).all()
    for settlement in settlements:
        db.session.delete(settlement)
        
    joinCodes = JoinCodes.query.filter_by(group_id=group_id).all()
    for joinCode in joinCodes:
        db.session.delete(joinCode)
        
    benefactors = Benefactors.query.filter_by(group_id=group_id).all()
    for benefactor in benefactors:
        db.session.delete(benefactor)
        
    db.session.delete(group)
    db.session.commit()
    
    flash('Group deleted successfully.', 'success')
    
    return redirect(url_for('main.groups'))

@main.route('/group/<int:group_id>/leave')
@login_required
def leave(group_id):
    group = Groups.query.filter_by(id=group_id).first()
    
    member = GroupMembers.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    
    if member is None:
        flash('You are not a member of this group.', 'error')
        return redirect(url_for('main.groups'))
    
    if group.owner_id == current_user.id:
        flash('You cannot leave a group you own. Delete the group instead.', 'error')
        return redirect(url_for('main.group', group_id=group_id))
    
    member.is_active = False
    group.num_participants -= 1
        
    db.session.commit()
    
    return redirect(url_for('main.groups'))



# Helper Functions -----

def generateJoinCode():
    characters = string.ascii_letters + string.digits
    joinCode = ''.join(random.choice(characters) for _ in range(6))
    #Check if the join code is already in use
    while JoinCodes.query.filter_by(code=joinCode).first():
        joinCode = ''.join(random.choice(characters) for _ in range(6))
    return joinCode