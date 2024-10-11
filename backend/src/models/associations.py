from sqlalchemy import Table, Column, Integer, ForeignKey
from .base import Base

api_key_project = Table('api_key_project', Base.metadata,
    Column('api_key_id', Integer, ForeignKey('api_keys.id'), primary_key=True),
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True)
)