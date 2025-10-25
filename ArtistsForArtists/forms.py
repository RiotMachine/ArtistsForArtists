from wtforms            import BooleanField, PasswordField, RadioField, StringField
from wtforms.validators import EqualTo, InputRequired
from flask_wtf          import FlaskForm

## credit to @dcrosta
## https://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms
class RequiredIf(InputRequired):
    # a validator which makes a field required if
    # another field is set and has a truthy value

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super().__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception(f'no field named {self.other_field_name} in form')
        if bool(other_field.data):
            super().__call__(form, field)


class AuthForm(FlaskForm):
    password = PasswordField('Password', validators=[
        InputRequired(message='You must provide a password')
        ])

class LoginForm(AuthForm):
    username = StringField('Username', validators=[
        InputRequired(message='You must provide a username')
        ])
    rememberMe = BooleanField('Remember me')

class RegisterForm(LoginForm):
    confirm = PasswordField(validators=[
        InputRequired(), 
        EqualTo('password', message='Your passwords must match')
        ])


class ChangePassForm(FlaskForm):
    oldpass = PasswordField(validators=[
        RequiredIf('newpass', message='You must input your old password to change it')
        ])
    newpass = PasswordField(validators=[
        RequiredIf('oldpass', message='You must input a new password to change it')
        ])
    confirm = PasswordField(validators=[
        EqualTo('newpass', message='Your password confirmation must match your new password')
        ])

class SubdomainSettingsForm(ChangePassForm):
    setauth = BooleanField('Require authentication', validators=[
        RequiredIf('oldpass', 
                   message='You cannot both change your password and turn off authentication'
                   )
        ])


class NewPassForm(FlaskForm):
    newpass = PasswordField(validators=[
        InputRequired(message='You must provide a password')
        ])
    confirm = PasswordField(validators=[
        EqualTo('newpass', message='Your password confirmation must match your new password')
        ])


class ModifyWorkForm(FlaskForm):
    newTitle = StringField(validators=[
        InputRequired(message='Your work must have a title')
        ])

class NewWorkForm(ModifyWorkForm):
    genres = RadioField(validators=[
        InputRequired(message='You must choose a genre')
        ])