from flask import (
   Flask,
   render_template,
   request,
   redirect,
   jsonify,
   url_for,
   flask,
   session as login_session
)
import random
import string
from flask import flash, make_response
import json
import requests
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
from ItemCatalog import Category, CategoryItem, Base, User
from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']

engn = create_engine(
    'sqlite:///ItemCatalog.db',
    connect_args={
        'check_same_thread': False})
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engn

Session = sessionmaker(bind=engn)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = Session()


@app.route('/')
@app.route('/catalog/')
@app.route('/catalog/items/')
def home():
    categories = session.query(Category).all()
    items = session.query(CategoryItem).order_by(
        CategoryItem.date_on.desc()).limit(10)
    # Detect login status
    login = None
    if 'email' in login_session:
        login = True
    return render_template(
        'index.html', categories=categories, items=items, login=login)


@app.route('/login')
def login():
    state = ''.join(
        random.choice(
            string.ascii_uppercase +
            string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, client_id=CLIENT_ID)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain token
    token = request.form['idtoken']
    print("token: %s", token)

    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), CLIENT_ID)

        # Or, if multiple clients access the backend server:
        # idinfo = id_token.verify_oauth2_token(token, requests.Request())
        # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
        #     raise ValueError('Could not verify audience.')

        if idinfo['iss'] not in [
            'accounts.google.com',
                'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # If auth request is from a G Suite domain:
        # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
        #     raise ValueError('Wrong hosted domain.')

        # ID token is valid. Get the user's Google Account ID from the decoded
        # token.
        login_session['credentials'] = idinfo['sub']
        login_session['username'] = idinfo['name']
        login_session['picture'] = idinfo['picture']
        login_session['email'] = idinfo['email']
    except ValueError:
        # Invalid token
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # See if the user exists. If it doesn't, make a new one.
    user_id = getUserID(idinfo["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:150px;'
    '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route('/logout')
@app.route('/gdisconnect')
def gdisconnect():
    """App route function to disconnect from Google login."""
    try:
        subId = login_session['credentials']
    except KeyError:
        flash('Failed to get access token')
        return redirect(url_for('home'))
    print("User's name was {}.".format(login_session['username']))
    if subId is None:
        print('subId is None')
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    del login_session['credentials']
    del login_session['picture']
    del login_session['username']
    del login_session['email']
    del login_session['user_id']
    print('Successfully logged out.')
    flash('Successfully logged out.')
    return redirect(url_for('home'))

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


@app.route('/catalog/additem/', methods=['GET', 'POST'])
def addItem():
    '''Add new item to database'''
    if 'username' not in login_session:
        return redirect('/login')
    else:
        if request.method == 'POST':
            newItem = CategoryItem(
                name=request.form['name'],
                detail=request.form['description'],
                user_id=login_session['user_id'],
                cat_id=request.form['category'])
            session.add(newItem)
            session.commit()
            return redirect(url_for('home'))
        else:
            categories = session.query(Category).all()
            return render_template('new_item.html', categories=categories)


@app.route('/catalog/<int:catalog_id>')
@app.route('/catalog/<int:catalog_id>/items')
def showCategory(catalog_id):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=catalog_id).first()
    categoryName = category.name
    categoryItems = session.query(
        CategoryItem).filter_by(cat_id=catalog_id).all()
    categoryItemsCount = session.query(
        CategoryItem).filter_by(cat_id=catalog_id).count()

    return render_template(
        'category.html',
        categories=categories,
        categoryItems=categoryItems,
        categoryName=categoryName,
        categoryItemsCount=categoryItemsCount)


@app.route('/catalog/<int:catalog_id>/items/<int:item_id>')
def showCategoryItem(catalog_id, item_id):
    categoryItem = session.query(CategoryItem).filter_by(id=item_id).first()
    # Detect login status
    login = None
    if 'email' in login_session:
        login = True

    return render_template('item.html', categoryItem=categoryItem, login=login)


@app.route('/catalog/<string:category>/<string:item>/')
def itemView(category, item):
    '''A detailed item view'''
    cat_id = session.query(Category).filter_by(name=category).one().id
    categoryItem = session.query(CategoryItem).filter_by(
        cat_id=cat_id, name=item).one()
    # Detect login status
    login = None
    if 'email' in login_session:
        login = True

    return render_template('item.html', categoryItem=categoryItem, login=login)

# Edit a category item


@app.route(
    '/catalog/<int:catalog_id>/<int:item_id>/edit',
    methods=[
        'GET',
        'POST'])
def editItem(catalog_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(CategoryItem).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=catalog_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.detail = request.form['description']
        if request.form['category']:
            editedItem.cat_id = request.form['category']
        editedItem.user_id = login_session['user_id']
        session.add(editedItem)
        session.commit()
        flash('Category Item Successfully Edited')
        return redirect(url_for('home'))
    else:
        categories = session.query(Category).all()
        return render_template(
            'edit_item.html',
            item=editedItem,
            categories=categories)

# Delete a category item


@app.route(
    '/restaurant/<int:catalog_id>/<int:item_id>/delete',
    methods=[
        'GET',
        'POST'])
def deleteItem(catalog_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=catalog_id).one()
    itemToDelete = session.query(CategoryItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Category Item Successfully Deleted')
        return redirect(url_for('home'))
    else:
        return render_template(
            'delete.html',
            category=category,
            item=itemToDelete)


# JSON APIs to view ItemCatalog Information
@app.route('/JSON')
@app.route('/catalog/JSON')
@app.route('/catalog/items/JSON')
def categoryJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[r.serialize for r in categories])


@app.route('/catalog/<int:catalog_id>/JSON')
@app.route('/catalog/<int:catalog_id>/items/JSON')
def categoryItemJSON(catalog_id):
    items = session.query(CategoryItem).filter_by(cat_id=catalog_id).all()
    return jsonify(CategoryItems=[i.serialize for i in items])


@app.route('/catalog/<int:catalog_id>/items/<int:item_id>/JSON')
def itemJSON(catalog_id, item_id):
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


@app.route('/catalog/<string:category>/<string:item>/JSON')
def itemDataJSON(category, item):
    cat_id = session.query(Category).filter_by(name=category).one().id
    categoryItem = session.query(CategoryItem).filter_by(
        cat_id=cat_id, name=item).one()
    return jsonify(Item=categoryItem.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
