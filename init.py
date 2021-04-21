import time
import struct

port = 6999

HEADERSIZE = 12
HEART_BEAT = 0          # 心跳包类型：0
NORMAL = 1              # 普通消息类型：1

QUIT = ':q'
