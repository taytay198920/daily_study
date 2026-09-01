# -*- coding: UTF-8 -*-
# @Time     : 2026/4/6
# @Author   : Li
# @File     : demo.py
import time

import requests

datas = {
    "switch_model": "GS110MX(Connect port 1 ~ port 2 <10GB>)",
    "server_no": "1234",
    "server_sn": "JJJJJJ",
    "server_ethernet_info": "AQC113 2.213",
    "server_phase": "UUU",
    "server_project_code": "JJSII",
    "server_os_version": "QQQQ",
    "server_bundle": "TTT",
    "server_username": "taylor",
    "server_hostname": "taylor.local",
    "client_no": "KK",
    "client_sn": "PIPOII",
    "client_ethernet_info": "AQC113 2.213",
    "client_phase": "DDD",
    "client_project_code": "YYYY",
    "client_os_version": "OOOO",
    "client_username": "TOM",
    "client_hostname": "TOM.local",
    "cable": "PHILIPS Cat.8 3m",
    "eee_status": "NO"
}

result = {
    "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "send_file": "450.4 Mbit/s\n358.7 Mbit/s\n254.3 Mbit/s",
    "switch_model": "GS110MX(Connect port 1 ~ port 2 <10GB>)",
    "client_os_version": "OOOO"
}
headers = {
    "Content-Type": "application/json"
}
url = "http://127.0.0.1:5002/api/update_test_result"

response = requests.post(url, json=result, headers=headers)
print(response.status_code)

