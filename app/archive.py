import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QLineEdit, QComboBox, QFormLayout, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from app.database import get_connection

class AddEditArchiveDialog(QDialog):
    def __init__(self, parent=None, archive_data=None):
        super().__init__(parent)
        self.archive_data = archive_data
        self.setWindowTitle("تعديل سجل الأرشيف" if archive_data else "أرشفة طير جديد")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self.init_ui()
        self.load_options()
        if archive_data:
            self.populate_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.txt_ring_num = QLineEdit()
        self.txt_color_mutations = QLineEdit()
        self.combo_gender = QComboBox()
        self.combo_reason = QComboBox()
        
        self.date_archive = QDateEdit()
        self.date_archive.setCalendarPopup(True)
        self.date_archive.setDate(QDate.currentDate())
        self.date_archive.setDisplayFormat("yyyy-MM-dd")

        self.txt_notes = QLineEdit()

        form_layout.addRow("رقم الحجل:", self.txt_ring_num)
        form_layout.addRow("اللون والطفرات:", self.txt_color_mutations)
        form_layout.addRow("الجنس:", self.combo_gender)
        form_layout.addRow("سبب الأرشفة:", self.combo_reason)
        form_layout.addRow("تاريخ الأرشفة:", self.date_archive)
        form_layout.addRow("ملاحظات:", self.txt_notes)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("حفظ")
        self.btn_cancel = QPushButton("إلغاء")
        
        self.btn_save.setStyleSheet("background-color: #3182CE; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        self.btn_cancel.setStyleSheet("background-color: #E53E3E; color: white; padding: 8px 16px; border-radius: 4px;")

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setStyleSheet("""
            QDialog { background-color: #2D3748; color: white; }
            QLabel { color: white; font-size: 13px; }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton { border-radius: 4px; }
        """)

    def load_options(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM settings_options WHERE category = 'gender'")
        genders = [row[0] for row in cursor.fetchall()]
        self.combo_gender.addItems(genders if genders else ["ذكر", "أنثى", "بانتظار DNA"])

        cursor.execute("SELECT value FROM settings_options WHERE category = 'archive_reason'")
        reasons = [row[0] for row in cursor.fetchall()]
        self.combo_reason.addItems(reasons if reasons else ["بيع", "نفوق", "استبعاد"])

        conn.close()

    def populate_data(self):
        self.txt_ring_num.setText(str(self.archive_data['ring_number'] or ''))
        self.txt_color_mutations.setText(str(self.archive_data['color_mutations'] or ''))
        
        g_idx = self.combo_gender.findText(str(self.archive_data['gender'] or ''))
        if g_idx >= 0: self.combo_gender.setCurrentIndex(g_idx)

        r_idx = self.combo_reason.findText(str(self.archive_data['reason'] or ''))
        if r_idx >= 0: self.combo_reason.setCurrentIndex(r_idx)

        if self.archive_data['archive_date']:
            self.date_archive.setDate(QDate.fromString(self.archive_data['archive_date'], "yyyy-MM-dd"))

        self.txt_notes.setText(str(self.archive_data['notes'] or ''))

    def get_data(self):
        return {
            "ring_number": self.txt_ring_num.text().strip(),
            "color_mutations": self.txt_color_mutations.text().strip(),
            "gender": self.combo_gender.currentText(),
            "reason": self.combo_reason.currentText(),
            "archive_date": self.date_archive.date().toString("yyyy-MM-dd"),
            "notes": self.txt_notes.text().strip()
        }


class ArchivePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_filter_options()
        self.load_archive()

    def input_style(self):
        return """
            background-color: #1A202C;
            color: white;
            border: 1px solid #4A5568;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 13px;
        """

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title = QLabel("سجل الأرشيف")
        title.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;")

        self.btn_add = QPushButton("+ إضافة طير للأرشيف")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #DD6B20;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #C05621; }
        """)
        self.btn_add.clicked.connect(self.add_archive)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # شريط البحث والفلترة لصفحة الأرشيف
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 بحث برقم الحجل، اللون/الطفرات، أو الملاحظات...")
        self.txt_search.setStyleSheet(self.input_style())
        self.txt_search.textChanged.connect(self.load_archive)

        self.combo_filter_reason = QComboBox()
        self.combo_filter_reason.setStyleSheet(self.input_style())
        self.combo_filter_reason.addItem("جميع الأسباب")
        self.combo_filter_reason.currentIndexChanged.connect(self.load_archive)

        self.combo_filter_gender = QComboBox()
        self.combo_filter_gender.setStyleSheet(self.input_style())
        self.combo_filter_gender.addItem("جميع الأجناس")
        self.combo_filter_gender.currentIndexChanged.connect(self.load_archive)

        filter_layout.addWidget(self.txt_search, 2)
        filter_layout.addWidget(self.combo_filter_reason, 1)
        filter_layout.addWidget(self.combo_filter_gender, 1)

        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "رقم الحجل", "اللون والطفرات", "الجنس", 
            "السبب", "تاريخ الأرشفة", "ملاحظات", "إجراءات"
        ])
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 210)

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

    def load_filter_options(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM settings_options WHERE category = 'archive_reason'")
        reasons = [row[0] for row in cursor.fetchall()]
        if reasons:
            self.combo_filter_reason.addItems(reasons)
        else:
            self.combo_filter_reason.addItems(["بيع", "نفوق", "استبعاد"])

        cursor.execute("SELECT value FROM settings_options WHERE category = 'gender'")
        genders = [row[0] for row in cursor.fetchall()]
        if genders:
            self.combo_filter_gender.addItems(genders)
        else:
            self.combo_filter_gender.addItems(["ذكر", "أنثى", "بانتظار DNA"])

        conn.close()

    def load_archive(self):
        search_text = self.txt_search.text().strip() if hasattr(self, 'txt_search') else ""
        selected_reason = self.combo_filter_reason.currentText() if hasattr(self, 'combo_filter_reason') else "جميع الأسباب"
        selected_gender = self.combo_filter_gender.currentText() if hasattr(self, 'combo_filter_gender') else "جميع الأجناس"

        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT id, ring_number, color_mutations, gender, reason, archive_date, notes FROM archive WHERE 1=1"
        params = []

        if search_text:
            query += " AND (ring_number LIKE ? OR color_mutations LIKE ? OR notes LIKE ?)"
            pattern = f"%{search_text}%"
            params.extend([pattern, pattern, pattern])

        if selected_reason != "جميع الأسباب":
            query += " AND reason = ?"
            params.append(selected_reason)

        if selected_gender != "جميع الأجناس":
            query += " AND gender = ?"
            params.append(selected_gender)

        query += " ORDER BY id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row_idx, row in enumerate(rows):
            self.table.insertRow(row_idx)

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row['ring_number'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row['color_mutations'] or "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row['gender'] or "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(row['reason'])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(row['archive_date'])))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(row['notes'] or "")))

            for col in range(0, 6):
                item = self.table.item(row_idx, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)
            
            btn_restore = QPushButton("إعادة للطيور")
            btn_edit = QPushButton("تعديل")
            btn_delete = QPushButton("حذف")
            
            btn_restore.setStyleSheet("background-color: #38A169; color: white; border-radius: 3px; padding: 2px 6px; font-weight: bold;")
            btn_edit.setStyleSheet("background-color: #3182CE; color: white; border-radius: 3px; padding: 2px 6px;")
            btn_delete.setStyleSheet("background-color: #E53E3E; color: white; border-radius: 3px; padding: 2px 6px;")

            archive_data = dict(row)
            btn_restore.clicked.connect(lambda checked, data=archive_data: self.restore_bird(data))
            btn_edit.clicked.connect(lambda checked, data=archive_data: self.edit_archive(data))
            btn_delete.clicked.connect(lambda checked, a_id=row['id']: self.delete_archive(a_id))

            btn_layout.addWidget(btn_restore)
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_delete)
            self.table.setCellWidget(row_idx, 6, btn_widget)

    def restore_bird(self, archive_data):
        ring_num = archive_data['ring_number']
        confirm = QMessageBox.question(
            self, 
            "تأكيد الاسترجاع", 
            f"هل أنت متأكد من إلغاء أرشفة الطير [{ring_num}] وإعادته إلى قائمة جميع الطيور؟",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # 1. إعادته إلى جدول جميع الطيور (individual_birds)
                cursor.execute("""
                    INSERT INTO individual_birds (ring_number, gender, color, status, source, notes)
                    VALUES (?, ?, ?, 'متاح', 'مسترجع من الأرشيف', ?)
                    ON CONFLICT(ring_number) DO UPDATE SET
                        gender=EXCLUDED.gender,
                        color=EXCLUDED.color,
                        status='متاح',
                        source='مسترجع من الأرشيف'
                """, (
                    ring_num, 
                    archive_data['gender'], 
                    archive_data['color_mutations'], 
                    archive_data['notes']
                ))

                # 2. حذفه من سجل الأرشيف
                cursor.execute("DELETE FROM archive WHERE id = ?", (archive_data['id'],))

                conn.commit()
                conn.close()

                QMessageBox.information(self, "تم الاسترجاع", f"تم استرجاع الطير [{ring_num}] وإعادته لقائمة جميع الطيور بنجاح.")
                self.load_archive()
            except Exception as err:
                QMessageBox.critical(self, "خطأ في الاسترجاع", f"حدث خطأ أثناء استرجاع الطير:\n{str(err)}")

    def add_archive(self):
        dialog = AddEditArchiveDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['ring_number']:
                QMessageBox.warning(self, "خطأ", "يجب إدخال رقم الحجل!")
                return

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO archive (ring_number, color_mutations, gender, reason, archive_date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data['ring_number'], data['color_mutations'], data['gender'], 
                  data['reason'], data['archive_date'], data['notes']))
            conn.commit()
            conn.close()
            self.load_archive()

    def edit_archive(self, archive_data):
        dialog = AddEditArchiveDialog(self, archive_data)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE archive 
                SET ring_number=?, color_mutations=?, gender=?, reason=?, archive_date=?, notes=?
                WHERE id=?
            """, (data['ring_number'], data['color_mutations'], data['gender'], 
                  data['reason'], data['archive_date'], data['notes'], archive_data['id']))
            conn.commit()
            conn.close()
            self.load_archive()

    def delete_archive(self, archive_id):
        reply = QMessageBox.question(
            self, "تأكيد الحذف", 
            "هل أنت متأكد من حذف هذا السجل من الأرشيف؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM archive WHERE id=?", (archive_id,))
            conn.commit()
            conn.close()
            self.load_archive()