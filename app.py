# -*- coding: UTF-8 -*-
# @Time     : 2026/3/25
# @Author   : Li
# @File     : app.py


from flask import Flask, render_template

from lib.config import db, APP_SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from lib.handle_log import log


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = APP_SECRET_KEY
with app.app_context():
    db.init_app(app)
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')
