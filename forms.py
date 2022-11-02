from wtforms import StringField, SubmitField, PasswordField, RadioField, SearchField, TextAreaField, BooleanField, IntegerField, DateField
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired as required, Length, EqualTo
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField, FileRequired


class UserForm(FlaskForm):
    """A form for taking user details for login, signup, etc."""
    firstname = StringField('Your first name', [required()])
    lastname = StringField('Your last name', [required()])
    email = StringField('Your email', [required()])
    tel = StringField('Your phone number', [Length(10, 12, 'Number is invalid')])
    password = PasswordField('Your password')
    pic = FileField('Profile image')
    admin = BooleanField('He is an Administrator', default=False)
    confirm = PasswordField('Type your password again', [EqualTo('password')])
    submit = SubmitField()

class Request(FlaskForm):
    """Creates and validates message"""
    id = IntegerField()
    email = SearchField('Your Email Address', [required()])
    name = StringField('Your name', [required()])
    tel = IntegerField('Your Phone', [required()])
    date = DateField()
    loc = StringField('Location. Ex: Lapas, Accra, G/A, Ghana', [required()])
    submit = SubmitField('Send')

class Contact(FlaskForm):
    """Creates and validates message"""
    email = SearchField('Your Email Address')
    name = StringField()
    text = TextAreaField('Enter your message', [required()])
    submit = SubmitField('Submit Message')

class SubscribeForm(FlaskForm):
    """Creates and validates message"""
    email = StringField('Your Email Address', [required()])
    name = StringField()
    submit = SubmitField('Done')

class NewArticle(FlaskForm):
    """Creates a post form"""
    subject = StringField('Enter your post title')
    message = CKEditorField()
    category = StringField(validators=[required()])
    submit = SubmitField()
    cover = FileField('Cover image')


class UploadFile(FlaskForm):
    """File Upload Form"""
    category = RadioField('Select the file type', [required()],
    choices=[('img', 'Image'), ('vid', 'Video')])
    content = FileField('Cover image', [FileRequired('You must select a file')],)
    f_name = StringField('Title')
    message = TextAreaField('Describe the file')
    submit = SubmitField()


class Search(FlaskForm):
    search = SearchField()
    submit = SubmitField()
