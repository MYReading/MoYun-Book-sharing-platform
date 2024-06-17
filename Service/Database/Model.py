"""数据模型"""
from typing import Union

from datetime import datetime

from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TEXT, DATETIME, BOOLEAN
from sqlalchemy import Column, Enum, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class Book(BaseModel):
    """图书 表 数据模型"""
    __tablename__ = "book"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    isbn = Column(VARCHAR(32), unique=True)
    title = Column(VARCHAR(128), unique=False)
    origin_title = Column(VARCHAR(128), unique=False)
    subtitle = Column(VARCHAR(128), unique=False)
    author = Column(VARCHAR(128), unique=False)
    page = Column(INTEGER, unique=False)
    publish_date = Column(VARCHAR(24), unique=False)
    publisher = Column(VARCHAR(32), unique=False)
    description = Column(TEXT, unique=False)
    type = Column(
        Enum("马列主义、毛泽东思想、邓小平理论", "哲学、宗教", "社会科学总论", "政治、法律", "军事", "经济",
             "文化、科学、教育、体育", "语言、文字", "文学", "艺术", "历史、地理", "自然科学总论",
             "数理科学和化学", "天文学、地球科学", "生物科学", "医药、卫生", "农业科学", "工业技术",
             "交通运输", "航空、航天", "环境科学、安全科学", "综合性图书"), unique=False)

    def __init__(self, isbn, title, origin_title, subtitle, author, page, publish_date, publisher, description, type):
        self.isbn = isbn
        self.title = title
        self.origin_title = origin_title if origin_title else None
        self.subtitle = subtitle if subtitle else None
        self.author = author
        self.page = page if page else None
        self.publish_date = publish_date if publish_date else None
        self.publisher = publisher if publisher else None
        self.description = description if description else None
        self.type = type if type else None


class Chat(BaseModel):
    """站内私信 表 数据模型"""
    __tablename__ = "chat"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    sender_id = Column(INTEGER, nullable=False)
    receiver_id = Column(INTEGER, nullable=False)
    content = Column(TEXT, nullable=False)
    send_time = Column(DATETIME, nullable=False)
    is_read = Column(BOOLEAN, nullable=False, default=False)

    def __init__(self, sender_id, receiver_id, content, send_time):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.send_time = send_time


class Error(BaseModel):
    """错误码及描述 表 数据模型"""
    __tablename__ = "error"
    error_code = Column(INTEGER, primary_key=True, autoincrement=True)
    title = Column(VARCHAR(128), unique=False)
    title_en = Column(VARCHAR(128), unique=False)
    content = Column(TEXT, unique=False)
    publish_time = Column(DATETIME, unique=False)
    reference_link = Column(VARCHAR(128), unique=False)

    def __init__(self, title, title_en, content, publish_time, reference_link):
        self.title = title
        self.title_en = title_en
        self.content = content
        self.publish_time = publish_time
        self.reference_link = reference_link


class Group(BaseModel):
    """圈子 表 数据模型"""
    __tablename__ = "group"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(32), unique=True)
    founder_id = Column(INTEGER, unique=False)
    establish_time = Column(DATETIME, unique=False)
    description = Column(TEXT, unique=False)

    def __init__(self, name, founder_id, description, establish_time):
        self.name = name
        self.founder_id = founder_id
        self.description = description
        self.establish_time = establish_time


class GroupDiscussion(BaseModel):
    """圈子-讨论 表 数据模型"""
    __tablename__ = "group_discussion"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    poster_id = Column(INTEGER, unique=False)
    group_id = Column(INTEGER, unique=False)
    post_time = Column(DATETIME, unique=False)
    title = Column(VARCHAR(256), unique=False)
    content = Column(TEXT, unique=False)
    is_read = Column(BOOLEAN, nullable=False, default=False)

    def __init__(self, poster_id: int, group_id: int, post_time: Union[str, datetime], title: str, content: str):
        self.poster_id = poster_id
        self.group_id = group_id
        self.post_time = post_time if isinstance(post_time, str) else datetime.strptime(post_time, "%Y-%m-%d %H:%M:%S")
        self.title = title
        self.content = content


class GroupDiscussionReply(BaseModel):
    """圈子-讨论-回复 表 数据模型"""
    __tablename__ = "group_discussion_reply"
    author_id = Column(INTEGER, unique=False)
    discussion_id = Column(INTEGER, unique=False)
    reply_time = Column(DATETIME, unique=False)
    __table_args__ = (PrimaryKeyConstraint('author_id', 'discussion_id', 'reply_time'),)  # 联合主键
    content = Column(TEXT, unique=False)
    is_read = Column(BOOLEAN, nullable=False, default=False)

    def __init__(self, author_id: int, discussion_id: int, reply_time, content):
        self.author_id = author_id
        self.discussion_id = discussion_id
        self.reply_time = reply_time
        self.content = content


class GroupUser(BaseModel):
    """圈子-成员 表 数据模型"""
    __tablename__ = "group_user"
    user_id = Column(INTEGER, unique=False)
    group_id = Column(INTEGER, unique=False)
    __table_args__ = (PrimaryKeyConstraint('user_id', 'group_id'),)  # 联合主键
    join_time = Column(DATETIME, unique=False)

    def __init__(self, user_id, group_id, join_time):
        self.user_id = user_id
        self.group_id = group_id
        self.join_time = join_time


class User(BaseModel):
    """用户 表 数据模型"""
    __tablename__ = "user"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    account = Column(VARCHAR(24), unique=True)
    password = Column(TEXT, unique=False)
    signature = Column(VARCHAR(128), unique=False)
    email = Column(VARCHAR(120), unique=False)
    telephone = Column(VARCHAR(11), unique=False)
    role = Column(Enum("student", "teacher", "admin"), unique=False)

    def __init__(
            self,
            account: str,
            password: str,
            signature: str,
            email: str,
            telephone: str,
            role: str
    ):
        self.account = account
        self.password = password
        self.signature = signature
        self.email = email
        self.telephone = telephone
        self.role = role


class Journal(BaseModel):
    """书评 表 数据模型"""
    __tablename__ = "journal"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    title = Column(VARCHAR(128), unique=False)
    first_paragraph = Column(TEXT, unique=False)
    content = Column(TEXT, unique=False)
    publish_time = Column(DATETIME, unique=False)
    author_id = Column(INTEGER, unique=False)
    book_id = Column(INTEGER, unique=False)

    def __init__(
            self,
            title: str,
            first_paragraph: str,
            content: str,
            publish_time: str,
            author_id: int,
            book_id: int
    ):
        self.title = title
        self.first_paragraph = first_paragraph
        self.content = content
        self.publish_time = publish_time
        self.author_id = author_id
        self.book_id = book_id


class JournalComment(BaseModel):
    """书评-评论 表 数据模型"""
    __tablename__ = "journal_comment"
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    publish_time = Column(DATETIME, unique=False)
    author_id = Column(INTEGER, unique=False)
    journal_id = Column(INTEGER, unique=False)
    content = Column(TEXT, unique=False)
    is_read = Column(BOOLEAN, nullable=False, default=False)

    def __init__(self, publish_time: Union[str, datetime], author_id: int, journal_id: int, content: Union[str, list]):
        self.publish_time = publish_time if isinstance(publish_time, datetime) else (
            datetime.strptime(publish_time, "%Y-%m-%d %H:%M:%S")
        )
        self.author_id = author_id
        self.journal_id = journal_id
        self.content = content if isinstance(content, str) else "\n".join(content)


class JournalLike(BaseModel):
    """书评-点赞 表 数据模型"""
    __tablename__ = "journal_like"
    author_id = Column(INTEGER, unique=False)
    journal_id = Column(INTEGER, unique=False)
    __table_args__ = (PrimaryKeyConstraint('author_id', 'journal_id'),)  # 让authorID和journalID作为联合主键
    publish_time = Column(DATETIME, unique=False)

    def __init__(self, author_id: int, journal_id: int, publish_time: Union[str, datetime]):
        self.author_id = author_id
        self.journal_id = journal_id
        self.publish_time = publish_time
