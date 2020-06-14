from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileAllowed,FileRequired
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField,BooleanField,TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo ,ValidationError
from website.models import User

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    # custom validation
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken').first()
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already taken')
    
class SignInForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile' , validators=[FileAllowed(['jpg','jpeg','png','gif'])])
    submit = SubmitField('Update')

    # custom validation
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken').first()
        
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('email already taken')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class OcrForm(FlaskForm):
    picture = FileField('Upload a Image', validators=[FileAllowed(['jpg', 'jpeg', 'png']) ])
    url = StringField('url')
    submit = SubmitField('Convert')
    content = TextAreaField('Content', validators=[DataRequired()])
    
