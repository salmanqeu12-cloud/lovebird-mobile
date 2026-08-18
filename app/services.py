import csv
from datetime import datetime
import glob
import io
import os
import shutil
import sys
import urllib.request
from database import DB_PATH, get_connection
from PIL import Image
import requests

# إعدادات Supabase Storage
SUPABASE_URL = "https://vryzzhnokjxynoxsxspk.supabase.co"
SUPABASE_KEY = (
    "sb_publishable_1bxIOEL10UlzC-ct6tgc0g_0SD6l"  # الصق مفتاحك كاملاً هنا
)
BUCKET_NAME = "lovebird-media"


def get_base_dir():
    """جلب المسار الرئيسي الحقيقي للملف التنفيذي أو ملفات السورس كود"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_cached_image_path(image_source):
    """إرجاع مسار الصورة محلياً، وتنزيلها وتخزينها مؤقتاً إذا كانت رابطاً سحابياً"""
    if not image_source:
        return ""

    if os.path.exists(image_source):
        return image_source

    if image_source.startswith("http://") or image_source.startswith("https://"):
        base_dir = get_base_dir()
        cache_dir = os.path.join(base_dir, "media", "cache")
        os.makedirs(cache_dir, exist_ok=True)

        filename = os.path.basename(image_source.split("?")[0])
        local_path = os.path.join(cache_dir, filename)

        if os.path.exists(local_path):
            return local_path

        try:
            urllib.request.urlretrieve(image_source, local_path)
            return local_path
        except Exception as e:
            print(f"Error caching cloud image: {e}")
            return ""

    return ""


def compress_and_upload_image(source_path, prefix="bird"):
    """ضغط الصورة ورفعها مباشرة إلى Supabase Storage مع حفظ نسخة محلية"""
    if not source_path or not os.path.exists(source_path):
        return ""

    try:
        # 1. حفظ نسخة محلية احتياطية
        save_image_to_media(source_path, prefix=prefix)

        # 2. ضغط وتصغير الصورة
        img = Image.open(source_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail((1080, 1080), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80, optimize=True)
        buffer.seek(0)

        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"

        # 3. الرفع إلى Supabase Storage
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "image/jpeg",
        }

        response = requests.post(upload_url, headers=headers, data=buffer.getvalue())

        if response.status_code in (200, 201):
            return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
        else:
            print(f"[Supabase Upload Error] {response.status_code}: {response.text}")
            return ""
    except Exception as e:
        print(f"[Upload Exception] {e}")
        return ""


def upload_pdf_certificate(source_path, prefix="cert"):
    """رفع شهادات DNA بصيغة PDF إلى Supabase Storage"""
    if not source_path or not os.path.exists(source_path):
        return ""

    try:
        ext = os.path.splitext(source_path)[1]
        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{ext}"

        upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/pdf",
        }

        with open(source_path, "rb") as f:
            file_data = f.read()

        response = requests.post(upload_url, headers=headers, data=file_data)
        if response.status_code in (200, 201):
            return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
        else:
            print(f"[Supabase PDF Upload Error] {response.text}")
            return ""
    except Exception as e:
        print(f"[PDF Upload Exception] {e}")
        return ""


def save_image_to_media(source_path, prefix="bird"):
    """نسخ صورة وحفظها داخل مجلد media الخارجي"""
    if not source_path or not os.path.exists(source_path):
        return ""

    base_dir = get_base_dir()
    media_dir = os.path.join(base_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    ext = os.path.splitext(source_path)[1]
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{ext}"
    destination = os.path.join(media_dir, filename)

    try:
        shutil.copy2(source_path, destination)
        return destination
    except Exception as e:
        print(f"Error copying image: {e}")
        return ""


def cleanup_old_backups(backup_folder, keep_count=5):
    """حذف النسخ الاحتياطية القديمة والإبقاء على أحدث 5 نسخ فقط"""
    if not os.path.exists(backup_folder):
        return

    try:
        list_of_files = glob.glob(os.path.join(backup_folder, "*.db")) + glob.glob(
            os.path.join(backup_folder, "*.sql")
        )
        latest_files = sorted(list_of_files, key=os.path.getmtime)

        if len(latest_files) > keep_count:
            files_to_remove = latest_files[:-keep_count]
            for file in files_to_remove:
                try:
                    os.remove(file)
                except Exception as err:
                    print(f"Error removing old backup {file}: {err}")
    except Exception as e:
        print(f"Error during backup cleanup: {e}")


def create_backup():
    """إنشاء نسخة احتياطية سريعة/محلية"""
    try:
        base_dir = get_base_dir()
        backup_dir = os.path.join(base_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")

        abs_db_path = os.path.abspath(DB_PATH) if os.path.exists(DB_PATH) else None
        if abs_db_path and os.path.exists(abs_db_path):
            shutil.copy2(abs_db_path, backup_file)
        else:
            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(
                    f"Supabase Cloud Backup Marker - {datetime.now().isoformat()}\n"
                )

        cleanup_old_backups(backup_dir, keep_count=5)
        return backup_file
    except Exception as e:
        print(f"[Backup Exception] {e}")
        return None


def restore_backup_file(backup_file_path):
    """استعادة قاعدة البيانات من ملف نسخة احتياطية محدد"""
    if not backup_file_path or not os.path.exists(backup_file_path):
        return False, "ملف النسخة الاحتياطية غير موجود."

    try:
        abs_db_path = os.path.abspath(DB_PATH)
        db_dir = os.path.dirname(abs_db_path)
        os.makedirs(db_dir, exist_ok=True)

        if os.path.exists(abs_db_path):
            safety_backup = abs_db_path + ".temp_bak"
            shutil.copy2(abs_db_path, safety_backup)

        shutil.copy2(backup_file_path, abs_db_path)

        if "safety_backup" in locals() and os.path.exists(safety_backup):
            os.remove(safety_backup)

        return (
            True,
            "تمت استعادة النسخة الاحتياطية بنجاح! يرجى إعادة تشغيل البرنامج لتطبيق التغييرات.",
        )
    except Exception as e:
        return False, f"حدث خطأ أثناء استعادة النسخة الاحتياطية:\n{str(e)}"


def export_table_to_csv(table_name, file_path):
    """تصدير أي جدول إلى ملف CSV مع التوافق التام مع Supabase"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    if rows and isinstance(rows[0], dict):
        column_names = list(rows[0].keys())
        data_rows = [list(r.values()) for r in rows]
    else:
        column_names = [desc[0] for desc in cursor.description]
        data_rows = rows

    with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(column_names)
        writer.writerows(data_rows)

    conn.close()


def get_settings_options_by_category(category):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, value FROM settings_options WHERE category = %s ORDER BY value ASC",
            (category,),
        )
        options = cursor.fetchall()
        conn.close()
        return options
    except Exception as e:
        print(f"Error fetching settings options for category {category}: {e}")
        return []


def add_settings_option(category, value):
    if not value or not value.strip():
        return False
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO settings_options (category, value) VALUES (%s, %s)",
            (category, value.strip()),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding settings option: {e}")
        return False


def delete_settings_option(option_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM settings_options WHERE id = %s", (option_id,)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting settings option: {e}")
        return False
