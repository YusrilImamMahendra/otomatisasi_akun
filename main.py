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
EMAIL = "cobaja@gmail.com"
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
    """
    Fungsi yang diperbaiki untuk mengambil kode verifikasi dari email Instagram
    """
    print("Mencari kode verifikasi di email...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Koneksi ke server IMAP dengan SSL
            print("Menghubungkan ke server email...")
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            mail.login(email_address, email_password)
            mail.select('inbox')
            
            # Cari email dari Instagram dengan berbagai kriteria
            search_criteria = [
                '(FROM "Instagram" UNSEEN)',  # Email belum dibaca dari Instagram
                '(FROM "Instagram")',         # Semua email dari Instagram
                '(FROM "noreply@instagram.com")',  # Email spesifik Instagram
                '(FROM "security@mail.instagram.com")',  # Email security Instagram
                '(SUBJECT "Instagram")',      # Subject mengandung Instagram
                '(BODY "verification")',      # Body mengandung verification
                '(BODY "confirm")'            # Body mengandung confirm
            ]
            
            email_found = False
            for criteria in search_criteria:
                print(f"Mencari dengan kriteria: {criteria}")
                result, data = mail.search(None, criteria)
                
                if result == 'OK' and data[0]:
                    email_ids = data[0].split()
                    if email_ids:
                        email_found = True
                        print(f"Ditemukan {len(email_ids)} email dengan kriteria ini")
                        
                        # Coba email terbaru hingga 3 email terakhir
                        for email_id in reversed(email_ids[-3:]):
                            print(f"Memeriksa email ID: {email_id}")
                            
                            result, data = mail.fetch(email_id, '(RFC822)')
                            if result == 'OK':
                                raw_email = data[0][1]
                                email_message = email.message_from_bytes(raw_email)
                                
                                # Cek subject dan dari
                                subject = email_message.get('Subject', '')
                                from_addr = email_message.get('From', '')
                                date = email_message.get('Date', '')
                                
                                print(f"Email - From: {from_addr}, Subject: {subject}, Date: {date}")
                                
                                # Ekstrak isi email
                                body = ""
                                if email_message.is_multipart():
                                    for part in email_message.walk():
                                        content_type = part.get_content_type()
                                        if content_type in ["text/plain", "text/html"]:
                                            try:
                                                payload = part.get_payload(decode=True)
                                                if payload:
                                                    body += payload.decode('utf-8', errors='ignore')
                                            except:
                                                continue
                                else:
                                    try:
                                        payload = email_message.get_payload(decode=True)
                                        if payload:
                                            body = payload.decode('utf-8', errors='ignore')
                                    except:
                                        continue
                                
                                print(f"Isi email (100 karakter pertama): {body[:100]}...")
                                
                                # Cari kode verifikasi dengan pattern yang lebih lengkap
                                patterns = [
                                    r'\b(\d{6})\b',  # 6 digit angka
                                    r'(?:code|kode)[:\s]*(\d{6})',  # "code: 123456" atau "kode: 123456"
                                    r'(?:verification|verifikasi)[:\s]*(\d{6})',  # "verification: 123456"
                                    r'(?:confirm|konfirmasi)[:\s]*(\d{6})',  # "confirm: 123456"
                                    r'(?:your|anda)[:\s]*(?:code|kode)[:\s]*(?:is|adalah)[:\s]*(\d{6})',  # "your code is 123456"
                                    r'(\d{6})[:\s]*(?:is|adalah)[:\s]*(?:your|anda)[:\s]*(?:code|kode)',  # "123456 is your code"
                                    r'Enter[:\s]*(?:the|)[:\s]*(?:code|kode)[:\s]*(\d{6})',  # "Enter the code 123456"
                                    r'<[^>]*>(\d{6})<[^>]*>',  # Kode dalam tag HTML
                                    r'(?:please|silakan)[:\s]*(?:enter|masukkan)[:\s]*(\d{6})',  # "please enter 123456"
                                ]
                                
                                for pattern in patterns:
                                    matches = re.findall(pattern, body, re.IGNORECASE)
                                    if matches:
                                        verification_code = matches[0]
                                        print(f"Kode verifikasi ditemukan dengan pattern '{pattern}': {verification_code}")
                                        
                                        # Validasi kode (harus 6 digit angka)
                                        if len(verification_code) == 6 and verification_code.isdigit():
                                            mail.close()
                                            mail.logout()
                                            return verification_code
                                        else:
                                            print(f"Kode tidak valid: {verification_code}")
                        
                        if email_found:
                            break  # Jika sudah menemukan email, tidak perlu cari dengan criteria lain
            
            if not email_found:
                print("Tidak ditemukan email dari Instagram")
            
            mail.close()
            mail.logout()
            
        except imaplib.IMAP4.error as e:
            print(f"Error IMAP: {e}")
            if "authentication failed" in str(e).lower():
                print("PERHATIAN: Authentication failed. Pastikan:")
                print("1. Email dan password benar")
                print("2. 2-Step Verification diaktifkan dan menggunakan App Password")
                print("3. 'Less secure app access' diaktifkan (jika tidak menggunakan App Password)")
                break
        except Exception as e:
            print(f"Error saat membaca email: {e}")
        
        print("Kode verifikasi belum ditemukan, menunggu 15 detik...")
        time.sleep(15)
    
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
        
        # Cek berbagai indikator halaman verifikasi
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
        ]
        
        if any(indicators):
            verification_detected = True
            print("Halaman verifikasi email terdeteksi!")
            break
        
        time.sleep(1)
    
    if not verification_detected:
        print("Halaman verifikasi tidak terdeteksi setelah 60 detik")
        return False
    
    # Beri waktu untuk halaman fully loaded
    time.sleep(2)
    
    # Debug elemen yang ada di halaman verifikasi
    print("=== DEBUG: Mencari field kode verifikasi ===")
    debug_screen_elements(d)
    
    # Coba ambil kode verifikasi dari email secara otomatis
    verification_code = None
    if EMAIL_PASSWORD:  # Jika password email sudah diset
        print("Mencoba mengambil kode verifikasi dari email...")
        verification_code = get_verification_code_from_email(EMAIL, EMAIL_PASSWORD, timeout=180)  # 3 menit
    
    # Jika gagal otomatis, minta input manual
    if not verification_code:
        verification_code = manual_input_verification_code()
    
    # Masukkan kode verifikasi dengan metode yang diperbaiki
    print(f"Memasukkan kode verifikasi: {verification_code}")
    
    success = False
    
    # Metode 1: Cari berdasarkan resource ID yang lebih lengkap
    possible_resource_ids = [
        "com.instagram.lite:id/confirmation_code",
        "com.instagram.lite:id/code_text",
        "com.instagram.lite:id/verify_code",
        "com.instagram.lite:id/code_input",
        "com.instagram.lite:id/verification_code",
        "com.instagram.lite:id/edittext_confirmation_code",
        "com.instagram.lite:id/code_field"
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
                
                # Verifikasi apakah kode berhasil dimasukkan
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
                
                # Cek apakah field ini kemungkinan untuk kode verifikasi
                bounds = field_info.get('bounds', {})
                current_text = field_info.get('text', '')
                
                print(f"EditText {i}: bounds={bounds}, text='{current_text}'")
                
                # Skip field yang sudah terisi dengan text yang tidak relevan
                if current_text and len(current_text) > 10:
                    continue
                
                # Coba isi field ini
                field.click()
                time.sleep(0.5)
                field.clear_text()
                time.sleep(0.5)
                field.set_text(verification_code)
                time.sleep(1)
                
                # Cek apakah berhasil terisi
                updated_text = field.get_text()
                if verification_code in updated_text or len(updated_text) == 6:
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
    # Metode 3: Cari field yang memiliki hint atau placeholder terkait kode
    if not success:
        print("Mencari field berdasarkan hint/placeholder...")
        possible_hints = ["code", "verification", "confirm", "6-digit", "digit"]
        
        for hint in possible_hints:
            elements = d(textContains=hint)
            if elements.exists:
                for i in range(elements.count):
                    try:
                        element = elements[i]
                        # Cek apakah ini EditText atau field input
                        if element.info.get('className') == 'android.widget.EditText':
                            element.click()
                            time.sleep(0.5)
                            element.clear_text()
                            time.sleep(0.5)
                            element.set_text(verification_code)
                            time.sleep(1)
                            
                            # Verifikasi
                            if verification_code in element.get_text():
                                print(f"Berhasil mengisi kode di field dengan hint '{hint}'")
                                success = True
                                break
                    except Exception as e:
                        print(f"Error pada field dengan hint '{hint}': {e}")
                        continue
                
                if success:
                    break
    
    # Metode 4: Input menggunakan koordinat berdasarkan gambar
    if not success:
        print("Mencoba input dengan koordinat berdasarkan gambar...")
        # Berdasarkan gambar, field kode verifikasi berada di tengah layar
        x, y = 450, 180  # Koordinat field input berdasarkan gambar
        
        # Klik pada field
        d.click(x, y)
        time.sleep(1)
        
        # Hapus text yang ada (jika ada)
        d.long_click(x, y)
        time.sleep(0.5)
        d.press("del")
        time.sleep(0.5)
        
        # Clear menggunakan Ctrl+A dan Delete
        d.press("ctrl+a")
        time.sleep(0.5)
        d.press("del")
        time.sleep(0.5)
        
        # Input kode menggunakan send_keys
        d.send_keys(verification_code)
        time.sleep(1)
        
        # Verifikasi dengan screenshot atau dump
        print("Kode dimasukkan menggunakan koordinat")
        success = True
    
    if success:
        print("Kode verifikasi berhasil dimasukkan")
        time.sleep(2)
        
        # Cari dan klik tombol konfirmasi
        confirmation_clicked = False
        
        # Daftar kemungkinan text tombol konfirmasi
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
        
        # Jika tidak ada tombol text, cari tombol berdasarkan koordinat
        if not confirmation_clicked:
            print("Mencari tombol konfirmasi berdasarkan koordinat...")
            # Berdasarkan gambar, tombol Next berada di bawah field input
            button_x, button_y = 450, 215  # Koordinat tombol Next berdasarkan gambar
            d.click(button_x, button_y)
            confirmation_clicked = True
            print("Tombol konfirmasi diklik menggunakan koordinat")
        
        time.sleep(3)
        
        # Cek apakah verifikasi berhasil (pindah ke halaman berikutnya)
        verification_success = False
        for _ in range(10):
            # Cek apakah sudah tidak ada lagi field kode verifikasi
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
    """Fungsi untuk debug elemen yang ada di layar"""
    print("=== DEBUG: Elemen yang ada di layar ===")
    try:
        # Dump semua elemen EditText
        edit_texts = d(className="android.widget.EditText")
        print(f"Jumlah EditText ditemukan: {edit_texts.count}")
        for i in range(edit_texts.count):
            try:
                info = edit_texts[i].info
                print(f"EditText {i}: text='{info.get('text', '')}', bounds={info.get('bounds', '')}, resourceId='{info.get('resourceId', '')}'")
            except:
                print(f"EditText {i}: Error getting info")
        
        # Dump semua tombol
        buttons = d(className="android.widget.Button")
        print(f"Jumlah Button ditemukan: {buttons.count}")
        for i in range(buttons.count):
            try:
                info = buttons[i].info
                print(f"Button {i}: text='{info.get('text', '')}', bounds={info.get('bounds', '')}, resourceId='{info.get('resourceId', '')}'")
            except:
                print(f"Button {i}: Error getting info")
        
        # Cari elemen yang mengandung kata kunci tertentu
        keywords = ["code", "verification", "confirm", "next", "digit"]
        for keyword in keywords:
            elements = d(textContains=keyword)
            if elements.exists:
                print(f"Elemen dengan '{keyword}': {elements.count} ditemukan")
                
    except Exception as e:
        print(f"Error saat debug: {e}")

def check_instagram_lite_installed():
    """Mengecek apakah Instagram Lite sudah terinstall"""
    print("Mengecek apakah Instagram Lite sudah terinstall...")
    d = u2.connect(MUMU_DEVICE)
    
    # Metode 1: Coba buka aplikasi Instagram Lite
    try:
        d.app_start("com.instagram.lite")
        time.sleep(3)
        # Jika berhasil dibuka, berarti sudah terinstall
        print("Instagram Lite sudah terinstall!")
        d.app_stop("com.instagram.lite")  # Tutup aplikasi
        time.sleep(1)
        return True
    except Exception as e:
        print(f"Instagram Lite belum terinstall: {e}")
    
    # Metode 2: Cek menggunakan ADB
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
    email_field = d(className="android.widget.MultiAutoCompleteTextView")
    if email_field.exists:
        email_field.clear_text()  # Bersihkan field terlebih dahulu
        time.sleep(0.5)
        email_field.set_text(email)
        time.sleep(2)
        print(f"Email '{email}' berhasil diisi")
    else:
        print("Field email tidak ditemukan!")
        return

    # Debug elemen yang ada setelah mengisi email
    debug_screen_elements(d)

    # Step 4: Cari dan klik tombol "Next" dengan berbagai metode
    print("Mencari tombol Next...")
    next_clicked = False
    
    # Metode 1: Cari berdasarkan text "Next"
    if d(text="Next").exists:
        print("Mengklik tombol Next berdasarkan text...")
        d(text="Next").click()
        next_clicked = True
    # Metode 2: Cari berdasarkan text "Berikutnya" (untuk bahasa Indonesia)
    elif d(text="Berikutnya").exists:
        print("Mengklik tombol Berikutnya...")
        d(text="Berikutnya").click()
        next_clicked = True
    # Metode 3: Cari tombol yang mengandung kata Next
    elif d(textContains="Next").exists:
        print("Mengklik tombol yang mengandung Next...")
        d(textContains="Next").click()
        next_clicked = True
    # Metode 4: Cari berdasarkan resource ID (jika ada)
    elif d(resourceId="com.instagram.lite:id/next_button").exists:
        print("Mengklik tombol Next berdasarkan resource ID...")
        d(resourceId="com.instagram.lite:id/next_button").click()
        next_clicked = True
    # Metode 5: Cari tombol di posisi yang lebih tepat (koordinat alternatif)
    else:
        print("Mencoba klik tombol Next dengan koordinat alternatif...")
        # Koordinat yang lebih tinggi dari sebelumnya
        d.click(450, 420)  # Koordinat lebih tinggi
        next_clicked = True
    
    if next_clicked:
        print("Tombol Next berhasil diklik, menunggu halaman berikutnya...")
        time.sleep(3)
    else:
        print("Gagal menemukan tombol Next!")
        return

    # Tunggu hingga halaman nama lengkap muncul
    print("Menunggu halaman nama lengkap...")
    if not wait_for(d, resourceId="com.instagram.lite:id/full_name", timeout=10):
        print("Halaman nama lengkap tidak muncul, mencoba lagi...")
        # Coba klik Next sekali lagi jika belum pindah halaman
        if d(text="Next").exists:
            d(text="Next").click()
            time.sleep(3)

    # Isi nama lengkap
    print("Mengisi nama lengkap...")
    if wait_for(d, resourceId="com.instagram.lite:id/full_name"):
        fullname_field = d(resourceId="com.instagram.lite:id/full_name")
        fullname_field.clear_text()
        fullname_field.set_text(fullname)
        time.sleep(1)
    else:
        print("Field nama lengkap tidak ditemukan.")
        return

    # Isi username
    print("Mengisi username...")
    if wait_for(d, resourceId="com.instagram.lite:id/username"):
        username_field = d(resourceId="com.instagram.lite:id/username")
        username_field.clear_text()
        username_field.set_text(username)
        time.sleep(1)
    else:
        print("Field username tidak ditemukan.")
        return

    # Isi password
    print("Mengisi password...")
    if wait_for(d, resourceId="com.instagram.lite:id/password"):
        password_field = d(resourceId="com.instagram.lite:id/password")
        password_field.clear_text()
        password_field.set_text(password)
        time.sleep(1)
    else:
        print("Field password tidak ditemukan.")
        return

    # Klik Next untuk melanjutkan
    print("Klik Next untuk melanjutkan registrasi...")
    if not (wait_and_click(d, text="Next") or wait_and_click(d, text="Berikutnya")):
        print("Tombol Next tidak ditemukan, mencoba koordinat...")
        d.click(450, 600)  # Koordinat alternatif untuk tombol Next
    
    time.sleep(3)

    # Handle verifikasi email jika muncul
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
    
    # Cek apakah Instagram Lite sudah terinstall
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
