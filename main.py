import difflib
import os
import time
from os import listdir
from os.path import isfile, join
from datetime import datetime

from flask import Flask, render_template, request
from flask_wtf.form import FlaskForm
from flask_wtf.file import FileField
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_uploads import configure_uploads, IMAGES, UploadSet, UploadNotAllowed

from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from wtforms.fields import (PasswordField, StringField, SubmitField,
                            BooleanField, TextAreaField, SelectField)
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from data import db_session
from data.users import User
from data.articles import Article
from data.images import Image


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOADED_IMAGES_DEST'] = basedir + '/static/img/users'
login_manager = LoginManager()
login_manager.init_app(app)


photos = UploadSet('images', IMAGES)
configure_uploads(app, photos)
class RegisterForm(FlaskForm):
    email = EmailField('Email*', validators=[DataRequired()])
    password = PasswordField('Пароль*', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль*', validators=[DataRequired()])
    surname = StringField("Фамилия*", validators=[DataRequired()])
    name = StringField('Имя*', validators=[DataRequired()])
    photo = FileField("Фотография")
    submit = SubmitField('Сохранить')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class ChangeLevelForm(FlaskForm):
    choices = [('2'), ('3')]
    levels = SelectField('Уровень доступа:', choices=choices)
    submit = SubmitField('Сохранить')


class ArticleForm(FlaskForm):
    title = StringField("Название")
    text = TextAreaField("Текст новости")
    keywords = StringField("Ключевые слова")
    submit = SubmitField("Сохранить")


class ArticleSearchForm(FlaskForm):
    choices = [('Все', 'Все'),
               ('Мои', 'Мои')]
    select = SelectField('Поиск только:', choices=choices)
    search = StringField('Поиск по словам:')
    choices = [('', ''),
               ('Дата добавления (сначала свежее)', 'Дата добавления (сначала свежее)'),
               ('Дата добавления (сначала старее)', 'Дата добавления (сначала старее)'),
               ('Дата обновления (сначала свежее)', 'Дата обновления (сначала свежее)'),
               ('Дата обновления (сначала старее)', 'Дата обновления (сначала старее)')]
    sorting = SelectField('Соритровка: ', choices=choices)
    submit = SubmitField("Поиск")


def get_articles(params=None) -> list:
    db_sess = db_session.create_session()
    articles = db_sess.query(Article).all()
    if params:
        for article in articles:
            if params[0] == 'Мои' and current_user:
                if article.user != current_user:
                    articles.remove(article)
                    continue
            if not params[1].lower() in article.title.lower() and not \
                    params[1].lower() in article.text.lower():
                articles.remove(article)
                continue
    if params:
        if params[2] == 'Дата добавления (сначала свежее)':
            articles.sort(key=lambda article: article.add_date)
            articles = articles[::-1]
        elif params[2] == 'Дата добавления (сначала старее)':
            articles.sort(key=lambda article: article.add_date)
        elif params[2] == 'Дата обновления (сначала свежее)':
            articles.sort(key=lambda article: article.modified_date)
            articles = articles[::-1]
        elif params[2] == 'Дата обновления (сначала старее)':
            articles.sort(key=lambda article: article.modified_date)
    return articles

def get_users() -> list:
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return users

def similarity(s1, s2):
    normalized1 = ''.join(sym for sym in s1.lower() if sym.isalnum())
    normalized2 = ''.join(sym for sym in s2.lower() if sym.isalnum())
    matched = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matched.ratio()

def get_last_file_name():
    min_date = None
    file_with_min_date = None
    for file in listdir(f'{basedir}/static/img/users'):
        current_time = time.ctime(os.path.getmtime(f'{basedir}/static/img/users/{file}'))
        if not min_date or current_time < min_date:
            min_date = current_time
            file_with_min_date = file
    return file_with_min_date


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ArticleSearchForm()
    articles = get_articles()
    if request.method == 'POST':
        articles = get_articles([form.select.data, form.search.data, form.sorting.data])
        return render_template('index.html', articles=articles, form=form)
    return render_template('index.html', articles=articles, form=form)


@app.route('/users')
def users():
    users = get_users()
    return render_template('users.html', users=users)


@app.route('/users/<int:id>/change', methods=['POST', 'GET'])
def user(id):
    form = RegisterForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id).first()
        if user:
            form.surname.data = user.surname
            form.name.data = user.name
            form.email.data = user.email
        else:
            abort(404)
    if request.method == 'POST':
        db_sess = db_session.create_session()
        such_email = db_sess.query(User).filter(User.email == form.email.data).first()
        if such_email and such_email != current_user:
            return render_template('register.html', title='Редактирование данных пользователя',
                                   form=form,
                                   message="Почта занята")
        user = db_sess.query(User).filter(User.id == id).first()
        if user:
            user.surname = form.surname.data
            user.name = form.name.data
            user.email = form.email.data
            photo = form.photo.data
            if photo:
                image = Image()
                db_sess.add(image)
                result = db_sess.query(Image).all()[-1]
                try:
                    filename = photos.save(form.photo.data)
                    os.rename(f'{basedir}/static/img/users/{filename}',
                              f'{basedir}/static/img/users/{result}')
                    if user.image.id != 1:
                        os.remove(f'{basedir}/static/img/users/{user.image}')
                        db_sess.delete(user.image)
                    user.image = result
                except UploadNotAllowed:
                    db_sess.delete(result)
                    return render_template('register.html', title='Регистрация',
                                           form=form, message='Не допустимый формат файла')
            date = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")).split()
            ymd = [int(element) for element in date[0].split('-')]
            hms = [int(element) for element in date[1].split(':')]
            user.modified_date = datetime(*ymd, *hms)
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template("register.html", title="Редактирование данных пользователя", form=form)


@app.route('/users/<int:id>/change_level', methods=['POST', 'GET'])
def user_change_level(id):
    form = ChangeLevelForm()
    if request.method == 'GET':
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id).first()
        if user:
            form.levels.data = str(user.level)
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id).first()
        if user:
            user.level = int(form.levels.data)
            print(user.level)
            db_sess.commit()
        else:
            abort(404)
        return redirect('/users')
    return render_template('change_level.html', title="Изменение уровня доступа", form=form)


@app.route('/users/<int:id>/delete')
def user_delete(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if user.image.id != 1:
        os.remove(f'{basedir}/static/img/users/{user.image}')
    db_sess.delete(user)
    db_sess.commit()
    return redirect('/users')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        email = form.email.data
        user = User(
            surname=form.surname.data,
            name=form.name.data,
            email=email

        )
        date = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")).split()
        ymd = [int(element) for element in date[0].split('-')]
        hms = [int(element) for element in date[1].split(':')]
        user.registrated_date = datetime(*ymd, *hms)
        user.modified_date = datetime(*ymd, *hms)
        user.set_password(form.password.data)
        photo = form.photo.data
        if photo:
            image = Image()
            db_sess.add(image)
            result = db_sess.query(Image).all()[-1]
            try:
                filename = photos.save(form.photo.data)
                os.rename(f'{basedir}/static/img/users/{filename}',
                          f'{basedir}/static/img/users/{result}')
                user.image = result
            except UploadNotAllowed:
                db_sess.delete(result)
                return render_template('register.html', title='Регистрация',
                                       form=form, message='Не допустимый формат файла')
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/articles', methods=['GET', 'POST'])
def articles_add():
    form = ArticleForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        # job = Job()
        article = Article()
        article.title = form.title.data
        article.text = form.text.data
        article.keywords = form.keywords.data
        article.user = current_user
        db_sess.merge(article)
        db_sess.commit()
        return redirect('/')
    return render_template("add_article.html", title="Добавление статьи", form=form)


@app.route('/articles/<int:id>', methods=['GET', 'POST'])
def article_show(id):
    form = ArticleForm()
    db_sess = db_session.create_session()
    article = db_sess.query(Article).filter(Article.id == id).first()
    articles = get_articles()
    such_articles = []
    if article:
        form.title.data = article.title
        form.keywords.data = article.keywords
        form.text.data = article.text

        title = article.title
        text = article.text
        for art in articles:
            if art.id == article.id:
                continue
            result = similarity(title, art.title)
            if result >= 0.5:
                such_articles.append((art, result))
                continue
            result = similarity(text, art.text)
            if result >= 0.5:
                such_articles.append((art, result))
        such_articles.sort(key=lambda x: x[1])
        such_articles = such_articles[:min(len(such_articles), 5)]
    else:
        abort(404)
    return render_template("article.html", title=f"{form.title.data}", form=form,
                           article=article, such_articles=such_articles)


@app.route('/articles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def articles_edit(id):
    form = ArticleForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        article = db_sess.query(Article).filter(Article.id == id, Article.user == current_user).first()
        if article:
            form.title.data = article.title
            form.keywords.data = article.keywords
            form.text.data = article.text
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        article = db_sess.query(Article).filter(Article.id == id, Article.user == current_user).first()
        if article:
            article.title = form.title.data
            article.keywords = form.keywords.data
            article.text = form.text.data
            article.modified_date = datetime.now()
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template("add_article.html", title="Редактирование статьи", form=form)


@app.route('/articles/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def articles_delete(id):
    db_sess = db_session.create_session()
    if current_user.level < 3:
        article = db_sess.query(Article).filter(Article.id == id).first()
    else:
        article = db_sess.query(Article).filter(Article.id == id, Article.user == current_user).first()
    if article:
        db_sess.delete(article)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.run(port=8080, host='127.0.0.1')
