# views are the handlers that responds to requests from the web browsers
from flask import render_template,url_for,redirect,flash, request
from werkzeug.utils import secure_filename

from app import app, login_manager
from app.form import LoginForm, publications, AdminForm
from publications_query import *
from calendar import monthrange
from app.authentication import auth
from flask_login import login_user, logout_user, login_required
from app.models import User
from threading import Thread

'''This is used to reload the user object from the user id stored'''
@login_manager.user_loader
def load_user(id):
    return User()


'''
   Login and validate the user on a client side form

   When the user clicks on a submit button data is validated
   ldap authentication used to verify user details from the server
   
  Returns: 
        
        If the user details are correct when verified by server using elap:
            directed to the next page called index page
        else
             user stays in the same page
'''
@app.route('/', methods=['GET', 'POST'])
def login():
    form=LoginForm()

    if form.validate_on_submit():
        user=(auth(form.username.data,form.password.data))
        if user==True:
                login_user(User(), remember=form.remember.data)
                return redirect('/index')
        else:
             flash('invalid username or password')
    return render_template('login.html', form=form)
'''
    only logged and authenticated users get access to this page
    to sends email of the publication to the librarians

    The is a time frame for publications to be sent which is the start date and the end date

    start_date is the minimum date that publications must start on
    end_date is the maximum date that publications must end on.
    
    Every publication is set to start from the first of the month and year entered on the start_date
    and end on the month and year of the month entered on the end_date.
    
    only the start_date must be provided always.
    If the end_date is not provided then taken from the month in the start_date provided then the end_date will
    be the last date of that same month provided in start_date

'''


@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = publications()

    if form.validate_on_submit():
        form.start_date.data = form.start_date.data.replace(day=1)
        if not form.end_date.data:
            print("End Date not provided")
            day = monthrange(form.start_date.data.year, form.start_date.data.month)
            print(day, form.start_date.data)
            form.end_date.data = form.start_date.data.replace(day=day[1])
            print(' base on the start date provide then the new end day is',form.end_date.data)
        else:
            print("End Date provided")
            day = monthrange(form.end_date.data.year, form.end_date.data.month)
            form.end_date.data = form.end_date.data.replace(day=day[1])
            print('this is the date when is provided', form.end_date.data)
        if form.start_date.data > form.end_date.data:
                flash('please enter the correct dates')
        elif form.start_date.data==form.end_date.data:
                form.start_date.data = form.start_date.data.replace(day=1)
                day = monthrange(form.end_date.data.year, form.end_date.data.month)
                form.end_date.data = form.end_date.data.replace(day=day[1])
        else:
            t = Thread(target=run_pub, args=(form.start_date.data, form.end_date.data))
            t.start()
            flash('Email will be sent, please check your emails')
    return render_template('index.html', form=form)

@app.route('/admin', methods=['GET'])
@login_required
def admin():
    form = AdminForm()
    return render_template('admin.html', form=form)
@app.route('/upload', methods=[ 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        key=request.files.get('keys')
        author=request.files.get('authors')
        if key is None and author is None :
            flash('No selected file')
            return redirect(url_for('admin'))
        else:
            if key is not None:
                key.save(os.path.join(app.config['UPLOAD_FOLDER'], "keys.txt"))
            if author is not None:
                author.save(os.path.join(app.config['UPLOAD_FOLDER'], "authors.txt"))
            return redirect(url_for('index'))
    return redirect(url_for('login'))
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('you logged out')
    return redirect(url_for('login'))






