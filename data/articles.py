import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Article(SqlAlchemyBase):
    __tablename__ = 'articles'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    text = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    keywords = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    add_date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True,
                                 default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True,
                                      default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    user = orm.relation('User')