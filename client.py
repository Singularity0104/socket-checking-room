import socket
import threading
from datetime import datetime
import sendmeg
import time
import signal
import sys
import struct
import os

# 客户端状态
quit = False

# 所需数据结构
sendfile_thread = {}
file_fp = {}

# 心跳函数
def ping(name, client):
    while True:
        send_ping_byte = sendmeg.create_send_msg_byte(name, type="ping")
        if not quit:
            try:
                client.send(send_ping_byte)
                # 心跳包演示
                time.sleep(1)
                # print("ping")
            except:
                return
        else:
            return

# 发送文件函数
def sendfile(name, client, filename, filepath):
    time.sleep(0.5)
    print("\033[1;32m%s uploading...\033[0m\n" % (filename))
    sendfile_thread.pop(filename)
    if os.path.isfile(filepath):
        fp = open(filepath, 'rb')
        b = 0
        while True:
            time.sleep(0.001)
            data = fp.read(512)
            if not data:
                fp.close()
                print ("\033[1;32m%s uploaded successfully!\033[0m\n" % (filename))
                break
            send_data = sendmeg.create_send_msg_byte(filename, type="fileblock", msg=data)
            client.send(send_data)
            b += 1
    enddata = sendmeg.create_send_msg_byte(filename, type="fileblockover")
    client.send(enddata)
    return

# 发送消息函数
def send(name, client):
    while True:
        msg = input()
        if quit:
            return
        if msg == ":q":
            send_mag_byte = sendmeg.create_send_msg_byte(name, type="quit_re")
            client.send(send_mag_byte)
            return
        elif msg == ":ud":
            filepath = input("\033[1;32mPlease input the filepath: \033[0m")
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                send_msg = sendmeg.create_send_msg_byte(name, type="upload", msg=filename)
                client.send(send_msg)
                s = threading.Thread(target=sendfile, args=(name, client, filename, filepath))
                sendfile_thread[filename] = s
            else:
                print("\033[1;31mFile not exists!\033[0m\n")
        elif msg == ":dd":
            filename = input("\033[1;32mPlease input the filename: \033[0m")
            filepath = input("\033[1;32mPlease input the download path: \033[0m")
            if filepath[-1] != "/":
                filepath = filepath + "/"
            if not os.path.exists(filepath):
                os.makedirs(filepath)
            send_msg = sendmeg.create_send_msg_byte(name, type="download", msg=filename)
            client.send(send_msg)
            fp = open(filepath + filename, 'wb')
            file_fp[filename] = fp
            print("\033[1;32m%s downloading...\033[0m\n" % (filename))
        elif msg == ":ls":
            client.send(sendmeg.create_send_msg_byte(name, type="ls"))
        else:
            send_msg_byte = sendmeg.create_send_msg_byte(name, msg=msg)
            client.send(send_msg_byte)

# 接受消息函数
def receive(name, client):
    dataBuffer = bytes()
    while True:
        data = client.recv(2048)
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
                # print("continue receive")
                break
            body = dataBuffer[4: 4 + length[0]]
            try:
                decode_data = eval(body)
                if decode_data["type"] == "quit_ok":
                    print("\033[1;31mQuit successfully!\033[0m\n")
                    quit = True
                    return
                elif decode_data["type"] == "pong":
                    pass
                elif decode_data["type"] == "join_inf":
                    print("\033[1;33m%s\033[0m \033[1;32mjoin the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["message"], decode_data["time"]))
                elif decode_data["type"] == "quit_inf":
                    print("\033[1;33m%s\033[0m \033[1;31mquit the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["message"], decode_data["time"]))
                elif decode_data["type"] == "quit_acc":
                    print("\033[1;31msomething wrong with\033[0m \033[1;33m%s\033[0m \033[1;31mat\033[0m \033[1;36m%s\033[0m\n" % (decode_data["message"], decode_data["time"]))
                elif decode_data["type"] == "newfile":
                    print("\033[1;33m%s\033[0m \033[1;32mupload %s at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["name"], decode_data["message"], decode_data["time"]))
                elif decode_data["type"] == "uploadok":
                    filename = decode_data["message"]
                    if filename in sendfile_thread:
                        sendfile_thread[filename].start()
                elif decode_data["type"] == "fileblock":
                    filename = decode_data["name"]
                    file_block = decode_data["message"]
                    file_fp[filename].write(file_block)
                elif decode_data["type"] == "fileblockover":
                    filename = decode_data["name"]
                    file_fp[filename].close()
                    print ("\033[1;32m%s downloaded successfully!\033[0m\n" % (filename))
                elif decode_data["type"] == "allfile":
                    print("\033[1;32mAll file in the server:\033[0m")
                    for f in decode_data["message"]:
                        print(f)
                    print()
                else:
                    print("\033[1;36m%s\033[0m\n\033[1;33m%s: \033[0m%s\n" % (decode_data["time"], decode_data["name"], decode_data["message"]))
            except:
                pass
            dataBuffer = dataBuffer[4 + length[0]:]


# 处理Ctrl C退出
def exit_me(signum, frame):
    send_mag_byte = sendmeg.create_send_msg_byte(name, type="quit_re")
    client.send(send_mag_byte)
    data = client.recv(1024)
    decode_data = eval(data[4:])
    if decode_data["type"] == "quit_ok":
        print("\033[1;31mQuit successfully!\033[0m\n")
    time.sleep(1)
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_me)
    signal.signal(signal.SIGTERM, exit_me)
    # 询问用户名并尝试连接
    name = input("\033[1;32mPlease input your name: \033[0m")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 6999))
    # 发送连接请求
    send_name = sendmeg.create_send_msg_byte(name)
    client.send(send_name)
    # 等待服务端回复
    data = client.recv(1024)
    decode_data = eval(data[4:])
    # 连接失败
    if decode_data["type"] == "join_f":
        print("\033[1;31mJoin failed!\033[0m\n")
        socket.SHUT_RDWR
        client.close()
    # 连接成功
    else:
        print("\033[1;32mJoin successfully!\033[0m\n")
        # 发送消息进程
        t1 = threading.Thread(target=send, args=(name, client))
        # 接受消息进程
        t2 = threading.Thread(target=receive, args=(name, client))
        # 心跳进程
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
