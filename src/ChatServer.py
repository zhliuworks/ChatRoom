import socket
import threading
import queue
import json
import time
import sys

PORT = 6666
msgque = queue.Queue()  # 消息队列：用于存储转发所有客户端发来的消息至其它已连接的客户端
lock = threading.RLock() # 可重入锁：保证线程安全，多线程操作数据修改不会混乱
users = []  # 在线用户信息列表：包括 (conn, user, addr)


''' 当前在线用户列表，需要在每个客户端实时更新 '''
def onlines():
    online_list = []
    for each in users:
        online_list.append(each[1])
    return json.dumps(online_list).encode() # 将list序列化为JSON格式并转换为二进制


class ChatServer(threading.Thread):
    global users, que, lock

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    ''' tcp_connect：处理和维持TCP连接，接收客户端发送的消息 '''
    def tcp_connect(self, conn, addr):
        user = conn.recv(1024).decode()  # 接收用户名user

        # 处理用户同名情况
        repeat_times = 0
        for each in users:
            if user == each[1]:
                repeat_times += 1
        if repeat_times != 0:
            user = user + '_' + str(repeat_times)

        # 用户没有输入用户名，默认IP:port作为用户名
        if user == 'default':
            user = addr[0] + ':' + str(addr[1])

        # 将当前用户添加到在线用户列表
        users.append((conn, user, addr))

        print('Connect from user [', user, ']', addr)

        # 刷新所有客户端的在线用户显示
        self.recv(onlines())

        # 维持TCP连接，接收客户端发送信息
        try:
            while True:
                data = conn.recv(1024)  # 每次最多接收1kB
                self.recv(data)
            conn.close()
        except:
            print('Disconnect from user [', user, ']', addr)
            self.delUser(user)    # 将断开连接的用户从users列表中删除
            conn.close()


    ''' delUser：将断开连接的用户从users列表中删除，更新在线用户显示 '''
    def delUser(self, user):
        for i in range(len(users)):
            if user == users[i][1]:
                users.pop(i)
                self.recv(onlines())
                break


    ''' recv：将从客户端接收到的消息存入消息队列，等待转发至各个客户端 '''
    def recv(self, msg):
        lock.acquire()
        try:
            msgque.put(msg)
        finally:
            lock.release()


    ''' forward：由一个线程来处理，将队列中的消息转发给所有客户端 '''
    def forward(self):
        while True:
            if not msgque.empty():
                msg = msgque.get()
                for each in users:
                    each[0].send(msg)


    ''' run：运行服务（重写Thread类run方法） '''
    def run(self):
        self.sock.bind(('0.0.0.0', PORT))  # 监听指定端口PORT
        self.sock.listen(5)   # 开始监听，等待连接的最大数量为5
        print('ChatServer starts running ...')
        q = threading.Thread(target=self.forward)  # 创建线程处理数据转发
        q.start()
        while True:
            conn, addr = self.sock.accept()    # 接受一个新连接
            t = threading.Thread(target=self.tcp_connect, args=(conn, addr))    # 处理新的TCP连接
            t.start()
        self.sock.close()


if __name__ == '__main__':
    server = ChatServer(PORT)
    server.start()

    while True:
        time.sleep(1)
        if not server.is_alive():
            print("Chat connection lost...")
            sys.exit(0)
