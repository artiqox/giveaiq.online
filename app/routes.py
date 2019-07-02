from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, LoginFormTwitter, LoginFormTelegram, RegistrationForm, RegistrationFormTwitter, RegistrationFormTelegram, WithdrawFundsForm, AddPromotedTweet, EditProfileForm, CreateVouchersForm, VoucherToWallet, VoucherToTwitter, VoucherToTelegram
from app.models import User, Verification, Withdraw, CatchyTweet, PromotedTweet, Voucher
import string
from random import *
import sys
import requests
import json
import subprocess
import re
from hashids import Hashids
from secrets import *

webserviceurl = "https://giveaiq.online"
core = "/home/debian/artiqox-node/artiqox-cli"
telegram_bot_name = "ArtiqoxBot"
telegram_bot_channel = "@Artiqox"

def get_voucher_number(id):
    hash_id = Hashids(salt=secretStringForVouchers, min_length=8)
    return hash_id.encode(id)

def get_voucher_id(voucher_number):
    hash_id = Hashids(salt=secretStringForVouchers, min_length=8)
    return hash_id.decode(voucher_number)[0]

def voucher_to_wallet(voucher_number, target, voucher_amount):
    withdraw_command = "{0} sendfrom {1} {2} {3}".format(core, "VOUCHER-"+voucher_number, target, voucher_amount)
    result_withdraw = subprocess.check_output([withdraw_command], shell=True)
    clean = (result_withdraw.strip()).decode("utf-8")
    return clean

def voucher_to_user(voucher_number, target, voucher_amount):
    withdraw_command = "{0} move {1} {2} {3}".format(core, "VOUCHER-"+voucher_number, target, voucher_amount)
    result_withdraw = subprocess.check_output([withdraw_command], shell=True)
    clean = (result_withdraw.strip()).decode("utf-8")
    return clean

def get_user_balance(user):
    balance_command = "{0} getbalance {1}".format(core, user)
    result_balance = subprocess.check_output([balance_command], shell=True)
    clean = (result_balance.strip()).decode("utf-8")
    balance  = float(clean)
    return balance

def get_user_wallet(user):
    walletid_command = "{0} getaccountaddress {1}".format(core, user)
    result_walletid = subprocess.check_output([walletid_command], shell=True)
    walletid = (result_walletid.strip()).decode("utf-8")
    return walletid

def get_user_transactions(user):
    transactions_command = "{0} listtransactions {1} 1000".format(core, user)
    result_transactions = subprocess.check_output([transactions_command], shell=True)
    transactions = (result_transactions.strip()).decode("utf-8")
    return transactions

def get_user_dashboard(user, fiat_price, btc_price):
    giveaiq_username = user
    giveaiq_displayname = giveaiq_username[3:]
    giveaiq_accounttype = giveaiq_username[0:3]
    giveaiq_wallet_name = giveaiq_accounttype+giveaiq_displayname.lower()
    balance = get_user_balance(giveaiq_wallet_name)
    last_fiat = float(fiat_price)
    fiat_balance = balance * last_fiat
    fiat_balance = str(round(fiat_balance,4))
    last_btc = float(btc_price)
    btc_balance = balance * last_btc
    btc_balance = '{0:.8f}'.format(btc_balance)
    balance = str(round(balance,8))
    walletid = get_user_wallet(giveaiq_wallet_name)
    transactions = get_user_transactions(giveaiq_wallet_name)
    cmd = "select total_gives_amount, total_gives_number, total_received_amount, total_received_number from usertwitter where screen_name = '{0}'".format(giveaiq_displayname)
    giveaiq_stats = db.session.execute(cmd, ).fetchall()
    return fiat_balance, btc_balance, balance, walletid, transactions, giveaiq_stats

def get_api_coingecko():
    api_url = requests.get('https://api.coingecko.com/api/v3/coins/artiqox?localization=false')
    market_data_json = api_url.json()
    community_data_json = json.loads(json.dumps(market_data_json['community_data']))
    twitter_followers = json.dumps(community_data_json['twitter_followers'])
    current_price_json = json.loads(json.dumps(market_data_json['market_data']))
    total_supply = json.dumps(current_price_json['total_supply'])
    circulating_supply = json.dumps(current_price_json['circulating_supply'])
    currency_json = json.loads(json.dumps(current_price_json['current_price']))
    btc_price = json.dumps(currency_json['btc'])
    fiat_price = json.dumps(currency_json['usd'])
    return twitter_followers, total_supply, circulating_supply, btc_price, fiat_price, currency_json

def update_tweet(tweet_id):
    
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    status = api.get_status(tweet_id, tweet_mode='extended')
    print(status)
    tweet_author_id = status.user.id
    tweet_author_screen_name = status.user.screen_name
    tweet_author_name = status.user.name
    tweet_author_description = status.user.description
    tweet_author_location = status.user.location
    tweet_author_url = status.user.url
    tweet_author_followers_count = status.user.followers_count
    tweet_author_friends_count = status.user.friends_count
    tweet_author_created_at = status.user.created_at
    tweet_full_text = status.full_text
    tweet_in_reply_to_status_id = status.in_reply_to_status_id
    tweet_in_reply_to_user_id = status.in_reply_to_user_id
    tweet_in_reply_to_screen_name = status.in_reply_to_screen_name
    tweet_geo = status.geo
    tweet_coordinates = status.coordinates
    tweet_place = status.place
    tweet_created_at = status.created_at
    tweet_contributors = status.contributors
    tweet_retweet_count = status.retweet_count
    tweet_favorite_count = status.favorite_count
    tweet_possibly_sensitive = ""
    tweet_lang = status.lang
    cmd = "INSERT OR IGNORE INTO usertwitter (screen_name) VALUES (?)"
    db.session.execute(cmd, (tweet_author_screen_name, ))
    
    if tweet_in_reply_to_screen_name:
        cmd = "INSERT OR IGNORE INTO usertwitter (screen_name) VALUES (?)"
        db.session.execute(cmd, (tweet_in_reply_to_screen_name))
    cmd = "UPDATE usertwitter SET name=?, location=?, description=?, url=?, followers_count=?, friends_count=? WHERE screen_name=?"
    db.session.execute(cmd, (tweet_author_name, tweet_author_location, tweet_author_description, tweet_author_url, tweet_author_followers_count, tweet_author_friends_count, tweet_author_screen_name))
    cmd = "INSERT OR IGNORE INTO twitter_tweet (id, added_date) VALUES (?, ?)"
    db.session.execute(cmd, (tweet_id, datetime.utcnow(), ))
    cmd = "UPDATE twitter_tweet SET full_text=?, usertwitter_screen_name=?, in_reply_to_status_id=?, in_reply_to_screen_name=?, possibly_sensitive=? WHERE id=?"
    db.session.execute(cmd, (tweet_full_text, tweet_author_screen_name, tweet_in_reply_to_status_id, tweet_in_reply_to_screen_name, tweet_possibly_sensitive, tweet_id))
    db.session.commit()
    return tweet_author_screen_name

def get_tweet_author_info(tweet_id):
    cmd = "SELECT twitter_tweet.usertwitter_screen_name, usertwitter.promote_me FROM twitter_tweet, usertwitter WHERE twitter_tweet.usertwitter_screen_name=usertwitter.screen_name and twitter_tweet.id=?"
    userinfo = db.session.execute(cmd, (tweet_id)).fetchall()
    if userinfo:
        for worder in userinfo:
            screen_name = worder[0]
            promote_me = worder[1]
    else:
        screen_name = update_tweet(tweet_id)
        promote_me = 0
    return screen_name, promote_me

def get_status_id(status_name):
    cmd = "select id from giveaiq_status where name = '{0}'".format(status_name)
    return db.session.execute(cmd, ).fetchone()[0]

def get_category_id(category_name):
    cmd = "select id from tweet_category where name = '{0}'".format(category_name)
    return db.session.execute(cmd, ).fetchone()[0]

def get_promotedtweets(status_id, cat_id):
    cmd = "SELECT promoted_tweet.tweet_id, twitter_tweet.total_received_amount, twitter_tweet.total_received_number FROM promoted_tweet, twitter_tweet WHERE promoted_tweet.tweet_id=twitter_tweet.id and status='{0}' and cat_id='{1}' ORDER BY RANDOM() LIMIT 30".format(status_id, cat_id)
    promotedtweets = db.session.execute(cmd, ).fetchall()
    if promotedtweets is None:
        return "None"
    else:
        return promotedtweets

def change_user_tweet(user_id):
    cmd = "select username, confirm_my_stuff from user where id={0}".format(user_id)
    userinfo = db.session.execute(cmd, ).fetchall()
    if userinfo:
        for worder in userinfo:
            giveaiq_username = worder[0]
            old_confirm_my_stuff = worder[1]
        giveaiq_displayname = giveaiq_username[3:]
        giveaiq_accounttype = giveaiq_username[0:3]
        if giveaiq_accounttype == "TW-":
            cmd = "SELECT tweet FROM catchy_tweet where tweet not like '(select confirm_my_stuff from user where id={0})%' ORDER BY RANDOM() LIMIT 1".format(user_id)
            new_user_tweet = db.session.execute(cmd, ).fetchone()[0]
        elif giveaiq_accounttype == "TG-":
            allchar = string.ascii_letters + string.digits
            new_user_tweet = "".join(choice(allchar) for x in range(randint(5, 5)))
        cmd = "UPDATE user SET confirm_my_stuff='{0}' where id={1}".format(new_user_tweet, user_id)
        db.session.execute(cmd, )
        db.session.commit()

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
#@login_required
def index():
    current_time = datetime.utcnow()
    #one_day_ago = current_time - datetime.timedelta(days=1)
    form_VoucherToWallet = VoucherToWallet()
    form_VoucherToTwitter = VoucherToTwitter()
    form_VoucherToTelegram = VoucherToTelegram()

    if form_VoucherToWallet.submit_VoucherToWallet.data and form_VoucherToWallet.validate():
        
        target = ''.join(str(e) for e in form_VoucherToWallet.target_VoucherToWallet.data)
        voucher_number = ''.join(str(e) for e in form_VoucherToWallet.voucher_number_VoucherToWallet.data)
        voucher_id = get_voucher_id(voucher_number)
        password = ''.join(str(e) for e in form_VoucherToWallet.password_VoucherToWallet.data)
        voucher = Voucher.query.filter_by(id=voucher_id).first()
        if voucher is None or not voucher.check_password(password):
            flash('Invalid voucher number or password')
            return redirect(url_for('index'))
        elif voucher.status == get_status_id('Voucher Used'):
            flash('Voucher Already Used')
            return redirect(url_for('index'))
        elif voucher.status == get_status_id('Voucher Active'):
            voucher_amount = get_user_balance("VOUCHER-"+voucher_number)
            if voucher_amount > 0:
                voucher_to_wallet(voucher_number, target, str(voucher_amount))
                textflash="Amount "+str(voucher_amount)+" AIQ from Voucher "+voucher_number+" Transfered to "+target
                flash(textflash)
            else:
                flash('Voucher Empty')
        else:
            flash('Something went wrong, talk to support')
        return redirect(url_for('index'))

    if form_VoucherToTwitter.submit_VoucherToTwitter.data and form_VoucherToTwitter.validate():
        
        target = ''.join(str(e) for e in form_VoucherToTwitter.target_VoucherToTwitter.data)
        target_wallet = "TW-"+target.lower()
        voucher_number = ''.join(str(e) for e in form_VoucherToTwitter.voucher_number_VoucherToTwitter.data)
        voucher_id = get_voucher_id(voucher_number)
        password = ''.join(str(e) for e in form_VoucherToTwitter.password_VoucherToTwitter.data)
        voucher = Voucher.query.filter_by(id=voucher_id).first()
        if voucher is None or not voucher.check_password(password):
            flash('Invalid voucher number or password')
            return redirect(url_for('index'))
        elif voucher.status == get_status_id('Voucher Used'):
            flash('Voucher Already Used')
            return redirect(url_for('index'))
        elif voucher.status == get_status_id('Voucher Active'):
            voucher_amount = get_user_balance("VOUCHER-"+voucher_number)
            if voucher_amount > 0:
                voucher_to_user(voucher_number, target_wallet, str(voucher_amount))
                textflash="Amount "+str(voucher_amount)+" AIQ from Voucher "+voucher_number+" Transfered to @"+target
                flash(textflash)
            else:
                flash('Voucher Empty')
        else:
            flash('Something went wrong, talk to support')
        return redirect(url_for('index'))

    if form_VoucherToTelegram.submit_VoucherToTelegram.data and form_VoucherToTelegram.validate():
        
        target = ''.join(str(e) for e in form_VoucherToTelegram.target_VoucherToTelegram.data)
        target_wallet = "TG-"+target.lower()
        voucher_number = ''.join(str(e) for e in form_VoucherToTelegram.voucher_number_VoucherToTelegram.data)
        voucher_id = get_voucher_id(voucher_number)
        password = ''.join(str(e) for e in form_VoucherToTelegram.password_VoucherToTelegram.data)
        voucher = Voucher.query.filter_by(id=voucher_id).first()
        if voucher is None or not voucher.check_password(password):
            flash('Invalid voucher number or password')
            return redirect(url_for('index'))
        elif voucher.status == get_status_id('Voucher Used'):
            flash('Voucher Already Used')
            return redirect(url_for('index'))
        elif voucher.status == get_status_id('Voucher Active'):
            voucher_amount = get_user_balance("VOUCHER-"+voucher_number)
            if voucher_amount > 0:
                voucher_to_user(voucher_number, target_wallet, str(voucher_amount))
                textflash="Amount "+str(voucher_amount)+" AIQ from Voucher "+voucher_number+" Transfered to @"+target
                flash(textflash)
            else:
                flash('Voucher Empty')
        else:
            flash('Something went wrong, talk to support')
        return redirect(url_for('index'))


    to_rain = ""
    user_number = 0
    users = db.session.execute("SELECT username FROM user where username like 'TW-%' ORDER BY RANDOM() LIMIT 30;").fetchall()
    for u in users:
        to_rain = to_rain+" @"+u.username[3:]
        user_number += 1
    if user_number > 1:
        tweet_rain = "@GiveAIQ cryptorain 0.01 USD"+to_rain+" #AIQ $AIQ #bestCryptocurrency"
    else:
        tweet_rain = "None"

    to_rain = ""
    users = db.session.execute("SELECT username FROM user where username like 'TG-%' ORDER BY RANDOM() LIMIT 30;").fetchall()
    for u in users:
        to_rain = to_rain+" @"+u.username[3:]
        user_number += 1
    if user_number > 1:
        telegram_rain = "/cryptorain 0.01 USD"+to_rain
    else:
        telegram_rain = "None"
    confirmedstatus_id = get_status_id('Promote Tweet Order Paid')
    promotedtweets = get_promotedtweets(confirmedstatus_id, get_category_id('Appreciate'))
    charitytweets = get_promotedtweets(confirmedstatus_id, get_category_id('Charity'))
    helptweets = get_promotedtweets(confirmedstatus_id, get_category_id('Help'))
    twitter_followers, total_supply, circulating_supply, btc_price, fiat_price, currency_json = get_api_coingecko()
    if current_user.is_authenticated:
        giveaiq_accounttype = current_user.username[:3]
        fiat_balance, btc_balance, balance, walletid, transactions, giveaiq_stats = get_user_dashboard(current_user.username, fiat_price, btc_price)
        data = json.loads(transactions)
        transactions_gives, transactions_receives, amount_gives, amounnt_receives = 0, 0, 0, 0
        for a in data:
            if a['amount'] > 0 and a['category'] == "move":
                amounnt_receives += a['amount']
                transactions_receives += 1
            elif a['category'] == "move":
                amount_gives += a['amount']
                transactions_gives += 1
    else:
        fiat_balance, btc_balance, balance, walletid, transactions, data, transactions_gives, transactions_receives, amount_gives, amounnt_receives, giveaiq_stats = "", "", "", "", "", "", "", "", "", "", ""
        giveaiq_accounttype = ""
        transactions_gives = 0
    return render_template('index.html', title='Home', balance=balance, fiat_balance=fiat_balance, btc_balance=btc_balance, walletid=walletid, circulating_supply=circulating_supply, total_supply=total_supply, twitter_followers=twitter_followers, tweet_rain=tweet_rain, telegram_rain = telegram_rain, promotedtweets=promotedtweets, charitytweets=charitytweets, helptweets=helptweets, transactions=data, amounnt_receives=amounnt_receives, transactions_receives=transactions_receives, amount_gives=amount_gives, transactions_gives=transactions_gives, giveaiq_stats=giveaiq_stats, giveaiq_accounttype=giveaiq_accounttype, form_VoucherToWallet=form_VoucherToWallet, form_VoucherToTwitter=form_VoucherToTwitter, form_VoucherToTelegram=form_VoucherToTelegram)


@app.route('/faq')
def faq():
    return render_template('faq.html', title='faq', webserviceurl=webserviceurl)

@app.route('/rules')
def rules():
    return render_template('rules.html', title='rules', webserviceurl=webserviceurl)


@app.route('/login', methods=['GET', 'POST'])
def login():
    rule = request.url_rule
    page_mode = rule.rule[1:]
#    if 'antitop' in rule.rule:
#        # request by '/antitop'
#        nothgingnew = 0
#    elif 'top' in rule.rule:
#        nothgingnew = 0
#    else:
#    print(rule.rule)
#    if current_user.is_authenticated and (page_mode.startswith( 'login' ) or page_mode.startswith( 'register' )):
#        return redirect(url_for('giveaiq'))

    if current_user.is_authenticated:
        giveaiq_username = current_user.username
        giveaiq_displayname = giveaiq_username[3:]
        giveaiq_accounttype = giveaiq_username[0:3]
    else:
        giveaiq_username = ""
        giveaiq_displayname = ""
        giveaiq_accounttype = ""

    giveaiq_wallet_name = ""
    confirm_my_stuff = ""
    title = "Login"

    form_LoginFormTwitter = LoginFormTwitter(request.values, account_type_login_twitter="TW-")
    form_LoginFormTelegram = LoginFormTelegram(request.values, account_type_login_telegram="TG-")

    if form_LoginFormTwitter.submit_login_twitter.data and form_LoginFormTwitter.validate_on_submit():
        user = User.query.filter_by(username=form_LoginFormTwitter.account_type_login_twitter.data+form_LoginFormTwitter.screen_name_login_twitter.data).first()
        if user is None or not user.check_password(form_LoginFormTwitter.password_login_twitter.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form_LoginFormTwitter.remember_me_login_twitter.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    elif form_LoginFormTelegram.submit_login_telegram.data and form_LoginFormTelegram.validate_on_submit():
        user = User.query.filter_by(username=form_LoginFormTelegram.account_type_login_telegram.data+form_LoginFormTelegram.name_login_telegram.data).first()
        if user is None or not user.check_password(form_LoginFormTelegram.password_login_telegram.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form_LoginFormTelegram.remember_me_login_telegram.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=title, form_LoginFormTwitter=form_LoginFormTwitter, form_LoginFormTelegram=form_LoginFormTelegram, confirm_my_stuff=confirm_my_stuff, giveaiq_username=giveaiq_username, giveaiq_displayname=giveaiq_displayname, giveaiq_accounttype=giveaiq_accounttype, telegram_bot_name=telegram_bot_name, telegram_bot_channel=telegram_bot_channel, page_mode=page_mode)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    rule = request.url_rule
    page_mode = rule.rule[1:]
#    if 'antitop' in rule.rule:
#        # request by '/antitop'
#        nothgingnew = 0
#    elif 'top' in rule.rule:
#        nothgingnew = 0
#    else:
#    print(rule.rule)
#    if current_user.is_authenticated and (page_mode.startswith( 'login' ) or page_mode.startswith( 'register' )):
#        return redirect(url_for('giveaiq'))

    if current_user.is_authenticated:
        giveaiq_username = current_user.username
        giveaiq_displayname = giveaiq_username[3:]
        giveaiq_accounttype = giveaiq_username[0:3]
    else:
        giveaiq_username = ""
        giveaiq_displayname = ""
        giveaiq_accounttype = ""

    giveaiq_wallet_name = ""
    confirm_my_stuff = ""
    title = "Register"

    if giveaiq_accounttype == "TW-":
        form_registrationTwitter = RegistrationFormTwitter(request.values, account_type_register_twitter="TW-", screen_name_register_twitter=giveaiq_displayname)
    else:
        form_registrationTwitter = RegistrationFormTwitter(request.values, account_type_register_twitter="TW-")

    if giveaiq_accounttype == "TG-":
        form_registrationTelegram = RegistrationFormTelegram(request.values, account_type_register_telegram="TG-", name_register_telegram=giveaiq_displayname)
    else:
        form_registrationTelegram = RegistrationFormTelegram(request.values, account_type_register_telegram="TG-")

    if form_registrationTwitter.submit_register_twitter.data and form_registrationTwitter.validate_on_submit():
        giveaiq_username = form_registrationTwitter.account_type_register_twitter.data+form_registrationTwitter.screen_name_register_twitter.data
        giveaiq_displayname = form_registrationTwitter.screen_name_register_twitter.data
        giveaiq_accounttype = form_registrationTwitter.account_type_register_twitter.data
        giveaiq_wallet_name = giveaiq_accounttype+giveaiq_displayname.lower()
        user_tweet = db.session.execute("SELECT tweet FROM catchy_tweet where tweet not in (select confirm_my_stuff from verification where username=:username) ORDER BY RANDOM() LIMIT 1", {"username": giveaiq_username}).fetchone()[0]
        #allchar = string.ascii_letters + string.digits
        #random_token = "".join(choice(allchar) for x in range(randint(5, 5)))
        confirm_my_stuff = "@GiveAIQ AIQ to the moon. " + user_tweet + " #AIQ $AIQ #cryptocurrency @artiqox"

        #totweet = "Almost done, to activate the access please use twitter @"+form.username.data+" and tweet: " + tweet
        verification = Verification(username=giveaiq_username, confirm_my_stuff=user_tweet)
        verification.set_password(form_registrationTwitter.password_register_twitter.data)
        db.session.add(verification)
        db.session.commit()
        title='Verify the account !'
        #flash(totweet)
        #return redirect(url_for('login'))
        return render_template('register.html', title=title, form=form_registrationTwitter, confirm_my_stuff=confirm_my_stuff, giveaiq_username=giveaiq_username, giveaiq_displayname=giveaiq_displayname, giveaiq_accounttype=giveaiq_accounttype, telegram_bot_name=telegram_bot_name, telegram_bot_channel=telegram_bot_channel)
    elif form_registrationTelegram.submit_register_telegram.data and form_registrationTelegram.validate_on_submit():
        giveaiq_username = form_registrationTelegram.account_type_register_telegram.data+form_registrationTelegram.name_register_telegram.data
        giveaiq_displayname = form_registrationTelegram.name_register_telegram.data
        giveaiq_accounttype = form_registrationTelegram.account_type_register_telegram.data
        giveaiq_wallet_name = giveaiq_accounttype+giveaiq_displayname.lower()
        allchar = string.ascii_letters + string.digits
        user_tweet = "".join(choice(allchar) for x in range(randint(5, 5)))
        #allchar = string.ascii_letters + string.digits
        #random_token = "".join(choice(allchar) for x in range(randint(5, 5)))
        confirm_my_stuff = "/verifyme " + user_tweet

        #totweet = "Almost done, to activate the access please use twitter @"+form.username.data+" and tweet: " + tweet
        verification = Verification(username=giveaiq_username, confirm_my_stuff=user_tweet)
        verification.set_password(form_registrationTelegram.password_register_telegram.data)
        db.session.add(verification)
        db.session.commit()
        title='Verify the account !'
        #flash(totweet)
        #return redirect(url_for('login'))
        return render_template('register.html', title=title, form=form_registrationTelegram, confirm_my_stuff=confirm_my_stuff, giveaiq_username=giveaiq_username, giveaiq_displayname=giveaiq_displayname, giveaiq_accounttype=giveaiq_accounttype, telegram_bot_name=telegram_bot_name, telegram_bot_channel=telegram_bot_channel)
    return render_template('register.html', title=title, form_registrationTwitter=form_registrationTwitter, form_registrationTelegram=form_registrationTelegram, confirm_my_stuff=confirm_my_stuff, giveaiq_username=giveaiq_username, giveaiq_displayname=giveaiq_displayname, giveaiq_accounttype=giveaiq_accounttype, telegram_bot_name=telegram_bot_name, telegram_bot_channel=telegram_bot_channel, page_mode=page_mode)


@app.route('/register_tobedeleted', methods=['GET', 'POST'])
def register_tobedeleted():
    title='Register/Reset Password'
    if current_user.is_authenticated:
        title='Change Passord'
        #return redirect(url_for('index'))
    form = RegistrationForm()
    confirm_my_stuff = ""
    giveaiq_username = ""
    giveaiq_displayname = ""
    giveaiq_accounttype = ""
    giveaiq_wallet_name = ""
    if form.validate_on_submit():
        giveaiq_username = form.account_type.data+form.username.data
        giveaiq_displayname = form.username.data
        giveaiq_accounttype = form.account_type.data
        giveaiq_wallet_name = giveaiq_accounttype+giveaiq_displayname.lower()
        user_tweet = db.session.execute("SELECT tweet FROM catchy_tweet where tweet not in (select confirm_my_stuff from verification where username=:username) ORDER BY RANDOM() LIMIT 1", {"username": giveaiq_username}).fetchone()[0]
        #allchar = string.ascii_letters + string.digits
        #random_token = "".join(choice(allchar) for x in range(randint(5, 5)))
        confirm_my_stuff = "@GiveAIQ AIQ to the moon. " + user_tweet + " #AIQ $AIQ #cryptocurrency @artiqox"

        #totweet = "Almost done, to activate the access please use twitter @"+form.username.data+" and tweet: " + tweet
        verification = Verification(username=giveaiq_username, confirm_my_stuff=user_tweet)
        verification.set_password(form.password.data)
        db.session.add(verification)
        db.session.commit()
        title='Please verify the account now !'
        #flash(totweet)
        #return redirect(url_for('login'))
    return render_template('register.html', title=title, form=form, confirm_my_stuff=confirm_my_stuff, giveaiq_username=giveaiq_username, giveaiq_displayname=giveaiq_displayname, giveaiq_accounttype=giveaiq_accounttype)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    giveaiq_username = current_user.username
    giveaiq_displayname = giveaiq_username[3:]
    giveaiq_accounttype = giveaiq_username[0:3]
    if form.validate_on_submit():
        notify_me = form.notify_me.data
        promote_me = form.promote_me.data
        
        if notify_me:
            notify_me = 1
        else:
            notify_me = 0

        if promote_me:
            promote_me = 1
        else:
            promote_me = 0
            
        if giveaiq_accounttype == "TW-":
            cmd = "UPDATE usertwitter SET notify_me='{0}', promote_me='{1}' WHERE screen_name='{2}'".format(notify_me, promote_me, current_user.displayname)
        elif giveaiq_accounttype == "TG-":
            cmd = "UPDATE usertelegram SET notify_me='{0}', promote_me='{1}' WHERE name='{2}'".format(notify_me, promote_me, current_user.displayname)
        db.session.execute(cmd, )
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        if giveaiq_accounttype == "TW-":
            cmd = "SELECT notify_me, promote_me FROM usertwitter WHERE screen_name='{0}'".format(current_user.displayname)
        elif giveaiq_accounttype == "TG-":
            cmd = "SELECT notify_me, promote_me FROM usertelegram WHERE name='{0}'".format(current_user.displayname)
        edit_me = db.session.execute(cmd, ).fetchall()
        if edit_me:
            for worder in edit_me:
                notify_me = worder[0]
                promote_me = worder[1]
        if notify_me == 1:
            form.notify_me.data = notify_me
        if promote_me == 1:
            form.promote_me.data = promote_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/delete_withdraw/<id>', methods=['GET', 'POST'])
@login_required
def delete_withdraw(id):
    if current_user.is_authenticated and id:
        cmd = "DELETE FROM withdraw WHERE id={0} and user_id={1}".format(id, current_user.id)
        db.session.execute(cmd, )
        db.session.commit()
        change_user_tweet(current_user.id)
    return redirect(url_for('toolbox'))

@app.route('/delete_awaiting_voucher/<voucher_number>', methods=['GET', 'POST'])
@login_required
def delete_awaiting_voucher(voucher_number):
    if current_user.is_authenticated and voucher_number:
        cmd = "DELETE FROM voucher WHERE id={0} and user_id={1}".format(get_voucher_id(voucher_number), current_user.id)
        db.session.execute(cmd, )
        db.session.commit()
        change_user_tweet(current_user.id)
    return redirect(url_for('toolbox'))

@app.route('/delete_promotedtweet/<id>', methods=['GET', 'POST'])
@login_required
def delete_promotedtweet(id):
    if current_user.is_authenticated and id:
        cmd = "DELETE FROM promoted_tweet WHERE id={0} and user_id={1}".format(id, current_user.id)
        db.session.execute(cmd, )
        db.session.commit()
        change_user_tweet(current_user.id)
    return redirect(url_for('toolbox'))

@app.route('/toolbox', methods=['GET', 'POST'])
@login_required
def toolbox():

    form = WithdrawFundsForm(current_user.username)
    form2 = AddPromotedTweet(current_user.username)
    form3 = CreateVouchersForm(current_user.username)

    giveaiq_username = current_user.username
    giveaiq_displayname = giveaiq_username[3:]
    giveaiq_accounttype = giveaiq_username[0:3]
    giveaiq_wallet_name = giveaiq_accounttype+giveaiq_displayname.lower()

    cmd = "UPDATE promoted_tweet set status={0} where added_date<date()-1 and user_id={1} and status={2}".format(get_status_id("Tweet Order Expired"), current_user.id, get_status_id("Tweet Awaiting Confirmation"))
    db.session.execute(cmd, )
    db.session.commit()



    twitter_followers, total_supply, circulating_supply, btc_price, fiat_price, currency_json = get_api_coingecko()

#    cat_1_price = 2.5/float(fiat_price)
#    cat_2_price = 0.5/float(fiat_price)
#    cat_3_price = 0
#    uppsymb = "USD"
#    decplace = 4

    cmd = "SELECT SUM(amount) FROM withdraw where user_id={0} and status={1}".format(current_user.id, get_status_id("Withdraw Awaiting Confirmation"))
    planned_ammount = db.session.execute(cmd, ).fetchone()[0]
    if planned_ammount is None:
        planned_ammount=0

    cmd = "select SUM(tweet_category.price) from promoted_tweet, tweet_category where promoted_tweet.cat_id=tweet_category.id and promoted_tweet.user_id={0} and promoted_tweet.status={1}".format(current_user.id, get_status_id("Tweet Awaiting Confirmation"))
    planned_ammount2 = db.session.execute(cmd, ).fetchone()[0]
    if planned_ammount2 is None:
        planned_ammount2=0

    cmd = "SELECT SUM(amount) FROM voucher where user_id={0} and status={1}".format(current_user.id, get_status_id("Voucher Awaiting Confirmation"))
    planned_ammount3 = db.session.execute(cmd, ).fetchone()[0]
    if planned_ammount3 is None:
        planned_ammount3=0

    if form.submit.data and form.validate():
        
        address = ''.join(str(e) for e in form.target.data)
        amount = float(form.amount.data)
        balance = get_user_balance(giveaiq_wallet_name)

        cmd = "SELECT SUM(amount) FROM withdraw where user_id={0} and status={1}".format(current_user.id, get_status_id("Withdraw Awaiting Confirmation"))
        planned_ammount = db.session.execute(cmd, ).fetchone()[0]
        if planned_ammount is None:
            planned_ammount=0

        if balance-float(planned_ammount) < amount:
            flash('Sorry, you have unsuficient funds.')
        else:
            withdraw = Withdraw(target_wallet=address, amount=amount, user_id=current_user.id, status=get_status_id("Withdraw Awaiting Confirmation"))
            db.session.add(withdraw)
            db.session.commit()
            change_user_tweet(current_user.id)

            cmd = "SELECT SUM(amount) FROM withdraw where user_id={0} and status={1}".format(current_user.id, get_status_id("Withdraw Awaiting Confirmation"))
            planned_ammount = db.session.execute(cmd, ).fetchone()[0]
            if planned_ammount is None:
                planned_ammount=0

    if form2.submit2.data and form2.validate():

        pattern = r"http[s]{0,1}://twitter.com/[a-zA-Z0-9_]*/status/(\d+).*"
        match = re.match(pattern,form2.tweet_id.data)
        tweet_id = match.group(1)
        cat_id = int(get_category_id(form2.cat_id.data))

        cmd = "select price from tweet_category where id={0}".format(cat_id)
        amount = db.session.execute(cmd, ).fetchone()[0]

        balance = get_user_balance(giveaiq_wallet_name)

        cmd = "select SUM(tweet_category.price) from promoted_tweet, tweet_category where promoted_tweet.cat_id=tweet_category.id and promoted_tweet.user_id={0} and promoted_tweet.status={1}".format(current_user.id, get_status_id("Tweet Awaiting Confirmation"))
        planned_ammount2 = db.session.execute(cmd, ).fetchone()[0]
        if planned_ammount2 is None:
            planned_ammount2=0

        if balance-float(planned_ammount2) < amount:
            flash('Sorry, you have insuficient funds.')
        else:
            promotedtweet = PromotedTweet(tweet_id=tweet_id, cat_id=cat_id, status=get_status_id("Tweet Awaiting Confirmation"), user_id=current_user.id)
            db.session.add(promotedtweet)
            db.session.commit()
            change_user_tweet(current_user.id)

            cmd = "select SUM(tweet_category.price) from promoted_tweet, tweet_category where promoted_tweet.cat_id=tweet_category.id and promoted_tweet.user_id={0} and promoted_tweet.status={1}".format(current_user.id, get_status_id("Tweet Awaiting Confirmation"))
            planned_ammount2 = db.session.execute(cmd, ).fetchone()[0]
            if planned_ammount2 is None:
                planned_ammount2=0

    if form3.submit3.data and form3.validate():
        
        voucher_pin = ''.join(str(e) for e in form3.password.data)
        voucher_value = float(form3.voucher_value.data)
        voucher_number = int(form3.voucher_number.data)
        total_value = voucher_value * voucher_number
        balance = get_user_balance(giveaiq_wallet_name)
        print(voucher_pin)
        print(voucher_value)
        print(voucher_number)
#        cmd = "SELECT SUM(amount) FROM voucher where user_id={0} and status={1}".format(current_user.id, get_status_id("Voucher Awaiting Confirmation"))
#        planned_ammount3 = db.session.execute(cmd, ).fetchone()[0]
#        if planned_ammount3 is None:
#            planned_ammount3=0

        if balance-float(planned_ammount3) < total_value:
            flash('Sorry, you have unsuficient funds.')
        else:
            status=get_status_id("Voucher Awaiting Confirmation")
            for x in range(voucher_number):
                voucher = Voucher(amount=voucher_value, user_id=current_user.id, status=status)
                voucher.set_password(voucher_pin)
                db.session.add(voucher)
                db.session.commit()
            change_user_tweet(current_user.id)

            cmd = "SELECT SUM(amount) FROM voucher where user_id={0} and status={1}".format(current_user.id, get_status_id("Voucher Awaiting Confirmation"))
            planned_ammount3 = db.session.execute(cmd, ).fetchone()[0]
            if planned_ammount3 is None:
                planned_ammount3=0

    confirm_my_stuff = db.session.execute("SELECT confirm_my_stuff FROM user where username=:username", {"username": giveaiq_username}).fetchone()[0]
    if confirm_my_stuff is None:
        confirm_my_stuff="Please change your password first at give.artiqox.com/register"

    if giveaiq_accounttype == "TW-":
        tweet = "@GiveAIQ you guys rock! "+confirm_my_stuff+" #AIQ $AIQ #cryptocurrency @artiqox"
        tweet2 = "@GiveAIQ AIQ supercrypto! "+confirm_my_stuff+" #AIQ $AIQ #cryptocurrency @artiqox"
        tweet3 = "@GiveAIQ AIQ cryptovouchers, so cool! "+confirm_my_stuff+" #AIQ $AIQ #cryptocurrency @artiqox"
    elif giveaiq_accounttype == "TG-":
        tweet = "/withdrawmystuff "+confirm_my_stuff
        tweet2 = "/promotemystuff "+confirm_my_stuff
        tweet3 = "/cryptovouchers "+confirm_my_stuff


    cmd="SELECT id, target_wallet, amount FROM withdraw WHERE user_id={0} and status={1}".format(current_user.id, get_status_id("Withdraw Awaiting Confirmation"))
    withdraws = db.session.execute(cmd, ).fetchall()
    cmd="SELECT promoted_tweet.id, promoted_tweet.tweet_id, tweet_category.price FROM promoted_tweet, tweet_category WHERE promoted_tweet.cat_id=tweet_category.id and promoted_tweet.user_id={0} and promoted_tweet.status={1}".format(current_user.id, get_status_id("Tweet Awaiting Confirmation"))
    promotedtweets = db.session.execute(cmd, ).fetchall()
    cmd="SELECT voucher.id, voucher.amount, voucher.comment, voucher.status FROM voucher WHERE voucher.user_id={0}".format(current_user.id)
    vouchers = db.session.execute(cmd, ).fetchall()
    vouchers_awaiting = []
    vouchers_valid = []
    if vouchers:
        status_awaiting=get_status_id("Voucher Awaiting Confirmation")
        status_active=get_status_id("Voucher Active")
        status_used=get_status_id("Voucher Used")
        for worder in vouchers:
            id = worder[0]
            if worder[3] == status_awaiting:
                vouchers_awaiting.append({'voucher_number':get_voucher_number(worder[0]),'voucher_amount':worder[1],'voucher_comment':worder[2]})
            elif worder[3] == status_active:
                vouchers_valid.append({'voucher_number':get_voucher_number(worder[0]),'voucher_amount':worder[1],'voucher_comment':worder[2],'voucher_status':"Active"})
            elif worder[3] == status_used:
                vouchers_valid.append({'voucher_number':get_voucher_number(worder[0]),'voucher_amount':worder[1],'voucher_comment':worder[2],'voucher_status':"Used"})
    fiat_balance, btc_balance, balance, walletid, transactions, giveaiq_stats = get_user_dashboard(current_user.username, fiat_price, btc_price)
    print(vouchers_awaiting)
    return render_template('toolbox.html', title='Toolbox', form=form, form2=form2, form3=form3, planned_ammount=planned_ammount, planned_ammount2=planned_ammount2, planned_ammount3=planned_ammount3, withdraws=withdraws, promotedtweets=promotedtweets, tweet=tweet, tweet2=tweet2, tweet3=tweet3, balance=balance, fiat_balance=fiat_balance, btc_balance=btc_balance, walletid=walletid, circulating_supply=circulating_supply, total_supply=total_supply, twitter_followers=twitter_followers, giveaiq_stats=giveaiq_stats, vouchers_awaiting=vouchers_awaiting, vouchers_valid=vouchers_valid, giveaiq_accounttype=giveaiq_accounttype, giveaiq_displayname=giveaiq_displayname, telegram_bot_name=telegram_bot_name)

@app.route('/get_tweet_author', methods=['POST'])
@login_required
def get_author_of_the_tweet_url():
    pattern = r"http[s]{0,1}://twitter.com/[a-zA-Z0-9_]*/status/(\d+).*"
    match = re.match(pattern,request.form['tweeturl'])
    tweet_id = match.group(1)
    screen_name, promote_me = get_tweet_author_info(tweet_id)
    return screen_name, promote_me
