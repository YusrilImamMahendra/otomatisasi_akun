import os
import subprocess
import time
import uiautomator2 as u2
import imaplib
import email
import re
from email.mime.text import MIMEText

# Konfigurasi path dan device
MUMU_EXE_PATH = r"C:\Program Files\Netease\MuMuPlayerGlobal-12.0\shell\MuMuPlayer.exe"
ADB_PATH = r"C:\Program Files\Netease\MuMuPlayerGlobal-12.0\shell\adb.exe"
MUMU_DEVICE = "127.0.0.1:7555"

# Data akun yang ingin diregistrasikan (ganti sesuai kebutuhan)
EMAIL = "cobaja.1933@gmail.com"
EMAIL_PASSWORD = "Yuima123"  # Password email untuk IMAP
FULLNAME = "Nama Lengkap"
USERNAME = "usernameunik12345"
PASSWORD = "PasswordKuat2025"

# Konfigurasi IMAP untuk Gmail (sesuaikan dengan provider email Anda)
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

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

def get_verification_code_from_email(email_address, email_password, timeout=300):
    print("Mencari kode verifikasi di email (termasuk folder Sosial)...")
    start_time = time.time()
    folders = ['inbox', '[Gmail]/Social', '[Gmail]/Sosial', 'CATEGORY_SOCIAL']
    while time.time() - start_time < timeout:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(email_address, email_password)
            # Print semua folder untuk debug
            status, allfolders = mail.list()
            print(f"Semua folder IMAP: {allfolders}")
            email_found = False
            for folder in folders:
                try:
                    result, data = mail.select(folder)
                    if result != 'OK':
                        print(f"Folder {folder} tidak ditemukan atau gagal dibuka.")
                        continue
                    print(f"Mencari di folder: {folder}")
                    result, data = mail.search(None, 'FROM "Instagram"')
                    if result == 'OK' and data[0]:
                        email_ids = data[0].split()
                        if email_ids:
                            email_found = True
                            latest_email_id = email_ids[-1]
                            result, data = mail.fetch(latest_email_id, '(RFC822)')
                            if result == 'OK':
                                raw_email = data[0][1]
                                email_message = email.message_from_bytes(raw_email)
                                subject = email_message.get('Subject', '')
                                print(f"Subject email: {subject}")

                                # Cari kode di subject dulu
                                match = re.search(r'\b(\d{6})\b', subject)
                                if match:
                                    verification_code = match.group(1)
                                    print(f"Kode verifikasi ditemukan di subject: {verification_code}")
                                    mail.close()
                                    mail.logout()
                                    return verification_code

                                # Jika tidak, cek di body
                                body = ""
                                if email_message.is_multipart():
                                    for part in email_message.walk():
                                        if part.get_content_type() == "text/plain":
                                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                            break
                                else:
                                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                                print(f"Isi email (untuk debug): {body[:200]}")
                                match = re.search(r'\b(\d{6})\b', body)
                                if match:
                                    verification_code = match.group(1)
                                    print(f"Kode verifikasi ditemukan di body: {verification_code}")
                                    mail.close()
                                    mail.logout()
                                    return verification_code
                except Exception as e:
                    print(f"Error saat cek folder {folder}: {e}")
                    continue
            mail.close()
            mail.logout()
            if not email_found:
                print("Belum ditemukan email kode verifikasi di folder mana pun.")
        except Exception as e:
            print(f"Error saat membaca email: {e}")
        print("Kode verifikasi belum ditemukan, menunggu 10 detik...")
        time.sleep(10)
    print("Timeout: Kode verifikasi tidak ditemukan dalam waktu yang ditentukan")
    return None

def manual_input_verification_code():
    """Fallback untuk input manual kode verifikasi"""
    print("\n" + "="*50)
    print("PERHATIAN: Tidak dapat mengambil kode verifikasi otomatis")
    print("Silakan cek email Anda dan masukkan kode verifikasi secara manual")
    print("="*50)
    
    while True:
        code = input("Masukkan kode verifikasi (6 digit): ").strip()
        if len(code) == 6 and code.isdigit():
            return code
        else:
            print("Kode harus 6 digit angka. Silakan coba lagi.")

def handle_email_verification(d):
    """Fungsi yang diperbaiki untuk menangani proses verifikasi email"""
    print("Mendeteksi halaman verifikasi email...")
    
    # Tunggu hingga halaman verifikasi muncul dengan lebih teliti
    verification_detected = False
    for attempt in range(60):  # tunggu maksimal 60 detik
        print(f"Attempt {attempt + 1}: Mencari halaman verifikasi...")
        indicators = [
            d(textContains="confirmation").exists,
            d(textContains="verification").exists,
            d(textContains="code").exists,
            d(textContains="confirm").exists,
            d(textContains="Enter").exists,
            d(textContains="6-digit").exists,
            d(textContains="digit").exists,
            d(className="android.widget.EditText").exists,
            d(resourceId="com.instagram.lite:id/confirmation_code").exists,
            d(className="android.widget.MultiAutoCompleteTextView").exists,
        ]
        if any(indicators):
            verification_detected = True
            print("Halaman verifikasi email terdeteksi!")
            break
        time.sleep(1)
    if not verification_detected:
        print("Halaman verifikasi tidak terdeteksi setelah 60 detik")
        return False

    time.sleep(2)
    print("=== DEBUG: Mencari field kode verifikasi ===")
    debug_screen_elements(d)

    verification_code = None
    if EMAIL_PASSWORD:
        print("Mencoba mengambil kode verifikasi dari email...")
        verification_code = get_verification_code_from_email(EMAIL, EMAIL_PASSWORD, timeout=180)
    if not verification_code:
        verification_code = manual_input_verification_code()

    print(f"Memasukkan kode verifikasi: {verification_code}")

    success = False
    possible_resource_ids = [
        "com.instagram.lite:id/confirmation_code",
        "com.instagram.lite:id/code_text",
        "com.instagram.lite:id/verify_code",
        "com.instagram.lite:id/code_input",
        "com.instagram.lite:id/verification_code",
        "com.instagram.lite:id/edittext_confirmation_code",
        "com.instagram.lite:id/code_field",
    ]
    for resource_id in possible_resource_ids:
        if d(resourceId=resource_id).exists:
            print(f"Menemukan field dengan resource ID: {resource_id}")
            try:
                code_field = d(resourceId=resource_id)
                code_field.click()
                time.sleep(1)
                code_field.clear_text()
                time.sleep(0.5)
                code_field.set_text(verification_code)
                time.sleep(1)
                current_text = code_field.get_text()
                if verification_code in current_text or len(current_text) == 6:
                    print("Kode berhasil dimasukkan!")
                    success = True
                    break
            except Exception as e:
                print(f"Error pada resource ID {resource_id}: {e}")
                continue

    # Metode 2: Cari semua EditText dan coba yang paling cocok
    if not success:
        print("Mencari melalui semua EditText...")
        edit_texts = d(className="android.widget.EditText")
        print(f"Ditemukan {edit_texts.count} EditText")
        for i in range(edit_texts.count):
            try:
                field = edit_texts[i]
                field_info = field.info
                bounds = field_info.get('bounds', {})
                current_text = field_info.get('text', '')
                print(f"EditText {i}: bounds={bounds}, text='{current_text}'")
                if current_text and len(current_text) > 10:
                    continue
                field.click()
                time.sleep(0.5)
                field.clear_text()
                time.sleep(0.5)
                field.set_text(verification_code)
                time.sleep(1)
                updated_text = field.get_text()
                if verification_code in updated_text or len(updated_text.strip()) == 6:
                    print(f"Berhasil mengisi kode di EditText {i}")
                    success = True
                    break
                else:
                    print(f"Gagal mengisi EditText {i} (text sekarang: '{updated_text}')")
            except Exception as e:
                print(f"Error pada EditText {i}: {e}")
                continue

    # PATCH: Tambahkan cek dan pengisian field MultiAutoCompleteTextView
    if not success:
        print("Mencari melalui MultiAutoCompleteTextView...")
        mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
        print(f"Ditemukan {mac_fields.count} MultiAutoCompleteTextView")
        for i in range(mac_fields.count):
            try:
                field = mac_fields[i]
                field_info = field.info
                print(f"MultiAutoCompleteTextView {i}: bounds={field_info.get('bounds')}, text='{field_info.get('text', '')}'")
                field.click()
                time.sleep(0.5)
                field.clear_text()
                time.sleep(0.5)
                field.set_text(verification_code)
                time.sleep(1)
                current_text = field.get_text()
                if verification_code in current_text or len(current_text.strip()) == 6:
                    print(f"Berhasil mengisi kode di MultiAutoCompleteTextView {i}")
                    success = True
                    break
                else:
                    print(f"Gagal mengisi MultiAutoCompleteTextView {i}, mencoba yang lain...")
            except Exception as e:
                print(f"Error pada MultiAutoCompleteTextView {i}: {e}")
                continue

    # Metode 3: Input menggunakan koordinat berdasarkan gambar
    if not success:
        print("Mencoba input dengan koordinat berdasarkan gambar...")
        x, y = 450, 180  # Koordinat field input berdasarkan gambar
        d.click(x, y)
        time.sleep(1)
        d.long_click(x, y)
        time.sleep(0.5)
        d.press("del")
        time.sleep(0.5)
        d.press("ctrl+a")
        time.sleep(0.5)
        d.press("del")
        time.sleep(0.5)
        d.send_keys(verification_code)
        time.sleep(1)
        print("Kode dimasukkan menggunakan koordinat")
        success = True

    if success:
        print("Kode verifikasi berhasil dimasukkan")
        time.sleep(2)
        confirmation_clicked = False
        confirm_buttons = [
            "Next", "Berikutnya", "Continue", "Lanjutkan",
            "Confirm", "Konfirmasi", "Verify", "Verifikasi",
            "Submit", "Kirim", "Done", "Selesai"
        ]
        for button_text in confirm_buttons:
            if d(text=button_text).exists:
                print(f"Mengklik tombol: {button_text}")
                d(text=button_text).click()
                confirmation_clicked = True
                break
        if not confirmation_clicked:
            print("Mencari tombol konfirmasi berdasarkan koordinat...")
            button_x, button_y = 450, 215
            d.click(button_x, button_y)
            confirmation_clicked = True
            print("Tombol konfirmasi diklik menggunakan koordinat")
        time.sleep(3)
        verification_success = False
        for _ in range(10):
            if not (d(textContains="confirmation").exists or 
                    d(textContains="verification").exists or
                    d(textContains="Enter").exists):
                verification_success = True
                break
            time.sleep(1)
        if verification_success:
            print("Verifikasi email berhasil!")
            return True
        else:
            print("Mungkin kode verifikasi salah atau ada masalah lain")
            return False
    else:
        print("Gagal memasukkan kode verifikasi")
        return False

def debug_screen_elements(d):
    print("=== DEBUG: Elemen yang ada di layar ===")
    try:
        edit_texts = d(className="android.widget.EditText")
        print(f"Jumlah EditText ditemukan: {edit_texts.count}")
        for i in range(edit_texts.count):
            try:
                info = edit_texts[i].info
                print(f"EditText {i}: text='{info.get('text', '')}', bounds={info.get('bounds', '')}, resourceId='{info.get('resourceId', '')}'")
            except:
                print(f"EditText {i}: Error getting info")
        mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
        print(f"Jumlah MultiAutoCompleteTextView ditemukan: {mac_fields.count}")
        for i in range(mac_fields.count):
            try:
                info = mac_fields[i].info
                print(f"MultiAutoCompleteTextView {i}: text='{info.get('text', '')}', bounds={info.get('bounds', '')}, resourceId='{info.get('resourceId', '')}'")
            except:
                print(f"MultiAutoCompleteTextView {i}: Error getting info")
        buttons = d(className="android.widget.Button")
        print(f"Jumlah Button ditemukan: {buttons.count}")
        for i in range(buttons.count):
            try:
                info = buttons[i].info
                print(f"Button {i}: text='{info.get('text', '')}', bounds={info.get('bounds', '')}, resourceId='{info.get('resourceId', '')}'")
            except:
                print(f"Button {i}: Error getting info")
        keywords = ["code", "verification", "confirm", "next", "digit"]
        for keyword in keywords:
            elements = d(textContains=keyword)
            if elements.exists:
                print(f"Elemen dengan '{keyword}': {elements.count} ditemukan")
    except Exception as e:
        print(f"Error saat debug: {e}")

def check_instagram_lite_installed():
    print("Mengecek apakah Instagram Lite sudah terinstall...")
    d = u2.connect(MUMU_DEVICE)
    try:
        d.app_start("com.instagram.lite")
        time.sleep(3)
        print("Instagram Lite sudah terinstall!")
        d.app_stop("com.instagram.lite")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Instagram Lite belum terinstall: {e}")
    try:
        result = subprocess.getoutput(f'"{ADB_PATH}" -s {MUMU_DEVICE} shell pm list packages | grep com.instagram.lite')
        if "com.instagram.lite" in result:
            print("Instagram Lite sudah terinstall (detected via ADB)!")
            return True
    except Exception as e:
        print(f"Error checking via ADB: {e}")
    print("Instagram Lite belum terinstall.")
    return False

def install_instagram_lite():
    print("Menghubungkan ke emulator dengan uiautomator2...")
    d = u2.connect(MUMU_DEVICE)
    print("Membuka Google Play Store...")
    d.app_start("com.android.vending")
    time.sleep(4)
    print("Klik ikon Search di sidebar (by coordinate)...")
    d.click(78, 450)
    time.sleep(2)
    print("Klik search bar di bagian atas...")
    if not wait_and_click(d, text="Search apps & games"):
        print("Gagal klik search bar di atas!")
        return False
    time.sleep(1)
    print("Ketik 'Instagram Lite'...")
    d.send_keys("Instagram Lite")
    time.sleep(1)
    print("Tekan tombol Enter pada keyboard virtual...")
    d.press("enter")
    time.sleep(3)
    print("Klik hasil aplikasi 'Instagram Lite' pada hasil pencarian...")
    d.click(400, 570)
    time.sleep(2)
    print("Klik tombol Install di panel kanan...")
    d.click(1160, 390)
    time.sleep(2)
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
    print("Klik tombol 'Create new account' (by coordinate)...")
    d.click(450, 916)
    time.sleep(3)
    print("Klik tombol 'Sign up with email' (by coordinate)...")
    d.click(450, 515)
    time.sleep(3)
    print("Mengisi field email...")
    email_field = d(className="android.widget.MultiAutoCompleteTextView")
    if email_field.exists:
        email_field.clear_text()
        time.sleep(0.5)
        email_field.set_text(email)
        time.sleep(2)
        print(f"Email '{email}' berhasil diisi")
    else:
        print("Field email tidak ditemukan!")
        return
    debug_screen_elements(d)
    print("Mencari tombol Next...")
    next_clicked = False
    if d(text="Next").exists:
        print("Mengklik tombol Next berdasarkan text...")
        d(text="Next").click()
        next_clicked = True
    elif d(text="Berikutnya").exists:
        print("Mengklik tombol Berikutnya...")
        d(text="Berikutnya").click()
        next_clicked = True
    elif d(textContains="Next").exists:
        print("Mengklik tombol yang mengandung Next...")
        d(textContains="Next").click()
        next_clicked = True
    elif d(resourceId="com.instagram.lite:id/next_button").exists:
        print("Mengklik tombol Next berdasarkan resource ID...")
        d(resourceId="com.instagram.lite:id/next_button").click()
        next_clicked = True
    else:
        print("Mencoba klik tombol Next dengan koordinat alternatif...")
        d.click(450, 420)
        next_clicked = True
    if next_clicked:
        print("Tombol Next berhasil diklik, menunggu halaman berikutnya...")
        time.sleep(5)
        debug_screen_elements(d)
    else:
        print("Gagal menemukan tombol Next!")
        return
    print("Menunggu halaman nama lengkap...")
    found_fullname = wait_for(d, resourceId="com.instagram.lite:id/full_name", timeout=10)
    if not found_fullname:
        for retry in range(3):
            print(f"Retry mencari field nama lengkap, percobaan ke-{retry+1}")
            time.sleep(3)
            debug_screen_elements(d)
            found_fullname = wait_for(d, resourceId="com.instagram.lite:id/full_name", timeout=5)
            if found_fullname:
                print("Field nama lengkap ditemukan pada percobaan retry")
                break
            if d(text="Next").exists:
                d(text="Next").click()
            elif d(text="Berikutnya").exists:
                d(text="Berikutnya").click()
            else:
                d.click(450, 420)
        else:
            print("Tetap tidak menemukan field nama lengkap! Cek kemungkinan UI berubah atau perlu update script.")
            debug_screen_elements(d)
            return
    print("Mengisi nama lengkap...")
    if wait_for(d, resourceId="com.instagram.lite:id/full_name"):
        fullname_field = d(resourceId="com.instagram.lite:id/full_name")
        fullname_field.clear_text()
        fullname_field.set_text(fullname)
        time.sleep(1)
    else:
        print("Field nama lengkap tidak ditemukan.")
        return
    print("Mengisi username...")
    if wait_for(d, resourceId="com.instagram.lite:id/username"):
        username_field = d(resourceId="com.instagram.lite:id/username")
        username_field.clear_text()
        username_field.set_text(username)
        time.sleep(1)
    else:
        print("Field username tidak ditemukan.")
        return
    print("Mengisi password...")
    if wait_for(d, resourceId="com.instagram.lite:id/password"):
        password_field = d(resourceId="com.instagram.lite:id/password")
        password_field.clear_text()
        password_field.set_text(password)
        time.sleep(1)
    else:
        print("Field password tidak ditemukan.")
        return
    print("Klik Next untuk melanjutkan registrasi...")
    if not (wait_and_click(d, text="Next") or wait_and_click(d, text="Berikutnya")):
        print("Tombol Next tidak ditemukan, mencoba koordinat...")
        d.click(450, 600)
    time.sleep(3)
    print("Mengecek apakah ada halaman verifikasi email...")
    if handle_email_verification(d):
        print("Verifikasi email berhasil!")
        time.sleep(3)
    else:
        print("Tidak ada verifikasi email atau verifikasi gagal")
    print("Registrasi Instagram Lite selesai!")
    print("Jika masih ada langkah tambahan, silakan lakukan secara manual.")

def main():
    start_mumu()
    unlock_screen()
    print("Menunggu 10 detik sebelum memulai automasi...")
    time.sleep(10)
    if check_instagram_lite_installed():
        print("Instagram Lite sudah terinstall, langsung menuju proses registrasi...")
        time.sleep(2)
        register_instagram_lite(EMAIL, FULLNAME, USERNAME, PASSWORD)
    else:
        print("Instagram Lite belum terinstall, memulai proses install...")
        if install_instagram_lite():
            print("Instagram Lite berhasil diinstall, melanjutkan ke proses registrasi...")
            time.sleep(5)
            register_instagram_lite(EMAIL, FULLNAME, USERNAME, PASSWORD)
        else:
            print("Automasi install Instagram Lite gagal, proses dihentikan.")

if __name__ == "__main__":
    main()
