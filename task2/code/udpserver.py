import random
import socket
import threading
import struct
import time

TYPE_INIT = 1
TYPE_AGREE = 2
TYPE_REQUEST = 3
TYPE_ANSWER = 4
HOST = '127.0.0.1'
PORT = 3000

class RecPacket:
    def __init__(self, send_type, send_data: bytes, send_timestamp: int, send_address: tuple, send_id: int):
        self.send_type = send_type
        self.send_data = send_data
        self.send_timestamp = send_timestamp
        self.send_address = send_address
        self.send_id = send_id



server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))


def create_packet(packet: RecPacket):
    return struct.pack('!BQI', packet.send_type, packet.send_timestamp, packet.send_id) + packet.send_data


def unpack_packet(address, data):
    send_type, timestamp, send_id = struct.unpack('!BQI', data[:13])
    send_data = data[13:]
    return RecPacket(send_type, send_data, timestamp, address, send_id)


def handle_client(address_rec, data_rec):
    packet = unpack_packet(address_rec, data_rec)
    if random.random() < 0.05:
        return
    time.sleep(0.05)
    try:
        if packet.send_type == TYPE_INIT:
            server.sendto(create_packet(RecPacket(TYPE_AGREE, b'', packet.send_timestamp, packet.send_address, packet.send_id)), address_rec)
        else:
            server.sendto(create_packet(RecPacket(TYPE_ANSWER, b'', packet.send_timestamp, packet.send_address, packet.send_id)), address_rec)
    except Exception:
        return


while True:
    try:
        data, address = server.recvfrom(1024)
    except:
        continue
    client_thread = threading.Thread(target=handle_client, args=(address, data))
    client_thread.start()


