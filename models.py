from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Sequence, create_engine

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle://oradmin:password1@oracle12c.localdomain/?service_name=pdb1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app=app, engine_options={'max_identifier_length': 30})


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, Sequence('id_seq'), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    surname = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(200), nullable=True, unique=True)
    phone = db.Column(db.String(25), nullable=True, unique=False)

    def __repr__(self):
        return '<Contacts %r>' % self.name
