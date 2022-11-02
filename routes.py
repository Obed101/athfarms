#!/usr/bin/env python
""" Routes Handler """
from faker import Faker
import random
import os
from flask_mail import Message
from models import Service, Subscriber, User, Article, File, Notice
from flask_login import login_required, login_user, logout_user, current_user
from flask import render_template, url_for, redirect, flash, request, send_from_directory
from utils import app, db, change_in_db, ckeditor, template, mail, article_mail
from forms import NewArticle, Request, SubscribeForm, UserForm, UploadFile, Search, Contact
from uuid import uuid4


template['subs'] = Subscriber.query.all()
template['users'] = User()
template['subs_no'] = len(template['subs'])
template['arts'] = Article.query.order_by(Article.id.desc()).all()
template['random'] = random
template['art'] = Article
template['services'] = Service.query.all()


@app.route('/')
def index():
    """Home page"""
    articles = Article.query.order_by(Article.id.desc()).all()
    return render_template('index.html', title='Home', articles=articles, template=template, str=str)


@app.errorhandler(404)
def not_found(_):
    """ Handles 404 error """
    return render_template('404.html', title='Page Not Found', template=template), 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs in a user"""
    if current_user.is_authenticated:
        flash('You are already logged in')
        return redirect(url_for('index'))
    form = UserForm()
    if form.is_submitted():
        user = User.query.filter_by(email=form.email.data).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, True)
        flash(f'Logged in as {current_user.fullname}')
        return redirect(request.args.get('next')) if request.args.get('next') else redirect(url_for('index'))
    return render_template('login.html', form=form, title='Login', template=template)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Creates a user account"""
    if current_user.is_authenticated:
        flash('You are already logged in')
        return redirect(url_for('index'))
    form = UserForm()
    if form.is_submitted():
        f = form.pic.data
        if f:
            _, fmt = os.path.splitext(f.filename)
            unique_name = str(uuid4()) + fmt
            path = os.path.join('static', 'img', unique_name)
            f.save(path)
        else:
            path = None
        exists = User.query.filter_by(email=form.email.data).first()
        if exists:
            flash('You already have an account')
            return redirect(url_for('index'))
        user = User(firstname=form.firstname.data, lastname=form.lastname.data, pic=path, email=form.email.data)
        user.password, user.fullname = user.set_password(form.password.data), user.set_fullname()
        db.session.add(user)
        db.session.commit()
        login_user(user, True)
        flash('Your account has been created')
        return redirect(url_for('index'))
    return render_template('signup.html', form=form, title='Create new account', template=template)


@app.route('/users')
@login_required
def users():
    """Returns all users"""
    if not current_user.admin:
        flash('You were redirected from an admin only page')
        return redirect(url_for('index'))
    number_of_users = User.query.count()
    users = User.query.order_by(User.admin.desc()).all()
    return render_template('users.html', users=users, title='All users', all=number_of_users, template=template)


@app.route('/users/receivers/<id>/add')
@login_required
def add_receiver(id):
    """Removes or adds a user's email to mailer list"""
    usr = User.query.filter_by(id=id).first()
    usr.add_to_receivers()
    return redirect(url_for('users'))


@app.route('/users/<int:id>/password/reset')
@login_required
def reset_password(id:int):
    """ Resets password for the user who matches `id` """
    user = User.query.filter_by(id=id).first()
    if current_user.admin:
        user.reset_password()
        db.session.commit()
        flash(f'You have reset {user.fullname}\'s password')
    else:
        flash(f'You don\'t have that permission')
        return redirect(url_for('index'))
    return redirect(url_for('users'))


@app.route('/users/new', methods=['POST', 'GET'])
@login_required
def add_user():
    """Create a new user"""
    if current_user.admin:
        user_form = UserForm()
        if user_form.is_submitted():
            user = User(firstname=user_form.firstname.data, lastname=user_form.lastname.data,
                             email=user_form.email.data, admin=user_form.admin.data)
            user.password, user.fullname = user.set_password('mm'), user.set_fullname()
            exists:User = User.query.filter_by(email=user.email).first()
            if exists and exists.admin:
                flash('That user is already an admin')
                return redirect(url_for('users'))
            exists.delete() if exists else print(end='')
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('users'))
    else:
        flash('You were redirected from an admin only page')
        return redirect(url_for('index'))
    return render_template('add_user.html', title='Add New User', form=user_form, template=template)


@app.route('/users/<id>/delete')
@login_required
def delete_user(id:int):
    try:
        going = User.query.filter_by(id=id).first()
        gone_name = going.fullname
        his_id = going.id
        if going:
            if current_user.admin:
                going.delete()
                flash(f'You have deleted {gone_name if not current_user.id == his_id else "yourself"} successfully')
            else:
                flash(f'You can\'t delete {gone_name if not current_user.id == his_id else "yourself"}')
    except AttributeError:
        flash('That user does not exist')
    return redirect(url_for('users'))


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    """ User Profile editor"""
    form = UserForm()
    if form.is_submitted():
        current_user.firstname = change_in_db(current_user.firstname, form.firstname.data)
        current_user.lastname = change_in_db(current_user.lastname, form.lastname.data)
        current_user.email = change_in_db(current_user.email, form.email.data)
        current_user.password = change_in_db(current_user.password, form.password.data)

        ######### Changing the profile picture if new one is selected
        f = form.pic.data
        if f:
            current_user.remove_pic()
            _, fmt = os.path.splitext(f.filename)
            unique_name = str(uuid4()) + fmt
            path = os.path.join('static', 'img', unique_name)
            f.save(path)
            current_user.pic = change_in_db(current_user.pic, path)
        db.session.commit()
        flash('Your profile has been updated')
        return redirect(url_for('index'))
    return render_template('profile.html', form=form, title='Your Profile', template=template)


@app.route('/logout')
def logout():
    """Logs out a user"""
    logout_user()
    flash('You have logged out')
    return redirect(url_for('index'))


@app.route('/messages')
@login_required
def messages():
    """Displays user messages"""
    if not current_user.admin:
        flash('You were redirected from an admin only page')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    notices = Notice.query.order_by(Notice.id.desc()).paginate(page, per_page=8)
    return render_template('messages.html', title='User messages', notices=notices, template=template)


@app.route('/messages/<id>/delete')
@login_required
def del_message(id:int):
    """Deletes a user message"""
    if current_user.admin:
        note = Notice.query.filter_by(id=id).first()
        note.delete() if note and current_user.admin else flash('Unable to delete message')
        db.session.commit()
        flash('Message deleted')
        return redirect(url_for('messages'))
    return redirect(url_for('index'))

@app.route('/contact', methods=('GET', 'POST'))
def contact():
    """Contact page with auto mailer"""
    subscribe = SubscribeForm()
    if subscribe.validate_on_submit():
        sub = Subscriber(name=subscribe.name.data, email=subscribe.email.data)
        db.session.add(sub)
        db.session.commit()
        template['subs'] = Subscriber.query.all()
        template['subs_no'] = len(template['subs'])
        flash(f"Thank you {subscribe.name.data}. {'You are done' if not current_user.is_active else 'Everything has been done in background'}. Find out more")
        return redirect(url_for('index'))
    users = User.query.filter(User.mail==True).all()
    form = Contact()
    if form.validate_on_submit():
        name,  email = current_user.fullname or form.name.data or 'Customer', current_user.email or form.email.data
        text = form.text.data.replace('\r\n', '<br>')
        with mail.connect() as conn:
            for user in users:
                message = f"""
Hello {user.firstname}, <br><br>
There is a new customer message from {name or email}.
Check it out immediately and take the required action.<br><br>
<i>Here is the message received:</i><hr><br>
{text} <hr>
Name: {name or 'Not provided'} <br>
Email: {email}<br><br>Best regards, <br>Athfarms <br><br><hr style='width:50%'>
<small><center>Athfarms &copy; All rights reserved</center></small>
"""
                subject = f"New Athfarms User Message"
                msg = Message(subject, sender=('Athfarms Customer Care', os.getenv('ansah_gmail')), recipients=[user.email], html=message)
                conn.send(msg)
            ###### Saving to the notices
            note = Notice(name=name or 'Customer', message=text, email=form.email.data)
            note.email = email
            db.session.add(note)
            db.session.commit()
        flash('Thank you. We received your message')
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form, title='Send us a message', template=template, subscribe=subscribe)


@app.route('/articles', methods=['GET', 'POST'])
def articles():
    """Opens the articles page ordered by newest first"""
    page = request.args.get('page', 1, type=int)
    form = Search()
    template['info'] = 'Select or search articles to read'
    if form.is_submitted() and form.search.data:
        query = form.search.data
        arts = Article.query.order_by(Article.id.desc()).msearch(query).paginate(page, per_page=5)
        count = len(arts.items)
        return render_template('articles.html', title='All articles', count=count, articles=arts,
                               template=template, form=form)

    articles = Article.query.order_by(
        Article.id.desc()).paginate(page, per_page=5)
    return render_template('articles.html', title='Articles', articles=articles,
                           template=template, form=form)


@app.route('/articles/new', methods=['GET', 'POST'])
@login_required
def new_article():
    """Route for creating a new article"""
    form = NewArticle()
    if form.is_submitted():
        """ Saving the cover image """
        f = form.cover.data
        _, fmt = os.path.splitext(f.filename)
        unique_name = str(uuid4()) + fmt
        full_path = os.path.join('static', 'img', unique_name)
        f.save(full_path)
        article = Article(subject=request.form.get('subject'),
                          message=request.form.get('ckeditor'),
                          category=form.category.data)
        article.user_id, article.cover, article.unique_name = current_user.id, full_path, unique_name
        db.session.add(article)
        db.session.commit()
        users = User.query.filter(User.mail==True).all()
        with mail.connect() as conn:
            for user in users:
                subject = f"New Athfarms Article"
                message = article_mail(user, article)
                msg = Message(subject, sender=('Articles', os.getenv('ansah_gmail')), recipients=[user.email], html=message)
                conn.send(msg)
        template['arts'] = Article.query.all()

        flash('You created a new article')
        return redirect(url_for('articles'))
    return render_template('new_article.html', form=form, title='Add New Article', template=template)


@app.route('/articles/cover/<unique_name>')
def display_image(unique_name:str):
    """Displays an article's cover image"""
    pth = os.path.join('static', 'img')
    return send_from_directory(pth, unique_name)


@app.route('/articles/<id>/view')
def view_article(id:int):
    """Opens an article"""
    article = Article.query.filter_by(id=id).first()
    f_type = article.cover.split('.')[-1]
    article.views = article.views + 1 if article.views else 1
    db.session.commit()
    return render_template('view_article.html', title=article.subject, article=article, f_type=f_type, template=template)


@app.route('/articles/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(id:int):
    """Edits an already posted article"""
    form = NewArticle()
    art = Article.query.filter_by(id=id).first()
    if form.is_submitted():
        art.subject = change_in_db(art.subject, form.subject.data)
        art.message = change_in_db(art.message, request.form.get('ckeditor'))
        f = form.cover.data
        if f:
            art.remove_cover()
            _, fmt = os.path.splitext(f.filename)
            unique_name = str(uuid4()) + fmt
            path = os.path.join('static', 'img', unique_name)
            f.save(path)
            art.cover = change_in_db(art.cover, path)
        db.session.commit()
        template['arts'] = Article.query.order_by(Article.id.desc()).all()
        flash('Your change is saved successfully')
        return redirect(url_for('articles'))
    return render_template('edit_article.html', title='Edit Article', article=art, form=form, template=template)


@app.route('/articles/categories/<category>', methods=['GET', 'POST'])
def article_categories(category:str):
    """Returns the articles in the specified `category`"""
    page = request.args.get('page', 1)
    form = Search()
    template['info'] = f'Articles on {category.replace("_", " ").capitalize()}s'
    if form.is_submitted():
        query = form.search.data
        arts = Article.query.order_by(Article.id.desc()).msearch(query).paginate(page, per_page=5)
        count = len(arts.items)
        return render_template('articles.html', title='All articles', count=count, articles=arts,
                               template=template, form=form)
    articles = Article.query.filter_by(category=category).order_by(
                                    Article.id.desc()).paginate(page, per_page=5)
    return render_template('articles.html', title=category.replace('_', ' ')+'s',
                           template=template, articles=articles, form=form)


@app.route('/articles/<id>/delete')
@login_required
def del_article(id:int):
    """Deletes an article if priveleges are met"""
    try:
        article = Article.query.filter_by(id=id).first()
        if article.user_id == current_user.id or current_user.admin:
            article.remove_cover()
            article.delete()
            db.session.commit()
        else:
            flash('You cannot delete that article')
            return redirect(url_for('articles'))
    except AttributeError:
        flash('That article doesn\'t exist anymore')
        return redirect(url_for('articles'))
    flash('Article deleted successfully')
    return redirect(url_for('articles'))


@app.route('/services', methods=['GET', 'POST'])
def services():
    """Services page"""
    new = Contact()
    if new.validate_on_submit():
        if current_user.admin:
            service = Service(name=new.name.data, description=new.text.data.replace('\r\n', '<br>'))
            db.session.add(service)
            db.session.commit()
            template['services'] = Service.query.all()
            flash('Your services is created')
        else:
            flash('You don\'nt have that access')
        return redirect(url_for('services'))
    return render_template('services.html', title='Services', template=template, new=new, request=Request())


@app.route('/services/<id>/request', methods=['GET', 'POST'])
def request_service(id:int):
    """Requesting a service"""
    request = Request()
    service_name = Service.query.filter_by(id=id).first().name
    if request.validate_on_submit():
        req = Notice(name=request.name.data, email=request.email.data)
        message = f"""
<h5>Requesting a service.</h5>
Type: <b>{service_name}</b><br>
Name: {request.name.data}<br>
Phone: {request.tel.data}<br>
Email: {request.email.data}<br>
Proposed date: {request.date.data or 'Not provided'}<br>
Location: {request.loc.data}<br><br>
Contact him as soon as possible
"""
        req.message = message
        db.session.add(req)
        db.session.commit()
        flash('Your request has been received. You will be contacted soon')
        return redirect(url_for('services'))
    return render_template('services.html', title='Services', template=template, new=Contact(), request=request, srv=service_name)


@app.route('/services/<id>/delete')
@login_required
def del_service(id:int):
    """Deletes a service if priveleges are met"""
    try:
        service = Service.query.filter_by(id=id).first()
        if current_user.admin:
            service.delete()
            db.session.commit()
            template['services'] = Service.query.all()
        else:
            flash('You cannot delete that service')
            return redirect(url_for('services'))
    except AttributeError:
        flash('That service doesn\'t exist anymore')
        return redirect(url_for('services'))
    flash('Service deleted successfully')
    return redirect(url_for('services'))


@app.route('/files/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Returns upload file page"""
    form = UploadFile()
    if form.is_submitted():
        f = form.content.data
        category = form.category.data
        o_name = form.f_name.data or f.filename.split('.')[0]
        _, extention = os.path.splitext(f.filename)
        unique_name = str(uuid4())
        f_path = os.path.join('static', category, unique_name + extention)
        f.save(f_path)
        file = File(user_id=current_user.id, original_name=o_name, u_name=unique_name,
                    f_type=category, path=f_path, fmt=extention[1:], message=form.message.data)
        db.session.add(file)
        db.session.commit()
        template['files'] = File
        flash(f'Your file has been saved')
        return redirect(url_for('gallery', category=category))
    return render_template('upload_file.html', title='Upload a File', form=form, template=template)


@app.route('/gallery')
def gallery():
    """Return Gallery for images and videos"""
    template['files'] = File
    return render_template('gallery.html', title='Gallery', template=template)


@app.route('/gallery/<category>/<id>/delete')
@login_required
def delete_file(category:str, id:int):
    """Deletes a file if priveleges are met"""
    try:
        file = File.query.filter_by(id=id, f_type=category).first()
        if current_user.admin:
            file.delete()
            db.session.commit()
            template['files'] = File
        else:
            flash('You cannot delete the file')
            return redirect(url_for('galley'))
    except AttributeError:
        flash('That file doesn\'t exist anymore')
        return redirect(url_for('gallery'))
    flash('File deleted successfully')
    return redirect(url_for('gallery'))


@app.route('/subs/<id>/delete')
@login_required
def del_subscriber(id:int):
    """Deletes a subscriber"""
    going = Subscriber.query.filter_by(id=id).first()
    if going:
        going.delete()
        db.session.commit()
        template['subs'] = Subscriber.query.all()
        template['subs_no'] = len(template['subs'])
        flash(f'The subscriber is removed')
    else:
        flash('User does not exist')
    return redirect('/users#subs')


# note = Notice(subject='A new Notice for testing',
#               message='This is the sample notice message <br> New notices will display like this')
# db.session.add(note) if 1 == random.randint(1, 19) else print()
# db.session.commit()

fake = Faker()

# u = User(firstname=fake.first_name(), lastname=fake.last_name(), email=fake.email())
# u.password, u.fullname = u.set_password('mm'), u.set_fullname())
# db.session.add(u)
# db.session.commit()


if __name__ == '__main__':
    app.run()
