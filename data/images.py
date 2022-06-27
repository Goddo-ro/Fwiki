import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase


class Image(SqlAlchemyBase, UserMixin):
    __tablename__ = 'images'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)

    def __repr__(self):
        return f"{self.id}.png"
