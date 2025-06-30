import sounddevice as sd                      # Thư viện ghi âm và phát âm thanh theo thời gian thực
from scipy.io.wavfile import write, read      # Ghi và đọc file WAV dùng scipy

# ===== Ghi âm từ micro và lưu thành file WAV =====
def record_audio(filename, duration=3, samplerate=44100):
    print("🎤 Đang ghi âm...")
    # Ghi âm trong khoảng 'duration' giây, tần số mẫu mặc định 44100 Hz (CD quality)
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    sd.wait()  # Đợi đến khi ghi âm xong
    write(filename, samplerate, audio)  # Lưu dữ liệu âm thanh vào file WAV
    print("✅ Đã ghi âm xong.")

# ===== Phát lại file âm thanh WAV =====
def play_audio(filename):
    print("🔊 Đang phát âm thanh...")
    samplerate, data = read(filename)   # Đọc dữ liệu và tần số mẫu từ file WAV
    sd.play(data, samplerate)          # Phát âm thanh với đúng tần số mẫu
    sd.wait()                          # Đợi đến khi phát xong
