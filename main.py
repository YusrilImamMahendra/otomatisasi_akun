import os
import subprocess
import time
import uiautomator2 as u2

# Konfigurasi path dan device
MUMU_EXE_PATH = r"C:\Program Files\Netease\MuMuPlayerGlobal-12.0\shell\MuMuPlayer.exe"
ADB_PATH = r"C:\Program Files\Netease\MuMuPlayerGlobal-12.0\shell\adb.exe"
MUMU_DEVICE = "127.0.0.1:7555"

# Data akun yang ingin diregistrasikan (ganti sesuai kebutuhan)
EMAIL = "contoh.email123@gmail.com"
FULLNAME = "Nama Lengkap"
USERNAME = "usernameunik12345"
PASSWORD = "PasswordKuat2025"

def start_mumu():
    print("Menjalankan emulator MuMu...")
    subprocess.Popen([MUMU_EXE_PATH])
    # Tunggu device ready dan tidak offline
    while True:
        out = subprocess.getoutput(f'"{ADB_PATH}" devices')
        print("ADB devices output:", out)
        lines = out.splitlines()
        ready = False
        for line in lines:
            if MUMU_DEVICE in line and "device" in line and "offline" not in line:
                ready = True
                break
        if ready:
            print("Emulator siap!")
            break
        time.sleep(3)

def unlock_screen():
    print("Membuka kunci layar (jika terkunci)...")
    os.system(f'"{ADB_PATH}" -s {MUMU_DEVICE} shell input keyevent 224')  # Power on
    os.system(f'"{ADB_PATH}" -s {MUMU_DEVICE} shell input keyevent 82')   # Unlock

def wait_and_click(d, text=None, resourceId=None, timeout=20):
    for _ in range(timeout):
        if text and d(text=text).exists:
            d(text=text).click()
            return True
        if resourceId and d(resourceId=resourceId).exists:
            d(resourceId=resourceId).click()
            return True
        time.sleep(1)
    print(f"Element {text or resourceId} not found.")
    return False

def wait_for(d, text=None, resourceId=None, timeout=20):
    for _ in range(timeout):
        if text and d(text=text).exists:
            return True
        if resourceId and d(resourceId=resourceId).exists:
            return True
        time.sleep(1)
    return False

def install_instagram_lite():
    print("Menghubungkan ke emulator dengan uiautomator2...")
    d = u2.connect(MUMU_DEVICE)
    print("Membuka Google Play Store...")
    d.app_start("com.android.vending")
    time.sleep(4)

    # Klik ikon Search di sidebar kiri (by coordinate)
    print("Klik ikon Search di sidebar (by coordinate)...")
    d.click(78, 450)
    time.sleep(2)

    # Klik search bar atas
    print("Klik search bar di bagian atas...")
    if not wait_and_click(d, text="Search apps & games"):
        print("Gagal klik search bar di atas!")
        return False
    time.sleep(1)

    # Ketik 'Instagram Lite'
    print("Ketik 'Instagram Lite'...")
    d.send_keys("Instagram Lite")
    time.sleep(1)
    
    # Tekan tombol Enter pada keyboard virtual
    print("Tekan tombol Enter pada keyboard virtual...")
    d.press("enter")
    time.sleep(3)

    print("Klik hasil aplikasi 'Instagram Lite' pada hasil pencarian...")
    # Klik pada list kiri, baris Instagram Lite (bukan sponsor)
    d.click(400, 570)  # Koordinat ini perlu disesuaikan jika posisi berubah
    time.sleep(2)

    print("Klik tombol Install di panel kanan...")
    d.click(1160, 390)  # Koordinat tombol Install di panel kanan
    time.sleep(2)

    # Tunggu proses install selesai
    print("Menunggu proses install selesai (tombol Buka muncul)...")
    for _ in range(60):
        if d(text="Open").exists or d(text="Buka").exists:
            print("Instagram Lite berhasil diinstall!")
            return True
        time.sleep(2)

    print("Timeout: Gagal mendeteksi bahwa Instagram Lite sudah terinstall.")
    return False

def register_instagram_lite(email, fullname, username, password):
    d = u2.connect(MUMU_DEVICE)
    print("Membuka aplikasi Instagram Lite...")
    d.app_start("com.instagram.lite")
    time.sleep(5)

    # Step 1: Klik tombol 'Create new account' (by coordinate)
    print("Klik tombol 'Create new account' (by coordinate)...")
    d.click(450, 916)
    time.sleep(3)

    # Step 2: Klik tombol 'Sign up with email' (by coordinate)
    print("Klik tombol 'Sign up with email' (by coordinate)...")
    d.click(450, 515)
    time.sleep(3)

    # Step 3: Isi email di field (className MultiAutoCompleteTextView)
    print("Mengisi field email...")
    d(className="android.widget.MultiAutoCompleteTextView").set_text(email)
    time.sleep(1)

    # Step 4: Klik tombol "Next" (by coordinate)
    print("Klik tombol Next (by coordinate)...")
    d.click(450, 485)
    time.sleep(2)

    # Isi nama lengkap
    print("Mengisi nama lengkap...")
    if wait_for(d, resourceId="com.instagram.lite:id/full_name"):
        d(resourceId="com.instagram.lite:id/full_name").set_text(fullname)
    else:
        print("Field nama lengkap tidak ditemukan.")
        return

    # Isi username
    print("Mengisi username...")
    if wait_for(d, resourceId="com.instagram.lite:id/username"):
        d(resourceId="com.instagram.lite:id/username").set_text(username)
    else:
        print("Field username tidak ditemukan.")
        return

    # Isi password
    print("Mengisi password...")
    if wait_for(d, resourceId="com.instagram.lite:id/password"):
        d(resourceId="com.instagram.lite:id/password").set_text(password)
    else:
        print("Field password tidak ditemukan.")
        return

    wait_and_click(d, text="Next") or wait_and_click(d, text="Berikutnya")
    time.sleep(2)

    print("Jika ada verifikasi, silakan input manual atau lanjutkan automasi di sini (misal dengan OTP email/SMS).")
    print("Registrasi Instagram Lite selesai hingga tahap awal (verifikasi manual jika diperlukan).")

def main():
    start_mumu()
    unlock_screen()
    print("Menunggu 10 detik sebelum automasi Play Store...")
    time.sleep(10)
    if install_instagram_lite():
        print("Melanjutkan ke proses registrasi Instagram Lite...")
        time.sleep(5)
        register_instagram_lite(EMAIL, FULLNAME, USERNAME, PASSWORD)
    else:
        print("Automasi install Instagram Lite gagal, proses dihentikan.")
        
if __name__ == "__main__":
    main()
