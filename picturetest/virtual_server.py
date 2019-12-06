# 向client发送图片
import time
import socket
import os,struct,sys
import shutil

#树莓派的监听地址
host = "127.0.0.1"
port = 7777


print("Starting socket: TCP...")
socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建socket
host_addr = (host, port)
socket_tcp.bind(host_addr)  # 绑定我的树莓派的ip地址和端口号
socket_tcp.listen(1)  # listen函数的参数是监听客户端的个数，这里只监听一个，即只允许与一个客户端创建连接


#等待连接
print('waiting for connection...')
socket_con, (client_ip, client_port) = socket_tcp.accept()  # 接收客户端的请求
print("Connection accepted from %s." % client_ip)
info = "已连接"

#相片编号
tag = 1

#接收到服务器信息则开始解析
#收到message 为‘picture’，则主机发送图片
#收到message 为‘quit’， 主机结束连接
#收到message 为‘danger’，发现危险情况，服务器保存相应图片，并控制小车发出警报

while True:
    print("Waiting for instructions")
    message = socket_con.recv(1024)
    message = message.decode()
    if message == 'picture':
        if tag == 1:
            filepath = 'bird.jpg'
        else:
            filepath = 'people.jpg'
        if os.path.isfile(filepath):
            # 定义定义文件信息。128s表示文件名为128bytes长，l表示一个int或log文件类型，在此为文件大小
            fileinfo_size = struct.calcsize('128sl')
            # 定义文件头信息，包含文件名和文件大小
            fhead = struct.pack('128sl', bytes(os.path.basename(filepath).encode('utf-8')), os.stat(filepath).st_size)
            socket_con.send(fhead)

            fp = open(filepath, 'rb')
            while 1:
                data = fp.read(1024)
                if not data:
                    print ('{0} file send over...'.format(filepath))
                    break
                socket_con.send(data)

        tag = tag + 1

    elif message == 'danger':
        # 树莓派将不用存储照片
        #src = '/home/pi/Desktop/image%s.jpg'%(i-1)
        #dst = 'home/pi/Desktop/dangerimg/image%s.jpg'%j
        #shutil.copyfile(src, dst)

        ####
        #蜂鸣器模块调用
        ####
        print("ring start...")
        # 模拟响铃3秒
        tik = time.time()
        while time.time() - tik < 3:
            continue
        print("ring finish")
        socket_con.send('ring_finished'.encode())
        print("Detected person stored")
        continue

    else:
        socket_con.close()
        print("server close")
        break

    
    
