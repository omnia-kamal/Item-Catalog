#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect
from flask import url_for, jsonify, flash, make_response
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from Database import Base, Category, CategoryItem
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json
import requests
import httplib2
from functools import wraps
app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
# Database Connection
engine = create_engine('sqlite:///Catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if (stored_access_token is not None and
       gplus_id == stored_gplus_id):
        response = make_response
        (json.dumps('Current user is already connected.'),
         200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['user_id'] = gplus_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;border-radius: 150px;
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return (output)


def login_required(f):
    @wraps(f)
    def login_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not authorized  to view this page")
            return redirect('/login')
    return login_function

# JSON Endpoints
# Categories


@app.route('/Catalog.JSON')
def showCategoriesJSON():
    session = DBSession()
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])

# items inside a category


@app.route('/Catalog/<string:category_name>.json')
def showItemsinCategory(category_name):
    session = DBSession()
    cat = session.query(Category).filter(Category.name == category_name)
    cat_id = cat[0].id
    items = (session.query(CategoryItem).filter
             (CategoryItem.category_id == cat_id))
    return jsonify(items=[i.serialize for i in items])

# Item


@app.route('/Catalog/<string:category_name>/<string:item_name>.json')
def showSpecificItem(category_name, item_name):
    session = DBSession()
    cat = session.query(Category).filter(Category.name == category_name)
    cat_id = cat[0].id
    item = (session.query(CategoryItem).filter
            (CategoryItem.category_id == cat_id,
            CategoryItem.name == item_name))
    return jsonify(item=[i.serialize for i in item])


# App Routes
# Main Page


@app.route('/')
@app.route('/Catalog')
def showCategoriesAndItems():
    session = DBSession()
    categories = session.query(Category).all()
    items = (session.query(CategoryItem).filter
             (CategoryItem.id).order_by(desc(CategoryItem.id)))
    if 'username' not in login_session:
            return (render_template
                    ('Main.html', xcategories=categories, xitems=items))
    else:
            return (render_template
                    ('loggedInCatalog.html',
                     xcategories=categories, xitems=items))

# Show items inside a category


@app.route('/Catalog/<string:category_name>/items')
def showCategoryItems(category_name):
    session = DBSession()
    cat = session.query(Category).filter(Category.name == category_name)
    cat_id = cat[0].id
    cat_name = cat[0].name
    categories = session.query(Category).all()
    items = (session.query(CategoryItem).filter
             (CategoryItem.category_id == cat_id))
    return (render_template('CategoryItems.html',
            xcategories=categories, xitems=items,
            xcat_name=cat_name))


# show a specific item and its description


@app.route('/Catalog/<string:category_name>/<string:item_name>')
def showSelectedItem(category_name, item_name):
    session = DBSession()
    category = session.query(Category).filter(Category.name == category_name)
    itemSelected = (session.query(CategoryItem).filter
                    (CategoryItem.name == item_name).one())
    categoryname = category[0].name
    if ('gplus_id' not in login_session or
       itemSelected.user_id != login_session['gplus_id']):
        return (render_template
                ('item.html', xcategoryname=categoryname,
                 xitemSelected=itemSelected))
    else:
        return (render_template
                ('loggedInItem.html',
                 xcategoryname=categoryname,
                 xitemSelected=itemSelected))

# Create New Item


@app.route('/Catalog/new', methods=['GET', 'POST'])
@login_required
def addNewItem():
    session = DBSession()
    if request.method == 'POST':
        newCatItem = CategoryItem(name=request.form['name'],
                                  description=request.form['description'],
                                  category_id=request.form['category_id'],
                                  user_id=login_session['gplus_id'])
        session.add(newCatItem)
        session.commit()
        flash("new item has been added!")
        return redirect(url_for('showCategoriesAndItems'))
    else:
        return render_template('newItem.html')
# Edit a specific item


@app.route('/Catalog/<string:category_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
@login_required
def editSelectedItem(category_name, item_name):
    session = DBSession()
    editedItem = session.query(CategoryItem).filter_by(name=item_name).one()
    if editedItem.user_id == login_session['gplus_id']:
        if request.method == 'POST':
            if request.form['name'] != "":
                editedItem.name = request.form['name']
            else:
                editedItem.name = editedItem.name
            if request.form['description'] != "":
                editedItem.description = request.form['description']
            else:
                editedItem.description = editedItem.description
        session.add(editedItem)
        session.commit()
        return redirect(url_for
                        ('showSelectedItem',
                         category_name=category_name, item_name=item_name))
    else:
        return (render_template
                ('edititem.html', category_name=category_name,
                 item_name=item_name, item=editedItem))

# Delete Specific Item


@app.route('/Catalog/<string:category_name>/<string:item_name>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteSelectedItem(category_name, item_name):
    session = DBSession()
    itemToDelete = session.query(CategoryItem).filter_by(name=item_name).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect
        (url_for('showCategoryItems', category_name=category_name))
    else:
        return render_template('deleteItem.html',
                               category_name=category_name,
                               item_name=item_name, item=itemToDelete)

if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
