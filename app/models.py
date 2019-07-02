from datetime import datetime
from hashlib import md5
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import app, db, login
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql import text, func, desc

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    displayname = db.Column(db.String(64), index=True, unique=False)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    confirm_my_stuff = db.Column(db.String(288), index=True, unique=False)
    confirm_my_stuff_reverse = db.Column(db.String(128), index=True, unique=False)
    username_confirmed_at = db.Column(db.DateTime(), default=datetime.utcnow)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')
    role = db.Column(db.Integer, db.ForeignKey('role.id'))
    promotedtweets = db.relationship('PromotedTweet', backref='author', lazy='dynamic')
    withdraws = db.relationship('Withdraw', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username[2:])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_confirm_my_stuff_reverse(self, password):
        self.confirm_my_stuff_reverse = generate_password_hash(password)

    def check_confirm_my_stuff_reverse(self, password):
        return check_password_hash(self.confirm_my_stuff_reverse, password)

class UserLinks(UserMixin, db.Model):
    __tablename__ = 'user_links'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    link_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Link {}>'.format(self.id)

# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


class Usertwitter(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=False, unique=False)
    screen_name = db.Column(db.String(64), index=True, unique=True)
    location = db.Column(db.String(120), index=True, unique=False)
    description = db.Column(db.String(288), index=False, unique=False)
    url = db.Column(db.String(288), index=False, unique=False)
    followers_count = db.Column(db.Integer, index=False, unique=False)
    friends_count = db.Column(db.Integer, index=False, unique=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_gives_amount = db.Column(db.Float, index=True, server_default='0')
    total_gives_number = db.Column(db.Integer, index=True, server_default='0')
    total_received_amount = db.Column(db.Float, index=True, server_default='0')
    total_received_number = db.Column(db.Integer, index=True, server_default='0')
    notify_me = db.Column(db.Boolean(), nullable=False, server_default='0')
    promote_me = db.Column(db.Boolean(), nullable=False, server_default='0')
    external_wallet = db.Column(db.String(34))
    #twittertweets = db.relationship('TwitterTweet', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.screen_name)



class Usertelegram(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=False, unique=True)
    total_gives_amount = db.Column(db.Float, index=True, server_default='0')
    total_gives_number = db.Column(db.Integer, index=True, server_default='0')
    total_received_amount = db.Column(db.Float, index=True, server_default='0')
    total_received_number = db.Column(db.Integer, index=True, server_default='0')
    notify_me = db.Column(db.Boolean(), nullable=False, server_default='0')
    promote_me = db.Column(db.Boolean(), nullable=False, server_default='0')
    external_wallet = db.Column(db.String(34))

    def __repr__(self):
        return '<User {}>'.format(self.name)

class Usermobile(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(20), index=False, unique=False)
    total_gives_amount = db.Column(db.Float, index=True, server_default='0')
    total_gives_number = db.Column(db.Integer, index=True, server_default='0')
    total_received_amount = db.Column(db.Float, index=True, server_default='0')
    total_received_number = db.Column(db.Integer, index=True, server_default='0')
    notify_me = db.Column(db.Boolean(), nullable=False, server_default='0')
    promote_me = db.Column(db.Boolean(), nullable=False, server_default='0')
    external_wallet = db.Column(db.String(34))

    def __repr__(self):
        return '<User {}>'.format(self.name)

class Useremail(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=False, unique=False)
    total_gives_amount = db.Column(db.Float, index=True, server_default='0')
    total_gives_number = db.Column(db.Integer, index=True, server_default='0')
    total_received_amount = db.Column(db.Float, index=True, server_default='0')
    total_received_number = db.Column(db.Integer, index=True, server_default='0')
    notify_me = db.Column(db.Boolean(), nullable=False, server_default='0')
    promote_me = db.Column(db.Boolean(), nullable=False, server_default='0')
    external_wallet = db.Column(db.String(34))

    def __repr__(self):
        return '<User {}>'.format(self.email)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Verification(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, nullable=False)
    password_hash = db.Column(db.String(128))
    confirm_my_stuff = db.Column(db.String(140), index=True, nullable=False)
    __table_args__ = (UniqueConstraint('username', 'confirm_my_stuff', name='_username_confirm_my_stuff_uc'),)
    
    def __repr__(self):
        return '<Verification {}>'.format(self.confirm_my_stuff)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Withdraw(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_wallet = db.Column(db.String(34))
    amount = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.Integer, db.ForeignKey('giveaiq_status.id'))
    comment = db.Column(db.String(288))
    
    def __repr__(self):
        return '<Withdraw {}>'.format(self.id)

class GiveaiqStatus(UserMixin, db.Model):
    __tablename__ = 'giveaiq_status'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False, unique=True)
    type = db.Column(db.String(64), index=True, nullable=True)
    comment = db.Column(db.String(64), index=True, nullable=True)
    
    def __repr__(self):
        return '<Status {}>'.format(self.name)

class CatchyTweet(UserMixin, db.Model):
    __tablename__ = 'catchy_tweet'
    id = db.Column(db.Integer, primary_key=True)
    tweet = db.Column(db.String(288), index=True, nullable=False)
    
    def __repr__(self):
        return '<Tweet {}>'.format(self.tweet)

class TwitterTweet(UserMixin, db.Model):
    __tablename__ = 'twitter_tweet'
    id = db.Column(db.Integer, primary_key=True)
    added_date = db.Column(db.DateTime, default=datetime.utcnow, index=False, nullable=False)
    created_at = db.Column(db.DateTime, index=False, nullable=True)
    full_text = db.Column(db.String(288), index=False, nullable=True)
    usertwitter_screen_name = db.Column(db.Integer, db.ForeignKey('usertwitter.screen_name'))
    in_reply_to_status_id = db.Column(db.Integer, index=False, nullable=True)
    in_reply_to_screen_name = db.Column(db.Integer, db.ForeignKey('usertwitter.screen_name'))
    expanded_url = db.Column(db.String(288), index=False, nullable=True)
    geo = db.Column(db.String(64), index=False, nullable=True)
    coordinates = db.Column(db.String(64), index=False, nullable=True)
    place = db.Column(db.String(64), index=False, nullable=True)
    contributors = db.Column(db.String(64), index=False, nullable=True)
    retweet_count = db.Column(db.Integer, index=False, nullable=True)
    favorite_count = db.Column(db.Integer, index=False, nullable=True)
    possibly_sensitive = db.Column(db.String(64), index=False, nullable=True)
    lang = db.Column(db.String(64), index=False, nullable=True)
    total_received_amount = db.Column(db.Float, index=True, server_default='0')
    total_received_number = db.Column(db.Integer, index=True, server_default='0')
    promoters = db.relationship('PromotedTweet', backref='promoter', lazy='dynamic')
    
    def __repr__(self):
        return '<Tweet {}>'.format(self.id)

#TODO: replace username with user_id = shit loads of work as twitter part also uses it
class PromotedTweet(UserMixin, db.Model):
    __tablename__ = 'promoted_tweet'
    id = db.Column(db.Integer, primary_key=True)
    tweet_id = db.Column(db.Integer, db.ForeignKey('twitter_tweet.id'))
    cat_id = db.Column(db.Integer, db.ForeignKey('tweet_category.id'))
    added_date = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    activated_date = db.Column(db.DateTime, index=True, nullable=True)
    validtill_date = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    status = db.Column(db.Integer, db.ForeignKey('giveaiq_status.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return '<Tweet {}>'.format(self.tweet_id)

class TweetCategory(UserMixin, db.Model):
    __tablename__ = 'tweet_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, nullable=False)
    price = db.Column(db.Float)
    
    def __repr__(self):
        return '<Category {}>'.format(self.name)

class Voucher(UserMixin, db.Model):
    __tablename__ = 'voucher'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.Integer, db.ForeignKey('giveaiq_status.id'))
    comment = db.Column(db.String(288))
    added_date = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    activated_date = db.Column(db.DateTime, index=True, nullable=True)
    validtill_date = db.Column(db.DateTime, index=True, nullable=True)
    password_hash = db.Column(db.String(128))
    
    def __repr__(self):
        return '<Voucher {}>'.format(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)