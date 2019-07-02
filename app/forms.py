from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, RadioField, IntegerField, HiddenField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Regexp, NumberRange
from app.models import User


class LoginForm(FlaskForm):
    account_type = HiddenField('Account Type')
    username = StringField('Username', validators=[DataRequired(), Regexp('^\w+$', message="Username must contain only letters numbers or underscore")])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit_login = SubmitField('Sign In')

class LoginFormTwitter(FlaskForm):
    account_type_login_twitter = HiddenField('Account Type')
    screen_name_login_twitter = StringField('Twitter Username (without @, case sensitive)', validators=[DataRequired(), Regexp('^\w+$', message="Username must contain only letters numbers or underscore")])
    password_login_twitter = PasswordField('GiveAIQ Password', validators=[DataRequired()])
    remember_me_login_twitter = BooleanField('Remember Me')
    submit_login_twitter = SubmitField('Sign In')

class LoginFormTelegram(FlaskForm):
    account_type_login_telegram = HiddenField('Account Type')
    name_login_telegram = StringField('Telegram Username (without @, case sensitive)', validators=[DataRequired(), Regexp('^\w+$', message="Username must contain only letters numbers or underscore")])
    password_login_telegram = PasswordField('GiveAIQ Password', validators=[DataRequired()])
    remember_me_login_telegram = BooleanField('Remember Me')
    submit_login_telegram = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    account_type = HiddenField('Account Type')
    username = StringField('Username (without @, case sensitive)', validators=[DataRequired(), Regexp('^\w+$', message="Username must contain only letters numbers or underscore")])
#    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('GiveAIQ Password', validators=[DataRequired(), Length(min=8, max=50)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    acceptRisk = BooleanField('I understand and accept <a href="/rules">Rules</a>', validators=[DataRequired(message="Required")])
    submit_register = SubmitField('Submit')

#    def validate_username(self, username):
#        user = User.query.filter_by(username=username.data).first()
#        if user is not None:
#            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class RegistrationFormTwitter(FlaskForm):
    account_type_register_twitter = HiddenField('Account Type')
    screen_name_register_twitter = StringField('Twitter Username (without @, case sensitive)', validators=[DataRequired(), Regexp('^\w+$', message="Username must contain only letters numbers or underscore")])
    password_register_twitter = PasswordField('GiveAIQ Password', validators=[DataRequired(), Length(min=8, max=50)])
    password2_register_twitter = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password_register_twitter')])
    acceptRisk_register_twitter = BooleanField('I understand and accept <a href="/rules">Rules</a>', validators=[DataRequired(message="Required")])
    submit_register_twitter = SubmitField('Submit')

class RegistrationFormTelegram(FlaskForm):
    account_type_register_telegram = HiddenField('Account Type')
    name_register_telegram = StringField('Telegram Username (without @, case sensitive)', validators=[DataRequired(), Regexp('^\w+$', message="Username must contain only letters numbers or underscore")])
    password_register_telegram = PasswordField('GiveAIQ Password', validators=[DataRequired(), Length(min=8, max=50)])
    password2_register_telegram = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password_register_telegram')])
    acceptRisk_register_telegram = BooleanField('I understand and accept <a href="/rules">Rules</a>', validators=[DataRequired(message="Required")])
    submit_register_telegram = SubmitField('Submit')

class WithdrawFundsForm(FlaskForm):
    amount = StringField('Amount', validators=[DataRequired(), NumberRange(min="0.00000001", max=None, message="Minimum amount is 0.00000001")])
    target = TextAreaField('Target Wallet Address', validators=[Length(min=34, max=34), Regexp('^\w+$', message="Wallet must contain only letters numbers or underscore")])
    submit = SubmitField('Add')

    def __init__(self, original_username, *args, **kwargs):
        super(WithdrawFundsForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class AddPromotedTweet(FlaskForm):
    tweet_id = StringField('Tweet URL', validators=[DataRequired(), Regexp('^http[s]{0,1}://twitter.com/[a-zA-Z0-9_]*/status/\d+.*', message="Please provide url to the tweet you want to promote")])
    #cat_id = SelectField(u'Category', choices=[('1', 'Commercial - 2.50 USD'), ('2', 'Community - 0.50 USD'), ('3', 'Charity - free')])
    cat_id = SelectField(u'Category', choices=[('Appreciate', 'Appreciate - 10000 AIQ'), ('Help', 'Help - free'), ('Charity', 'Charity - free')])
    submit2 = SubmitField('Add')

    def __init__(self, original_username, *args, **kwargs):
        super(AddPromotedTweet, self).__init__(*args, **kwargs)
        self.original_username = original_username

class EditProfileForm(FlaskForm):
    #username = StringField('Username', validators=[DataRequired()])
    notify_me = BooleanField('Notify me when I receive donation')
    promote_me = BooleanField('Allow my tweets to be promoted')
    #external_wallet = TextAreaField('Trusted Wallet Address', validators=[Length(min=34, max=34), Regexp('^\w+$', message="Wallet must contain only letters numbers or underscore")])
    submit = SubmitField('Submit')

class CreateVouchersForm(FlaskForm):
    voucher_value = StringField('Voucher Value in AIQ', validators=[DataRequired(), Regexp('^[\d]+[\.]{0,1}[\d]*$', message="Amount in format X.Y"), NumberRange(min="0.00000001", max=None, message="Minimum amount is 0.00000001")])
    voucher_number = IntegerField('Number of Vouchers', validators=[DataRequired()])
    password = PasswordField('PIN - min 4 characters (letters and digits)', validators=[DataRequired(), Length(min=4, max=50), Regexp('^\w+$', message="PIN must contain only letters numbers or underscore")])
    password2 = PasswordField('Repeat PIN', validators=[DataRequired(), EqualTo('password')])
    submit3 = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(CreateVouchersForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

class VoucherToWallet(FlaskForm):
    voucher_number_VoucherToWallet = StringField('Voucher Number', validators=[DataRequired(), Length(min=8, max=8), Regexp('^\w+$', message="field must contain only letters numbers or underscore")])
    password_VoucherToWallet = PasswordField('PIN', validators=[DataRequired(), Length(min=4, max=50), Regexp('^\w+$', message="PIN must contain only letters numbers or underscore")])
    target_VoucherToWallet = TextAreaField('Target Wallet Address', validators=[Length(min=34, max=34), Regexp('^\w+$', message="Wallet must contain only letters numbers or underscore")])
    submit_VoucherToWallet = SubmitField('Submit')

class VoucherToTwitter(FlaskForm):
    voucher_number_VoucherToTwitter = StringField('Voucher Number', validators=[DataRequired(), Length(min=8, max=8), Regexp('^\w+$', message="field must contain only letters numbers or underscore")])
    password_VoucherToTwitter = PasswordField('PIN', validators=[DataRequired(), Length(min=4, max=50), Regexp('^\w+$', message="PIN must contain only letters numbers or underscore")])
    target_VoucherToTwitter = StringField('Twitter username (without @, case sensitive)', validators=[DataRequired(), Regexp('^\w+$', message="Username must contain only letters numbers or underscore")])
    submit_VoucherToTwitter = SubmitField('Submit')

class VoucherToTelegram(FlaskForm):
    voucher_number_VoucherToTelegram = StringField('Voucher Number', validators=[DataRequired(), Length(min=8, max=8), Regexp('^\w+$', message="field must contain only letters numbers or underscore")])
    password_VoucherToTelegram = PasswordField('PIN', validators=[DataRequired(), Length(min=4, max=50), Regexp('^\w+$', message="PIN must contain only letters numbers or underscore")])
    target_VoucherToTelegram = StringField('Telegram username (without @, case sensitive)', validators=[DataRequired(), Regexp('^\w+$', message="Username must contain only letters numbers or underscore")])
    submit_VoucherToTelegram = SubmitField('Submit')
