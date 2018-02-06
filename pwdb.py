from peewee import Model, BooleanField, TextField, ForeignKeyField, IntegerField, TimestampField, CompositeKey
from playhouse.apsw_ext import APSWDatabase

db = APSWDatabase(None)


class BaseModel(Model):
    class Meta:
        database = db


class AuthorFlair(BaseModel):
    class Meta:
        table_name = 'author_flair'

    text = TextField(unique=True)


class Author(BaseModel):
    class Meta:
        table_name = 'author'

    name = TextField(unique=True)


class Url(BaseModel):
    class Meta:
        table_name = 'url'

    link = TextField(unique=True)
    path = TextField(default=None, null=True)


class Domain(BaseModel):
    class Meta:
        table_name = 'domain'

    value = TextField(unique=True)


class Subreddit(BaseModel):
    class Meta:
        table_name = 'subreddit'

    name = TextField(unique=True)


class Submission(BaseModel):
    class Meta:
        table_name = 'submission'

    link_id = TextField(unique=True)  # 7ub3rk",
    author = ForeignKeyField(Author, backref='submission')
    author_flair = ForeignKeyField(AuthorFlair, backref='submission', default=None, null=True)  # verified",
    created_utc = TimestampField(index=True)  # 1517416133,
    title = TextField()  # Playing with dolls (f)",
    domain = ForeignKeyField(Domain, backref='submission', default=None, null=True)  # imgur.com",
    is_crosspostable = BooleanField(default=None, null=True)  # true,
    is_reddit_media_domain = BooleanField(default=None, null=True)  # false,
    is_self = BooleanField(default=None, null=True)  # false,
    is_video = BooleanField(default=None, null=True)  # false,
    locked = BooleanField(default=None, null=True)  # false,
    num_comments = IntegerField(default=None, null=True)  # 0,
    media = ForeignKeyField(Url, default=None, null=True)
    over_18 = BooleanField(default=None, null=True)  # true,
    preview = ForeignKeyField(Url, default=None, null=True)  # https://imgur.com/a/Zp1D8",
    pinned = BooleanField(default=None, null=True)  # false,
    retrieved_on = TimestampField(default=None, null=True, index=True)  # 1517416135,
    score = IntegerField(default=0, null=True)  # 1,
    selftext = TextField(default=None, null=True)  # ",
    spoiler = BooleanField(default=None, null=True)  # false,
    stickied = BooleanField(default=None, null=True)  # false,
    subreddit = ForeignKeyField(Subreddit, backref='submission')  # gonewild",
    thumbnail = ForeignKeyField(Url, default=None, null=True)  # default",
    view_count = IntegerField(default=None, null=True)
    permalink = TextField(default=None, null=True)  # /r/gonewild/comments/7ub3rk/playing_with_dolls_f/",
    deleted = BooleanField(default=None, null=True)


class SubmissionLinks(BaseModel):
    class Meta:
        table_name = 'sublink'
        primary_key = CompositeKey('post', 'url')

    post = ForeignKeyField(Submission, backref='sublink', default=None, null=True)
    url = ForeignKeyField(Url, backref='sublink', default=None, null=True)


class SubmissionCommentIDs(BaseModel):
    class Meta:
        table_name = 'subcommid'
        primary_key = CompositeKey('link', 'comment_id')

    link = ForeignKeyField(Submission, backref='subcommid', default=None, null=True)  # 7ub3rk",
    comment_id = IntegerField()  # 7ub3rk",


class Comment(BaseModel):
    class Meta:
        table_name = 'comment'

    comment_id = TextField(unique=True)
    approved_at_utc = BooleanField(default=None, null=True)
    author = ForeignKeyField(Author, backref='comment')
    author_flair = ForeignKeyField(AuthorFlair, backref='comment', default=None, null=True)
    archived = BooleanField(default=None, null=True)
    banned_at_utc = BooleanField(default=None, null=True)
    body = TextField()
    created_utc = TimestampField(index=True)
    edited = BooleanField(default=None, null=True)
    gilded = IntegerField(default=None, null=True)
    is_submitter = BooleanField(default=None, null=True)
    link_id = TextField(default=None, null=True)
    parent_id = TextField(default=None, null=True)
    retrieved_on = TimestampField(default=None, null=True, index=True)
    score = IntegerField(default=0, null=True)
    stickied = BooleanField(default=None, null=True)
    subreddit = ForeignKeyField(Subreddit, backref='comment')
    number_urls = IntegerField(default=None, null=True)
    deleted = BooleanField(default=None, null=True, index=True)


class CommentLinks(BaseModel):
    class Meta:
        table_name = 'commlink'
        primary_key = CompositeKey('comment', 'url')

    comment = ForeignKeyField(Comment, backref='commlink', default=None, null=True)
    url = ForeignKeyField(Url, backref='commlink', default=None, null=True)
