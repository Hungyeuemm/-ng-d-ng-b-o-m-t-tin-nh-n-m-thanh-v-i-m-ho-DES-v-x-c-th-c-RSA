import json
import struct

def send_json(sock, data):
    """
    Gửi một đối tượng Python (dict, list...) dưới dạng JSON qua socket.
    Dữ liệu được đóng gói: [4 byte độ dài] + [nội dung JSON mã hóa]
    """
    msg = json.dumps(data).encode()  # Mã hóa đối tượng Python thành bytes JSON
    sock.sendall(len(msg).to_bytes(4, 'big') + msg)  # Gửi độ dài (4 byte big-endian) + nội dung

def recv_json(sock):
    """
    Nhận dữ liệu JSON từ socket.
    Đầu tiên nhận 4 byte độ dài → sau đó nhận đúng số byte của nội dung JSON → decode thành dict.
    """
    raw_len = recvall(sock, 4)  # Nhận 4 byte đầu tiên chứa độ dài nội dung
    if not raw_len:
        return None  # Nếu không nhận được gì thì trả về None
    msg_len = struct.unpack('>I', raw_len)[0]  # Giải mã 4 byte độ dài (big-endian unsigned int)
    return json.loads(recvall(sock, msg_len).decode())  # Nhận đủ msg_len byte rồi decode thành object

def recvall(sock, n):
    """
    Hàm hỗ trợ: đảm bảo nhận đúng n byte từ socket, kể cả khi recv trả về từng phần nhỏ.
    """
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))  # Nhận phần còn thiếu
        if not packet:
            return None  # Nếu bị ngắt kết nối
        data += packet
    return data
