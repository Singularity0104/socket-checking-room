import socket
import threading
import json
from datetime import datetime
import sendmeg

all_client = []

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(('localhost',6999))
server.listen(5)

def connect(name, conn):
    while True:
        data = conn.recv(1024)
        decode_data = json.loads(data[4:])
        if decode_data["type"] == "quit_re":
            print("\033[1;33m%s\033[0m \033[1;31mquit the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["name"], decode_data["time"]))
            send_quit_ok = sendmeg.create_send_msg_byte("server", type="quit_ok")
            conn.send(send_quit_ok)
            all_client.remove(conn)
            conn.close
            return
        elif decode_data["type"] == "ping":
            # print(name, "ping ok!")
            conn.send(sendmeg.create_send_msg_byte("server", type="pong"))
        else:
            print("\033[1;36m%s\033[0m\n\033[1;33m%s: \033[0m%s\n" % (decode_data["time"], decode_data["name"], decode_data["message"]))
        for c in all_client:
            c.send(data)

if __name__ == "__main__":
    i = 0
    while True:
        conn, addr = server.accept()
        all_client.append(conn)
        data = conn.recv(1024)
        decode_data = json.loads(data[4:])
        print("\033[1;33m%s\033[0m \033[1;32mjoin the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["name"] + str(i), decode_data["time"]))
        t = threading.Thread(target=connect, args=(decode_data["name"] + str(i), conn))
        t.start()
        i += 1
