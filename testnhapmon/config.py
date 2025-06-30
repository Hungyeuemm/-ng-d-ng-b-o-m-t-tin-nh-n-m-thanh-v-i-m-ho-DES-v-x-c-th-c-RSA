# config.py
HOST = '127.0.0.1'# tu ket noi voi chinh minh
PORT = 12354

# ✅ Đặt đúng tên file chứa khóa
PUBLIC_KEY_FILE = 'keys/sender_public.pem'     # hoặc receiver tùy máy
PRIVATE_KEY_FILE = 'keys/sender_private.pem'   # hoặc receiver tùy máy
#Đường dẫn đến file chứa khóa RSA công khai (public.pem) và khóa riêng tư (private.pem).
TEMP_SEND_FILE = 'temp_send.wav'#chứa âm thanh sau khi thu từ mic để mã hóa gửi đi.
TEMP_RECEIVE_FILE = 'temp_receive.wav'#chứa âm thanh đã giải mã từ người nhận để phát lại.
DES_KEY_SIZE = 8  # DES key size in bytes (64 bits)