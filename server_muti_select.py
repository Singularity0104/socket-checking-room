import socket
import threading
from datetime import datetime
import sendmeg
import select
import time
import queue
import struct
import os

workerThreadNum = 8
inputs = {}
outputs = {}
dataBuffer = {}
all_name = {}
all_id = {}
all_name_list = []
all_client = []
ping_list = {}
map_name = {}
file_fp = {}

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# server.bind(('192.168.43.122',6999))
server.bind(('localhost',6999))
server.listen(5)

def join_conn(name, conn, workerId):
    all_client.append(conn)
    inputs[workerId].append(conn)
    all_name[conn] = name
    all_id[conn] = workerId
    all_name_list.append(name)
    dataBuffer[conn] = bytes()
    ping_list[conn] = datetime.now()
    map_name[name] = conn

def remove_conn(name, conn, workerId):
    all_client.remove(conn)
    inputs[workerId].remove(conn)
    if conn in outputs[workerId]:
        outputs[workerId].remove(conn)
    all_name.pop(conn)
    all_name_list.remove(name)
    all_id.pop(conn)
    ping_list.pop(conn)
    dataBuffer.pop(conn)
    map_name.pop(name)
    conn.close()


def check_ping():
    while True:
        try:
            for c in ping_list:
                if (datetime.now() - ping_list[c]).seconds > 3:
                    print("loss ping!")
                    # remove_conn(all_name[c], c, all_id[c])
            # print("check ok!")
        except:
            pass
        time.sleep(0.05)
    
def sendfile(name, conn, filename, filepath):
    time.sleep(0.5)
    print("send begin")
    if os.path.isfile(filepath):
        fp = open(filepath, 'rb')
        b = 0
        while True:
            time.sleep(0.001)
            data = fp.read(512)
            if not data:
                fp.close()
                print ('{0} file send over...'.format(os.path.basename(filepath)))
                break
            send_data = sendmeg.create_send_msg_byte(filename, type="fileblock", msg=data)
            print(filename, "block", b)
            # send_data = sendmeg.create_send_msg_byte(dest, type="fileblock", msg=data.decode())
            conn.send(send_data)
            b += 1
    enddata = sendmeg.create_send_msg_byte(filename, type="fileblockover")
    conn.send(enddata)
    return
                

def connect(data, name, conn, workerId):
    # data = conn.recv(1024)
    try:
        decode_data = eval(data)
        if decode_data["type"] == "quit_re":
            if decode_data["name"] == "test":
                print("\033[1;32mtest end\033[0m \033[1;36m%s\033[0m\n" % (decode_data["time"]))
            else:
                print("\033[1;33m%s\033[0m \033[1;31mquit the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (name, decode_data["time"]))
                send_quit_ok = sendmeg.create_send_msg_byte("server", type="quit_ok")
                conn.send(send_quit_ok)
                remove_conn(name, conn, workerId)
                send_quit = sendmeg.create_send_msg_byte("server", type="quit_inf", msg=name, time=decode_data["time"])
                for c in all_client:
                    c.send(send_quit)
        elif decode_data["type"] == "ping":
            # print(name, "ping ok!")
            ping_list[conn] = datetime.now()
            conn.send(sendmeg.create_send_msg_byte("server", type="pong"))
        elif decode_data["type"] == "upload":
            filename = decode_data["message"]
            print(name, "want to upload", filename)
            fp = open('./serverfile/' + filename, 'wb')
            file_fp[filename] = fp
            print(fp)
            print(file_fp[filename])
            conn.send(sendmeg.create_send_msg_byte("server", type="uploadok", msg=filename))
            print ('start receiving...', filename)
        elif decode_data["type"] == "download":
            filename = decode_data["message"]
            filepath = "./serverfile/" + filename
            print(name, "want to download", filename)
            s = threading.Thread(target=sendfile, args=("server", conn, filename, filepath))
            s.start()
        elif decode_data["type"] == "ls":
            conn.send(sendmeg.create_send_msg_byte("server", type="allfile", msg=(os.listdir("./serverfile"))))
        elif decode_data["type"] == "fileblock":
            filename = decode_data["name"]
            print(filename, "block")
            file_block = decode_data["message"]
            file_fp[filename].write(file_block)
        elif decode_data["type"] == "fileblockover":
            filename = decode_data["name"]
            file_fp[filename].close()
            print(filename, "end receive...")
            for c in all_client:
                c.send(sendmeg.create_send_msg_byte(name, type="newfile", msg=filename))
        else:
            print("\033[1;36m%s\033[0m\n\033[1;33m%s: \033[0m%s\n" % (decode_data["time"], name, decode_data["message"]))
            length = len(data)
            header = struct.pack("!1I", length)
            for c in all_client:
                c.send(header + data)
    except:
        pass

            
def workerThread(workerId):
    while True:
        # print("in")
        time.sleep(0.001)
        while(len(inputs[workerId]) + len(outputs[workerId])) <= 0:
            time.sleep(0.5)
        r_list, w_list, e_list = select.select(inputs[workerId], outputs[workerId], inputs[workerId], 100)
        # print(r_list)
        # print(w_list)
        # print(e_list)
        for obj in r_list:
            data = obj.recv(2048)
            # print(data)
            if len(data) == 0:
                name = all_name[obj]
                print("\033[1;31msomething wrong with\033[0m \033[1;33m%s\033[0m \033[1;31mat\033[0m \033[1;36m%s\033[0m\n" % (name, datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
                remove_conn(all_name[obj], obj, workerId)
                send_quit = sendmeg.create_send_msg_byte("server", type="quit_acc", msg=name)
                for c in all_client:
                    c.send(send_quit)
            else:
                dataBuffer[obj] += data
                if obj not in outputs[workerId]:
                    outputs[workerId].append(obj)
        for w_obj in w_list:
            # try:
            #     while not dataBuffer[w_obj].empty():
            #         t_data = dataBuffer[w_obj].get()
            #         connect(t_data,all_name[obj], w_obj, workerId)
            #     outputs[workerId].remove(w_obj)
            # except:
            #     pass
            try:
                while len(dataBuffer[w_obj]) > 4:
                    length = struct.unpack('!1I', dataBuffer[w_obj][:4])
                    if len(dataBuffer[w_obj]) < 4 + length[0]:
                        print("continue receive")
                        break
                    body = dataBuffer[w_obj][4: 4 + length[0]]
                    connect(body,all_name[w_obj], w_obj, workerId)

                    # 获取下一个数据包，类似于把数据pop出去
                    dataBuffer[w_obj] = dataBuffer[w_obj][4 + length[0]:]
            except:
                pass
        for e_obj in e_list:
            print(e_obj, "ERROR!")

if __name__ == "__main__":
    for i in range(0,workerThreadNum):
        inputs[i] = []
        outputs[i] = []
        worker = threading.Thread(target=workerThread, args=(i,))
        worker.start()

    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind(('localhost',6999))
    server.listen(5)

    ping_checker = threading.Thread(target=check_ping)
    ping_checker.start()

    index = 0
    test_num = 0
    while True:
        conn, addr = server.accept()
        data = conn.recv(1024)
        conn.setblocking(0)
        decode_data = eval(data[4:])
        if decode_data["name"] == "test":
            send_join_ok = sendmeg.create_send_msg_byte("server", type="join_ok")
            conn.send(send_join_ok)
            print("\033[1;32mtest %d begin\033[0m \033[1;36m%s\033[0m\n" % (test_num, decode_data["time"]))
            workerId = index % workerThreadNum
            name = "test" + str(test_num)
            join_conn(name, conn, workerId)
            index = index + 1
            test_num = test_num + 1
        elif decode_data["name"] in all_name_list:
            send_join_failed = sendmeg.create_send_msg_byte("server", type="join_f")
            conn.send(send_join_failed)
            conn.close()
        else:
            send_join_ok = sendmeg.create_send_msg_byte("server", type="join_ok")
            conn.send(send_join_ok)
            print("\033[1;33m%s\033[0m \033[1;32mjoin the chatting room at\033[0m \033[1;36m%s\033[0m\n" % (decode_data["name"], decode_data["time"]))
            send_join = sendmeg.create_send_msg_byte("server", type="join_inf", msg=decode_data["name"], time=decode_data["time"])
            for c in all_client:
                c.send(send_join)
            workerId = index % workerThreadNum
            join_conn(decode_data["name"], conn, workerId)
            index = index + 1
    server.close()

