import socket
import threading
import struct

TYPE_INIT = 1
TYPE_AGREE = 2
TYPE_REQUEST = 3
TYPE_ANSWER = 4
HOST = '127.0.0.1'
PORT = 3000


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print(f"正在监听 {HOST}:{PORT}")

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


def handle_client(client_now):
    while True:
        try:
            type, length, message = receive_packet(client_now)
            if type == TYPE_INIT:
                client_now.sendall(create_packet(TYPE_AGREE, b''))
            else:
                client_now.sendall(create_packet(TYPE_ANSWER, message[::-1]))
        except ConnectionResetError:
            break
    client_now.close()


while True:
    client, address = server.accept()
    client_thread = threading.Thread(target=handle_client, args=(client, ))
    client_thread.start()
