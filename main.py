import os
import subprocess
import time
import uiautomator2 as u2
import imaplib
import email
import re
import uuid
import random

# KONFIGURASI PATH DAN DEVICE UNTUK LDPLAYER
LDPLAYER_EXE_PATH = r"C:\LDPlayer\LDPlayer9\dnplayer.exe"
ADB_PATH = r"C:\LDPlayer\LDPlayer9\adb.exe"
LDPLAYER_DEVICE = "emulator-5554"

# Data akun yang ingin diregistrasikan (ganti sesuai kebutuhan)
EMAIL = "cobaja.1933@gmail.com"
EMAIL_PASSWORD = "hpxifkmjcxzmjrrq"
FULLNAME = "yaboyunik12345"
PASSWORD = "PasswordKuat2025"

# Konfigurasi IMAP untuk Gmail
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

def start_ldplayer_and_connect_adb():
    print("Menjalankan emulator LDPlayer...")
    subprocess.Popen([LDPLAYER_EXE_PATH])
    # Tunggu emulator benar-benar berjalan dan terdeteksi oleh ADB
    max_wait = 180  # detik
    wait_time = 0
    while wait_time < max_wait:
        out = subprocess.getoutput(f'"{ADB_PATH}" devices')
        print("ADB devices output:", out)
        lines = out.splitlines()
        for line in lines:
            if "device" in line and "offline" not in line and "List of devices" not in line:
                print(f"Emulator siap, adb sudah terhubung sebagai: {line.strip()}")
                global LDPLAYER_DEVICE
                LDPLAYER_DEVICE = line.split()[0]
                return
        print("ADB belum terhubung ke emulator, mencoba connect ke port umum LDPlayer...")
        for port in [5554, 5555, 5556, 62001]:
            os.system(f'"{ADB_PATH}" connect 127.0.0.1:{port}')
        time.sleep(3)
        wait_time += 3
    raise RuntimeError("Gagal mendapatkan koneksi ADB ke emulator! Pastikan LDPlayer sudah running dan Android siap.")

def unlock_screen():
    print("Membuka kunci layar (jika terkunci)...")
    os.system(f'"{ADB_PATH}" -s {LDPLAYER_DEVICE} shell input keyevent 224')
    os.system(f'"{ADB_PATH}" -s {LDPLAYER_DEVICE} shell input keyevent 82')

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

def handle_permission_popup(d, timeout=30):
    """
    Menangani pop-up perizinan Instagram Lite secara otomatis.
    Akan mengklik tombol ALLOW/IZINKAN untuk semua jenis perizinan.
    """
    print("Memulai pengecekan pop-up perizinan...")
    
    permission_handled = False
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Cek berbagai variasi tombol Allow/Izinkan
        permission_buttons = [
            "ALLOW",
            "Allow", 
            "IZINKAN",
            "Izinkan",
            "OK",
            "WHILE USING THE APP",
            "While using the app"
        ]
        
        permission_found = False
        
        for button_text in permission_buttons:
            if d(text=button_text).exists:
                print(f"Pop-up perizinan terdeteksi dengan tombol '{button_text}', mengklik...")
                d(text=button_text).click()
                time.sleep(2)
                permission_found = True
                permission_handled = True
                print(f"Tombol '{button_text}' berhasil diklik.")
                break
        
        # Cek pop-up berdasarkan resource ID jika ada
        permission_resource_ids = [
            "com.android.permissioncontroller:id/permission_allow_button",
            "android:id/button1",
            "com.android.packageinstaller:id/permission_allow_button"
        ]
        
        if not permission_found:
            for resource_id in permission_resource_ids:
                if d(resourceId=resource_id).exists:
                    print(f"Pop-up perizinan terdeteksi dengan resource ID '{resource_id}', mengklik...")
                    d(resourceId=resource_id).click()
                    time.sleep(2)
                    permission_found = True
                    permission_handled = True
                    print(f"Resource ID '{resource_id}' berhasil diklik.")
                    break
        
        # Cek apakah ada dialog dengan keyword "Instagram Lite" dan "contacts"
        if not permission_found:
            if (d(textContains="Instagram Lite").exists and 
                (d(textContains="contacts").exists or d(textContains="kontak").exists)):
                print("Pop-up perizinan Instagram Lite untuk akses kontak terdeteksi...")
                
                # Cari tombol di bagian kanan bawah dialog (biasanya ALLOW)
                buttons = d(className="android.widget.Button")
                if buttons.exists:
                    for i in range(buttons.count):
                        try:
                            button = buttons[i]
                            button_text = button.info.get('text', '')
                            bounds = button.info.get('bounds', {})
                            
                            # Tombol ALLOW biasanya di posisi kanan
                            if bounds and bounds.get('right', 0) > 600:  # Asumsi layar > 600px
                                print(f"Mengklik tombol kanan (kemungkinan ALLOW): '{button_text}'")
                                button.click()
                                time.sleep(2)
                                permission_found = True
                                permission_handled = True
                                break
                        except Exception as e:
                            print(f"Error saat cek button {i}: {e}")
                            continue
    if permission_handled:
        print("Pop-up perizinan berhasil ditangani.")
    else:
        print("Tidak ada pop-up perizinan yang terdeteksi atau sudah selesai.")
    
    return permission_handled

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
                if wait_and_click(d, text="I didn't get the code", timeout=5):
                    print("Tombol 'I didn't get the code' berhasil diklik.")
                    time.sleep(2)
                    if wait_and_click(d, text="Resend confirmation code", timeout=5):
                        print("Opsi 'Resend confirmation code' diklik, menunggu kode baru...")
                        time.sleep(10)
                        exclude_codes.append(verification_code)
                        continue
                    else:
                        print("Opsi 'Resend confirmation code' tidak ditemukan!")
                        return False
                else:
                    print("Tombol 'I didn't get the code' tidak ditemukan berdasarkan teks, mencoba koordinat...")
                    d.click(450, 600)
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

def set_birthday(d, min_year=1980, max_year=2004):
    print("Mendeteksi dan mengisi tanggal lahir (acak, metode klik RecyclerView)...")
    year = random.randint(min_year, max_year)
    month = random.randint(1, 12)
    if month == 2:
        max_day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
    elif month in [4, 6, 9, 11]:
        max_day = 30
    else:
        max_day = 31
    day = random.randint(1, max_day)
    print(f"Target birthday: {day:02d}-{month:02d}-{year}")

    for _ in range(10):
        pickers = d(className="androidx.recyclerview.widget.RecyclerView")
        if pickers.exists and pickers.count == 3:
            break
        time.sleep(1)
    else:
        print("Picker birthday tidak muncul!")
        return

    picker_day = d(className="androidx.recyclerview.widget.RecyclerView")[0]
    picker_month = d(className="androidx.recyclerview.widget.RecyclerView")[1]
    picker_year = d(className="androidx.recyclerview.widget.RecyclerView")[2]

    try:
        picker_day.child(index=day-1).click()
        time.sleep(0.3)
        picker_month.child(index=month-1).click()
        time.sleep(0.3)
        clicked_year = False
        for i in range(picker_year.count):
            item = picker_year.child(index=i)
            item_text = item.info.get("text", "")
            if item_text == str(year):
                item.click()
                clicked_year = True
                break
        if not clicked_year:
            print("Tahun tidak ditemukan di picker, klik tahun default paling atas.")
            picker_year.child(index=0).click()
        time.sleep(0.3)
    except Exception as e:
        print(f"Error klik picker birthday: {e}")

    print(f"Tanggal lahir dipilih: {day:02d}-{month:02d}-{year}")

    next_x, next_y = 450, 1550
    d.click(next_x, next_y)
    print("Tombol Next (Birthday) diklik.")
    time.sleep(2)

def check_instagram_lite_installed():
    print("Mengecek apakah Instagram Lite sudah terinstall...")
    try:
        result = subprocess.getoutput(f'"{ADB_PATH}" -s {LDPLAYER_DEVICE} shell pm list packages com.instagram.lite')
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
    d = u2.connect(LDPLAYER_DEVICE)
    print("Membuka Google Play Store...")
    d.app_start("com.android.vending")
    time.sleep(4)
    print("Klik search bar di bagian atas (LDPlayer)...")
    d.click(350, 60)
    time.sleep(2)
    d.send_keys("Instagram Lite")
    time.sleep(1)
    d.press("enter")
    time.sleep(3)
    print("Klik tombol Install di panel kanan (detail aplikasi, via XPath)...")
    xpath_install = '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View[2]/android.view.View/android.view.View[1]/android.view.View[5]/android.widget.Button[2]'
    if d.xpath(xpath_install).exists:
        d.xpath(xpath_install).click()
        print("Tombol Install (detail aplikasi) berhasil diklik via XPath.")
    elif d(text="Install").exists:
        d(text="Install").click()
        print("Tombol Install diklik via text (fallback).")
    else:
        print("Tombol Install tidak ditemukan! Gagal install Instagram Lite.")
        return False
    
    print("Menunggu proses install selesai (tombol Buka muncul)...")
    for _ in range(60):
        # Tambahkan pengecekan tombol Open dengan XPath yang diberikan
        xpath_open = '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View[2]/android.view.View/android.view.View[1]/android.view.View[5]/android.widget.Button'
        if d.xpath(xpath_open).exists:
            print("Tombol Open ditemukan via XPath, mengklik...")
            d.xpath(xpath_open).click()
            time.sleep(3)
            # Handle permission popup setelah membuka aplikasi
            handle_permission_popup(d)
            return True
        elif d(text="Open").exists:
            print("Tombol Open ditemukan via text, mengklik...")
            d(text="Open").click()
            time.sleep(3)
            # Handle permission popup setelah membuka aplikasi
            handle_permission_popup(d)
            return True
        elif d(text="Buka").exists:
            print("Tombol Buka ditemukan, mengklik...")
            d(text="Buka").click()
            time.sleep(3)
            # Handle permission popup setelah membuka aplikasi
            handle_permission_popup(d)
            return True
        time.sleep(2)
    print("Timeout: Gagal mendeteksi bahwa Instagram Lite sudah terinstall.")
    return False

def register_instagram_lite(email, fullname, password):
    d = u2.connect(LDPLAYER_DEVICE)
    print("Membuka aplikasi Instagram Lite...")
    d.app_start("com.instagram.lite")
    time.sleep(5)
    handle_permission_popup(d)

    print("Klik tombol 'Create new account' (by text/XPath)...")
    if d(text="Create new account").exists:
        d(text="Create new account").click()
        time.sleep(2)
    elif d.xpath('//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[2]/android.view.ViewGroup[2]').exists:
        d.xpath('//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[2]/android.view.ViewGroup[2]').click()
        time.sleep(2)
    else:
        print("Tombol 'Create new account' tidak ditemukan! (text/XPath)")
        debug_screen_elements(d)
        return

    print("Klik tombol 'Sign up with email' (by text/XPath)...")
    if d(text="Sign up with email").exists:
        d(text="Sign up with email").click()
        time.sleep(2)
    elif d.xpath('//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[3]/android.view.ViewGroup[3]').exists:
        d.xpath('//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[3]/android.view.ViewGroup[3]').click()
        time.sleep(2)
    else:
        print("Tombol 'Sign up with email' tidak ditemukan! (text/XPath)")
        debug_screen_elements(d)
        return
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
        d(text="Next").click()
        next_clicked = True
    elif d(text="Berikutnya").exists:
        d(text="Berikutnya").click()
        next_clicked = True
    elif d(textContains="Next").exists:
        d(textContains="Next").click()
        next_clicked = True
    elif d(resourceId="com.instagram.lite:id/next_button").exists:
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

    print("Cek apakah langsung masuk ke halaman verifikasi kode...")
    for _ in range(10):
        mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
        if mac_fields.exists and "_" in mac_fields[0].info.get("text", ""):
            print("Halaman verifikasi kode terdeteksi, mengeksekusi handle_email_verification ...")
            verif_ok = handle_email_verification(d)
            print("Registrasi: handle_email_verification selesai. Melanjutkan isi nama lengkap & password.")
            for _ in range(15):
                mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
                if not (mac_fields.exists and "_" in mac_fields[0].info.get("text", "")):
                    print("Field kode sudah hilang, lanjut ke pengisian nama lengkap.")
                    break
                print("Masih di halaman verifikasi kode, menunggu...")
                time.sleep(1)
            break
        time.sleep(1)

    print("Mencari dan mengisi field nama lengkap & password...")
    for _ in range(10):
        mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
        if mac_fields.exists and mac_fields.count >= 2:
            name_field = mac_fields[0]
            pass_field = mac_fields[1]
            name_field.click()
            name_field.clear_text()
            name_field.set_text(fullname)
            time.sleep(1)
            print(f"Field nama lengkap diisi dengan '{fullname}'.")
            pass_field.click()
            pass_field.clear_text()
            pass_field.set_text(password)
            time.sleep(1)
            print("Field password diisi.")
            break
        print("Field nama lengkap/password belum muncul, menunggu...")
        time.sleep(1)
    else:
        print("Field nama lengkap/password tidak ditemukan! Cek UI.")
        return

    print("Klik Next untuk melanjutkan registrasi...")
    if d(text="Next").exists:
        d(text="Next").click()
        print("Tombol Next diklik berdasarkan text.")
    elif d(text="Berikutnya").exists:
        d(text="Berikutnya").click()
        print("Tombol Berikutnya diklik.")
    else:
        d.click(450, 513)
        print("Tombol Next diklik berdasarkan koordinat.")
    time.sleep(3)

    print("Masuk ke halaman birthday, mengisi tanggal lahir...")
    set_birthday(d)
    time.sleep(3)
    print("Registrasi Instagram Lite selesai! Jika masih ada langkah tambahan, lakukan manual.")
    return

def main():
    start_ldplayer_and_connect_adb()
    unlock_screen()
    print("Menunggu 10 detik sebelum memulai automasi...")
    time.sleep(10)
    if check_instagram_lite_installed():
        print("Instagram Lite sudah terinstall, langsung menuju proses registrasi...")
        time.sleep(2)
        register_instagram_lite(EMAIL, FULLNAME, PASSWORD)
    else:
        print("Instagram Lite belum terinstall, memulai proses install...")
        if install_instagram_lite():
            print("Instagram Lite berhasil diinstall, melanjutkan ke proses registrasi...")
            time.sleep(5)
            register_instagram_lite(EMAIL, FULLNAME, PASSWORD)
        else:
            print("Automasi install Instagram Lite gagal, proses dihentikan.")

if __name__ == "__main__":
    main()
