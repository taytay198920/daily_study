# -*- coding: UTF-8 -*-
# @Time     : 2026/3/25
# @Author   : Li
# @File     : handle_path.py

import os


root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

instance_dir = os.path.join(root_dir, 'instance')
db_path = os.path.join(instance_dir, 'app.db')

log_dir = os.path.join(root_dir, 'log')
log_path = os.path.join(log_dir, 'app.log')
