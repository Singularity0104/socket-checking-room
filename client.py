import socket
import json
import threading
from datetime import datetime
import sendmeg
import time
import signal
import sys

quit = False

def ping(name, client):
    while True:
        send_ping_byte = sendmeg.create_send_msg_byte(name, type="ping")
        if not quit:
            client.send(send_ping_byte)
            time.sleep(1)
        else:
            return

def send(name, client):
    while True:
        msg = input()
        if (msg == ":q"):
            send_mag_byte = sendmeg.create_send_msg_byte(name, type="quit_re")
            client.send(send_mag_byte)
            return
        send_msg_byte = sendmeg.create_send_msg_byte(name, msg=msg)
        client.send(send_msg_byte)

def receive(name, client):
    while True:
        data = client.recv(1024)
        try:
            decode_data = json.loads(data)
            if decode_data["type"] == "quit_ok":
                print("\033[1;31mquit successfully!\033[0m")
                global quit
                quit = True
                return
            elif decode_data["type"] == "join_inf":
                print("\033[1;33m%s\033[0m \033[1;32mjoin the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["message"], decode_data["time"]))
            elif decode_data["type"] == "quit_inf":
                print("\033[1;33m%s\033[0m \033[1;31mquit the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["message"], decode_data["time"]))
            elif decode_data["type"] == "quit_acc":
                print("\033[1;31msomething wrong with\033[0m \033[1;33m%s\033[0m \033[1;31mat\033[0m \033[1;36m%s\033[0m\n" % (decode_data["message"], decode_data["time"]))
            else:
                print("\033[1;36m%s\033[0m\n\033[1;33m%s: \033[0m%s\n" % (decode_data["time"], decode_data["name"], decode_data["message"]))
        except:
            pass

def exit_me(signum, frame):
    send_mag_byte = sendmeg.create_send_msg_byte(name, type="quit_re")
    client.send(send_mag_byte)
    data = client.recv(1024)
    decode_data = json.loads(data)
    if decode_data["type"] == "quit_ok":
        print("\033[1;31mquit successfully!\033[0m")
        # global quit
        # quit = True
    time.sleep(1)
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_me)
    signal.signal(signal.SIGTERM, exit_me)
    name = input("Please input your name: ")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6999))
    send_name = sendmeg.create_send_msg_byte(name)
    client.send(send_name)
    data = client.recv(1024)
    decode_data = json.loads(data)
    if decode_data["type"] == "join_f":
        print("join failed!")
        socket.SHUT_RDWR
        client.close()
    else:
        t1 = threading.Thread(target=send, args=(name, client))
        t2 = threading.Thread(target=receive, args=(name, client))
        t3 = threading.Thread(target=ping, args=(name, client))
        t1.setDaemon(True)
        t2.setDaemon(True)
        t3.setDaemon(True)
        t1.start()
        t2.start()
        t3.start()
        try:
            t1.join()
            t2.join()
            t3.join()
        except:
            pass
        socket.SHUT_RDWR
        client.close()
