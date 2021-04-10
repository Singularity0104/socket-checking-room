import socket
import json
import threading
from datetime import datetime
import sendmeg


def send(name, client):
    while True:
        msg = input()
        if (msg == ":q"):
            send_mag_byte = sendmeg.create_send_msg_byte(name, type="quit")
            client.send(send_mag_byte)
            return
        send_msg_byte = sendmeg.create_send_msg_byte(name, msg=msg)
        client.send(send_msg_byte)

def receive(name, client):
    while True:
        data = client.recv(1024)
        decode_data = json.loads(data)
        if decode_data["type"] == "quit_ok":
            print("\033[1;31mquit successfully!\033[0m")
            return
        else:
            print("\033[1;36m%s\033[0m\n\033[1;33m%s: \033[0m%s\n" % (decode_data["time"], decode_data["name"], decode_data["message"]))

if __name__ == "__main__":
    name = input("Please input your name: ")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6999))
    send_name_byte = sendmeg.create_send_msg_byte(name)
    client.send(send_name_byte)
    t1 = threading.Thread(target=send, args=(name, client))
    t2 = threading.Thread(target=receive, args=(name, client))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    client.close()
