import sqlite3
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QMessageBox, QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt
from app.database import get_connection
from app.services import create_backup, restore_backup_file, add_settings_option, delete_settings_option
from app.drive_service import upload_backup_to_drive

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("إعدادات النظام والتكامل السحابي")
        header.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;")
        layout.addWidget(header)

        # قسم Google Drive والنسخ الاحتياطي والاستعادة
        group_drive = QGroupBox("النسخ الاحتياطي والاستعادة والسحابي")
        group_drive.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-weight: bold;
                border: 1px solid #3182CE;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        drive_layout = QHBoxLayout(group_drive)

        self.btn_backup_local = QPushButton("إنشاء نسخة محلية")
        self.btn_backup_local.setStyleSheet("background-color: #3182CE; color: white; padding: 8px 12px; border-radius: 4px; font-weight: bold;")
        self.btn_backup_local.clicked.connect(self.make_local_backup)

        # زر استعادة نسخة احتياطية
        self.btn_restore_local = QPushButton("📥 استعادة نسخة احتياطية")
        self.btn_restore_local.setStyleSheet("background-color: #D69E2E; color: white; padding: 8px 12px; border-radius: 4px; font-weight: bold;")
        self.btn_restore_local.clicked.connect(self.restore_local_backup)

        self.btn_sync_drive = QPushButton("☁️ رفع النسخة إلى Google Drive")
        self.btn_sync_drive.setStyleSheet("background-color: #805AD5; color: white; padding: 8px 12px; border-radius: 4px; font-weight: bold;")
        self.btn_sync_drive.clicked.connect(self.sync_to_drive)

        drive_layout.addWidget(self.btn_backup_local)
        drive_layout.addWidget(self.btn_restore_local)
        drive_layout.addWidget(self.btn_sync_drive)
        drive_layout.addStretch()

        layout.addWidget(group_drive)

        # قسم إدارة القوائم المنسدلة والألوان
        group_add = QGroupBox("إدارة القوائم المنسدلة والألوان")
        group_add.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-weight: bold;
                border: 1px solid #4A5568;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        form_layout = QHBoxLayout(group_add)
        
        self.combo_category = QComboBox()
        self.combo_category.addItem("قائمة الألوان والطفرات", "color")
        self.combo_category.addItem("حالات الأزواج", "pair_status")
        self.combo_category.addItem("حالات الفروخ", "chick_status")
        self.combo_category.addItem("خيارات الجنس", "gender")
        self.combo_category.addItem("أسباب الأرشفة", "archive_reason")

        # ربط تغيير الفئة بالجدول لتحديث العرض فوراً
        self.combo_category.currentIndexChanged.connect(self.load_options)

        self.txt_value = QLineEdit()
        self.txt_value.setPlaceholderText("أدخل اسم اللون أو الخيار الجديد...")

        self.btn_add_option = QPushButton("+ إضافة للقائمة")
        self.btn_add_option.setStyleSheet("""
            QPushButton {
                background-color: #38A169;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2F855A; }
        """)
        self.btn_add_option.clicked.connect(self.add_option)

        form_layout.addWidget(QLabel("الفئة:"))
        form_layout.addWidget(self.combo_category)
        form_layout.addWidget(QLabel("القيمة:"))
        form_layout.addWidget(self.txt_value)
        form_layout.addWidget(self.btn_add_option)

        layout.addWidget(group_add)

        # جدول الخيارات المفلترة
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["الفئة", "القيمة / الخيار", "إجراءات"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2D3748;
                color: #FFFFFF;
                gridline-color: #4A5568;
                border: none;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #1A202C;
                color: #A0AEC0;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item { padding: 6px; }
        """)
        layout.addWidget(self.table)
        self.load_options()

    def make_local_backup(self):
        file_path = create_backup()
        if file_path:
            QMessageBox.information(self, "نجاح", f"تم إنشاء نسخة احتياطية بنجاح:\n{file_path}")
        else:
            QMessageBox.critical(self, "خطأ", "فشل إنشاء النسخة الاحتياطية!")

    def restore_local_backup(self):
        """فتح نافذة اختيار ملف الباك أب واسناده لعملية الاستعادة"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف النسخة الاحتياطية", "", "Database Files (*.db)"
        )
        if file_path:
            reply = QMessageBox.question(
                self, "تأكيد الاستعادة",
                "هل أنت متأكد من استعادة هذه النسخة الاحتياطية؟\nسيتم استبدال البيانات الحالية بالكامل.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                success, msg = restore_backup_file(file_path)
                if success:
                    QMessageBox.information(self, "نجاح الاستعادة", msg)
                else:
                    QMessageBox.critical(self, "خطأ", msg)

    def sync_to_drive(self):
        file_path = create_backup()
        if not file_path:
            QMessageBox.critical(self, "خطأ", "لم يتم العثور على ملف النسخة الاحتياطية.")
            return

        QMessageBox.information(self, "تنبيه", "سيتم فتح المتصفح لتأكيد تسجيل الدخول إلى حساب Google Drive الخاص بك.")
        success, msg = upload_backup_to_drive(file_path)
        if success:
            QMessageBox.information(self, "نجاح", msg)
        else:
            QMessageBox.warning(self, "تنبيه", msg)

    def load_options(self):
        """عرض الخيارات التابعة للفئة المحددة فقط"""
        category_code = self.combo_category.currentData()
        if not category_code:
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, value FROM settings_options WHERE category = ? ORDER BY id DESC", (category_code,))
        rows = cursor.fetchall()
        conn.close()

        category_map = {
            "color": "قائمة الألوان والطفرات",
            "pair_status": "حالات الأزواج",
            "chick_status": "حالات الفروخ",
            "gender": "خيارات الجنس",
            "archive_reason": "أسباب الأرشفة"
        }

        self.table.setRowCount(0)
        for row_idx, row in enumerate(rows):
            self.table.insertRow(row_idx)

            cat_display = category_map.get(row['category'], row['category'])
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(cat_display))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row['value'])))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)

            btn_delete = QPushButton("حذف")
            btn_delete.setStyleSheet("background-color: #E53E3E; color: white; border-radius: 3px; padding: 2px 6px;")
            btn_delete.clicked.connect(lambda checked, opt_id=row['id']: self.delete_option(opt_id))

            btn_layout.addWidget(btn_delete)
            self.table.setCellWidget(row_idx, 2, btn_widget)

    def add_option(self):
        category_code = self.combo_category.currentData()
        value = self.txt_value.text().strip()

        if not value:
            QMessageBox.warning(self, "خطأ", "يجب كتابة قيمة للخيارات المنسدلة!")
            return

        if add_settings_option(category_code, value):
            self.txt_value.clear()
            self.load_options()
        else:
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء إضافة الخيار.")

    def delete_option(self, option_id):
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت تأكد من حذف هذا الخيار؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            delete_settings_option(option_id)
            self.load_options()