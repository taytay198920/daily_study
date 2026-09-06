# -*- coding: UTF-8 -*-
# @Time     : 2026/9/6
# @Author   : Li
# @File     : auto.py

import subprocess
import time

current_date = time.strftime("%b %d", time.localtime()).replace(" 0", " ")
print(current_date)
total_cycle = ["Reboot 123", "Shutdown 888", "Sleep 999"]
update_template = f"""
<div>==========================================</div>
<div>Update:</div>
<div><i><br></i></div>
<div><b>{current_date}</b><br></div>
<div><br></div>"""

plaintext_cmd = """osascript << EOF
tell application "Notes"
    activate
    delay 1
    get plaintext of every note of folder "Notes" whose name is "try"
end tell
EOF
"""
plaintext_p = subprocess.Popen(plaintext_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
plaintext_output, plaintext_err = plaintext_p.communicate()
print(plaintext_output)
html_content_cmd = """osascript << EOF
tell application "Notes"
    activate
    delay 1
    get body of every note of folder "Notes" whose name is "try"
end tell
EOF
"""
html_content_p = subprocess.Popen(html_content_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
html_content_output, html_content_err = html_content_p.communicate()
html_content_output_list = html_content_output.split("\n")
print(html_content_output_list)
for tc in total_cycle:
    if tc in plaintext_output:
        update_template += f"<div>{tc}</div>\n"
    else:
        update_template += f"<div><font color='blue'>{tc}</font></div>\n"
new_content = ""
if "=====" not in html_content_output:
    html_content_output_list.append(update_template)
    new_content = "\n".join(html_content_output_list)
else:
    for line in html_content_output_list:
        if "=====" in line:
            insert_index = html_content_output_list.index(line)
            print(f"insert index: {insert_index}")
            html_content_output_list.insert(insert_index, update_template)
            new_content = "\n".join(html_content_output_list)
            break


print(new_content)
new_content_cmd = f"""osascript << EOF
tell application "Notes"
    activate
    delay 1
    set targetNote to first note of folder "Notes" whose name is "try"
    set body of targetNote to "{new_content.replace('"', '\\"')}"
end tell
EOF
"""
new_content_p = subprocess.Popen(new_content_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
new_content_output, new_content_err = new_content_p.communicate()
print(new_content_output)
print(new_content_err)