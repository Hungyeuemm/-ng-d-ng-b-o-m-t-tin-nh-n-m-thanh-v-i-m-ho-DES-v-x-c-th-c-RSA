import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import socket
import base64
import time
from config import *
from network_utils import send_json, recv_json
from crypto_utils import *
from audio_utils import record_audio, play_audio

class SecureChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Chat & Voice")  # Đặt tiêu đề cửa sổ
        self.root.geometry("600x500")  # Đặt kích thước cửa sổ

        # ==== Giao diện nhập tên ====
        self.name_frame = tk.Frame(self.root)
        self.name_frame.pack(pady=10)

        tk.Label(self.name_frame, text="\U0001F464 Tên của bạn:").pack(side=tk.LEFT)
        self.name_entry = tk.Entry(self.name_frame)
        self.name_entry.pack(side=tk.LEFT, padx=5)

        # ==== Giao diện chọn chế độ máy chủ/máy khách ====
        self.mode_frame = tk.Frame(self.root)
        self.mode_frame.pack(pady=10)

        tk.Label(self.mode_frame, text="Chọn chế độ:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="server")
        tk.Radiobutton(self.mode_frame, text="\U0001F4BB Máy chủ", variable=self.mode_var, value="server").pack(side=tk.LEFT)
        tk.Radiobutton(self.mode_frame, text="\U0001F4F6 Máy khách", variable=self.mode_var, value="client").pack(side=tk.LEFT)

        # ==== Nút kết nối ====
        self.connect_button = tk.Button(self.root, text="Kết nối", command=self.connect)
        self.connect_button.pack(pady=10)

        # ==== Vùng hiển thị hội thoại ====
        self.chat_log = scrolledtext.ScrolledText(self.root, state='disabled', width=70, height=15)
        self.chat_log.pack(pady=10)

        # ==== Nhãn trạng thái đối phương ====
        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack()

        # ==== Nhập và gửi văn bản ====
        self.message_frame = tk.Frame(self.root)
        self.message_frame.pack(pady=5)

        self.message_entry = tk.Entry(self.message_frame, width=40)
        self.message_entry.pack(side=tk.LEFT, padx=5)
        self.message_entry.bind("<KeyPress>", lambda e: self.send_typing_status())
        self.send_text_button = tk.Button(self.message_frame, text="Gửi văn bản", command=self.send_text)
        self.send_text_button.pack(side=tk.LEFT)

        # ==== Gửi âm thanh ====
        self.send_audio_button = tk.Button(self.root, text="\U0001F3A4 Ghi và gửi âm thanh", command=self.send_audio)
        self.send_audio_button.pack(pady=5)

        # ==== Biến kết nối và khóa ====
        self.sock = None
        self.my_priv = None
        self.peer_pub = None
        self.des_key = None
        self.running = False

    def connect(self):
        name = self.name_entry.get()
        mode = self.mode_var.get()
        if not name:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên của bạn.")
            return

        self.append_message(f"\U0001F91D Kết nối như {name} ({'Máy chủ' if mode == 'server' else 'Máy khách'})")
        self.my_priv = load_rsa_private_key(PRIVATE_KEY_FILE)  # Tải khóa riêng
        my_pub_data = open(PUBLIC_KEY_FILE, 'rb').read().decode()  # Đọc khóa công khai

        if mode == "server":
            self.sock = socket.socket()
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((HOST, PORT))
            self.sock.listen()
            self.append_message("🟢 Đang chờ kết nối...")
            conn, _ = self.sock.accept()
            self.sock = conn
            self.append_message("🟢 Đã kết nối với máy khách.")
        else:
            time.sleep(1)  # Đợi máy chủ sẵn sàng
            self.sock = socket.socket()
            self.sock.connect((HOST, PORT))
            self.append_message("🟢 Đã kết nối tới máy chủ.")

        # ==== Gửi và nhận khóa công khai ====
        send_json(self.sock, {'type': 'public_key', 'data': my_pub_data})
        peer_key_data = recv_json(self.sock)
        self.peer_pub = load_rsa_public_key_from_str(peer_key_data['data'])

        # ==== Gửi tên đã ký ====
        signature = sign_data(name.encode(), self.my_priv)
        send_json(self.sock, {
            'type': 'auth', 'name': name, 'signature': base64.b64encode(signature).decode()
        })

        # ==== Nhận xác thực từ peer ====
        peer_auth = recv_json(self.sock)
        verify_signature(
            peer_auth['name'].encode(), base64.b64decode(peer_auth['signature']), self.peer_pub
        )
        self.append_message(f"🔐 Đã xác thực {peer_auth['name']}")

        # ==== Đồng bộ khóa DES ====
        if mode == "server":
            self.des_key = generate_des_key()
            encrypted_key = rsa_encrypt(self.des_key, self.peer_pub)
            send_json(self.sock, {'type': 'des_key', 'data': base64.b64encode(encrypted_key).decode()})
        else:
            peer_key = recv_json(self.sock)
            self.des_key = rsa_decrypt(base64.b64decode(peer_key['data']), self.my_priv)

        # ==== Bắt đầu luồng nhận ====
        self.running = True
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def receive_loop(self):
        while self.running:
            try:
                msg = recv_json(self.sock)
                if msg['type'] == 'text':
                    plaintext = des_decrypt(base64.b64decode(msg['data']), self.des_key).decode()
                    self.append_message(f"\n\U0001F4E2 Đối phương: {plaintext}")
                    self.status_label.config(text="")  # Xóa trạng thái gõ
                elif msg['type'] == 'voice':
                    data = base64.b64decode(msg['data'])
                    decrypted = des_decrypt(data, self.des_key)
                    with open(TEMP_RECEIVE_FILE, 'wb') as f:
                        f.write(decrypted)
                    self.append_message("\U0001F3A4 Đã nhận âm thanh.")
                    play_audio(TEMP_RECEIVE_FILE)
                    self.status_label.config(text="")
                elif msg['type'] == 'typing':
                    self.status_label.config(text="✍️ Đối phương đang gõ...")
                elif msg['type'] == 'recording':
                    self.status_label.config(text="🎙️ Đối phương đang ghi âm...")
            except Exception as e:
                self.append_message(f"❌ Lỗi nhận: {e}")
                break

    def send_typing_status(self):
        if self.sock:
            try:
                send_json(self.sock, {'type': 'typing'})
            except:
                pass

    def send_text(self):
        text = self.message_entry.get()
        if text and self.sock and self.des_key:
            encrypted = des_encrypt(text.encode(), self.des_key)
            send_json(self.sock, {
                'type': 'text',
                'data': base64.b64encode(encrypted).decode()
            })
            self.append_message(f"\U0001F4AC Bạn: {text}")
            self.message_entry.delete(0, tk.END)

    def send_audio(self):
        if self.sock and self.des_key:
            self.append_message("\U0001F3A4 Đang ghi âm và gửi...")
            try:
                send_json(self.sock, {'type': 'recording'})  # Gửi trạng thái đang ghi
            except:
                pass
            record_audio(TEMP_SEND_FILE)
            with open(TEMP_SEND_FILE, 'rb') as f:
                audio_data = f.read()
            encrypted = des_encrypt(audio_data, self.des_key)
            send_json(self.sock, {
                'type': 'voice',
                'data': base64.b64encode(encrypted).decode()
            })
            self.append_message("\U0001F3A4 Đã gửi âm thanh.")
            self.status_label.config(text="")

    def append_message(self, msg):
        self.chat_log.config(state='normal')
        self.chat_log.insert(tk.END, msg + '\n')
        self.chat_log.yview(tk.END)
        self.chat_log.config(state='disabled')

if __name__ == '__main__':
    root = tk.Tk()
    app = SecureChatGUI(root)
    root.mainloop()
