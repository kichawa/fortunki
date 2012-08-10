import hashlib
import uuid
import datetime

import peewee
from playhouse import sqlite_ext

import settings


database = sqlite_ext.SqliteExtDatabase(settings.DATABASE_PATH)


class Model(peewee.Model):
    class Meta:
        database = database


class Entry(Model, sqlite_ext.FTSModel):
    id = peewee.PrimaryKeyField(column_class=peewee.VarCharColumn)
    content = peewee.TextField()
    created = peewee.DateTimeField(default=datetime.datetime.now)
    votes_count = peewee.IntegerField(default=0)


class Vote(Model):
    entry = peewee.ForeignKeyField(Entry, related_name='votes')
    created = peewee.DateTimeField(default=datetime.datetime.now)
    userid = peewee.CharField(max_length=32)


def random_id():
    return hashlib.md5(str(uuid.uuid4())).hexdigest()


Entry.create_table(True)
Vote.create_table(True)
