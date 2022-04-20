from flask import Blueprint, render_template, flash, redirect
from flask_login import login_required, current_user
from flask import current_app as app
from flask import request,session,flash,url_for
from .import db
from .models import AccessRequest, Borroweditem,Inventory
import re

views = Blueprint("views",__name__)
##regex
pidpattern = '^[0-9]{5}$'
strpattern ='[A-Za-z]{2,25}||\s[A-Za-z]{2,200}'
quantitypattern = '^[0-9]*$'

@views.route("/")
@views.route("/login")
def home():
    return render_template("login.html") ## PP: got rid of refesh 
                       
@views.route("/user")
@login_required## needs to be logged in to be accessed
def user():
    if session.get("SCHOOL_ID", None) is not None and session.get("FNAME",None) is not None:
        items = Inventory.query.filter().all()
        return render_template("user.html",user = current_user,data = items)
    else:
        flash("You do not have access to this page! Pls, Log in!", category="error")
        return redirect(url_for('views.home'))

@views.route("/user/account_info")
@login_required## needs to be logged in to be accessed
def account_info():
    if session.get("SCHOOL_ID", None) is not None and session.get("FNAME",None) is not None and session.get("LNAME",None) is not None and session.get("DATE",None) is not None and session.get("SF",None) is not None:
        return render_template("account_info.html",user = current_user)
    else:
        flash("You do not have access to this page! Pls, Log in!", category="error")
        return redirect(url_for('views.home'))

@views.route("/user/Check-in")
@login_required
def Check_in():
    if session.get("SCHOOL_ID", None) is not None and session.get("FNAME",None) is not None and session.get("LNAME",None) is not None and session.get("DATE",None) is not None and session.get("SF",None) is not None and session.get("id",None) is not None:
        itemsborrowed = Borroweditem.query.filter_by(borrower=session['SCHOOL_ID']).all()
        return render_template("Check-in.html",user = current_user ,data=itemsborrowed)
    else:
        flash("You do not have access to this page! Pls, Log in!", category="error")
        return redirect(url_for('views.home'))

@views.route("user/Check-in-confirmed/<id>")
@login_required
def Confirmed_Check_in(id):
    if session.get("id",None) is not None:
        item = Borroweditem.query.filter_by(id=id).first()#querys the item from the given html row.id
        
        returnitemtoinv = Inventory.query.filter_by(product_id=item.product_id).first()##from that item, searches for the productid from inventory and adds back the quantity taken out
        returnitemtoinv.quantity = returnitemtoinv.quantity + item.quantity
        db.session.commit()
        ##deletes the item nowfrom the borroweditem database
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('views.user'))
    else:
        flash("Currently not logged in!", category="error")
        return redirect(url_for('views.home'))


@views.route("/user/Checked_out_items")
@login_required
def Checked():
    if session.get("id",None) is not None and session.get("sf", "Staff"):
        itemsborrowed = Borroweditem.query.all()
        return render_template("Checked_out_items.html",user = current_user, data=itemsborrowed)
    else:
        flash("You do not have access to this page! Pls, Log in!", category="error")
        return redirect(url_for('views.home'))

@views.route("/user/access-request")
@login_required
def access():
    if session.get("id",None) is not None and session.get("sf", "Staff"):
        requests = AccessRequest.query.all()
        return render_template("access-request.html",user = current_user, data=requests)
    else:
        flash("You do not have access to this page! Pls, Log in!", category="error")
        return redirect(url_for('views.home'))

@views.route("/user/Inventory/Add",methods=['GET', 'POST'])
@login_required
def add():
    if session.get("id",None) is not None:
        if request.method == 'POST':
            products_id = request.form.get("product_id")
            product_name =request.form.get("product_name")
            desc= request.form.get("desc")
            group = request.form.get("group")
            subgroup = request.form.get("subgroup")
            i_loc= request.form.get("i_loc")
            quantity= request.form.get("quantity")##can only check one item a time
                       
            product_id = Inventory.query.filter_by(product_id=products_id).first()

            if product_id:
                flash("product id already exists",category="error")
                return redirect(request.url)
            else:
                if products_id == '' and product_name == '' and desc == '' and group == '' and subgroup == '' and i_loc =='' and quantity =='':             
                    flash("Cannot be empty",category="error")
                    return redirect(request.url)
                else:
                    ##add input validation here regex
                    if re.search(pidpattern,products_id) and re.search(strpattern,product_name) and re.search(strpattern,group) and re.search(strpattern,desc) and re.search(strpattern,i_loc) and re.search(quantitypattern,quantity) and int(quantity)>0:                    
                        add = Inventory(product_id=products_id, product_name=product_name, quantity=quantity, desc=desc, group=group, subgroup=subgroup, i_loc=i_loc,Creator=current_user.id)
                        db.session.add(add)
                        db.session.commit()
                        flash("Successfully added.",category="success")
                        return redirect(url_for('views.user'))
                    else:
                        flash("Failed to add",category="error")
        return render_template("add.html",user=current_user)       
    else:
        flash("You do not have access to this page!", category="error")
        return redirect(url_for('views.home'))

@views.route("/user/Inventory/Check_out", methods=["GET", "POST"])
@login_required
def Check_out():
    if session.get("id",None) is not None:
        if request.method == 'POST':
            if request.form['submit_button'] == "Submit":
                products_id = request.form.get("product_id")  
                reason = request.form.get("reason")  
                quantity = 1    ##can only check one item a time

                product = Inventory.query.filter_by(product_id=products_id).first()
        
                if products_id == '' or reason == '':             
                    flash("Cannot be empty",category="success")
                    return redirect(request.url)
                else:
                    if re.search(pidpattern, products_id) and product:
                        borrowing = Borroweditem(product_id=products_id, quantity=quantity, reason=reason, borrower=current_user.s_id)
                        db.session.add(borrowing)
                        db.session.commit()

                        product.quantity = product.quantity - quantity
                        db.session.commit()

                        flash("Successfully borrowed.",category="success")
                        return redirect(url_for('views.user'))
                    else:
                        flash("Error Product ID.Pls Check input.",category="error")
                        return redirect(request.url)
            
        return render_template("Check-out.html",user=current_user)
    else:
        flash("You do not have access to this page!", category="error")
        return redirect(url_for('views.home'))

@views.route("/user/Inventory/Check_Out_Check/<id>")
@login_required
def check_out_check(id):
    if session.get("id",None) is not None:
        product = Inventory.query.filter_by(id = id).first()
        return render_template("Check-out.html",user=current_user, data = product) 
    else:
        flash("You do not have access to this page!", category="error")
        return redirect(url_for('views.home'))

@views.route("/user/Inventory/Edit_Check/<id>")
@login_required
def edit_check(id):
    if session.get("id",None) is not None:
        product = Inventory.query.filter_by(id = id).first()
        return render_template("edit.html",user=current_user, data = product) 
    else:
        flash("You do not have access to this page!", category="error")
        return redirect(url_for('views.home'))

@views.route("/user/Inventory/Edit",methods=["GET", "POST"])
@login_required
def edit():
    if session.get("id",None) is not None:
        if request.method == 'POST':
            if request.form['submit_button'] == "Submit":
                products_id = request.form.get("product_id")
                product_name = request.form.get("product_name")
                desc = request.form.get("desc")
                i_loc = request.form.get("i_loc")
                quantity = request.form.get("quantity")
                       
                product = Inventory.query.filter_by(product_id=products_id).first()

                if product and product_name == product.product_name:
                    if products_id == '' and product_name == '' and desc == '' and i_loc =='' and quantity =='':
                        flash("Fields Cannot be empty",category="error")
                        redirect(url_for('views.edit_check', id=product.id))
                    else:
                        if re.search(strpattern,desc) and re.search(strpattern,i_loc) and re.search(quantitypattern,quantity) and int(quantity)>0:
                            product.desc=desc
                            product.i_loc=i_loc
                            product.quantity=quantity
                            db.session.commit()                 
                            flash("Changed des, location, or quantity successfully",category="success")
                            return redirect(url_for('views.user'))
                        else:
                            flash("Error in input",category="error")
                            redirect(url_for('views.edit_check', id=product.id))                    
            elif request.form['submit_button'] == 'Delete Item':
                products_id = request.form.get("product_id")
                product_name =request.form.get("product_name")
                       
                product = Inventory.query.filter_by(product_id=products_id).first()

                if product and product_name == product.product_name:                    
                    db.session.delete(product)
                    db.session.commit()
                    return redirect(url_for('views.user'))
       
                else:
                    flash("Item does not exist",category="error")
                    return redirect(url_for('views.user'))
        return render_template("edit.html",user=current_user)       
    else:
        flash("You do not have access to this page!", category="error")
        return redirect(url_for('views.home'))
    
