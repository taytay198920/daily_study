# -*- coding: UTF-8 -*-
# @Time     : 2026/3/25
# @Author   : Li
# @File     : app.py


from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from lib.config import db, APP_SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from lib.models import ServerModel, SwitchModel, CableModel, ClientModel, TestGroup
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

@app.route('/api/options')
def get_options():
    """获取所有下拉框选项数据"""
    try:
        clients = [{'id': c.id, 'unit_no': c.unit_no} for c in ClientModel.query.filter_by(is_active=True).all()]
        servers = [{'id': s.id, 'unit_no': s.unit_no} for s in ServerModel.query.filter_by(is_active=True).all()]
        switches = [{'id': sw.id, 'model': sw.model} for sw in SwitchModel.query.filter_by(is_active=True).all()]
        cables = [{'id': c.id, 'description': c.description} for c in CableModel.query.filter_by(is_active=True).all()]

        return jsonify({
            'success': True,
            'data': {
                'clients': clients,
                'servers': servers,
                'switches': switches,
                'cables': cables
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test_groups', methods=['GET'])
def get_test_groups():
    """获取所有测试组"""
    try:
        groups = TestGroup.query.order_by(TestGroup.created_at.desc()).all()
        groups_data = []
        for group in groups:
            groups_data.append({
                'id': group.id,
                'client': group.client.unit_no if group.client else None,
                'client_id': group.client_id,
                'server': group.server.unit_no if group.server else None,
                'server_id': group.server_id,
                'switch': group.switch.model if group.switch else None,
                'switch_id': group.switch_id,
                'cable': group.cable.description if group.cable else None,
                'cable_id': group.cable_id,
                'status': group.status,
                'test_result': group.test_result,
                'created_at': group.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return jsonify({'success': True, 'data': groups_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test_groups', methods=['POST'])
def create_test_group():
    """创建新的测试组"""
    try:
        data = request.json
        new_group = TestGroup(
            client_id=data.get('client_id'),
            server_id=data.get('server_id'),
            switch_id=data.get('switch_id'),
            cable_id=data.get('cable_id'),
            status='pending'
        )
        db.session.add(new_group)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'id': new_group.id,
                'client': new_group.client.unit_no if new_group.client else None,
                'server': new_group.server.unit_no if new_group.server else None,
                'switch': new_group.switch.model if new_group.switch else None,
                'cable': new_group.cable.description if new_group.cable else None,
                'status': new_group.status
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test_groups/<int:group_id>', methods=['PUT'])
def update_test_group(group_id):
    """更新测试组"""
    try:
        group = TestGroup.query.get_or_404(group_id)
        data = request.json

        if 'client_id' in data:
            group.client_id = data['client_id']
        if 'server_id' in data:
            group.server_id = data['server_id']
        if 'switch_id' in data:
            group.switch_id = data['switch_id']
        if 'cable_id' in data:
            group.cable_id = data['cable_id']
        if 'status' in data:
            group.status = data['status']
        if 'test_result' in data:
            group.test_result = data['test_result']

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test_groups/<int:group_id>', methods=['DELETE'])
def delete_test_group(group_id):
    """删除测试组"""
    try:
        group = TestGroup.query.get_or_404(group_id)
        db.session.delete(group)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test_groups/<int:group_id>/run', methods=['POST'])
def run_test(group_id):
    """运行测试"""
    try:
        group = TestGroup.query.get_or_404(group_id)
        # group.status = 'running'
        # db.session.commit()
        log.info(f"client unit no: {group.client.unit_no}")
        log.info(f"server unit no: {group.server.unit_no}")
        log.info(f"switch model: {group.switch.model}")
        log.info(f"cable: {group.cable.description}")

        # 这里可以添加实际的测试逻辑
        # 模拟异步测试
        # import threading
        # def perform_test():
        #     import time
        #     time.sleep(3)  # 模拟测试耗时
        #     with app.app_context():
        #         test_group = TestGroup.query.get(group_id)
        #         test_group.status = 'passed'
        #         test_group.test_result = f"Test completed successfully at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        #         db.session.commit()
        #
        # thread = threading.Thread(target=perform_test)
        # thread.start()

        return jsonify({'success': True, 'status': 'running'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
