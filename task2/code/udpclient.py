import threading
import time
import socket
import struct
import pandas

TYPE_INIT = 1
TYPE_AGREE = 2
TYPE_REQUEST = 3
TYPE_ANSWER = 4

lock = threading.Lock()
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_open = False


class RecPacket:
    def __init__(self, send_type, send_data: bytes, send_timestamp: int, send_address: tuple, send_id: int):
        self.send_type = send_type
        self.send_data = send_data
        self.send_timestamp = send_timestamp
        self.send_address = send_address
        self.send_id = send_id


class LockDict:
    def __init__(self):
        self.lock = threading.Lock()
        self.dict = {}

    def locked(self):
        return self.lock


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
        client.connect((socket.gethostbyname(HOST), PORT))
        client_open = True
        break
    except socket.gaierror | ValueError:
        print("尝试连接服务器失败，请检查输入的地址与端口是否正确后重新输入(仅支持ipv4)")


def is_same_ip(ip1, ip2):
    return socket.gethostbyname(ip1) == socket.gethostbyname(ip2)


def get_timestamp():
    return int(time.time() * 1000)


def create_packet(packet: RecPacket):
    return struct.pack('!BQI', packet.send_type, packet.send_timestamp, packet.send_id) + packet.send_data


def unpack_packet(address, data):
    send_type, timestamp, send_id = struct.unpack('!BQI', data[:13])
    send_data = data[13:]
    return RecPacket(send_type, send_data, timestamp, address, send_id)


def handle_receive():
    global window_size, packet_num, timeout, rtt_arr, client_open
    while client_open:
        data_rec, address_rec = client.recvfrom(1024)
        packet = unpack_packet(address_rec, data_rec)
        with window_packets.locked():
            if packet.send_id not in sent_suc_packets:
                sent_suc_packets.add(packet.send_id)
                window_size += len(window_packets.dict.get(packet.send_id)[2])
                window_packets.dict.pop(packet.send_id)
                rtt = get_timestamp() - packet.send_timestamp
                rtt_arr.append(rtt)
                print(
                    f"第{packet.send_id + 1}个(第{packet.send_id * per_packet_size + 1}~{per_packet_size * packet.send_id + per_packet_size}字节)server端已收到, RTT是{rtt}ms")
                packet_num -= 1
                timeout = (timeout + rtt) // (total_packets_num - packet_num)
            if packet_num == 0:
                client_open = False
                client.close()
                print(f"丢包率: {total_resent_packets_num / total_packets_num * 100}%")
                rtt_series = pandas.Series(rtt_arr)
                print(f"最大RTT为{rtt_series.max()} 最小RTT为{rtt_series.min()} 平均RTT为{rtt_series.mean()} RTT的标准差为{rtt_series.std()}")


server_thread = threading.Thread(target=handle_receive)
server_thread.start()


def resend_packet():
    global window_packets, total_resent_packets_num
    while client_open:
        time.sleep(0.02)
        to_resend = []
        with window_packets.locked():
            for packet_id, (timestamp, times, data) in window_packets.dict.items():
                if get_timestamp() - timestamp > timeout:
                    to_resend.append((packet_id, timestamp, times, data))

        for packet_id, timestamp, times, data in to_resend:
            if packet_id in sent_suc_packets:
                continue
            total_resent_packets_num += 1
            packet = create_packet(RecPacket(TYPE_REQUEST, data.encode(), get_timestamp(), (), packet_id))
            if client_open:
                client.sendto(packet, (HOST, PORT))
                with window_packets.locked():
                    window_packets.dict[packet_id] = (get_timestamp(), times + 1, data)
                if packet_id in sent_suc_packets:
                    total_resent_packets_num -= 1
                    continue
                print(
                    f"重传第{packet_id + 1}个(第{packet_id * per_packet_size + 1}~{(packet_id + 1) * per_packet_size}字节)数据包")


resend_thread = threading.Thread(target=resend_packet)
resend_thread.start()

total_packets_num = 200
packet_num = 200
window_size = 400
sent_packets_num = 0
sent_suc_packets = set()
per_packet_size = 80
window_packets = LockDict()
timeout = 500
total_resent_packets_num = 0
rtt_arr = []

while sent_packets_num < total_packets_num:
    if window_size < per_packet_size:
        continue
    send_data = ' ' * per_packet_size
    client.sendto(create_packet(RecPacket(TYPE_REQUEST, send_data.encode(), get_timestamp(), (), sent_packets_num)),
                  (HOST, PORT))
    window_size -= per_packet_size
    with window_packets.locked():
        window_packets.dict[sent_packets_num] = (get_timestamp(), 0, send_data)
    print(
        f"第{sent_packets_num + 1}个(第{sent_packets_num * per_packet_size + 1}~{(sent_packets_num + 1) * per_packet_size}字节)client端已发送")
    sent_packets_num += 1
