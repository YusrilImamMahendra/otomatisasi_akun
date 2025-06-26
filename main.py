import os
import subprocess
import time
import uiautomator2 as u2
import imaplib
import email
import re
import uuid

# Konfigurasi path dan device
MUMU_EXE_PATH = r"C:\Program Files\Netease\MuMuPlayerGlobal-12.0\shell\MuMuPlayer.exe"
ADB_PATH = r"C:\Program Files\Netease\MuMuPlayerGlobal-12.0\shell\adb.exe"
MUMU_DEVICE = "127.0.0.1:7555"

# Data akun yang ingin diregistrasikan (ganti sesuai kebutuhan)
EMAIL = "cobaja.1933@gmail.com"
EMAIL_PASSWORD = "hpxifkmjcxzmjrrq"
FULLNAME = "yaboyunik12345"
USERNAME = "usernameunik12345"
PASSWORD = "PasswordKuat2025"

# Konfigurasi IMAP untuk Gmail
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

def start_mumu():
    print("Menjalankan emulator MuMu...")
    subprocess.Popen([MUMU_EXE_PATH])
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
    os.system(f'"{ADB_PATH}" -s {MUMU_DEVICE} shell input keyevent 224')
    os.system(f'"{ADB_PATH}" -s {MUMU_DEVICE} shell input keyevent 82')

def wait_and_click(d, text=None, resourceId=None, bounds=None, timeout=20):
    for _ in range(timeout):
        if text and d(text=text).exists:
            d(text=text).click()
            return True
        if resourceId and d(resourceId=resourceId).exists:
            d(resourceId=resourceId).click()
            return True
        if bounds and d(className="android.view.ViewGroup", clickable=True, bounds=bounds).exists:
            d(className="android.view.ViewGroup", clickable=True, bounds=bounds).click()
            return True
        time.sleep(1)
    print(f"Element {text or resourceId or bounds} not found.")
    return False

def wait_for(d, text=None, resourceId=None, bounds=None, timeout=20):
    for _ in range(timeout):
        if text and d(text=text).exists:
            return True
        if resourceId and d(resourceId=resourceId).exists:
            return True
        if bounds and d(className="android.view.ViewGroup", clickable=True, bounds=bounds).exists:
            return True
        time.sleep(1)
    return False

def get_verification_code_from_email(email_address, email_password, timeout=300, exclude_codes=None):
    print("Mencari kode verifikasi di email (termasuk folder Sosial)...")
    start_time = time.time()
    folders = ['inbox', '[Gmail]/Social', '[Gmail]/Sosial', 'CATEGORY_SOCIAL']
    if exclude_codes is None:
        exclude_codes = []
    while time.time() - start_time < timeout:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(email_address, email_password)
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
                                match = re.search(r'\b(\d{6})\b', subject)
                                if match:
                                    verification_code = match.group(1)
                                    if verification_code in exclude_codes:
                                        print(f"Kode {verification_code} sudah pernah dicoba, skip.")
                                        continue
                                    print(f"Kode verifikasi ditemukan di subject: {verification_code}")
                                    mail.close()
                                    mail.logout()
                                    return verification_code

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
                                    if verification_code in exclude_codes:
                                        print(f"Kode {verification_code} sudah pernah dicoba, skip.")
                                        continue
                                    print(f"KodeGeo verifikasi ditemukan di body: {verification_code}")
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

def handle_email_verification(d, max_attempts=3):
    print("Mendeteksi halaman verifikasi email...")
    verification_detected = False
    for attempt in range(60):
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

    exclude_codes = []
    for attempt in range(max_attempts):
        print(f"Percobaan verifikasi kode ke-{attempt+1}...")
        verification_code = None
        if EMAIL_PASSWORD:
            print("Mencoba mengambil kode verifikasi dari email...")
            verification_code = get_verification_code_from_email(EMAIL, EMAIL_PASSWORD, timeout=90, exclude_codes=exclude_codes)
        if not verification_code:
            verification_code = manual_input_verification_code()
        exclude_codes.append(verification_code)

        print(f"Memasukkan kode verifikasi: {verification_code}")

        # Isi field kode
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

        if not success:
            print("Mencoba input dengan koordinat berdasarkan gambar...")
            x, y = 450, 180  # Koordinat perkiraan untuk field kode
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
            # Klik tombol Next dengan koordinat berdasarkan gambar
            print("Mengklik tombol Next untuk mengirim kode verifikasi...")
            next_x, next_y = 450, 400  # Koordinat perkiraan untuk tombol Next
            d.click(next_x, next_y)
            print("Tombol Next diklik berdasarkan koordinat.")
            time.sleep(3)

            # Cek apakah kode valid
            if d(textContains="That code isn't valid").exists:
                print("Kode tidak valid, akan melakukan resend code.")
                # Klik "I didn't get the code" dengan teks atau koordinat
                if wait_and_click(d, text="I didn't get the code", timeout=5):
                    print("Tombol 'I didn't get the code' berhasil diklik.")
                    time.sleep(2)
                    # Klik "Resend confirmation code" dengan teks atau koordinat
                    if wait_and_click(d, text="Resend confirmation code", timeout=5):
                        print("Opsi 'Resend confirmation code' diklik, menunggu kode baru...")
                        time.sleep(10)  # Tunggu kode baru
                        exclude_codes.append(verification_code)  # Tambahkan kode lama ke exclude_codes
                        continue  # Ulangi proses dengan kode baru
                    else:
                        print("Opsi 'Resend confirmation code' tidak ditemukan!")
                        return False
                else:
                    # Jika teks tidak ditemukan, coba koordinat default (sesuaikan berdasarkan UI)
                    print("Tombol 'I didn't get the code' tidak ditemukan berdasarkan teks, mencoba koordinat...")
                    d.click(450, 600)  # Koordinat perkiraan, sesuaikan jika perlu
                    time.sleep(2)
                    if wait_and_click(d, text="Resend confirmation code", timeout=5):
                        print("Opsi 'Resend confirmation code' diklik, menunggu kode baru...")
                        time.sleep(10)
                        exclude_codes.append(verification_code)
                        continue
                    else:
                        print("Gagal menemukan atau mengklik 'Resend confirmation code'!")
                        return False
            else:
                # Cek apakah sudah pindah ke halaman berikutnya
                mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
                if mac_fields.exists and "_" in mac_fields[0].info.get("text", ""):
                    print("Masih di halaman verifikasi kode, kemungkinan kode salah.")
                    continue
                print("Verifikasi email berhasil!")
                return True

    print("Gagal verifikasi kode setelah beberapa percobaan.")
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
    try:
        result = subprocess.getoutput(f'"{ADB_PATH}" -s {MUMU_DEVICE} shell pm list packages com.instagram.lite')
        print(f"Hasil ADB: {result}")
        if "com.instagram.lite" in result:
            print("Instagram Lite sudah terinstall.")
            return True
    except Exception as e:
        print(f"Error saat mengecek aplikasi terinstall: {e}")
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

    # PATCH: Deteksi flow verifikasi kode di awal
    print("Cek apakah langsung masuk ke halaman verifikasi kode...")
    for _ in range(10):
        mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
        if mac_fields.exists and "_" in mac_fields[0].info.get("text", ""):
            print("Halaman verifikasi kode terdeteksi, mengeksekusi handle_email_verification ...")
            verif_ok = handle_email_verification(d)
            print("Registrasi: handle_email_verification selesai. Melanjutkan isi nama lengkap, username, password.")
            # PATCH: Setelah handle_email_verification, tunggu sampai field kode hilang benar2
            for _ in range(15):
                mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
                if not (mac_fields.exists and "_" in mac_fields[0].info.get("text", "")):
                    print("Field kode sudah hilang, lanjut ke pengisian nama lengkap.")
                    break
                print("Masih di halaman verifikasi kode, menunggu...")
                time.sleep(1)
            break
        time.sleep(1)

    # Lanjut pengisian data akun
    max_attempts = 5
    for step in range(max_attempts):
        print(f"Mencari dan mengisi field nama lengkap (percobaan {step + 1}/{max_attempts})...")
        if wait_for(d, resourceId="com.instagram.lite:id/full_name", timeout=5):
            fullname_field = d(resourceId="com.instagram.lite:id/full_name")
            fullname_field.clear_text()
            fullname_field.set_text(fullname)
            time.sleep(1)
        else:
            print("Field nama lengkap tidak ditemukan berdasarkan resourceId, mencoba dengan MultiAutoCompleteTextView...")
            mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
            if mac_fields.exists and mac_fields.count > 0:
                fullname_field = mac_fields[0]  # Ambil field pertama sebagai nama lengkap
                fullname_field.clear_text()
                fullname_field.set_text(fullname)
                time.sleep(1)
                print(f"Field nama lengkap diisi dengan '{fullname}' menggunakan MultiAutoCompleteTextView.")
            else:
                print("Field nama lengkap tidak ditemukan, lanjut ke langkah berikutnya setelah percobaan...")
                if step == max_attempts - 1:  # Jika sudah maksimal percobaan
                    break

        print("Mengisi username...")
        if wait_for(d, resourceId="com.instagram.lite:id/username", timeout=5):
            username_field = d(resourceId="com.instagram.lite:id/username")
            username_field.clear_text()
            username_field.set_text(username)
            time.sleep(1)
        else:
            print("Field username tidak ditemukan berdasarkan resourceId, mencoba dengan MultiAutoCompleteTextView...")
            mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
            if mac_fields.exists and mac_fields.count > 1:
                username_field = mac_fields[1]  # Ambil field kedua sebagai username
                username_field.clear_text()
                username_field.set_text(username)
                time.sleep(1)
                print(f"Field username diisi dengan '{username}' menggunakan MultiAutoCompleteTextView.")
            else:
                print("Field username tidak ditemukan, lanjut ke langkah berikutnya...")
                break

        print("Mengisi password...")
        if wait_for(d, resourceId="com.instagram.lite:id/password", timeout=5):
            password_field = d(resourceId="com.instagram.lite:id/password")
            password_field.clear_text()
            password_field.set_text(password)
            time.sleep(1)
        else:
            print("Field password tidak ditemukan berdasarkan resourceId, mencoba dengan MultiAutoCompleteTextView...")
            mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
            if mac_fields.exists and mac_fields.count > 2:
                password_field = mac_fields[2]  # Ambil field ketiga sebagai password
                password_field.clear_text()
                password_field.set_text(password)
                time.sleep(1)
                print(f"Field password diisi dengan '{password}' menggunakan MultiAutoCompleteTextView.")
            else:
                print("Field password tidak ditemukan, lanjut ke langkah berikutnya...")
                break

        print("Klik Next untuk melanjutkan registrasi...")
        if not (wait_and_click(d, text="Next") or wait_and_click(d, text="Berikutnya")):
            print("Tombol Next tidak ditemukan berdasarkan teks, mencoba koordinat...")
            d.click(450, 513)  # Koordinat tengah dari bounds [18,480][882,546]
            print("Tombol Next diklik berdasarkan koordinat.")
        time.sleep(3)

        # PATCH: Jika masih ada verifikasi email di belakang, handle lagi!
        print("Cek apakah ada halaman verifikasi email lagi setelah isi data...")
        if d(className="android.widget.MultiAutoCompleteTextView").exists and "_" in d(className="android.widget.MultiAutoCompleteTextView")[0].info.get('text', ''):
            print("Ditemukan halaman verifikasi kode lagi, handle ulang...")
            handle_email_verification(d)
            print("Registrasi: handle_email_verification kedua selesai.")

        print("Registrasi Instagram Lite selesai! Jika masih ada langkah tambahan, lakukan manual.")
        return

    print("Gagal mengisi semua field setelah beberapa percobaan, mencoba klik Next...")
    d.click(450, 513)  # Coba klik Next meskipun field tidak terdeteksi semua
    time.sleep(3)
    print("Registrasi selesai atau gagal, periksa manual jika perlu.")

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
