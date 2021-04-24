import struct
from datetime import datetime

def create_send_msg_byte(
    name,
    type="meg",
    msg="NULL",
    time="NULL"
    ):
    curr_time = datetime.now()
    if (time == "NULL"):
        time_str = datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
    else:
        time_str = time
    send_mag = {
        "name": name,
        "time": time_str,
        "type": type,
        "message": msg
    }
    send_mag_byte = bytes(str(send_mag).encode("UTF-8"))
    length = len(send_mag_byte)
    header = struct.pack("!1I", length)
    return header + send_mag_byte