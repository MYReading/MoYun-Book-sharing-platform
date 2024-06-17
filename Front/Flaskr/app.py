import statistics
import datetime

from flask import Flask, redirect, url_for, request, flash, abort, session
from flask import Flask, render_template
from sqlalchemy.sql.functions import now

from Front.Flaskr.form import RegistrationForm, LoginForm, ReviewForm, CommentForm, BookForm_add, BookForm_modify, \
    CircleForm, PostForm, AddUserForm, ReplyForm
from Service.Database.DAO import Database
from Service.Database.Model import Book, GroupDiscussionReply

app=Flask(__name__)
app.secret_key='114514'

Database()

#登录页
@app.route('/login',methods=['GET','POST'])
def login():
    #如果有session直接跳主页(未写)
    form=LoginForm()
    if request.method=='POST':
        id = Database.checkLogin(request.form['username'], request.form['password'])
        role=request.form['role']
        userdata=Database.checkUser(request.form['username'], request.form['password'])

        if id and role==userdata['role']:
            if str(role)=='student':
                session['email'] = userdata['email']
                session['id'] = userdata['id']
                session['signature'] = userdata['signature']
                session['telephone'] = userdata['telephone']
                session['username'] = request.form['username']
                session['role']='student'
                return redirect(url_for('studentpage'))

            elif str(role)=='teacher':
                session['email'] = userdata['email']
                session['id'] = userdata['id']
                session['signature'] = userdata['signature']
                session['telephone'] = userdata['telephone']
                session['username'] = request.form['username']
                session['role'] = 'teacher'
                return redirect(url_for('teacherpage'))


            elif str(role)=='admin':
                session['email'] = userdata['email']
                session['id'] = userdata['id']
                session['signature'] = userdata['signature']
                session['telephone'] = userdata['telephone']
                session['username'] = request.form['username']
                session['role'] = 'admin'
                return redirect(url_for('adminpage'))
        else:
            error='错误的用户名或密码'
            return render_template("login.html",form=form,error=error)
    elif request.method=='GET':
        return render_template("login.html",form=form,error=None)

#注册页
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if request.method=='POST':
        if form.validate()==False:
            flash('请填写完整')
            return render_template('register.html',form=form)
        else:
            Database.addUser(account=request.form['username'],raw_password=request.form['password']
                             ,email=request.form['email'],telephone=request.form['phone'],role=str(request.form['role']))
            return redirect(url_for('login'))
    elif request.method=='GET':
        return render_template('register.html',form=form)

#教师身份进入的主页
@app.route('/teacherpage')
def teacherpage():
    if session['role']=='student':
        return redirect(url_for('studentpage'))
    else:
        return render_template('teacherpage.html')

#学生身份进入的主页
@app.route('/studentpage')
def studentpage():
    if session['role']!='student':
        return redirect(url_for('teacherpage'))
    else:
        return render_template('studentpage.html')

#
@app.route('/user_detail')
def user_detail():
    return render_template('user_detail.html')

@app.route('/user_detail/edituser')
def edit_user():
    return render_template('deit_user.html')


#学生身份进入的图书总页，其他身份也可进入
@app.route('/bookspage',methods=['GET', 'POST'])
def bookspage():
    books=Database.getAllBooks(self=None)
    return render_template('bookspage.html',books=books)

#书籍详细信息
@app.route('/<book_title>', methods=['GET', 'POST'])
def book_detail(book_title):
    form=ReviewForm()
    if request.method=='POST':
        book=Database.getBook(1,title=book_title)
        Database.addJournal(title=request.form['review_title'], content=request.form['review_content'] ,publish_time=datetime.datetime.now(),author_id=session['id'],book_id=book['id'])
        return redirect(url_for('book_detail',book_title=book_title,form=form))
    elif request.method=='GET':
        books = Database.getAllBooks(self=None)
        book = next((b for b in books if b['title'] == book_title), None)
        if book is None:
            return "Book not found", 404
        reviews = Database.getJournal(0, book_id=book['id'])  # Dummy reviews
        return render_template('book_detail.html', book=book, reviews=reviews,form=form,book_title=book_title)

#评论的点赞功能
@app.route('/review/<int:review_id>/like',methods=['GET','POST'])
def review_like(review_id):
    if request.method=='POST':
        Database.addJournalLike(review_id,session['id'])
        return redirect(url_for('review_detail',review_id=review_id))

#评论的详细信息
@app.route('/review/<int:review_id>',methods=['GET','POST'])
def review_detail(review_id):
    form=CommentForm()
    if request.method=='POST':
        Database.addJournalComment(journal_id=review_id,content=request.form['content'],author_id=session['id'],publish_time=datetime.datetime.now())
        return redirect(url_for('review_detail',review_id=review_id,form=form))
    elif request.method=='GET':
        # review = Database.session.query(Review).get(review_id)
        review = Database.getJournal(1, id=review_id)
        follow_reviews = Database.getJournalComments(journal_id=review_id)
        likes = Database.getJournalLikesNum(review_id)
        return render_template('review_detail.html', review=review, followreviews=follow_reviews, likes=likes,form=form)

#教师身份进入的图书页
@app.route('/teacherpage/teacherbookspage')
def teacherbookpage():
    if session['role']=='student':
        return redirect(url_for('studentpage'))
    books = Database.getAllBooks(self=None)
    return render_template('teacherbookpage.html',books=books)

#教师的图书页面
@app.route('/teacherpage/teacherbookspage/bookdetail/<book_title>',methods=['GET','POST'])
def book_detail_teacher(book_title):
    form=ReviewForm()
    if request.method=='POST':
        book=Database.getBook(1,title=book_title)
        Database.addJournal(title=request.form['review_title'], content=request.form['review_content'] ,publish_time=datetime.datetime.now(),author_id=session['id'],book_id=book['id'])
        return redirect(url_for('book_detail_teacher',book_title=book_title,form=form))
    elif request.method=='GET':
        books = Database.getAllBooks(self=None)
        book = next((b for b in books if b['title'] == book_title), None)
        if book is None:
            return "Book not found", 404
        reviews = Database.getJournal(0, book_id=book['id'])  # Dummy reviews
        return render_template('book_detail_teacher.html', book=book, reviews=reviews,form=form,book_title=book_title)

#教师删除书评
@app.route('/teacherpage/teacherbookspage/bookdetail/<book_title>/<review_id>')
def delete_review(review_id,book_title):
    if session=='student':
        return redirect(url_for('studentpage'))
    Database.deleteJournal(Journal_id=review_id)
    return redirect(url_for('book_detail_teacher',book_title=book_title))


#/+增删改图书
#添加图书
@app.route('/teacherpage/teacherbookspage/addbook',methods=['GET','POST'])
def add_book():
    if session['role']=='student':
        return redirect(url_for('studentpage'))
    form=BookForm_add()
    if request.method=='POST':
        Database.addBook(isbn=request.form['isbn']
                         ,title=request.form['title']
                         ,origin_title=request.form['origin_title']
                         ,subtitle=request.form['subtitle']
                         ,author=request.form['author']
                         ,page=request.form['pages']
                         ,publish_date=request.form['publish_date']
                         ,publisher=request.form['publisher']
                         ,description=request.form['description']
                         ,type=request.form['type'])
        return redirect(url_for('teacherbookpage'))
    elif request.method=='GET':
        return render_template('add_book.html', form=form)

#删除图书
@app.route('/teacherpage/teacherbookspage/deletebook/<int:book_id>')
def delete_book(book_id):
    if session['role']=='student':
        return redirect(url_for('studentpage'))
    Database.deleteBook(book_id)
    return redirect(url_for('teacherbookpage'))

#修改图书
@app.route('/teacherpage/teacherbookspage/editbook/<int:book_id>',methods=['GET','POST'])
def edit_book(book_id):
    if session['role']=='student':
        return redirect(url_for('studentpage'))
    form=BookForm_modify()
    book=Database.getBook(limit=1,id=book_id)
    if request.method=='POST':
        Database.modifyBook(book_id=book_id,
                            isbn=request.form['isbn']
                            , title=request.form['title']
                            , origin_title=request.form['origin_title']
                            , subtitle=request.form['subtitle']
                            , author=request.form['author']
                            , page=request.form['pages']
                            , publish_date=request.form['publish_date']
                            , publisher=request.form['publisher']
                            , description=request.form['description']
                            , type=request.form['type'])
        return redirect(url_for('teacherbookpage'))
    elif request.method=='GET':
        return render_template('edit_book.html',book=book,form=form)

#学生身份的圈子页面
@app.route('/studentpage/mygroup')
def mygroup_student():
    if session['role']!='student':
        return redirect(url_for(mygroup_teacher))
    groups=Database.getGroupbyuser(session['id'])
    return render_template('mygroup_student.html',user_email=session['email'],user_name=session['username'],groups=groups)



#教师身份的圈子页面
@app.route('/teacherpage/mygroup')
def mygroup_teacher():
    if session['role']=='student':
        return redirect(url_for(mygroup_student))
    groups=Database.getGroupbyuser(session['id'])
    return render_template('mygroup_teacher.html',user_email=session['email'],user_name=session['username'],groups=groups)

#教师创建圈子
@app.route('/teacherpage/mygroup/addgroup',methods=['GET','POST'])
def add_group():
    if session['role'] == 'student':
        return redirect(url_for(mygroup_student))
    if request.method=='POST':
        group_id=Database.addGroup(name=request.form['circle_name'],description=request.form['circle_description'],founder_id=session['id'],establish_time=datetime.datetime.now())
        Database.addUsertoGroup(user_id=session['id'],group_id=group_id,send_time=datetime.datetime.now())
        return redirect(url_for('mygroup_teacher'))
    elif request.method=='GET':
        form=CircleForm()
        return render_template('add_group.html',form=form)



#学生的圈子详细信息
@app.route('/studentpage/mygroup/<int:group_id>',methods=['GET','POST'])
def group_detail_student(group_id):
    form = PostForm()
    if request.method == 'POST':
        Database.addGroupDiscussion(poster_id=session['id'], group_id=group_id, post_time=datetime.datetime.now(),
                                    title=request.form['title'], content=request.form['content'])
        return redirect(url_for('group_detail_student', group_id=group_id))
    elif request.method == 'GET':
        group = Database.getGroup(limit=1, id=group_id)
        posts = Database.getGroupDiscussion(limit=-1, group_id=group_id)
        users = Database.getUserbyGroup(group_id=group_id)
        return render_template('group_detail_student.html', group_name=group['name'], posts=posts, form=form,
                               group_id=group_id, users=users)

#教师的圈子详细信息
#删除圈子，帖子，学生未实现
@app.route('/teacherpage/mygroup/<int:group_id>',methods=['GET','POST'])
def group_detail_teacher(group_id):
    #未实现post删除功能
    form=PostForm()
    if request.method=='POST':
        Database.addGroupDiscussion(poster_id=session['id'],group_id=group_id,post_time=datetime.datetime.now(),title=request.form['title'],content=request.form['content'])
        return redirect(url_for('group_detail_teacher',group_id=group_id))
    elif request.method=='GET':
        group = Database.getGroup(limit=1, id=group_id)
        posts = Database.getGroupDiscussion(limit=-1, group_id=group_id)
        users=Database.getUserbyGroup(group_id=group_id)
        return render_template('group_detail_teacher.html', group_name=group['name'], posts=posts, form=form,
                               group_id=group_id,users=users)

#教师添加学生
@app.route('/teacherpage/mygroup/<int:group_id>/addstudent',methods=['GET','POST'])
def addstudent_togroup(group_id):
    form=AddUserForm()
    if request.method=='POST':
        users=Database.getUser(limit=-1,account=request.form['username'])
        return render_template('add_student.html',form=form,users=users,group_id=group_id)
    elif request.method=='GET':
        return render_template('add_student.html', form=form,users=None,group_id=group_id)

#添加学生到圈子的函数的子函数
@app.route('/teacherpage/mygroup/addstudent/<int:user_id>/<int:group_id>')
def add_student(user_id,group_id):
    Database.addUsertoGroup(user_id=user_id,group_id=group_id,send_time=datetime.datetime.now())
    return redirect(url_for('addstudent_togroup',group_id=group_id))


@app.route('/studentpage/postpage/<int:post_id>',methods=['GET','POST'])
def post_detail_student(post_id):
    form=ReplyForm()
    if request.method=='POST':
        Database.addGroupDiscussionReply(author_id=session['id'],discussion_id=post_id,content=request.form['content'],reply_time=datetime.datetime.now())
        return redirect(url_for('post_detail_student',post_id=post_id))
    elif request.method=='GET':
        authorpost = Database.getGroupDiscussion(limit=1, id=post_id)
        author = Database.getUser(limit=1, id=authorpost['poster_id'])
        replies = Database.getGroupDiscussionReplies(limit=-1, discussion_id=post_id)
        sorted_replies = sorted(replies, key=lambda x: x['reply_time'])
        # 替换回复中的 author_id 为 用户名
        for reply in sorted_replies:
            reply_author = Database.getUser(limit=1, id=reply['author_id'])
            reply['author_id'] = reply_author['account']
        return render_template('post_detail_student.html', form=form, author=author, authorpost=authorpost,
                               replies=sorted_replies)



@app.route('/teacherpage/postpage/<int:post_id>',methods=['GET','POST'])
def post_detail_teacher(post_id):
    form=ReplyForm()
    if request.method=='POST':
        Database.addGroupDiscussionReply(author_id=session['id'],discussion_id=post_id,content=request.form['content'],reply_time=datetime.datetime.now())
        return redirect(url_for('post_detail_teacher',post_id=post_id))
    elif request.method=='GET':
        authorpost = Database.getGroupDiscussion(limit=1, id=post_id)
        author = Database.getUser(limit=1, id=authorpost['poster_id'])
        replies = Database.getGroupDiscussionReplies(limit=-1, discussion_id=post_id)
        sorted_replies = sorted(replies, key=lambda x: x['reply_time'])
        # 替换回复中的 author_id 为 用户名
        for reply in sorted_replies:
            reply_author = Database.getUser(limit=1, id=reply['author_id'])
            reply['author_id'] = reply_author['account']
        return render_template('post_detail_teacher.html', form=form, author=author, authorpost=authorpost,
                               replies=sorted_replies)


if __name__ == '__main__':
    app.run(debug=True,threaded=True)