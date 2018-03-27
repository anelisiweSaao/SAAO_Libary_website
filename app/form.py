from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField
from flask_wtf.file import FileField

'''This contains data validators to confirm if the data entered in the browser by the user is valid'''

class LoginForm(FlaskForm):
    username = StringField("username", validators=[DataRequired('username is required')])
    password = PasswordField("password", validators=[DataRequired('password is required')])
    remember = BooleanField("Remember me")


class publications(FlaskForm):
    start_date = DateField('Start date', format='%Y-%m-%d', validators=[DataRequired('enter the month and the year')])
    end_date = DateField('End date', format='%Y-%m-%d', validators=[DataRequired(False)])


class AdminForm(FlaskForm):
    keys = FileField("Keys file",)
    authors = FileField("Authors file")

