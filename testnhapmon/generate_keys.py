# ✅ File: config.py
IS_SERVER = None  # được gán tại runtime (1: server, 2: client)

# Địa chỉ và cổng kết nối
HOST = "127.0.0.1"
PORT = 5000

# Kích thước key
RSA_KEY_SIZE = 2048
DES_KEY_SIZE = 8  # DES dùng 8 byte

# Thư mục chứa khóa
if IS_SERVER:
    PUBLIC_KEY_FILE = "keys/receiver_public.pem"
    PRIVATE_KEY_FILE = "keys/receiver_private.pem"
else:
    PUBLIC_KEY_FILE = "keys/sender_public.pem"
    PRIVATE_KEY_FILE = "keys/sender_private.pem"

# File tạm cho audio
temp_send_audio = "temp_send.wav"
temp_receive_audio = "temp_receive.wav"

# Kích thước mỗi chunk gửi
CHUNK_SIZE = 4096
