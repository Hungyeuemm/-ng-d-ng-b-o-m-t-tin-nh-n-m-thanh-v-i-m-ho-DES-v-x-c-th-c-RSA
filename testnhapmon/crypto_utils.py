import base64
from Crypto.Cipher import DES, PKCS1_OAEP  # Thư viện mã hóa DES và RSA (OAEP)
from Crypto.PublicKey import RSA           # Quản lý khóa RSA
from Crypto.Signature import pkcs1_15      # Thư viện ký số RSA (PKCS#1 v1.5)
from Crypto.Hash import SHA256             # Thuật toán băm SHA-256
from Crypto.Random import get_random_bytes # Sinh dữ liệu ngẫu nhiên an toàn
from config import DES_KEY_SIZE            # Kích thước khóa DES từ file config

# ===== Hàm padding cho dữ liệu trước khi mã hóa DES =====
def pad(data):
    pad_len = 8 - len(data) % 8
    return data + bytes([pad_len]) * pad_len

#Bổ sung byte đệm để độ dài data chia hết cho 8 (yêu cầu của DES – block size = 8).

# ===== Hàm loại bỏ padding sau khi giải mã DES =====
def unpad(data):
    return data[:-data[-1]]
#Xóa phần padding sau khi giải mã để khôi phục dữ liệu gốc.

# ===== Sinh khóa DES ngẫu nhiên 8 byte =====
def generate_des_key():
    return get_random_bytes(DES_KEY_SIZE)

# ===== Mã hóa dữ liệu bằng DES (CBC mode) với IV ngẫu nhiên =====
def des_encrypt(data, key):
    iv = get_random_bytes(8)  # Sinh IV 8 byte
    cipher = DES.new(key, DES.MODE_CBC, iv)
    return iv + cipher.encrypt(pad(data))  # Ghép IV + ciphertext

# ===== Giải mã dữ liệu DES (CBC mode) =====
def des_decrypt(ciphertext, key):
    iv = ciphertext[:8]  # Lấy IV từ đầu
    cipher = DES.new(key, DES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext[8:]))

# ===== Tạo đối tượng băm SHA-256 từ dữ liệu =====
def hash_data(data):
    return SHA256.new(data)

# ===== Ký dữ liệu bằng RSA private key =====
def sign_data(data, private_key):
    h = hash_data(data)
    return pkcs1_15.new(private_key).sign(h)

# ===== Xác thực chữ ký RSA bằng public key =====
def verify_signature(data, signature, public_key):
    h = hash_data(data)
    pkcs1_15.new(public_key).verify(h, signature)
#sign_data: tạo chữ ký RSA với private key trên bản băm của data.
# ===== Tải khóa RSA private từ file =====
def load_rsa_private_key(path):
    return RSA.import_key(open(path, 'rb').read())

# ===== Tải khóa RSA public từ file =====
def load_rsa_public_key(path):
    return RSA.import_key(open(path, 'rb').read())

# ===== Tải khóa RSA public từ chuỗi (dùng khi nhận qua mạng) =====
def load_rsa_public_key_from_str(s):
    return RSA.import_key(s.encode())

# ===== Mã hóa dữ liệu bằng RSA public key (PKCS1_OAEP) =====
def rsa_encrypt(data, public_key):
    return PKCS1_OAEP.new(public_key).encrypt(data)

# ===== Giải mã RSA ciphertext bằng private key (PKCS1_OAEP) =====
def rsa_decrypt(ciphertext, private_key):
    return PKCS1_OAEP.new(private_key).decrypt(ciphertext)
