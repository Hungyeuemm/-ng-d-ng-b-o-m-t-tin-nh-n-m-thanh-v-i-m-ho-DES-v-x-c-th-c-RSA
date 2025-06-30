import socket
import threading
import base64
from config import *
from network_utils import send_json, recv_json
from crypto_utils import *
from audio_utils import record_audio, play_audio
import time

def handle_connection(sock, is_server):
    try:
        # === Trao đổi khóa công khai ===
        send_json(sock, { 'type': 'public_key', 'data': open(PUBLIC_KEY_FILE, 'rb').read().decode() })
        peer_key_data = recv_json(sock)
        peer_public_key = load_rsa_public_key_from_str(peer_key_data['data'])

        # === Gửi xác thực ===
        my_name = input("\U0001F464 Nhập tên của bạn: ")
        signature = sign_data(my_name.encode(), load_rsa_private_key(PRIVATE_KEY_FILE))
        send_json(sock, {
            'type': 'auth',
            'name': my_name,
            'signature': base64.b64encode(signature).decode()
        })

        # === Nhận xác thực ===
        peer_auth = recv_json(sock)
        verify_signature(
            peer_auth['name'].encode(),
            base64.b64decode(peer_auth['signature']),
            peer_public_key
        )
        print(f"\U0001F510 Đã xác thực {peer_auth['name']}")

        # === Trao đổi khóa DES ===
        des_key = generate_des_key()
        encrypted_key = rsa_encrypt(des_key, peer_public_key)
        send_json(sock, {
            'type': 'des_key',
            'data': base64.b64encode(encrypted_key).decode()
        })

        # Nhận khóa DES từ phía bên kia
        key_data = recv_json(sock)
        des_key_received = rsa_decrypt(base64.b64decode(key_data['data']), load_rsa_private_key(PRIVATE_KEY_FILE))

    except Exception as e:
        print("\u274c Lỗi trong quá trình bắt tay:", e)
        sock.close()
        return

    # === Thread nhận tin nhắn ===
    def receive():
        while True:
            try:
                msg = recv_json(sock)
                if msg['type'] == 'text':
                    plaintext = des_decrypt(base64.b64decode(msg['data']), des_key_received).decode()
                    print(f"\n\U0001F4AC Tin nhắn: {plaintext}")
                elif msg['type'] == 'voice':
                    ciphertext = base64.b64decode(msg['data'])
                    decrypted = des_decrypt(ciphertext, des_key_received)
                    with open(TEMP_RECEIVE_FILE, 'wb') as f:
                        f.write(decrypted)
                    play_audio(TEMP_RECEIVE_FILE)
            except Exception as e:
                print("\u274c Lỗi nhận tin nhắn:", e)
                break

    threading.Thread(target=receive, daemon=True).start()

    # === Luồng gửi tin nhắn ===
    while True:
        try:
            print("\n1. Gửi văn bản")
            print("2. Gửi âm thanh")
            choice = input("Chọn: ")
            if choice == '1':
                text = input("Nhập tin nhắn: ")
                encrypted = des_encrypt(text.encode(), des_key)
                send_json(sock, {
                    'type': 'text',
                    'data': base64.b64encode(encrypted).decode()
                })
            elif choice == '2':
                record_audio(TEMP_SEND_FILE)
                with open(TEMP_SEND_FILE, 'rb') as f:
                    audio_data = f.read()
                encrypted = des_encrypt(audio_data, des_key)
                send_json(sock, {
                    'type': 'voice',
                    'data': base64.b64encode(encrypted).decode()
                })
        except Exception as e:
            print("\u274c Lỗi gửi tin nhắn:", e)
            break

def main():
    print("Chọn chế độ:")
    print("1. Máy chủ (chờ kết nối)")
    print("2. Máy khách (kết nối đến máy chủ)")
    mode = input("> ")

    if mode == '1':
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen()
            print("\U0001F7E2 Đang chờ kết nối...")
            conn, _ = s.accept()
            print("\U0001F7E2 Máy khách đã kết nối.")
            handle_connection(conn, is_server=True)
    elif mode == '2':
        with socket.socket() as s:
            time.sleep(1)  # tránh connect sớm khi server chưa sẵn sàng
            s.connect((HOST, PORT))
            print("\U0001F7E2 Máy khách đã kết nối.")
            handle_connection(s, is_server=False)

if __name__ == "__main__":
    main()
