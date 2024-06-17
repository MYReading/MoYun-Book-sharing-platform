"""数据持久层，与数据库交互"""
from typing import List

from werkzeug.security import generate_password_hash, check_password_hash
from Service.Database.Utils import *
from Service.Utils import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import or_
from Service.Database.Model import User

class Database:
    """
    基本函数类别：get__(), getAll__(), add__(), modify__(), delete__()
    如果是添加或者修改信息时需要时间，允许传入datetime对象，否则会自动获取当前时间
    """

    db = None
    session = None

    def __init__(self):
        info = Config.get("Database")
        client = f"{info['Type'].lower()}+{info['Driver']}"
        host = info["Host"]
        port = info["Port"]
        account = info["Account"]
        password = info["Password"]
        database = info["Database"]
        URI = f"{client}://{account}:{password}@{host}:{port}/{database}"

        Database.db = create_engine(URI, echo=True)
        Database.session = sessionmaker(bind=Database.db)()

    """User相关"""

    @staticmethod
    def addUser(account: str, raw_password: str, email: str, telephone: str, role: str = "student") -> int:
        """
        添加用户
        :param account: 用户名
        :param raw_password: 密码(明文)
        :param email: 邮箱
        :param telephone: 电话
        :param role: 角色身份
        :return:
        """
        email = None if email == "" else email
        telephone = None if telephone == "" else telephone
        user = User(account=account, password=generate_password_hash(raw_password), signature="",
                    email=email, telephone=telephone, role=role)
        Database.session.add(user)
        Database.session.commit()
        return user.id

    @staticmethod
    def modifyUser(filter_id: int = None, filter_account: str = None, **kwargs) -> bool:
        """
        通用的修改用户信息的函数
        :param filter_id: 用于确定用户的id
        :param filter_account: 用于确定用户的account
        :param kwargs: 用于修改的参数，包括User的全部字段
        """
        if filter_id:
            user = Database.session.query(User).filter_by(id=filter_id).first()
        elif filter_account:
            user = Database.session.query(User).filter_by(account=filter_account).first()
        else:
            return False
        if not user:
            return False
        for key in kwargs:
            if hasattr(user, key):
                setattr(user, key, kwargs[key])
        Database.session.commit()
        return True

    @staticmethod
    def getUser(limit: int = 1, with_password: bool = False, **filters) -> Union[
        list[UserDict], UserDict, list[None], None
    ]:
        """
        通用的获取用户信息的函数
        :param limit: 限制返回的数量，默认为1即返回单个用户信息，其他正值为限制量，0、负值、None为不限制
        :param with_password: 是否返回密码，默认为False，此时返回值的password字段为None
        :param filters: 用于筛选的参数，包括User的全部字段和"keyword"字段(用于模糊搜索)
        """

        if filters and "keyword" in filters:
            users = Database.session.query(User).filter(User.account.like(f"%{filters.get('keyword')}%"))
        else:
            users = Database.session.query(User).filter_by(**filters) if filters else Database.session.query(User)

        if limit == 1:
            user = users.first()
            res = extractUser(user, with_password) if user else None
            return res
        elif limit > 1:
            users = users.limit(limit).all()
            res = [extractUser(user, with_password) for user in users]
            return res
        else:
            users = users.all()
            res = [extractUser(user, with_password) for user in users]
            return res

    @staticmethod
    def checkUser(account:str,password:str) -> Union[User,None]:
        """
        与getusser不同的是通过账号密码获取用户的所有信息
        """
        users_info = Database.getUser(limit=0, with_password=True, account=account)
        if len(users_info) == 0:
            return None
        else:
            for info in users_info:
                if check_password_hash(info["password"], password):
                    return info
            return None

    @staticmethod
    def checkLogin(account: str, password: str) -> Union[int, bool]:
        """
        检查登录信息是否正确
        """
        users_info = Database.getUser(limit=0, with_password=True, account=account)
        if len(users_info) == 0:
            return False
        else:
            for info in users_info:
                if check_password_hash(info["password"], password):
                    return info["id"]
            return False

    """Journal相关"""
    @staticmethod
    def addJournal(title: str, content: Union[list, str], publish_time: str, author_id: int, book_id: int) -> int:
        """
        添加书评
        :return: journal_id
        """
        journal = Journal(
            title=title,
            first_paragraph=content[0],
            content="\n".join(content) if isinstance(content, list) else content,
            publish_time=publish_time,
            author_id=author_id,
            book_id=book_id
        )
        Database.session.add(journal)
        Database.session.commit()
        journal_dict = extractJournal(Database.session.query(Journal).filter_by(title=title, author_id=author_id).first())
        journal_dict['content'] = "\n".join(content) if isinstance(content, list) else content
        return journal_dict.get('id')

    @staticmethod
    def getJournal(limit: int = 1, **filters) -> Union[list[JournalDict], JournalDict, list[None], None]:
        """
        通用的获取书评信息的函数
        """
        if filters and "keyword" in filters:
            journals = Database.session.query(Journal).filter(
                Journal.title.like(f"%{filters.get('keyword')}%") | Journal.content.like(f"%{filters.get('keyword')}%")
            )
        else:
            journals = Database.session.query(Journal).filter_by(**filters) if filters else Database.session.query(Journal)
        if limit == 1:
            journal = journals.first()
            return extractJournal(
                journal,
                Database.getJournalCommentsNum(journal_id=journal.id),
                Database.getJournalLikesNum(journal.id)
            ) if journal else None
        elif limit > 1:
            journals = journals.limit(limit).all()
            return [extractJournal(
                journal,
                Database.getJournalCommentsNum(journal_id=journal.id),
                Database.getJournalLikesNum(journal.id)
            ) for journal in journals]
        else:
            journals = journals.all()
            return [extractJournal(
                journal,
                Database.session.query(JournalComment).filter_by(journal_id=journal.id).count(),
                Database.session.query(JournalLike).filter_by(journal_id=journal.id).count()
            ) for journal in journals]


    @staticmethod
    def deleteJournal(Journal_id):
        """
        删除书评
        :param Journal_id:书评id
        """
        journal=Database.session.query(Journal).filter_by(id=Journal_id).first()
        if not journal:
            return False
        Database.session.delete(journal)
        Database.session.commit()
        return True


    """JournalComment相关"""
    @staticmethod
    def addJournalComment(journal_id: int, content: Union[str, list], author_id: int, publish_time: str = None):
        """
        添加针对journal_id的回复
        :return: 是否成功添加回复
        """
        if not publish_time:
            publish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        comment = JournalComment(
            publish_time=publish_time,
            author_id=author_id,
            journal_id=journal_id,
            content=content
        )
        if author_id == Database.session.query(Journal).filter_by(id=journal_id).first().author_id:
            comment.is_read = True  # 如果是作者自己回复，自动标记为已读
        Database.session.add(comment)
        Database.session.commit()
        return True

    @staticmethod
    def markJournalCommentsAsRead(*journals_id) -> bool:
        """
        将Journal的所有Comments都标记为已读
        :param journals_id: Journal的id，可以传入多个
        :return: 是否成功标记
        """
        if not journals_id:
            return False
        for journal_id in journals_id:
            Database.session.query(JournalComment).filter_by(journal_id=journal_id).update({"is_read": True})
        Database.session.commit()
        return True

    @staticmethod
    def getJournalComments(**filters) -> list[JournalCommentDict]:
        """
        根据journal_id获取全部关于这个书评的评论
        :return: 书评和用户信息
        """
        comments = (Database.session.query(JournalComment).filter_by(**filters)
                    .order_by(JournalComment.publish_time.desc()).all())
        if not comments:
            return []
        else:
            return [extractJournalComment(comment) for comment in comments]

    @staticmethod
    def getJournalCommentsNum(**filters) -> int:
        """
        根据journal_id获取评论数
        """
        return Database.session.query(JournalComment).filter_by(**filters).count()

    """JournalLike相关"""

    @staticmethod
    def addJournalLike(journal_id: int, author_id: int) -> bool:
        """
        根据journal_id和author_id添加点赞记录
        :return: 是否成功添加点赞记录(False说明已经存在该点赞记录)
        """
        publish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if Database.session.query(JournalLike).filter_by(journal_id=journal_id, author_id=author_id).first():
            return False
        else:
            like = JournalLike(
                journal_id=journal_id,
                author_id=author_id,
                publish_time=publish_time
            )
            Database.session.add(like)
            Database.session.commit()
            return True

    @staticmethod
    def getJournalLike(journal_id: int) -> list[JournalLikeDict]:
        """
        根据journal_id获取所有点赞记录
        :return: 点赞记录
        """
        likes = Database.session.query(JournalLike).filter_by(journal_id=journal_id).all()
        return [extractJournalLike(like) for like in likes]

    @staticmethod
    def getJournalLikesNum(journal_id: int) -> int:
        """
        根据journal_id获取点赞数
        :return: 点赞数
        """
        return Database.session.query(JournalLike).filter_by(journal_id=journal_id).count()

    """Book相关"""

    @staticmethod
    def addBook(
            isbn,
            title,
            origin_title,
            subtitle,
            author,
            page,
            publish_date,
            publisher,
            description,
            type
    ) -> Union[bool, int]:
        """
        添加书籍
        :return: book_id
        """
        if not title or not author or not isbn:
            return False
        # 检查是否已有该书
        if Database.session.query(Book).filter(Book.title == title, Book.author == author).first():
            return False
        if Database.session.query(Book).filter(Book.isbn == isbn).first():
            return False

        book = Book(
            isbn=isbn, title=title, origin_title=origin_title, subtitle=subtitle, author=author, page=page,
            publish_date=publish_date, publisher=publisher, description=description, type=type
        )
        Database.session.add(book)
        Database.session.commit()
        return Database.session.query(Book).filter_by(title=title, author=author).first().id

    @staticmethod
    def deleteBook(book_id) -> bool:
        """
        删除书籍
        :param book_id:书籍id
        """
        book=Database.session.query(Book).filter_by(id=book_id).first()
        if not book:
            return False
        Database.session.delete(book)
        Database.session.commit()
        return True


    @staticmethod
    def getBook(limit: int = 1, **filters) -> Union[list[BookDict], BookDict, list[None], None]:
        """
        通用的获取书籍信息的函数
        :param limit: 限制返回的数量，默认为1即返回单个书籍信息，其他正值为限制量，0、负值、None为不限制
        :param filters: 用于筛选的参数，包括Book的全部字段和"keyword"字段(用于模糊搜索)
        :return: 书籍信息
        """
        if filters and "keyword" in filters:
            books = Database.session.query(Book).filter(
                Book.title.like(f"%{filters.get('keyword')}%") |
                Book.subtitle.like(f"%{filters.get('keyword')}%") |
                Book.author.like(f"%{filters.get('keyword')}%")
            )
        else:
            books = Database.session.query(Book).filter_by(**filters) if filters else Book.query
        if limit == 1:
            book = books.first()
            return extractBook(book) if book else None
        elif limit > 1:
            books = books.limit(limit).all()
            return [extractBook(book) for book in books]
        else:
            books = books.all()
            return [extractBook(book) for book in books]

    @staticmethod
    def getAllBooks(self) -> List[BookDict]:
        """
        获取所有书籍信息的函数
        :return: 所有书籍信息的列表
        """
        books = Database.session.query(Book).all()
        return [extractBook(book) for book in books]

    @staticmethod
    def modifyBook(book_id: int, **kwargs) -> bool:
        """
        根据book_id修改书籍信息
        :param book_id: book_id
        :return:
        """
        book = Database.session.query(Book).filter_by(id=book_id).first()
        if not book:
            return False
        for key, value in kwargs.items():
            if hasattr(book, key):
                if value == "":
                    value = None
                setattr(book, key, value)
        Database.session.commit()
        return True

    """Group相关"""

    @staticmethod
    def addGroup(name: str, description: str, founder_id: int, establish_time: Union[datetime, str] = None) -> Union[
        bool, int]:
        """
        添加圈子
        :return: group_id
        """
        if not establish_time:
            establish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(establish_time, datetime):
            establish_time = establish_time.strftime("%Y-%m-%d %H:%M:%S")
        group = Group(name=name, description=description, founder_id=founder_id, establish_time=establish_time)
        Database.session.add(group)
        Database.session.commit()
        return Database.session.query(Group).filter_by(name=name, founder_id=founder_id, establish_time=establish_time).first().id

    @staticmethod
    def modifyGroup(group_id: int, **kwargs) -> bool:
        """
        根据groupID修改圈子信息
        :param group_id: group_id
        :return:
        """
        group = Database.session.query(Group).filter_by(id=group_id).first()
        if not group:
            return False
        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)
        Database.session.commit()
        return True

    @staticmethod
    def getGroup(limit: int = 1, **filters) -> Union[list[GroupDict], GroupDict, list[None], None]:
        """
        通用的获取圈子信息的函数
        """
        if filters and "keyword" in filters:
            groups = Database.session.query(Group).filter(
                Group.name.like(f"%{filters.get('keyword')}%") |
                Group.description.like(f"%{filters.get('keyword')}%")
            )
        else:
            groups = Database.session.query(Group).filter_by(**filters) if filters else Group.query
        groups = groups.order_by(Group.establish_time.desc())
        if limit == 1:
            group = groups.first()
            return extractGroup(group) if group else None
        elif limit > 1:
            groups = groups.limit(limit).all()
            return [extractGroup(group) for group in groups]
        else:
            groups = groups.all()
            return [extractGroup(group) for group in groups]

    """GroupDiscussion相关"""

    @staticmethod
    def addGroupDiscussion(
            poster_id: int,
            group_id: int,
            post_time: Union[str, datetime],
            title: str,
            content: str
    ) -> int:
        """
        添加帖子
        :param poster_id:
        :param group_id:
        :param post_time:
        :param title:
        :param content:
        :return:
        """
        discussion = GroupDiscussion(
            poster_id=poster_id,
            group_id=group_id,
            post_time=post_time if isinstance(post_time, str) else post_time.strftime("%Y-%m-%d %H:%M:%S"),
            title=title,
            content=content
        )
        if poster_id == Database.session.query(Group).filter_by(id=group_id).first().founder_id:
            discussion.is_read = True  # 如果是圈主发表的帖子，自动标记为已读
        Database.session.add(discussion)
        Database.session.commit()
        return Database.session.query(GroupDiscussion).filter_by(poster_id=poster_id, group_id=group_id, post_time=post_time).first()

    @staticmethod
    def getGroupDiscussion(
            limit: int = 1,
            **filters
    ) -> Union[list[GroupDiscussionDict], GroupDiscussionDict, list[None], None]:
        """
        通用的获取圈子内帖子的函数
        :param limit: 限制返回的数量，默认为1即返回单个帖子信息，其他正值为限制量，0、负值、None为不限制
        :param filters: 用于筛选的参数，包括GroupDiscussion的全部字段和"keyword"字段(用于模糊搜索)
        :return:
        """
        if filters and "keyword" in filters:
            discussions = Database.session.query(GroupDiscussion).filter(
                GroupDiscussion.title.like(f"%{filters.get('keyword')}%") |
                GroupDiscussion.content.like(f"%{filters.get('keyword')}%")
            )
        else:
            discussions = Database.session.query(GroupDiscussion).filter_by(**filters) if filters else GroupDiscussion.query
        if limit == 1:
            discussion = discussions.first()
            return extractGroupDiscussion(discussion) if discussion else None
        elif limit > 1:
            discussions = discussions.limit(limit).all()
            return [extractGroupDiscussion(discussion) for discussion in discussions]
        else:
            discussions = discussions.all()
            return [extractGroupDiscussion(discussion) for discussion in discussions]

    @staticmethod
    def getGroupDiscussionNum(**filters) -> int:
        return Database.session.query(GroupDiscussion).filter_by(**filters).count()

    @staticmethod
    def markGroupDiscussionsAsRead(*groups_id) -> bool:
        """
        将Group的所有Journals都标记为已读
        :param groups_id: Group的id，可以传入多个
        :return: 是否成功标记
        """
        if not groups_id:
            return False
        for group_id in groups_id:
            Database.session.query(GroupDiscussion).filter_by(group_id=group_id).update({"is_read": True})
        Database.session.commit()
        return True

    @staticmethod
    def deleteGroupDiscussion(discuss_id: int) -> bool:
        """
        根据discussID删除帖子
        :param discuss_id:
        :return:
        """
        discussion = Database.session.query(GroupDiscussion).filter_by(id=discuss_id).first()
        if not discussion:
            return False
        Database.session.delete(discussion)
        Database.session.commit()
        return True

    """GroupDiscussionReply相关"""

    @staticmethod
    def addGroupDiscussionReply(
            author_id: int, discussion_id: int, content: str, reply_time: Union[str, datetime] = None
    ) -> bool:
        """
        为某个GroupDiscussion添加回复
        :param author_id: 回复者id
        :param discussion_id: 帖子id
        :param content: 回复内容
        :param reply_time: 回复时间
        :return: 是否成功添加回复
        """
        if not reply_time:
            reply_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(reply_time, datetime):
            reply_time = reply_time.strftime("%Y-%m-%d %H:%M:%S")
        reply = GroupDiscussionReply(
            author_id=author_id,
            discussion_id=discussion_id,
            reply_time=reply_time,
            content=content
        )
        if author_id == Database.session.query(GroupDiscussion).filter_by(id=discussion_id).first().poster_id:
            reply.is_read = True  # 如果是帖子作者回复，自动标记为已读
        Database.session.add(reply)
        Database.session.commit()
        return True

    @staticmethod
    def getGroupDiscussionReplies(
            limit: int = 1, **filters
    ) -> Union[list[GroupDiscussionReplyDict], GroupDiscussionReplyDict, list[None], None]:
        """
        通用的获取帖子回复的函数
        :param limit: 限制返回的数量，默认为1即返回单个回复信息，其他正值为限制量，0、负值、None为不限制
        :param filters: 用于筛选的参数，包括GroupDiscussionReply的全部字段和"keyword"字段(用于模糊搜索)
        """
        if filters and "keyword" in filters:
            replies = Database.session.query(GroupDiscussionReply).filter(
                GroupDiscussionReply.content.like(f"%{filters.get('keyword')}%")
            )
        else:
            replies = Database.session.query(GroupDiscussionReply).filter_by(**filters) if filters else GroupDiscussionReply.query
        if limit == 1:
            reply = replies.first()
            return extractGroupDiscussionReply(reply) if reply else None
        elif limit > 1:
            replies = replies.limit(limit).all()
            return [extractGroupDiscussionReply(reply) for reply in replies]
        else:
            replies = replies.all()
            return [extractGroupDiscussionReply(reply) for reply in replies]

    @staticmethod
    def getGroupReply(group_id: int, limit=5) -> list[dict]:
        """
        按照时间降序获取圈子内所有回复
        :param group_id: 圈子id
        :return:
        :param limit: 限制返回的数量

        """
        discussion_id = Database.session.query(GroupDiscussion.id).filter_by(group_id=group_id).all()
        replies = Database.session.query(GroupDiscussionReply).filter(GroupDiscussionReply.discussion_id.in_(discussion_id)).order_by(
            GroupDiscussionReply.reply_time.desc()).limit(limit).all()
        return [extractGroupDiscussionReply(reply) for reply in replies]

    @staticmethod
    def getGroupDiscussionReplyNum(**filters) -> int:
        return Database.session.query(GroupDiscussionReply).filter_by(**filters).count()

    @staticmethod
    def markDiscussionRepliesAsRead(*discussions_id) -> bool:
        """
        将GroupDiscussion的所有Replies都标记为已读
        :param discussions_id: GroupDiscussion的id，可以传入多个
        :return: 是否成功标记
        """
        if not discussions_id:
            return False
        for discussion_id in discussions_id:
            Database.session.query(GroupDiscussionReply).filter_by(discussion_id=discussion_id).update({"is_read": True})
        Database.session.commit()
        return True

    """GroupUser相关"""

    @staticmethod
    def getGroupUser(limit: int = 1, **filters) -> Union[list[GroupUserDict], GroupUserDict, list[None], None]:
        """
        通用的获取圈子成员信息的函数
        """
        users = Database.session.query(GroupUser).filter_by(**filters) if filters else GroupUser.query
        if limit == 1:
            user = users.first()
            return extractGroupUser(user) if user else None
        elif limit > 1:
            users = users.limit(limit).all()
            return [extractGroupUser(user) for user in users]
        else:
            users = users.all()
            return [extractGroupUser(user) for user in users]

    @staticmethod
    def getGroupbyuser(user_id: int) -> Union[list[GroupDict],None]:
        """
        输入用户id获取该用户所在的group
        """
        users=Database.session.query(GroupUser).all()
        groups=[]
        for user1 in users:
            user1=extractGroupUser(user1)
            if user1['user_id']==user_id:
                groups.append(Database.getGroup(id=user1['group_id']))
        if len(groups)==0:
            return None
        else:
            return groups



    @staticmethod
    def getUserbyGroup(group_id: int)-> Union[list[UserDict],None]:
        """
        输入圈子id获得该圈子所有的成员
        """
        users=Database.session.query(GroupUser).all()
        groupusers=[]
        for user1 in users:
            user1=extractGroupUser(user1)
            if user1['group_id']==group_id:
                groupusers.append(Database.getUser(id=user1['user_id']))
        if len(groupusers)==0:
            return None
        else:
            return groupusers


    @staticmethod
    def addUsertoGroup(user_id,group_id,send_time) -> bool:
        """
        将学生加入圈子
        """
        if isinstance(send_time,datetime):
            send_time=send_time.strftime("%Y-%m-%d %H:%M:%S")
        groupuser=  GroupUser(
            user_id=user_id,
            group_id=group_id,
            join_time=send_time
        )
        Database.session.add(groupuser)
        Database.session.commit()
        return True

    @staticmethod
    def getGroupUsersNum(group_id: int) -> int:
        return Database.session.query(GroupUser).filter_by(group_id=group_id).count()




    """Chat相关"""

    @staticmethod
    def addChat(sender_id, receiver_id, send_time, content) -> bool:
        """
        添加聊天信息
        :return: 是否成功添加聊天信息
        """
        if isinstance(send_time, datetime):
            send_time = send_time.strftime("%Y-%m-%d %H:%M:%S")
        chat = Chat(
            sender_id=sender_id,
            receiver_id=receiver_id,
            send_time=send_time,
            content=content
        )
        Database.session.add(chat)
        Database.session.commit()
        return True

    @staticmethod
    def getChat(sender_id, receiver_id, each=False, limit=0) -> Union[list[ChatDict], ChatDict, list[None], None]:
        if each:
            chats = Database.session.query(Chat).filter(
                or_(
                    (Chat.sender_id == sender_id) & (Chat.receiver_id == receiver_id),
                    (Chat.sender_id == receiver_id) & (Chat.receiver_id == sender_id)
                )
            )
        else:
            chats = Database.session.query(Chat).filter_by(sender_id=sender_id, receiver_id=receiver_id)
        chats = chats.order_by(Chat.send_time.asc())
        if limit == 1:
            chat = chats.first()
            return extractChat(chat) if chat else None
        elif limit > 1:
            chats = chats.limit(limit).all()
            return [extractChat(chat) for chat in chats]
        else:
            chats = chats.all()
            return [extractChat(chat) for chat in chats]

    @staticmethod
    def getChatNum(sender_id, receiver_id, each=False) -> int:
        if each:
            return (Database.session.query(Chat).filter_by(sender_id=sender_id, receiver_id=receiver_id).count() +
                    Database.session.query(Chat).filter_by(sender_id=receiver_id, receiver_id=sender_id).count())
        return Database.session.query(Chat).filter_by(sender_id=sender_id, receiver_id=receiver_id).count()

    @staticmethod
    def getChatLastTime(sender_id, receiver_id, each=False):
        """
        获取两人之间最后的聊天时间
        :param sender_id: sender_id字段
        :param receiver_id: receiver_id字段
        :param each: 是否包含交换sender_id和receiver_id后的结果(默认为False)
        """
        if not each:
            chat = Database.session.query(Chat).filter_by(
                sender_id=sender_id, receiver_id=receiver_id
            ).order_by(Chat.send_time.desc()).first()
        else:
            chat1 = Database.session.query(Chat).filter_by(
                sender_id=sender_id, receiver_id=receiver_id
            ).order_by(Chat.send_time.desc()).first()
            chat2 = Database.session.query(Chat).filter_by(
                sender_id=receiver_id, receiver_id=sender_id
            ).order_by(Chat.send_time.desc()).first()
            if not (chat1 and chat2):
                chat = chat2 if chat2 else chat1
            else:
                chat = chat1 if chat1.send_time > chat2.send_time else chat2
        return chat.send_time if chat else None

    @staticmethod
    def markChatsAsRead(receiver_id, *sender_ids):
        """
        将Chat的所有信息都标记为已读
        :param receiver_id: receiver_id字段
        :param sender_ids: sender_id字段，可以传入多个
        :return: 是否成功标记
        """
        if not sender_ids:
            return False
        for sender_id in sender_ids:
            Database.session.query(Chat).filter_by(receiver_id=receiver_id, sender_id=sender_id).update({"is_read": True})
        Database.session.commit()
        return True

    """错误响应相关"""

    @staticmethod
    def getError(error_code: int) -> ErrorDict:
        """
        根据errorCode获取错误信息
        :param error_code: 错误码
        :return: 错误信息
        """
        error = Database.session.query(Error).filter_by(error_code=error_code).first()
        return extractError(error)

    """消息相关"""

    def getAllUnreadMessage(self, user_id: int) -> UnreadMessagesDict:
        """
        获取用户的所有未读消息(各类消息，包括书评回复、帖子回复、新私信、圈子新帖)
        :param user_id: 用户id，获取该用户的全部未读信息
        :return: 未读消息字典，UnreadMessagesDict类型
        """
        # 书评回复
        journals = self.getJournal(limit=0, author_id=user_id)
        journal_comments: list[dict] = [
            extractJournalComment(comment)
            for comment in
            Database.session.query(JournalComment).filter(
                JournalComment.journal_id.in_([
                    journal.get("id")
                    for journal
                    in journals
                ]),
                JournalComment.is_read == False
            ).order_by(
                JournalComment.publish_time.desc()
            ).all()
        ]
        for comment in journal_comments:
            comment["account"] = self.getUser(id=comment.get("author_id")).get("account")

        # 圈子新帖(先找到该用户创建的圈子，再找到该圈子的所有未读帖子)
        group_ids = Database.session.query(Group.id).filter_by(founder_id=user_id).all()
        group_discussions: list[dict] = [
            extractGroupDiscussion(discussion)
            for discussion in Database.session.query(GroupDiscussion).filter(
                GroupDiscussion.group_id.in_(group_ids),
                GroupDiscussion.is_read == False
            ).order_by(
                GroupDiscussion.post_time.desc()
            ).all()
        ]
        for discussion in group_discussions:
            discussion["account"] = self.getUser(id=discussion.get("poster_id")).get("account")

        # 帖子回复(先找到该用户发表的帖子，再找到该帖子的所有未读回复)
        discussion_ids = Database.session.query(GroupDiscussion.id).filter_by(poster_id=user_id).all()
        discussion_replies: list[dict] = [
            extractGroupDiscussionReply(reply)
            for reply in Database.session.query(GroupDiscussionReply).filter(
                GroupDiscussionReply.discussion_id.in_(discussion_ids),
                GroupDiscussionReply.is_read == False
            ).order_by(
                GroupDiscussionReply.reply_time.desc()
            ).all()
        ]
        for reply in discussion_replies:
            reply["account"] = self.getUser(id=reply.get("author_id")).get("account")

        # 私信
        chats: list[dict] = [
            extractChat(chat)
            for chat in
            Database.session.query(Chat).filter_by(
                receiver_id=user_id,
                is_read=False
            ).order_by(
                Chat.send_time.asc()
            ).all()
        ]
        for chat in chats:
            chat["account"] = self.getUser(id=chat.get("sender_id")).get("account")

        return UnreadMessagesDict(
            journal_comments=journal_comments,
            group_discussions=group_discussions,
            discussion_replies=discussion_replies,
            chats=chats
        )

    @staticmethod
    def getAllUnreadMessageNum(userID: int) -> dict[str, int]:
        """
        获取用户的所有未读消息数量(各类消息，包括书评回复、帖子回复、新私信、圈子新帖)
        :param userID:
        :return:
        """
        # 书评回复
        journalCommentsNum = Database.session.query(JournalComment).filter_by(author_id=userID, is_read=False).count()
        # 圈子新帖
        group_id = Database.session.query(Group.id).filter_by(founder_id=userID).all()
        groupDiscussionsNum = Database.session.query(GroupDiscussion).filter(
            GroupDiscussion.group_id.in_(group_id), GroupDiscussion.is_read == False).count()
        # 帖子回复
        discussion_id = Database.session.query(GroupDiscussion.id).filter_by(poster_id=userID).all()
        discussionRepliesNum = Database.session.query(GroupDiscussionReply).filter(
            GroupDiscussionReply.discussion_id.in_(discussion_id), GroupDiscussionReply.is_read == False).count()
        # 私信
        chatsNum = Database.session.query(Chat).filter_by(receiver_id=userID, is_read=False).count()
        return {"journalComment": journalCommentsNum,
                "groupDiscussion": groupDiscussionsNum,
                "discussionReply": discussionRepliesNum,
                "chat": chatsNum}
