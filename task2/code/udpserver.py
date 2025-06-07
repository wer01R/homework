import socket
import threading
import struct

TYPE_INIT = 1
TYPE_AGREE = 2
TYPE_REQUEST = 3
TYPE_ANSWER = 4
HOST = '127.0.0.1'
PORT = 3000


server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

def create_packet(send_type, send_data: bytes):
    length = len(send_data)
    return struct.pack('!BI', send_type, length) + send_data

def handle_client(address_rec, data_rec):


while True:
    try:
        data, address = server.recvfrom(1024)
        client_thread = threading.Thread(target=handle_client, args=(address, data))
        client_thread.start()


