import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QLineEdit, QComboBox, QFormLayout, QMessageBox, QDateEdit, QSpinBox
)
from PySide6.QtCore import Qt, QDate
from app.database import get_connection

class AddEditProductionDialog(QDialog):
    def __init__(self, parent=None, prod_data=None):
        super().__init__(parent)
        self.prod_data = prod_data
        self.setWindowTitle("تعديل بيانات البطن" if prod_data else "إضافة بطن جديد")
        self.setMinimumWidth(400)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self.init_ui()
        self.load_pairs()
        if prod_data:
            self.populate_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.combo_pair_num = QComboBox()
        
        # استخدام QSpinBox لضمان إدخال الأرقام الموجبة فقط
        self.spin_clutch_num = QSpinBox()
        self.spin_clutch_num.setRange(1, 100)
        self.spin_clutch_num.setValue(1)

        self.spin_eggs_count = QSpinBox()
        self.spin_eggs_count.setRange(0, 30)

        self.spin_chicks_count = QSpinBox()
        self.spin_chicks_count.setRange(0, 30)
        
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate())
        self.date_start.setDisplayFormat("yyyy-MM-dd")

        self.date_first_egg = QDateEdit()
        self.date_first_egg.setCalendarPopup(True)
        self.date_first_egg.setDate(QDate.currentDate())
        self.date_first_egg.setDisplayFormat("yyyy-MM-dd")

        self.txt_notes = QLineEdit()

        form_layout.addRow("رقم الزوج:", self.combo_pair_num)
        form_layout.addRow("رقم البطن:", self.spin_clutch_num)
        form_layout.addRow("عدد البيض:", self.spin_eggs_count)
        form_layout.addRow("عدد الفروخ:", self.spin_chicks_count)
        form_layout.addRow("تاريخ البداية:", self.date_start)
        form_layout.addRow("تاريخ أول بيضة:", self.date_first_egg)
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
            QLineEdit, QComboBox, QDateEdit, QSpinBox {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton { border-radius: 4px; }
        """)

    def load_pairs(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT pair_number FROM pairs ORDER BY CAST(pair_number AS INTEGER) ASC, pair_number ASC")
        pairs = [str(row[0]) for row in cursor.fetchall()]
        self.combo_pair_num.addItems(pairs)
        conn.close()

    def populate_data(self):
        p_idx = self.combo_pair_num.findText(str(self.prod_data['pair_number']))
        if p_idx >= 0: self.combo_pair_num.setCurrentIndex(p_idx)
        self.combo_pair_num.setEnabled(False)

        try:
            clutch_val = int(self.prod_data['clutch_number'])
            self.spin_clutch_num.setValue(clutch_val)
        except (ValueError, TypeError):
            pass
        self.spin_clutch_num.setEnabled(False)

        try:
            self.spin_eggs_count.setValue(int(self.prod_data['eggs_count'] or 0))
        except (ValueError, TypeError):
            self.spin_eggs_count.setValue(0)

        try:
            self.spin_chicks_count.setValue(int(self.prod_data['chicks_count'] or 0))
        except (ValueError, TypeError):
            self.spin_chicks_count.setValue(0)

        if self.prod_data['start_date']:
            self.date_start.setDate(QDate.fromString(self.prod_data['start_date'], "yyyy-MM-dd"))
        if self.prod_data['first_egg_date']:
            self.date_first_egg.setDate(QDate.fromString(self.prod_data['first_egg_date'], "yyyy-MM-dd"))

        self.txt_notes.setText(self.prod_data['notes'] or "")

    def get_data(self):
        return {
            "pair_number": self.combo_pair_num.currentText(),
            "clutch_number": self.spin_clutch_num.value(),
            "eggs_count": self.spin_eggs_count.value(),
            "chicks_count": self.spin_chicks_count.value(),
            "start_date": self.date_start.date().toString("yyyy-MM-dd"),
            "first_egg_date": self.date_first_egg.date().toString("yyyy-MM-dd"),
            "notes": self.txt_notes.text().strip()
        }


class ProductionPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_pair_filter_options()
        self.load_production()

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
        title = QLabel("سجل الإنتاج (البطون)")
        title.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;")

        self.btn_add = QPushButton("+ تسجيل بطن جديد")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #38A169;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #2F855A; }
        """)
        self.btn_add.clicked.connect(self.add_production)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        # شريط البحث والفلترة لصفحة سجل الإنتاج
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 بحث برقم الزوج، رقم البطن، أو الملاحظات...")
        self.txt_search.setStyleSheet(self.input_style())
        self.txt_search.textChanged.connect(self.load_production)

        self.combo_filter_pair = QComboBox()
        self.combo_filter_pair.setStyleSheet(self.input_style())
        self.combo_filter_pair.addItem("جميع الأزواج")
        self.combo_filter_pair.currentIndexChanged.connect(self.load_production)

        filter_layout.addWidget(self.txt_search, 2)
        filter_layout.addWidget(self.combo_filter_pair, 1)

        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "رقم الزوج", "رقم البطن", "عدد البيض", 
            "عدد الفروخ", "تاريخ البداية", "أول بيضة", 
            "ملاحظات", "إجراءات"
        ])
        
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

    def load_pair_filter_options(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT pair_number FROM pairs ORDER BY CAST(pair_number AS INTEGER) ASC, pair_number ASC")
        pairs = [str(row[0]) for row in cursor.fetchall()]
        if pairs:
            self.combo_filter_pair.addItems(pairs)
        conn.close()

    def load_production(self):
        search_text = self.txt_search.text().strip() if hasattr(self, 'txt_search') else ""
        selected_pair = self.combo_filter_pair.currentText() if hasattr(self, 'combo_filter_pair') else "جميع الأزواج"

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, pair_number, clutch_number, eggs_count, chicks_count, start_date, first_egg_date, notes 
            FROM production 
            WHERE 1=1
        """
        params = []

        if search_text:
            query += " AND (pair_number LIKE ? OR CAST(clutch_number AS TEXT) LIKE ? OR notes LIKE ?)"
            pattern = f"%{search_text}%"
            params.extend([pattern, pattern, pattern])

        if selected_pair != "جميع الأزواج":
            query += " AND pair_number = ?"
            params.append(selected_pair)

        query += " ORDER BY id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row_idx, row in enumerate(rows):
            self.table.insertRow(row_idx)

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row['pair_number'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row['clutch_number'])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row['eggs_count'])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(row['chicks_count'])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(row['start_date'] or "")))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(row['first_egg_date'] or "")))
            self.table.setItem(row_idx, 6, QTableWidgetItem(str(row['notes'] or "")))

            for col in range(0, 7):
                item = self.table.item(row_idx, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)
            
            btn_edit = QPushButton("تعديل")
            btn_delete = QPushButton("حذف")
            
            btn_edit.setStyleSheet("background-color: #3182CE; color: white; border-radius: 3px; padding: 2px 6px;")
            btn_delete.setStyleSheet("background-color: #E53E3E; color: white; border-radius: 3px; padding: 2px 6px;")

            prod_data = dict(row)
            btn_edit.clicked.connect(lambda checked, data=prod_data: self.edit_production(data))
            btn_delete.clicked.connect(lambda checked, p_id=row['id']: self.delete_production(p_id))

            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_delete)
            self.table.setCellWidget(row_idx, 7, btn_widget)

    def add_production(self):
        dialog = AddEditProductionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['pair_number']:
                QMessageBox.warning(self, "خطأ", "يجب اختيار رقم الزوج!")
                return

            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO production (pair_number, clutch_number, eggs_count, chicks_count, start_date, first_egg_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data['pair_number'], data['clutch_number'], data['eggs_count'], 
                      data['chicks_count'], data['start_date'], data['first_egg_date'], data['notes']))
                conn.commit()
                conn.close()
                self.load_production()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {e}")

    def edit_production(self, prod_data):
        dialog = AddEditProductionDialog(self, prod_data)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE production 
                SET eggs_count=?, chicks_count=?, start_date=?, first_egg_date=?, notes=?
                WHERE id=?
            """, (data['eggs_count'], data['chicks_count'], data['start_date'], 
                  data['first_egg_date'], data['notes'], prod_data['id']))
            conn.commit()
            conn.close()
            self.load_production()

    def delete_production(self, prod_id):
        reply = QMessageBox.question(
            self, "تأكيد الحذف", 
            "هل أنت متأكد من حذف سجل هذا البطن؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM production WHERE id=?", (prod_id,))
            conn.commit()
            conn.close()
            self.load_production()