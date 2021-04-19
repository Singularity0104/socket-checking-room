import socket
import json
import threading
from datetime import datetime
import sendmeg
import time
import signal
import sys
import struct
import os

quit = False

sendfile_thread = {}

def ping(name, client):
    while True:
        send_ping_byte = sendmeg.create_send_msg_byte(name, type="ping")
        if not quit:
            try:
                client.send(send_ping_byte)
                time.sleep(1)
                # print("ping")
            except:
                return
        else:
            return

def sendfile(name, client, dest, filepath):
    print("send begin")
    sendfile_thread.pop(dest)
    if os.path.isfile(filepath):
        fp = open(filepath, 'rb')
        while True:
            print("block")
            data = fp.read(512)
            if not data:
                print ('{0} file send over...'.format(os.path.basename(filepath)))
                break
            send_data = sendmeg.create_send_msg_byte(dest, type="fileblock", msg=data.decode())
            client.send(send_data)
            time.sleep(0.01)
    enddata = sendmeg.create_send_msg_byte(dest, type="fileblock")
    client.send(enddata)
    return


def send(name, client):
    while True:
        msg = input()
        if quit:
            return
        if msg == ":q":
            send_mag_byte = sendmeg.create_send_msg_byte(name, type="quit_re")
            client.send(send_mag_byte)
            return
        elif msg == "sendfile":
            dest = input("please input the destination: ")
            filepath = input("please input the filename: ")
            filename = os.path.basename(filepath)
            send_msg = sendmeg.create_send_msg_byte(dest, type="sendfile", msg=filename)
            client.send(send_msg)
            s = threading.Thread(target=sendfile, args=(name, client, dest, filepath))
            sendfile_thread[dest] = s
        else:
            send_msg_byte = sendmeg.create_send_msg_byte(name, msg=msg)
            client.send(send_msg_byte)

def receive(name, client):
    dataBuffer = bytes()
    while True:
        data = client.recv(1024)
        if len(data) == 0:
                print("\033[1;31msomething wrong with\033[0m \033[1;33mserver\033[0m \033[1;31mat\033[0m \033[1;36m%s\033[0m\n" % (datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
                client.close()
                global quit
                quit = True
                return
        dataBuffer += data
        while len(dataBuffer) > 4:
            length = struct.unpack('!1I', dataBuffer[:4])
            if len(dataBuffer) < 4 + length[0]:
                print("continue receive")
                break
            body = dataBuffer[4: 4 + length[0]]
            try:
                decode_data = json.loads(body)
                if decode_data["type"] == "quit_ok":
                    print("\033[1;31mquit successfully!\033[0m")
                    quit = True
                    return
                elif decode_data["type"] == "join_inf":
                    print("\033[1;33m%s\033[0m \033[1;32mjoin the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["message"], decode_data["time"]))
                elif decode_data["type"] == "quit_inf":
                    print("\033[1;33m%s\033[0m \033[1;31mquit the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["message"], decode_data["time"]))
                elif decode_data["type"] == "quit_acc":
                    print("\033[1;31msomething wrong with\033[0m \033[1;33m%s\033[0m \033[1;31mat\033[0m \033[1;36m%s\033[0m\n" % (decode_data["message"], decode_data["time"]))
                elif decode_data["type"] == "sendfileok":
                    print("ready")
                    dest = decode_data["message"]
                    if dest in sendfile_thread:
                        sendfile_thread[dest].start()
                elif decode_data["type"] == "receivefile":
                    filename = decode_data["message"]
                    fp = open('./' + filename, 'wb')
                    print ('start receiving...')
                    while True:
                            block = client.recv(1024)
                            decode_block = json.loads(block[4:])
                            if decode_block["type"] != "fileblock":
                                continue
                            elif decode_block["message"] == "NULL":
                                break
                            else:
                                file_block = decode_block["message"]
                                fp.write(file_block.encode())
                    fp.close()
                    print ('end receive...')
                else:
                    print("\033[1;36m%s\033[0m\n\033[1;33m%s: \033[0m%s\n" % (decode_data["time"], decode_data["name"], decode_data["message"]))
            except:
                pass
            dataBuffer = dataBuffer[4 + length[0]:]



def exit_me(signum, frame):
    send_mag_byte = sendmeg.create_send_msg_byte(name, type="quit_re")
    client.send(send_mag_byte)
    data = client.recv(1024)
    decode_data = json.loads(data[4:])
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
    decode_data = json.loads(data[4:])
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
