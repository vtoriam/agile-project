from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, StringField
from wtforms.validators import AnyOf, DataRequired, Email, EqualTo, Length


ALLOWED_AVATARS = (
    "user-round",
    "cat",
    "dog",
    "bird",
    "fish",
    "rabbit",
    "bug",
    "turtle",
    "squirrel",
    "snail",
)

class SignupForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    display_name = StringField('Display Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])


class LoginForm(FlaskForm):
    class Meta:
        csrf = False

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class EditProfileForm(FlaskForm):
    display_name = StringField(
        "Display Name",
        validators=[DataRequired(), Length(max=80)],
    )
    avatar = StringField(
        "Avatar",
        validators=[DataRequired(), AnyOf(ALLOWED_AVATARS)],
    )


class CreateHouseholdForm(FlaskForm):
    household_name = StringField(
        "Household Name",
        validators=[DataRequired(), Length(max=100)],
    )


class JoinHouseholdForm(FlaskForm):
    join_code = StringField(
        "Invite Code",
        validators=[DataRequired(), Length(max=20)],
    )


class SwitchHouseholdForm(FlaskForm):
    household_id = HiddenField(validators=[DataRequired()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
