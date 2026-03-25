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
    return render_template('index.html', current_url='index')

@app.route('/monitor')
def monitor():
    return render_template('monitor.html', current_url='monitor')

@app.route('/switch_management')
def switch_management():
    return render_template('switch_management.html', current_url='management')

@app.route('/server_management')
def server_management():
    return render_template('server_management.html', current_url='management')

@app.route('/client_management')
def client_management():
    return render_template('client_management.html', current_url='management')

@app.route('/cable_management')
def cable_management():
    return render_template('cable_management.html', current_url='management')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002, debug=True)
