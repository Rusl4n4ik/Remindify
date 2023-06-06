from sqlite3 import Date

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_NAME = 'remindify.sqlite'

engine = create_engine(f"sqlite:///{DATABASE_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


def create_db():
    Base.metadata.create_all(engine)
    session = Session()
    session.commit()


class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    text = Column(String)
    date = Column(DateTime)


class Users(Base):
    __tablename__ = 'Clients'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    first_name = Column(String(100), nullable=True)
    username = Column(String(50), nullable=True)


def add_user(id, first_name, username):
    session = Session()
    exist = check_existing(id)
    if not exist:
        user = Users(chat_id=id,
                       first_name=first_name,
                       username=username)
        session.add(user)
    session.commit()
    session.close()


def check_existing(id):
    session = Session()
    result = session.query(Users.chat_id).filter(Users.chat_id == id).all()
    return result


def __init__(self, user_id, text, date):
    self.user_id = user_id
    self.text = text
    self.date = date


def get_user_reminders(user_id):
    session = Session()
    reminders = session.query(Reminder).filter(Reminder.user_id == user_id).all()
    return reminders


def get_reminder_by_id(reminder_id):
    session = Session()
    reminder = session.query(Reminder).get(reminder_id)
    return reminder


if __name__ == '__main__':
    create_db()