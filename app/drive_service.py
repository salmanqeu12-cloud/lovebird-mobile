import os
import webbrowser

def upload_backup_to_drive(file_path):
    """فتح Google Drive في المتصفح أو رفعه عبر API إذا كان ملف المعرفات متوفراً"""
    if not os.path.exists(file_path):
        return False, "ملف النسخة الاحتياطية غير موجود."

    # التحقق من وجود ملف client_secrets.json
    if not os.path.exists("client_secrets.json"):
        full_path = os.path.abspath(file_path)
        webbrowser.open("https://drive.google.com")
        return True, f"تم فتح Google Drive في المتصفح.\n\nمسار النسخة الاحتياطية المرفوعة محلياً:\n{full_path}"

    try:
        from pydrive2.auth import GoogleAuth
        from pydrive2.drive import GoogleDrive

        gauth = GoogleAuth()
        gauth.LoadCredentialsFile("mycreds.txt")
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
            
        gauth.SaveCredentialsFile("mycreds.txt")
        drive = GoogleDrive(gauth)

        filename = os.path.basename(file_path)
        file_drive = drive.CreateFile({'title': filename})
        file_drive.SetContentFile(file_path)
        file_drive.Upload()

        return True, "تم رفع النسخة الاحتياطية إلى Google Drive بنجاح."
    except Exception as e:
        return False, f"فشل الرفع التلقائي: {str(e)}"