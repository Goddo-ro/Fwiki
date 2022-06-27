import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    level = sqlalchemy.Column(sqlalchemy.Integer, nullable=True, default=3)
    image_id = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("images.id"), default=1)
    registrated_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                         default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                      default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    image = orm.relation('Image')

    def __repr__(self):
        return f"{self.surname} {self.name}"

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
