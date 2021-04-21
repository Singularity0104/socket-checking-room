#coding: utf-8
import time
from socket import *
from locust import TaskSet, task, between, Locust, events, User
import struct
import init
import sendmeg

def packData(data, packetType):
    # 数据包头部3个4位无符号整数：版本号 消息类型 包长度
    # 其中 packetType=0 为心跳检测包 packetType=1 为普通消息
    # 消息内部是一个字典，包括：发送者name + 发送time + 发送内容 (但是客户端已经打包好了)
    version = 1
    bodyLen = len(data)
    header = [version, packetType, bodyLen]   
    headPack = struct.pack("!3I", *header) # !代表网络字节顺序NBO（Network Byte Order），3I代表3个unsigned int数据
    return headPack + data

class SocketUser(User):
    host = gethostname()
    port = init.port
    wait_time = between(0.1, 1)     # 等待时间, 用户连续的请求之间随机等待0.1~1s

    def __init__(self, *args, **kwargs):
        super(SocketUser, self).__init__(*args, **kwargs)
        self.client = socket(AF_INET,SOCK_STREAM)

    def on_start(self):
        self.client.connect((self.host, self.port))
        send_name = sendmeg.create_send_msg_byte("test")
        self.client.send(send_name)
        time.sleep(0.1)

    def on_stop(self):
        send_mag_byte = sendmeg.create_send_msg_byte("test", type="quit_re")
        self.client.send(send_mag_byte)
        self.client.close()

    @task(100)
    def sendHeartBeat(self):
        start_time = time.time()
        try:
            self.client.send(sendmeg.create_send_msg_byte("test", type="ping"))
            # time.sleep(1)
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="Normal", name="SendMessage", response_time=total_time, response_length=0, exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="Normal", name="SendMessage", response_time=total_time, response_length=0)


        start_time = time.time()
        try:
            data = self.client.recv(1024)
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="Normal", name="RecvMessage", response_time=total_time, response_length=0, exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="Normal", name="RecvMessage", response_time=total_time, response_length=0)

        