# -*- coding: UTF-8 -*-
# @Time     : 2026/3/25
# @Author   : Li
# @File     : models.py


from lib.config import db


class SwitchModel(db.Model):
    __tablename__ = 'switch'
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(128), nullable=False)
    model = db.Column(db.String(256), nullable=False, unique=True)
    description = db.Column(db.String(256), nullable=False)
    capabilities = db.Column(db.String(256), nullable=False)


class ServerModel(db.Model):
    __tablename__ = 'server'
    id = db.Column(db.Integer, primary_key=True)
    unit_no = db.Column(db.Integer, nullable=False)
    unit_sn = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(128), nullable=False)


class ClientModel(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    unit_no = db.Column(db.Integer, nullable=False)
    unit_sn = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(128), nullable=False)


class CableModel(db.Model):
    __tablename__ = 'cable'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256), nullable=False)

