import os, string, sys, webbrowser, threading
import subprocess
import time
from datetime import datetime, timezone
import uiautomator2 as u2
import uuid
import random
from sms_api_utils import (
    request_phone_number,
    get_phone_code,
    strip_country_code,
    get_sms_code,
)
    
# KONFIGURASI PATH DAN DEVICE UNTUK LDPLAYER
LDPLAYER_EXE_PATH = r"C:\LDPlayer\LDPlayer9\dnplayer.exe"
ADB_PATH = r"C:\LDPlayer\LDPlayer9\adb.exe"
LDPLAYER_DEVICE = "emulator-5554"
APK_PATH = r"C:\xampp\htdocs\otomatisai_akun\instagram-lite-466-0-0-9-106.apk"  
API_KEY = "9d3fc401fB8665790fd1dfB167547e92"
ID_NEGARA = 73 

def generate_random_fullname(length=10):
    # Membuat username random, misal: "user123abc"
    chars = string.ascii_lowercase + string.digits
    return 'JaWa' + ''.join(random.choices(chars, k=length))

def generate_random_password(length=12):
    # Kombinasi huruf besar, kecil, angka, dan simbol
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

FULLNAME = generate_random_fullname()
PASSWORD = generate_random_password()

def inspect_ui_elements(d, filter_texts=None):
    print("\n======= UI Elements Inspector (Filtered) =======\n")
    try:
        dump = d.dump_hierarchy(compressed=False, pretty=True)
        elements = d.xpath('//*').all()
        total_elements = len(elements)
        print(f"Total elements found: {total_elements}")

        found_matching = False
        for element in elements:
            text = element.attrib.get('text')
            resource_id = element.attrib.get('resource-id')
            class_name = element.attrib.get('class')
            bounds = element.attrib.get('bounds')
            clickable = element.attrib.get('clickable')

            display_element = False
            if filter_texts:
                for f_text in filter_texts:
                    if (text and f_text.lower() in text.lower()) or \
                       (resource_id and f_text.lower() in resource_id.lower()) or \
                       (class_name and f_text.lower() in class_name.lower()):
                        display_element = True
                        found_matching = True
                        break
            else:
                display_element = True # Display all if no filter

            if display_element:
                print(f"  Text: {text}")
                print(f"  Resource ID: {resource_id}")
                print(f"  Class Name: {class_name}")
                print(f"  Bounds: {bounds}")
                print(f"  Clickable: {clickable}")
                print("-" * 20)

        if filter_texts and not found_matching:
            print("No matching elements found with the provided filters.")
        print("\n=================================================\n")
    except Exception as e:
        print(f"Error inspecting UI elements: {e}")
        
def connect_device():
    d = u2.connect(LDPLAYER_DEVICE)
    print('Connected:', d.info)
    # Optional: buka UI Inspector
    print("Buka browser ke http://localhost:7912 untuk debug UI realtime")
    return d

def start_ldplayer_and_connect_adb():
    print("Menjalankan emulator LDPlayer...")
    subprocess.Popen([LDPLAYER_EXE_PATH])
    max_wait = 180  # detik
    wait_time = 0
    offline_count = 0
    while wait_time < max_wait:
        out = subprocess.getoutput(f'"{ADB_PATH}" devices')
        print("ADB devices output:", out)
        lines = out.splitlines()
        found_online = False
        for line in lines:
            if "device" in line and "offline" not in line and "List of devices" not in line:
                print(f"Emulator siap, adb sudah terhubung sebagai: {line.strip()}")
                global LDPLAYER_DEVICE
                LDPLAYER_DEVICE = line.split()[0]
                return
            if "offline" in line:
                offline_count += 1
        if offline_count > 5:
            print("Device selalu offline, kemungkinan ada masalah dengan ADB/LDPlayer.")
            print("Cek apakah LDPlayer sudah benar-benar running, atau coba restart ADB dan emulator.")
            raise RuntimeError("Device ADB selalu offline. Proses dihentikan.")
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

def handle_permission_popup(d, timeout=10):
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
        
        for button_text in permission_buttons:
            if d(text=button_text).exists:
                print(f"Pop-up perizinan terdeteksi dengan tombol '{button_text}', mengklik...")
                d(text=button_text).click()
                time.sleep(1)
                permission_handled = True
                print(f"Tombol '{button_text}' berhasil diklik.")
                break
        
        if permission_handled:
            break
            
        # Cek pop-up berdasarkan resource ID jika ada
        permission_resource_ids = [
            "com.android.permissioncontroller:id/permission_allow_button",
            "android:id/button1",
            "com.android.packageinstaller:id/permission_allow_button"
        ]
        
        for resource_id in permission_resource_ids:
            if d(resourceId=resource_id).exists:
                print(f"Pop-up perizinan terdeteksi dengan resource ID '{resource_id}', mengklik...")
                d(resourceId=resource_id).click()
                time.sleep(1)
                permission_handled = True
                print(f"Resource ID '{resource_id}' berhasil diklik.")
                break
        
        if permission_handled:
            break
            
        # Cek apakah ada dialog dengan keyword "Instagram Lite" dan "contacts"
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
                            time.sleep(1)
                            permission_handled = True
                            break
                    except Exception as e:
                        print(f"Error saat cek button {i}: {e}")
                        continue
        
        if permission_handled:
            break
            
        time.sleep(0.5)  # Mengurangi waktu tunggu antara pengecekan
    
    if permission_handled:
        print("Pop-up perizinan berhasil ditangani.")
    else:
        print("Tidak ada pop-up perizinan yang terdeteksi dalam waktu yang ditentukan.")
    
    return permission_handled

def handle_existing_account_popup(d, timeout=15):
    """
    Menangani pop-up dari Instagram Lite ketika email sudah terdaftar di akun lain.
    WAJIB klik tombol 'Create new account' via XPath sebelum lanjut.
    """
    print("Memeriksa pop-up email sudah terdaftar di Instagram Lite...")

    xpath_create_new_account = (
        "//android.widget.FrameLayout[@resource-id=\"com.instagram.lite:id/main_layout\"]"
        "/android.widget.FrameLayout/android.view.ViewGroup[3]/android.view.ViewGroup"
        "/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]"
    )

    start_time = time.time()
    while time.time() - start_time < timeout:
        # Cek apakah popup muncul
        if (d(text="This email is on another account").exists or
            d(textContains="email is on another account").exists or
            d.xpath(xpath_create_new_account).exists):
            print("Popup 'email is on another account' Terdeteksi")
            # Klik tombol "Create new account" via XPath AKURAT
            if d.xpath(xpath_create_new_account).exists:
                print("Klik tombol 'Create new account' (XPath)")
                d.xpath(xpath_create_new_account).click()
                time.sleep(2)
                # Tunggu popup benar-benar hilang sebelum lanjut
                for _ in range(10):
                    if not d.xpath(xpath_create_new_account).exists:
                        print("Popup sudah hilang.")
                        return True
                    time.sleep(0.5)
                print("Popup belum hilang setelah klik. Coba lagi...")
            else:
                print("XPath 'Create new account' tidak ditemukan. Inspect UI...")
                inspect_ui_elements(d)
        time.sleep(0.5)

    print("Pop-up email sudah terdaftar tidak terdeteksi atau gagal klik.")
    return False

def set_birthday(d, min_age=18, max_age=30):
    def save_xml_to_file(d, prefix):
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"birthday_page_{prefix}_{timestamp}.xml"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(d.dump_hierarchy())
            print(f"Saved page inspection to {filename}")
        except Exception as e:
            print(f"Gagal menyimpan XML: {e}")

    print("\nStarting birthday setup process...")
    time.sleep(3)

    # --- LANGKAH 1: Klik tombol Next di halaman Add your birthday ---
    print("\nLangkah 1: Mengklik tombol Next...")
    xpath_next = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]'
    
    if d.xpath(xpath_next).exists:
        d.xpath(xpath_next).click()
        print("Tombol Next berhasil diklik")
        time.sleep(2)
    else:
        print("Gagal menemukan tombol Next!")
        return False

    # --- LANGKAH 2: Menangani popup 'Enter your real birthday' ---
    print("\nLangkah 2: Menangani popup birthday...")
    time.sleep(2)

    # Klik OK di popup
    try:
        d.click(430, 840)  # Koordinat tengah
        print("Klik koordinat tengah untuk popup")
        time.sleep(1)
        d.click(450, 850)  # Koordinat OK
        print("Klik koordinat tombol OK")
    except Exception as e:
        print(f"Gagal klik popup: {e}")
        return False

    time.sleep(2)

    # --- LANGKAH 3: Klik tombol "Enter age instead" ---
    print("\nLangkah 3: Mencari dan mengklik tombol 'Enter age instead'...")
    
    # Coba klik menggunakan koordinat yang tepat dari XML
    try:
        d.click(354, 1481)  # Titik tengah dari bounds="[354,1481][546,1510]"
        print("Enter age instead diklik via koordinat yang tepat")
        time.sleep(3)
    except Exception as e:
        print(f"Gagal klik Enter age instead via koordinat: {e}")
        return False

    # Verifikasi halaman Enter your age muncul
    time.sleep(2)

    # Cek field input
    if not d(className="android.widget.MultiAutoCompleteTextView").exists:
        print("Halaman Enter your age tidak terdeteksi!")
        return False
    
    print("Halaman Enter your age terdeteksi")

    # --- LANGKAH 4: Mengisi field age ---
    print("\nLangkah 4: Mengisi field age...")
    age = str(random.randint(min_age, max_age))
    
    input_field = d(className="android.widget.MultiAutoCompleteTextView")
    if input_field.exists:
        try:
            input_field.click()
            time.sleep(1)
            input_field.set_text(age)
            print(f"Berhasil mengisi usia: {age}")
        except Exception as e:
            print(f"Gagal mengisi age: {e}")
            return False
    else:
        print("Field age tidak ditemukan!")
        return False

    time.sleep(2)

    # --- LANGKAH 5: Klik Next final ---
    print("\nLangkah 5: Klik Next final...")
    try:
        # Menggunakan koordinat dari bounds="[30,385][870,451]"
        d.click(425, 404)  # Titik tengah dari bounds Next button
        print("Next final diklik via koordinat")
        time.sleep(2)
        
        # Verifikasi tambahan - coba klik sekali lagi jika masih di halaman yang sama
        if d(className="android.widget.MultiAutoCompleteTextView").exists:
            d.click(450, 418)  # Coba klik lagi
            print("Mencoba klik Next lagi")
            time.sleep(2)
    except Exception as e:
        print(f"Gagal klik Next final: {e}")
        return False

    # Verifikasi proses selesai
    time.sleep(2)
    if d(className="android.widget.MultiAutoCompleteTextView").exists:
        print("Masih di halaman age input!")
        save_xml_to_file(d, "process_not_completed")
        return False

    print("Proses pengisian birthday selesai!")
    return True

def get_utc_timestamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def save_registration_result(result_data, cookies=None):
    timestamp = get_utc_timestamp()
    filename = f"registration_result_{timestamp.replace(':', '_').replace(' ', '_')}.txt"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== INSTAGRAM LITE REGISTRATION RESULT ===\n")
            f.write(f"Registration Time (UTC): {timestamp}\n")
            f.write(f"System User: {os.getlogin()}\n")
            f.write("\n=== ACCOUNT DETAILS ===\n")
            f.write(f"Status: {result_data.get('status', 'N/A')}\n")
            f.write(f"Username: {result_data.get('username', 'N/A')}\n")
            f.write(f"Password: {result_data.get('password', 'N/A')}\n")
            f.write(f"Email: {result_data.get('email', 'N/A')}\n")
            
            if cookies:
                f.write("\n=== COOKIES ===\n")
                f.write(cookies)
                
            f.write("\n\n=== ADDITIONAL INFO ===\n")
            f.write(f"Device: {LDPLAYER_DEVICE}\n")
            f.write(f"Instagram Lite Package: com.instagram.lite\n")
            
        print(f"\nRegistration result saved to: {filename}")
        return True
    except Exception as e:
        print(f"Error saving registration result: {e}")
        return False

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

def uninstall_instagram_lite():
    print("Menguninstall Instagram Lite jika sudah terinstall...")
    try:
        uninstall_cmd = f'"{ADB_PATH}" -s {LDPLAYER_DEVICE} uninstall com.instagram.lite'
        result = subprocess.getoutput(uninstall_cmd)
        print(f"Hasil perintah ADB uninstall: {result}")
        if "Success" in result:
            print("Instagram Lite berhasil diuninstall.")
            return True
        else:
            print("Gagal menguninstall Instagram Lite!")
            return False
    except Exception as e:
        print(f"Error saat menguninstall Instagram Lite: {e}")
        return False

def install_instagram_lite():
    print("Menghubungkan ke emulator dengan uiautomator2...")
    d = connect_device()
    
    # Cek apakah file APK ada
    if not os.path.exists(APK_PATH):
        print(f"File APK tidak ditemukan di: {APK_PATH}")
        return False
    
    print(f"Memulai instalasi Instagram Lite dari APK: {APK_PATH}...")
    try:
        # Install APK menggunakan ADB
        install_cmd = f'"{ADB_PATH}" -s {LDPLAYER_DEVICE} install "{APK_PATH}"'
        result = subprocess.getoutput(install_cmd)
        print(f"Hasil perintah ADB install: {result}")
        
        if "Success" in result:
            print("Instalasi APK berhasil.")
        else:
            print("Instalasi APK gagal!")
            return False
    except Exception as e:
        print(f"Error saat instalasi APK: {e}")
        return False

    # Tunggu beberapa saat untuk memastikan aplikasi terinstall
    time.sleep(5)
    
    # Verifikasi instalasi
    if not check_instagram_lite_installed():
        print("Verifikasi gagal: Instagram Lite tidak terdeteksi setelah instalasi.")
        return False
    print("Instalasi dan pembukaan aplikasi Instagram Lite berhasil.")
    return True


def register_instagram_lite(fullname, password):
    activation_id, full_number = request_phone_number(API_KEY, ID_NEGARA, service='ig')
    if not activation_id or not full_number:
        print(f"Nomor telepon untuk negara ID {ID_NEGARA} tidak tersedia atau gagal divalidasi.")
        return False
    
    phone_code = get_phone_code(ID_NEGARA)
    if not phone_code:
        print(f"Kode telepon untuk negara ID {ID_NEGARA} tidak ditemukan.")
        return False
    
    local_number = strip_country_code(full_number, phone_code)
    print(f"Nomor Telepon Didapat: +{phone_code}{local_number} (Lokal: {local_number})")

    d = connect_device()
    d.app_start("com.instagram.lite")
    time.sleep(10)
    handle_permission_popup(d)

    print("Inspect elemen setelah aplikasi dibuka:")
    inspect_ui_elements(d, filter_texts=["create", "account", "button"])

    xpath_create = '//android.widget.FrameLayout[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout/android.view.ViewGroup[2]/android.view.ViewGroup[2]'
    if d.xpath(xpath_create).wait(timeout=20): # Menggunakan wait
        d.xpath(xpath_create).click()
        time.sleep(5)
    else:
        print("Tombol 'Create new account' tidak ditemukan!")
        return False

    # Klik field code negara
    d.xpath('//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[2]').click()
    time.sleep(2)

    # Klik search, isi kode negara
    if d.xpath('//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.View[1]').wait(timeout=5):
        d.xpath('//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.View[1]').click()
    search_field = d(className="android.widget.MultiAutoCompleteTextView")
    search_field.set_text(phone_code)
    time.sleep(2)

    # Pilih negara pertama
    d.xpath('//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]').click_exists(timeout=5)
    time.sleep(1)

    # Isi nomor hp lokal
    phone_field = d(className="android.widget.MultiAutoCompleteTextView")
    phone_field.set_text(local_number)
    time.sleep(1)

    # Klik Next
    d.xpath('//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]').click_exists(timeout=5)
    print("Nomor dan negara berhasil diinput, menunggu halaman verifikasi kode...")

    # Menunggu halaman verifikasi kode muncul
    print("Menunggu halaman verifikasi kode muncul...")
    
    otp_field_selector = d(className="android.widget.MultiAutoCompleteTextView", textContains="_")
    if otp_field_selector.wait(timeout=30):
        print("Halaman verifikasi terdeteksi (berdasarkan field input).")
        print("Meminta kode OTP dari API...")
        
        otp = get_sms_code(API_KEY, activation_id)
        if not otp:
            print("Tidak menerima kode OTP dari API. Proses registrasi gagal.")
            return False
        # Mengisi kode ke field yang sama yang sudah kita temukan
        # Kita panggil selectornya lagi untuk memastikan elemennya fresh
        d(className="android.widget.MultiAutoCompleteTextView", textContains="_").set_text(otp)
        print(f"Kode OTP '{otp}' berhasil diinput.")
        time.sleep(1)
    else:
        print("Gagal mendeteksi halaman verifikasi kode dalam 30 detik.")
        return False

    # Klik tombol Next setelah memasukkan OTP
    if d.xpath('//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]').click_exists(timeout=10):
        print("Tombol Next (setelah OTP) diklik.")
    else:
        d.click(500, 400) 
        print("Tombol Next (setelah OTP) diklik via koordinat.")

    time.sleep(3)
    
    print("Mencari dan mengisi field nama lengkap & password...")
    for _ in range(10):
        mac_fields = d(className="android.widget.MultiAutoCompleteTextView")
        if mac_fields.exists and mac_fields.count >= 2:
            name_field = mac_fields[0]
            pass_field = mac_fields[1]
            name_field.click()
            time.sleep(0.5)
            name_field.clear_text()
            name_field.set_text(fullname)
            time.sleep(1)
            print(f"Field nama lengkap diisi dengan '{fullname}'.")
            
            pass_field.click()
            time.sleep(0.5)
            pass_field.clear_text()
            pass_field.set_text(password)
            time.sleep(1)
            print("Field password diisi.")
            break
        print("Field nama lengkap/password belum muncul, menunggu...")
        time.sleep(1)
    else:
        print("Field nama lengkap/password tidak ditemukan! Cek UI.")
        return False

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
    if not set_birthday(d):
        print("Gagal mengatur tanggal lahir. Proses dihentikan.")
        return False
    
    print("halaman 'your account is almost ready'...")
    time.sleep(2)
    
    xpathnext = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[6]'
    if d.xpath(xpathnext).wait(timeout=15):      
        d.xpath(xpathnext).click()
        print("Tombol next pada halaman 'almost ready' berhasil diklik via xpath.")
        time.sleep(2)
    elif d(text="Next").wait(timeout=5):
        d(text="Next").click()
        print("Tombol Next diklik via text.")
        time.sleep(2)
    else:
        print("Tombol Next pada halaman 'almost ready' tidak ditemukan!") 
        
    print('masuk ke halaman sync contact')
    time.sleep(5)
    xpath_skip_contacts = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]/android.view.View[1]'
    if d.xpath(xpath_skip_contacts).wait(timeout=15):
        d.xpath(xpath_skip_contacts).click()
        print("Tombol Skip pada halaman sync kontak berhasil diklik via xpath.")
        time.sleep(2)
    elif d(text="Skip").wait(timeout=5):
        d(text="Skip").click()
        print("Tombol Skip diklik via text.")
        time.sleep(2)
    else:
        print("Tombol Skip pada halaman sync kontak tidak ditemukan!")
        
    print("Mencoba melewati halaman profil poto")
    xpathskips = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[3]/android.view.View[1]'
    if d.xpath(xpathskips).wait(timeout=10):
        d.xpath(xpathskips).click()
        print("Tombol Skip pada halaman add poto berhasil diklik via xpath.")
        time.sleep(2)
    else:
        print("Halaman 'add poto' tidak ditemukan atau sudah dilewati.")
        
    print("halaman follow 5 orangs")
    xpathnextf = '//*[@resource-id="com.instagram.lite:id/main_layout"]/android.widget.FrameLayout[1]/android.view.ViewGroup[3]/android.view.ViewGroup[1]'
    if d.xpath(xpathnextf).wait(timeout=10):
        d.xpath(xpathnextf).click()
        print("Tombol next (follow) berhasil di klik")
        time.sleep(5)
    else:
        print("Halaman 'follow' tidak ditemukan atau sudah dilewati.")
        
    print("\n✨ REGISTRASI BERHASIL ✨")
    print("Masuk Ke halaman HOME")
    print("\nCollecting registration results...")
    
    registration_result = {
        'status': 'success',
        'username': fullname,
        'password': password,
        'phone_number': f"+{phone_code}{local_number}", 
        'email': 'N/A', 
        'registration_time': get_utc_timestamp(),
        'system_user': os.getlogin()
    }

    try:
        cookies = d.shell(['cat', '/data/data/com.instagram.lite/app_webview/Cookies']).output
        print("\nSuccessfully retrieved cookies")
    except Exception as e:
        print(f"Failed to get cookies: {e}")
        cookies = None

    save_registration_result(registration_result, cookies)
    
    print("\n=== REGISTRATION COMPLETED ===")
    print(f"Status: {registration_result['status']}")
    print(f"Username: {registration_result['username']}")
    print(f"Password: {registration_result['password']}")
    print(f"Phone Number: {registration_result['phone_number']}")
    print(f"Registration Time (UTC): {registration_result['registration_time']}")
    
    if cookies:
        print("\n=== COOKIES RETRIEVED (truncated) ===")
        print(cookies[:300] + "...") 

    return registration_result


def main():
    start_ldplayer_and_connect_adb()
    unlock_screen()
    print("Menunggu 5 detik sebelum memulai automasi...")
    time.sleep(5)
    
    if check_instagram_lite_installed():
        print("Instagram Lite sudah terinstall, menguninstall terlebih dahulu...")
        if not uninstall_instagram_lite():
            print("Gagal menguninstall Instagram Lite, proses dihentikan.")
            return
        time.sleep(5)  
    
    print("Memulai proses install Instagram Lite...")
    if install_instagram_lite():
        print("Instagram Lite berhasil diinstall, melanjutkan ke proses registrasi...")
        time.sleep(5)
        register_instagram_lite(FULLNAME, PASSWORD)
    else:
        print("Automasi install Instagram Lite gagal, proses dihentikan.")

if __name__ == "__main__":
    try:
        result = main()
        if isinstance(result, dict):
            print("\n=== FINAL RESULTS ===")
            print(f"Registration Status: {result.get('status', 'N/A')}")
            print(f"Username: {result.get('username', 'N/A')}")
            print(f"Password: {result.get('password', 'N/A')}")
            print(f"Phone Number: {result.get('phone_number', 'N/A')}")
            print(f"Registration Time (UTC): {result.get('registration_time', 'N/A')}")
    except Exception as e:
        print(f"\nAn error occurred in the main execution: {e}")
