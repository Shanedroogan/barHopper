from flask import render_template, flash, redirect, url_for, request, jsonify, session
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.forms import CustomizePreferences
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Crawl, Deal, Bar_MasterList
from app.email import send_password_reset_email
from werkzeug.urls import url_parse
from datetime import datetime
from app.utils import create_crawl, get_lat_and_lon, toDate, check_if_saved
import json
import ast
import urllib.parse
from markupsafe import Markup


@app.template_filter('urlencode')
def urlencode_filter(s):
    """ Encodes string for entry into URL, e.g. '&', '=', etc. """
    if type(s) == 'Markup':
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.parse.quote_plus(s)
    return Markup(s)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home')


@app.route('/customize_crawl', methods=['GET', 'POST'])
def customize_crawl():
    #WTForms populates page with built-in form functionality
    form = CustomizePreferences()

    #Endpoint with API key used to interact with Google Maps Javascript API
    maps_endpoint = f"https://maps.googleapis.com/maps/api/js?key={app.config['GEO_KEY']}&callback=initMap"

    #POST request sent on form submission with AJAX
    if request.method == "POST":
        
        #Data sent in JSON format, so we interact with request.get_json() to get variables
        date = request.get_json()['form_data'][5:]
        
        #lat,lng sourced from marker position on interactive map
        lat, lng = request.get_json()['FinalLatLng']['lat'], request.get_json()['FinalLatLng']['lng']

        #create_crawl queries the database to retrieve a list of bar_ids based on a ranking function
        result_list = create_crawl(user_lat=lat, user_long=lng, date=datetime.strptime(date, '%Y-%m-%d'))
        
        #list needs to be stringified to be passed as a URL parameter
        result_list = ','.join(str(r) for r in result_list)

        #redirect handled in AJAX due to client-server relationship
        return jsonify(result_list=result_list, date=date)
        
    return render_template("customize_crawl.html", form=form, title='Customize', maps_endpoint=maps_endpoint)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    """
    We used Flask-Login paired with WTForms to handle login validation 
    """

    #Redirect user if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    #WTForms has custom server-side validation to prevent SQLInjection
    if form.validate_on_submit():
        #queries user table to see if user exists, returns first result or None
        user = User.query.filter_by(username=form.username.data).first()

        #Checks if user doesn't exist or password is wrong
        #Reason for denying login is obfuscated to obstruct hackers
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        #Built in login function from Flask-Login
        login_user(user, remember=form.remember_me.data)

        #If user was redirected to login page, redirect to previous page stored in session upon redirect
        #else, redirect to next page stored in the request
        if 'url' in session:
            return redirect(session['url'])
        else:
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    #Built in Flask-Login functionality for logout process, redirect to home_page
    logout_user()
    return redirect(url_for('index'))


@app.route('/output', methods=['GET', 'POST'])
def output():
    #receives list of bar ids in bar hop
    params = request.args.get('result_list')
    result_list = [int(r) for r in params.split(',')]

    if request.method == "GET":

        date = request.args.get('date')
        date = datetime.strptime(date, "%Y-%m-%d")
    
        #Boolean value indicating whether user has saved this bar hop to profile
        saved = False

        #Only check if saved if user is authenticated, otherwise db check fails because current_user has no id
        #if already saved, the "Save to Profile" form is disabled 
        if current_user.is_authenticated:
            saved = check_if_saved(result_list, date)
    
        #queries only bars in the result_list
        bars = Bar_MasterList.query.filter(Bar_MasterList.bar_id.in_(result_list)).all()

        #string formatting for output page
        ratings = [int(bar.rating) * '★' for bar in bars]
        prices = [int(bar.price) * '$' for bar in bars]

        #maps endpoint used to generate interactive map on output
        maps_endpoint = f"https://maps.googleapis.com/maps/api/js?key={app.config['GEO_KEY']}&callback=initMap"


    #POST method called if user chooses to save bar crawl
    if request.method == "POST":
        
        #Only logged in users can save crawl, so we redirect to login if not authenticated
        if not current_user.is_authenticated:
            # session url is stored so that user can be redirected back after login, 
            # even if they have to register in between
            session['url'] = request.url
            return redirect(url_for('login'))
        #remove session url if there, else return None
        session.pop('url', None)
        #polyline stores the route plotted on map in a unique string of characters,
        #used to generate static maps on user page 
        polyline = request.get_json()['polyline']

        #Gets date of bar crawl from url
        date = datetime.strptime(request.get_json()['date'], "%Y-%m-%d")

        #User can name their Bar Hop for reference later
        #urllib.parse.unquote used to decode URI encoding in form data
        name = urllib.parse.unquote(request.get_json()['form_data'][5:])

        #crawl object generated and added to db with backref to the current user
        crawl = Crawl(name=name, bar_list=str(result_list), author=current_user, polyline_string=polyline, date=date)
        db.session.add(crawl)
        db.session.commit()
    
        return jsonify(crawl.name) #returns crawl name so client knows the request succeeded
        

    return render_template('final_crawl.html', title='Your Bar Hop', bars=bars,
                            ratings=ratings, prices=prices, maps_endpoint=maps_endpoint, saved=saved)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
        Same process as login, but with added step of updating the user table in db
        Server-side validation implemented in forms.py class declaration
    """

    #checks if user is logged in, if they are - redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congrats! It\'s time to get hoppin!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    #Only allow user to reset password if not loggin in
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            #function inherited from email.py
            #sends asynchronous request to email server to send reset instructions
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                            title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Only accessible from reset password email
    Secure token used to authenticate request using jwt library 
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    #verifies token
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form, title="Reset Password")


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    """
        Each user has unique page denoted by username url parameter
    """
    user = User.query.filter_by(username=username).first_or_404()

    #Pagination used to speed up loading if user has saved many bar hops
    page = request.args.get('page', 1, type=int)

    #Order display by most recent timestamp
    crawls = user.crawls.order_by(Crawl.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    
    crawl_list = []

    for crawl in crawls.items:
        crawl_list.append(Bar_MasterList.query.filter(Bar_MasterList.bar_id.in_(ast.literal_eval(crawl.bar_list))).all()) #ast.literal_eval allows us to convert a string representation of a list into a list object
    
    #Pagination controls
    next_url = url_for('user', username=user.username, page=crawls.next_num) \
        if crawls.has_next else None
    prev_url = url_for('user', username=user.username, page=crawls.prev_num) \
        if crawls.has_next else None

    return render_template('user.html', user=user, title='Your Hops', crawls=crawls.items,
                            next_url=next_url, prev_url=prev_url)
