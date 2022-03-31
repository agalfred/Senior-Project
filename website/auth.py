##have all the routes related to authentication
from flask import Blueprint, render_template, redirect, url_for,flash, request,session
from flask import current_app as app
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message, Mail
from .import db 
from .import sess
from .models import User,Inventory
from flask_login import login_user,logout_user,login_required,current_user
from werkzeug.security import generate_password_hash, check_password_hash ##used to hash password. Instead of storing passwords in plain text
import re
import redis

from itsdangerous.exc import BadTimeSignature, SignatureExpired
auth = Blueprint("auth",__name__)
serializer = URLSafeTimedSerializer('VdJeu8dSmW-55Zwk')

##regex patterns for input validation
emailpattern='^[a-z 0-9]+[\._]?[a-z 0-9]+[@]\w+[.]\w{2,3}$'
namepattern ='[A-Za-z]{2,25}||\s[A-Za-z]{2,25}'##for first and last name can have a space in between 
zippattern = '^[0-9]{5}$'
phonepattern ='^(\+\d{1,2}\s?)?1?\-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$'
schoolidpattern='^[0]{3}[0-9]{6}$'
bdaypattern='^[0-9]{4}[-][0-9]{2}[-][0-9]{2}$'

@auth.route("/login", methods=['GET', 'POST'])##login page
def login():
    ##email pattern
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if email=='' or password=='':
            flash("Email or password field can't be empty", category="error")
            return redirect(request.url)
        else:
            if re.search(emailpattern, email):##if user typed in the correct email
                if user:##checks if user exists in db
                    if check_password_hash(user.password, password):##hashes the user input password and compares it to the hashed password stored in 'user'
                        login_user(user, remember=True)#remembers wheter session is expired
                        ##--here grabs apps configs
                        app.config.get("SECRET_KEY")
                        app.config.get("SESSION_TYPE")
                        app.config.get("SESSION_PERMANENT")
                        app.config.get("SESSION_USE_SIGNER")
                        app.config.get("SESSION_REDIS")

                        session['SCHOOL_ID'] = user.s_id
                        session['FNAME']=user.fname
                        session['LNAME']=user.lname
                        session['DATE']=user.date_created
                        session['SF']=user.sf
                        session['id']=user.id

                        if user.sf == "Staff":
                            session['ISstaff']="access" ##creates a session if user is staff-->using it in html for add edit and delete
                            app.config.get('mailconfig.cfg')
                                    
                        return redirect(url_for('views.user'))                        
                    else:
                        flash("Incorrect Password!", category="warning")
                        return redirect(request.url)
                else:
                    flash("There is no account with that email address.",category="error")
                    return redirect(request.url)
            else:
                flash("Invalid email", category="error")
                return redirect(request.url)

    return render_template("login.html",user = current_user)

@auth.route("/register", methods=['GET', 'POST'] )##register page-->email validation to registration form link
def register():    
     ##pattern to validate email input   
    app.config.get('mailconfig.cfg')
    mail = Mail(app)

    if request.method == 'POST':
        email = request.form.get("email")
        email_exists = User.query.filter_by(email=email).first()##checks if email is already in use. 
        token = serializer.dumps(email, salt='email-confirm')
        msg = Message('Register Now For The SMU Nursing Inventory',sender = 'buakthaimuay@gmail.com',recipients=[email])       
        link = url_for('auth.confirmed_registration', token=token, _external=True)        
        msg.body = "The link to register is {}".format(link)
        
        if email == '':
            flash("Email field cannot be empty", category="warning")
            return redirect(request.url)
        else:
            if re.search(emailpattern, email):
                if email_exists:
                    flash("Email is already in use.", category="error")
                    return redirect(request.url)
                else:
                    flash("Check your inbox for the registration link using the email address you provided.","success")               
                    mail.send(msg)
                    return redirect(request.url)
            else:
                flash("Invalid Email, please try again.",category="error")
                return redirect(request.url)
    
    return render_template("register.html",user=current_user)

@auth.route('/confirmed_registration/<token>',methods=['GET','POST'])##gets input from confirmed_registration.html
def confirmed_registration(token):
    try:        
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash("Token has expired. Please try again.",category="error")
        return redirect(url_for("views.home"))
    except BadTimeSignature:
        flash("Token is invalid. Please try again.",category="error")
        return redirect(url_for("views.home"))
    
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        s_id = request.form.get("s_id")
        zip = request.form.get("zip")
        telnum = request.form.get("telnum")##telephone number
        bday = request.form.get("bday")
        sf= request.form.get("sf")##student or staff
        password = request.form.get("password1")
        confirmedpassword = request.form.get("password2")

        
        email_exists = User.query.filter_by(email=email).first()##checks if email email_exists in the db
        schoolid_exists = User.query.filter_by(s_id=s_id).first()##checks if schoolid already exists in the db
        telnum_exists = User.query.filter_by(telnum=telnum).first()##checks if an account with that telephone number exists in the db

        ##regexpatterns        
        if email_exists or schoolid_exists or telnum_exists: ##checks if any of these are true. if so account already exist and cant register an account.
            flash("Account already exists. Pls login with your existing account", category="error")
            return redirect(url_for("views.home"))
        else:
            ##maybe add firstname and lastname length validation
            if email == '' or fname == '' or lname == ''or s_id=='' or zip == '' or telnum =='' or bday =='' or sf == '' or confirmedpassword == '' or password == '':
                flash("All input fields must be filled up",category="warning")
                return redirect(request.url)
            else:
                if re.search(emailpattern, email) and re.search(namepattern, lname) and re.search(namepattern,fname) and re.search(phonepattern,telnum) and re.search(zippattern,zip) and re.search(schoolidpattern, s_id) and re.search(bdaypattern,bday) and sf == 'Staff' or sf =='Student':
                    if password == confirmedpassword and len(password)>=6:
                        new_user = User(email=email, telnum=telnum,s_id=s_id, fname=fname, lname=lname, password=generate_password_hash(password, method='sha256'), sf=sf, zip=zip, bday=bday) ##stores user input using the model created
                        db.session.add(new_user)
                        db.session.commit()
                        login_user(new_user, remember=True)                   
                        flash("Account created successfully", category="success")
                        return redirect(url_for("views.home"))
                    else:
                        flash("passwords don't match up or password needs to be atleast 6 characters long . Pls try again!","error")
                else: 
                    flash("Error in inputs. Please try again!", category="warning")
                    return redirect(request.url)
           
    return render_template('confirmed_registration.html')
    
@auth.route("/forgot_password",methods=['GET', 'POST'])##asks for users email, checks if exists and sends link to change password
def forgot_password():
    
    app.config.get('mailconfig.cfg') ##takes app's current config and takes the mail config from there and import in this function
    mail = Mail(app)

    if request.method == 'POST':
        email = request.form.get("email")
        token = serializer.dumps(email, salt='email-confirm')
        msg = Message('Change your password for the SMU nursing inventory website',sender = 'buakthaimuay@gmail.com',recipients=[email])       
        link = url_for('auth.confirmedforgot_password', token=token, _external=True)        
        msg.body = "The link to change your password is {}".format(link)
        
        user = User.query.filter_by(email=email).first()
        
        if email=='':
            flash("Email field cannot be empty.", category="error")
            return redirect(request.url)
        else:
            if re.search(emailpattern, email):##if user typed in the correct email
                if user:##checks if user exists in db
                    flash("Check your email for the forgot password link",category="success")
                    mail.send(msg)
                    return redirect(request.url)
                else:
                    flash("There is no account with that email address.",category="error")
                    return redirect(request.url)
            else:
                flash("Invalid email", category="error")
                return redirect(request.url)

    return render_template("forgot_password.html")

@auth.route('/confirmedforgot_password/<token>',methods=['GET','POST'])##gets token and updates password
def confirmedforgot_password(token):
    try:        
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash("Token has expired. Please try again.",category="error")
        return redirect(url_for("views.home"))
    except BadTimeSignature:
        flash("Token is invalid. Please try again.",category="error")
        return redirect(url_for("views.home"))
    
    if request.method == 'POST':
        email = request.form.get("email")
        s_id = request.form.get("s_id")
        zip = request.form.get("zip")
        telnum = request.form.get("telnum")
        bday = request.form.get("bday")
        password = request.form.get("password1")
        confirmpassword = request.form.get("password2")

        user = User.query.filter_by(email=email).first()
        
        if email == '' or s_id == '' or zip == '' or telnum == '' or password == '' or confirmpassword == '' or  bday == '':
            flash("All fields are required", category="warning")
            return redirect(request.url)
        else:
            if re.search(emailpattern, email) and re.search(phonepattern,telnum) and re.search(zippattern,zip) and re.search(schoolidpattern, s_id) and re.search(bdaypattern,bday):
                if user.email == email and user.zip ==zip and user.telnum == telnum and user.bday == bday:
                    if password==confirmpassword and len(password)>=6:
                        flash("Password successfully changed", category="success")
                        user.password = generate_password_hash(password, method='sha256')
                        db.session.commit()
                        return redirect(url_for('views.home'))
                    else:
                        flash("Password does not match and password needs to be atleast 6 characters", category="error")
                        return redirect(request.url)
                else:
                    flash("Information provided does not match the user's information.", category="error")
                    return redirect(request.url)
            else:
                flash("Incorrect input format", category="warning")
                return redirect(request.url)
 
    return render_template("confirmedforgot_password.html")

@auth.route("/logout")##logouts user deletes sessions and logout func deletes the remember me saved cookies 
@login_required
def logout():
    session.pop("SCHOOL_ID",None)##deletes sessions
    session.pop("FNAME",None)
    session.pop("LNAME",None)
    session.pop("DATE",None)
    session.pop("SF",None)
    session.pop("ISstaff",None)
    session.pop("id",None)
    logout_user()
    flash("Successfully logged out",category="success")
    return redirect(url_for('views.home'))
