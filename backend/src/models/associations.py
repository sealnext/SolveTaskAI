from sqlalchemy import Table, Column, Integer, ForeignKey
from .base import Base

api_key_project_association = Table('api_key_project', Base.metadata,
    Column('api_key_id', Integer, ForeignKey('api_keys.id'), primary_key=True),
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True)
)

user_project_association = Table(
    'user_project',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True)
)