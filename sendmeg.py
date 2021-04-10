
import json
from datetime import datetime

def create_send_msg_byte(
    name,
    type="meg",
    msg="NULL"
    ):
    curr_time = datetime.now()
    time_str = datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
    send_mag = {
        "name": name,
        "time": time_str,
        "type": type,
        "message": msg
    }
    send_mag_byte = bytes(json.dumps(send_mag).encode('utf-8'))
    return send_mag_byte