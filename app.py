# -*- coding: UTF-8 -*-
# @Time     : 2026/3/25
# @Author   : Li
# @File     : app.py


from flask import Flask, render_template
from flask_cors import CORS

from lib.config import db, APP_SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from lib.models import ServerModel, SwitchModel, CableModel, ClientModel
from lib.handle_log import log


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = APP_SECRET_KEY
with app.app_context():
    db.init_app(app)
    db.create_all()
    if SwitchModel.query.count() == 0:
        sample_switches = [
            SwitchModel(vendor='Netgear', model='GS110MX', description='NETGEAR 10-Port Gigabit/10G Ethernet', capabilities='10G/5G/2.5G/1G/100M'),
            SwitchModel(vendor='Netgear', model='XS508M', description='NETGEAR 8-Port 10G Ethernet', capabilities='10G/5G/2.5G/1G/100M'),
            SwitchModel(vendor='Buffalo', model='BS-MP2008', description='Buffalo Multi-Gigabit 8 Port Business Switch', capabilities='10G/5G/2.5G/1G/100M'),
        ]
        db.session.add_all(sample_switches)
    if ServerModel.query.count() == 0:
        sample_servers = [
            ServerModel(unit_no=5421, unit_sn='NDHJTU8783', username='a5421'),
            ServerModel(unit_no=6895, unit_sn='PPJIKEHJ89', username='a6895'),
            ServerModel(unit_no=8857, unit_sn='TTHDJHE87S', username='a8857'),
        ]
        db.session.add_all(sample_servers)
    if ClientModel.query.count() == 0:
        sample_clients = [
            ClientModel(unit_no=5898, unit_sn='YUHGHDGH89', username='a5898'),
            ClientModel(unit_no=7858, unit_sn='IJHYTRTHBE', username='a7858'),
            ClientModel(unit_no=3598, unit_sn='P25OKJNMJE', username='a3598'),
        ]
        db.session.add_all(sample_clients)
    if CableModel.query.count() == 0:
        sample_cables = [
            CableModel(description='SAMZHE Cat.7 2m'),
            CableModel(description='SAMZHE Cat.7 3m'),
            CableModel(description='PHILIPS Cat.8 3m'),
        ]
        db.session.add_all(sample_cables)
    db.session.commit()

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
