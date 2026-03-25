# -*- coding: UTF-8 -*-
# @Time     : 2026/3/25
# @Author   : Li
# @File     : config.py


from flask_sqlalchemy import SQLAlchemy
from lib.handle_path import db_path


SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_path
SQLALCHEMY_TRACK_MODIFICATIONS = False
APP_SECRET_KEY = 'ethernet automatic test key'
db = SQLAlchemy()
