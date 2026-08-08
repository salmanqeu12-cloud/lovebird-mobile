import os
import sys
import shutil
import sqlite3
import glob
from datetime import datetime
import csv
from app.database import DB_PATH, get_connection

def get_base_dir():
    """جلب المسار الرئيسي الحقيقي للملف التنفيذي أو ملفات السورس كود"""
    if getattr(sys, 'frozen', False):
        # إذا كان التطبيق يعمل كـ EXE مجمع بواسطة PyInstaller
        return os.path.dirname(sys.executable)
    else:
        # إذا كان التطبيق يعمل عبر السكريبت العادي main.py
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def cleanup_old_backups(backup_folder, keep_count=5):
    """حذف النسخ الاحتياطية القديمة والإبقاء على أحدث 5 نسخ فقط"""
    if not os.path.exists(backup_folder):
        return

    try:
        list_of_files = glob.glob(os.path.join(backup_folder, "*.db"))
        latest_files = sorted(list_of_files, key=os.path.getmtime)

        if len(latest_files) > keep_count:
            files_to_remove = latest_files[:-keep_count]
            for file in files_to_remove:
                try:
                    os.remove(file)
                    print(f"[Cleanup Success] Removed old backup: {file}")
                except Exception as err:
                    print(f"Error removing old backup {file}: {err}")
    except Exception as e:
        print(f"Error during backup cleanup: {e}")

def create_backup():
    """إنشاء نسخة احتياطية تلقائية داخل مجلد backups الخارجي بجانب الـ EXE"""
    try:
        abs_db_path = os.path.abspath(DB_PATH)
        print(f"[Backup] Checking database path: {abs_db_path}")

        if not os.path.exists(abs_db_path):
            print(f"[Backup Error] Database file not found at: {abs_db_path}")
            return None

        # استخدام مسار الـ EXE الخارجي الرئيسي
        base_dir = get_base_dir()
        backup_dir = os.path.join(base_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")

        # نسخ الملف
        shutil.copy2(abs_db_path, backup_file)
        print(f"[Backup Success] Backup created successfully at: {backup_file}")

        # الإبقاء على أحدث 5 نسخ
        cleanup_old_backups(backup_dir, keep_count=5)

        return backup_file
    except Exception as e:
        print(f"[Backup Exception] Error creating backup: {e}")
        return None

def restore_backup_file(backup_file_path):
    """استعادة قاعدة البيانات من ملف نسخة احتياطية محدد (.db)"""
    if not backup_file_path or not os.path.exists(backup_file_path):
        return False, "ملف النسخة الاحتياطية غير موجود."

    try:
        abs_db_path = os.path.abspath(DB_PATH)
        db_dir = os.path.dirname(abs_db_path)
        os.makedirs(db_dir, exist_ok=True)

        # إنشاء نسخة أمان احتياطية قبل الاستبدال
        if os.path.exists(abs_db_path):
            safety_backup = abs_db_path + ".temp_bak"
            shutil.copy2(abs_db_path, safety_backup)

        # استبدال قاعدة البيانات الحالية بالملف المختار
        shutil.copy2(backup_file_path, abs_db_path)

        # مسح نسخة الأمان المؤقتة بعد النجاح
        if 'safety_backup' in locals() and os.path.exists(safety_backup):
            os.remove(safety_backup)

        return True, "تمت استعادة النسخة الاحتياطية بنجاح! يرجى إعادة تشغيل البرنامج لتطبيق التغييرات."
    except Exception as e:
        return False, f"حدث خطأ أثناء استعادة النسخة الاحتياطية:\n{str(e)}"

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

def export_table_to_csv(table_name, file_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]

    with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(column_names)
        writer.writerows(rows)

    conn.close()

def get_settings_options_by_category(category):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, value FROM settings_options WHERE category = ? ORDER BY value ASC", (category,))
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
        cursor.execute("INSERT INTO settings_options (category, value) VALUES (?, ?)", (category, value.strip()))
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
        cursor.execute("DELETE FROM settings_options WHERE id = ?", (option_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting settings option: {e}")
        return False