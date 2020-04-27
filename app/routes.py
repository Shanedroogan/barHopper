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


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home')


@app.route('/customize_crawl', methods=['GET', 'POST'])
def customize_crawl():
    form = CustomizePreferences()

    if form.validate_on_submit():
        #create_crawl() fetches ordered list of bar ids
        lat, lon = get_lat_and_lon(form.address.data)
        result_list = create_crawl(user_lat = lat, user_long=lon, date=form.date.data)
        
        #join converts to comma separated values to pass as parameters
        result_list = ','.join(str(r) for r in result_list)
        return redirect(url_for('output', result_list=result_list, date=form.date.data.strftime("%m-%d-%Y")))
        
    return render_template("customize_crawl.html", form=form, title='Customize')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        if 'url' in session:
            return redirect(session['url']) #Can we make this a post request so user doesn't have to click Save again?
        else:
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/output', methods=['GET', 'POST'])
def output():
    #receives list of bar ids from the customize page
    params = request.args.get('result_list')
    date = request.args.get('date', type=toDate)
    result_list = [int(r) for r in params.split(',')]
    
    #Boolean value indicating whether user has saved this bar hop to profile
    saved = False

    if current_user.is_authenticated:
        saved = check_if_saved(result_list, date)
    
    
    #For Testing :
    # bar schema: bar.(name) (address) (neighborhood) (price) 
    # bar.(rating) (num_ratings) (latitude) (longitude)
    bars = Bar_MasterList.query.filter(Bar_MasterList.bar_id.in_(result_list)).all()
    ratings = [int(bar.rating) * '★' for bar in bars]
    prices = [int(bar.price) * '$' for bar in bars]
    maps_endpoint = f"https://maps.googleapis.com/maps/api/js?key={app.config['GEO_KEY']}&callback=initMap"
    
    if request.method == "POST":
        if not current_user.is_authenticated:
            session['url'] = request.url
            return redirect(url_for('login'))
        session.pop('url', None)
        crawl = Crawl(name='My Crawl', bar_1 = result_list[0], bar_2 = result_list[1], bar_3 = result_list[2],
                    bar_4=result_list[3], bar_5 = result_list[4], timestamp=date, author=current_user)
        db.session.add(crawl)
        db.session.commit()
        flash('Hop saved to profile!')

    return render_template('final_crawl.html', title='Your Bar Hop', bars=bars,
                            ratings=ratings, prices=prices, maps_endpoint=maps_endpoint, saved=saved)


@app.route('/register', methods=['GET', 'POST'])
def register():

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
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                            title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    crawls = user.crawls.order_by(Crawl.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=crawls.next_num) \
        if crawls.has_next else None
    prev_url = url_for('user', username=user.username, page=crawls.prev_num) \
        if crawls.has_next else None

    return render_template('user.html', user=user, title='Your Hops', crawls=crawls.items,
                            next_url=next_url, prev_url=prev_url)
