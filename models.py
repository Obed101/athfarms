#!/usr/bin/env python
""" Model for handling database requests"""
from datetime import date
import os
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from utils import app, db

login = LoginManager(app)
login.login_view = 'login'


@login.user_loader
def load_user(id):
    return User.query.get(id)


class User(UserMixin, db.Model):
    """A user instance"""
    id = db.Column(db.Integer, db.Identity(cycle=True), primary_key=True)
    firstname = db.Column(db.String(64), nullable=False)
    lastname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(100))
    fullname = db.Column(db.String(100))
    admin = db.Column(db.Boolean())
    mail = db.Column(db.Boolean())
    pic = db.Column(db.String(100))
    password = db.Column(db.String(40))

    def get_id(self):
        return self.id

    def set_fullname(self):
        """Creates a fullname for the user"""
        self.fullname = self.firstname + " " + self.lastname
        return self.fullname

    def set_password(self, password):
        """Generates a password hash"""
        return generate_password_hash(password)

    def check_password(self, password):
        """Checks if password is correct"""
        return check_password_hash(self.password, password)
    
    def reset_password(self):
        """Resets the user's password to `mm`"""
        self.password = self.set_password('mm')

    def remove_pic(self):
        """Removes a user's profile image"""
        if self.pic and os.path.exists(self.pic):
            os.remove(self.pic)
            self.pic = None
        db.session.commit()

    def add_to_receivers(self):
        """Removes or adds user to mail receivers"""
        self.mail = True if not self.mail else False
        db.session.commit()

    def delete(self):
        """Deletes a User"""
        self.remove_pic()
        db.session.delete(self)
        db.session.commit()


class Article(db.Model):
    """Creates a new article"""
    __searchable__ = ['subject', 'date', 'message', 'cover', 'category']
    id = db.Column(db.Integer(), primary_key=True)
    cover = db.Column(db.String(80), default=os.path.join('static', 'img', '5.jpg'))
    subject = db.Column(db.String(80))
    message = db.Column(db.Text())
    category = db.Column(db.String(50))
    unique_name = db.Column(db.String(100))
    user = db.relationship('User', secondary='user_article')
    date = db.Column(db.String(), default=str(date.today().strftime('%B %d, %Y')))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    views = db.Column(db.Integer, default=1)

    def delete(self):
        """Deletes an article"""
        db.session.delete(self)
        db.session.commit()

    def remove_cover(self):
        """Removes an article's cover image"""
        if self.cover and os.path.exists(self.cover):
            os.remove(self.cover)
            self.cover = None
        db.session.commit()


class Subscriber(db.Model):
    """Saves a subscriber"""
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(100), nullable=False)
    tel = db.Column(db.Integer())

    def delete(self):
        """Unsubscribes a user"""
        db.session.delete(self)
        db.session.commit()

class File(db.Model):
    """ Saves images and videos """
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    original_name = db.Column(db.String(110))
    u_name = db.Column(db.String(100))
    message = db.Column(db.Text())
    f_type = db.Column(db.String(15))
    path = db.Column(db.String(110))
    fmt = db.Column(db.String(10))
    date = db.Column(db.String(30), default=str(date.today().strftime('%B %d, %Y')))

    def delete(self):
        """Deletes a file"""
        if os.path.exists(self.path):
            os.remove(self.path)
        db.session.delete(self)
        db.session.commit()


class Notice(db.Model):
    """Notice message instance"""
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(80))
    message = db.Column(db.Text())
    date = db.Column(db.String(), default=str(date.today().strftime('%A, %B %d %Y')))

    def delete(self):
        """Deletes a notice"""
        db.session.delete(self)
        db.session.commit()

class Service(db.Model):
    """Creates a New Service"""
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80))
    description = db.Column(db.Text())

    def delete(self):
        """Deletes a service"""
        db.session.delete(self)
        db.session.commit()


"""Creating a relationship between a user and an article"""
user_article = db.Table('user_article', db.Column('user_id', db.Integer, db.ForeignKey('user.id'), 
                     primary_key=True), db.Column('article_id', db.Integer, db.ForeignKey('article.id'), 
                     primary_key=True)
                     )
db.create_all()
