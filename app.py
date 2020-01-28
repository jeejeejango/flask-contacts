from flask import Flask, redirect, url_for, render_template, request, flash, g
from flask_oidc import OpenIDConnect
from models import db, Contact
from forms import ContactForm
import cx_Oracle

# Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my secret'
app.config['DEBUG'] = True

# OIDC with RHSSO
app.config.update({
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'demo',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
})

oidc = OpenIDConnect(app)

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle+cx_oracle://@oracle12c.localdomain/?service_name=pdb1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.before_request
def before_request():
    if not hasattr(g, 'username'):
        # print("before request")
        try:
            info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
            username = info.get('preferred_username')
            #email = info.get('email')
            user_id = info.get('sub')

            if user_id in oidc.credentials_store:
                try:
                    from oauth2client.client import OAuth2Credentials
                    # access_token = OAuth2Credentials.from_json(oidc.credentials_store[user_id]).access_token
                    access_token = oidc.get_access_token()
                    #print('access_token=<%s>' % access_token)
                    #cred = oidc.credentials_store[user_id]
                    #print(cred)
                except:
                    print("Could not access greeting-service")

            # print("your username is %s and your email is %s and your user_id is %s!" % (username, email, user_id))
            g.username = username
        except:
            print("user is not authenticated")


@app.route("/")
def index():
    '''
    Home page
    '''
    return redirect(url_for('contacts'))


@app.route("/new_contact", methods=('GET', 'POST'))
@oidc.require_login
def new_contact():
    '''
    Create new contact
    '''
    form = ContactForm()
    if form.validate_on_submit():
        my_contact = Contact()
        form.populate_obj(my_contact)
        db.session.add(my_contact)
        try:
            db.session.commit()
            # User info
            flash('Contact created correctly', 'success')
            return redirect(url_for('contacts'))
        except:
            db.session.rollback()
            flash('Error generating contact.', 'danger')

    return render_template('web/new_contact.html', form=form, username=g.username)


@app.route("/edit_contact/<id>", methods=('GET', 'POST'))
@oidc.require_login
def edit_contact(id):
    '''
    Edit contact

    :param id: Id from contact
    '''
    my_contact = Contact.query.filter_by(id=id).first()
    form = ContactForm(obj=my_contact)
    if form.validate_on_submit():
        try:
            # Update contact
            form.populate_obj(my_contact)
            db.session.add(my_contact)
            db.session.commit()
            # User info
            flash('Saved successfully', 'success')
        except:
            db.session.rollback()
            flash('Error update contact.', 'danger')
    return render_template(
        'web/edit_contact.html',
        form=form, username=g.username)


@app.route("/contacts")
@oidc.require_login
def contacts():
    '''
    Show alls contacts
    '''
    get_db_username()
    contacts = Contact.query.order_by(Contact.name).all()
    return render_template('web/contacts.html', contacts=contacts, username=g.username)


@app.route("/search")
@oidc.require_login
def search():
    '''
    Search
    '''
    name_search = request.args.get('name')
    all_contacts = Contact.query.filter(
        Contact.name.contains(name_search)
    ).order_by(Contact.name).all()
    return render_template('web/contacts.html', contacts=all_contacts, username=g.username)


@app.route("/contacts/delete", methods=('POST',))
@oidc.require_login
def contacts_delete():
    '''
    Delete contact
    '''
    try:
        mi_contacto = Contact.query.filter_by(id=request.form['id']).first()
        db.session.delete(mi_contacto)
        db.session.commit()
        flash('Delete successfully.', 'danger')
    except:
        db.session.rollback()
        flash('Error delete  contact.', 'danger')

    return redirect(url_for('contacts'))


def get_db_username():
    try:
        dsn = cx_Oracle.makedsn("oracle12c.localdomain", 1521, service_name="pdb1")
        conn = cx_Oracle.connect(dsn=dsn, encoding="UTF8")
        cur = conn.cursor()
        cur.execute("select user from dual")
        rows = cur.fetchall()
        for row in rows:
            print(row)
        cur.close()
    except:
        print("unable to query user")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
