import random
import socket
import struct

TYPE_INIT = 1
TYPE_AGREE = 2
TYPE_REQUEST = 3
TYPE_ANSWER = 4


def client_main():
    while True:
        try:
            HOST = input("输入要连接的服务器的地址：").strip(' ')
            while True:
                try:
                    PORT = int(input("输入要连接的服务器的端口：").strip(' '))
                    if PORT < 0 or PORT > 65535:
                        raise ValueError
                    break
                except ValueError:
                    print("端口输入错误，请输入一个0~65535的整数")
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((HOST, PORT))
            break
        except socket.gaierror:
            print("尝试连接服务器失败，请检查输入的地址与端口是否正确后重新输入")
    while True:
        try:
            Lmin = int(input("输入最小长度：").strip(' '))
            Lmax = int(input("输入最大长度：").strip(' '))
            if Lmin > Lmax:
                raise ValueError
            break
        except ValueError:
            print("长度输入错误，请输入正整数并且最小长度不得大于最大长度")

    def create_packet(send_type, send_data: bytes):
        length = len(send_data)
        return struct.pack('!BI', send_type, length) + send_data
    def receive_n(receive_socket, n):
        data_receive = b''
        while len(data_receive) < n:
            pack = receive_socket.recv(n - len(data_receive))
            if not pack:
                break
            data_receive += pack
        return data_receive
    def receive_packet(receive_socket):
        header = receive_n(receive_socket, 5)
        type, length = struct.unpack('!BI', header)
        body = receive_n(receive_socket, length)
        return type, length, body


    with open('source.txt', 'r', encoding='utf-8') as f:
        data = f.read()

    index, arr = 0, []
    while index < len(data):
        ran = random.randint(Lmin, Lmax)
        l = min(ran + index, len(data))
        arr.append(data[index:l])
        index = l

    client.sendall(create_packet(TYPE_INIT, len(arr).to_bytes()))
    type, length, body = receive_packet(client)
    if type == TYPE_AGREE:
        get = []
        for i in range(len(arr)):
            client.sendall(create_packet(TYPE_REQUEST, arr[i].encode()))
            type, length, body = receive_packet(client)
            print(f'{i + 1}: {body.decode()}')
            get.append(body.decode())
        print("传输完成")
        print("开始写文件")
        with open('target.txt', 'w', encoding='utf-8') as f:
            for i in range(len(get) - 1, -1, -1):
                f.write(get[i])
        print("文件写入完成，保存在target.txt当中")
    else:
        print("服务器拒绝连接")

    client.close()


client_main()