from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextField, TextAreaField, SubmitField, DateField
from wtforms.validators import InputRequired, EqualTo, Email, DataRequired, Length


class LoginForm(FlaskForm):
    role = SelectField('Role', choices=[('teacher', 'Teacher'), ('student', 'Student'), ('admin', 'Administrator')], validators=[InputRequired()])
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

class RegistrationForm(FlaskForm):
    role = SelectField('Role', choices=[('teacher', 'Teacher'), ('student', 'Student')], validators=[InputRequired()])
    username = TextField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password', message='确认密码与密码不符')])
    email = StringField('Email', validators=[InputRequired(), Email()])
    phone = StringField('Phone')

class ReviewForm(FlaskForm):
    review_title = StringField('Review Title', validators=[DataRequired()])
    review_content = TextAreaField('Review Content', validators=[DataRequired()])
    submit = SubmitField('Submit Review')


class CommentForm(FlaskForm):
    content=TextAreaField('Review Content', validators=[DataRequired()])

class BookForm_add(FlaskForm):
    isbn = StringField('ISBN', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    origin_title = StringField('Origin Title')
    subtitle = StringField('Subtitle')
    author = StringField('Author', validators=[DataRequired()])
    pages = StringField('Pages')
    publish_date =DateField('Publishtime', format='%Y-%m-%d', default=datetime.now())
    publisher = StringField('Publisher')
    description =TextField('Description')
    type = SelectField('Type', choices=[
        ('哲学、宗教'),('社会科学总论'),('政治、法律'),('军事'),('经济'),('文化、科学、教育、体育'),
        ('语言、文字'),('文学'),('艺术'),('历史、地理'),('自然科学总论'),('数理科学与化学'),('天文学、地理科学'),
        ('生物科学'),('医药、卫生'),('农业科学'),('工业技术'),('交通运输'),('航空、航天'),('环境科学、安全科学'),('综合性图书')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit')

class BookForm_modify(FlaskForm):
    isbn = StringField('ISBN', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    origin_title = StringField('Origin Title')
    subtitle = StringField('Subtitle')
    author = StringField('Author', validators=[DataRequired()])
    pages = StringField('Pages')
    publish_date = DateField('Publishtime', format='%Y-%m-%d')
    publisher = StringField('Publisher')
    description =TextField('Description')
    type = SelectField('Type', choices=[
        ('哲学、宗教'), ('社会科学总论'), ('政治、法律'), ('军事'), ('经济'), ('文化、科学、教育、体育'),
        ('语言、文字'), ('文学'), ('艺术'), ('历史、地理'), ('自然科学总论'), ('数理科学与化学'), ('天文学、地理科学'),
        ('生物科学'), ('医药、卫生'), ('农业科学'), ('工业技术'), ('交通运输'), ('航空、航天'), ('环境科学、安全科学'), ('综合性图书')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit')

class CircleForm(FlaskForm):
    circle_name = StringField('圈子名称', validators=[DataRequired(), Length(max=100)])
    circle_description = TextAreaField('圈子描述', validators=[DataRequired(), Length(max=500)])

class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired()])
    content = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('发布')

class AddUserForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    submit = SubmitField('搜索')

class ReplyForm(FlaskForm):
    content = TextAreaField('内容', validators=[DataRequired()])
