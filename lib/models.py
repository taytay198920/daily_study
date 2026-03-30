# -*- coding: UTF-8 -*-
# @Time     : 2026/3/25
# @Author   : Li
# @File     : models.py
from email.policy import default

from lib.config import db


class SwitchModel(db.Model):
    __tablename__ = 'switch'
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(128), nullable=False)
    model = db.Column(db.String(256), nullable=False, unique=True)
    description = db.Column(db.String(256), nullable=False)
    capabilities = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'vendor': self.vendor,
            'model': self.model,
            'description': self.description,
            'capabilities': self.capabilities
        }


class ServerModel(db.Model):
    __tablename__ = 'server'
    id = db.Column(db.Integer, primary_key=True)
    unit_no = db.Column(db.Integer, nullable=False)
    unit_sn = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'unit_no': self.unit_no,
            'unit_sn': self.unit_sn,
            'username': self.username
        }


class ClientModel(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    unit_no = db.Column(db.Integer, nullable=False)
    unit_sn = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'unit_no': self.unit_no,
            'unit_sn': self.unit_sn,
            'username': self.username
        }


class CableModel(db.Model):
    __tablename__ = 'cable'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description
        }


class TestGroup(db.Model):
    __tablename__ = 'test_group'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    server_id = db.Column(db.Integer, db.ForeignKey('server.id'))
    switch_id = db.Column(db.Integer, db.ForeignKey('switch.id'))
    cable_id = db.Column(db.Integer, db.ForeignKey('cable.id'))
    status = db.Column(db.String(50), default='pending')   # pending, running, passed, failed
    test_result = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    test_config = db.Column(db.JSON, nullable=True, default={})

    # relationship
    client = db.relationship('ClientModel')
    server = db.relationship('ServerModel')
    switch = db.relationship('SwitchModel')
    cable = db.relationship('CableModel')
