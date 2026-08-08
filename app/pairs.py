import sqlite3
import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QComboBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from app.database import get_connection
from app.services import get_settings_options_by_category

# --- نافذة إضافة زوج جديد ---
class AddPairDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة زوج جديد")
        self.setFixedSize(420, 520)
        self.setLayoutDirection(Qt.RightToLeft)
        self.image_path = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        color_rows = get_settings_options_by_category('color')
        db_colors = [row['value'] for row in color_rows]
        colors_list = ["اختر اللون..."] + db_colors

        self.input_pair_num = QLineEdit()
        self.input_male_ring = QLineEdit()
        self.input_female_ring = QLineEdit()
        
        self.combo_male_color = QComboBox()
        self.combo_male_color.addItems(colors_list)
        self.combo_male_color.setEditable(True)

        self.combo_female_color = QComboBox()
        self.combo_female_color.addItems(colors_list)
        self.combo_female_color.setEditable(True)

        self.combo_status = QComboBox()
        status_rows = get_settings_options_by_category('pair_status')
        db_statuses = [row['value'] for row in status_rows]
        if db_statuses:
            self.combo_status.addItems(db_statuses)
        else:
            self.combo_status.addItems(["إنتاج", "تجهيز", "راحة", "مستبعد"])

        form.addRow("رقم الزوج *:", self.input_pair_num)
        form.addRow("حجل الذكر:", self.input_male_ring)
        form.addRow("حجل الأنثى:", self.input_female_ring)
        form.addRow("لون الذكر:", self.combo_male_color)
        form.addRow("لون الأنثى:", self.combo_female_color)
        form.addRow("الحالة:", self.combo_status)

        layout.addLayout(form)

        btn_img_layout = QHBoxLayout()
        self.btn_select_img = QPushButton("اختر صورة للزوج")
        self.btn_select_img.clicked.connect(self.select_image)
        self.lbl_img_path = QLabel("لم يتم اختيار صورة")
        self.lbl_img_path.setStyleSheet("color: #A0AEC0; font-size: 11px;")
        
        btn_img_layout.addWidget(self.btn_select_img)
        btn_img_layout.addWidget(self.lbl_img_path)
        layout.addLayout(btn_img_layout)

        btns_layout = QHBoxLayout()
        btn_save = QPushButton("حفظ")
        btn_save.setStyleSheet("background-color: #38A169; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        btn_save.clicked.connect(self.save_pair)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setStyleSheet("background-color: #E53E3E; color: white; padding: 8px 15px; border-radius: 4px;")
        btn_cancel.clicked.connect(self.reject)

        btns_layout.addWidget(btn_save)
        btns_layout.addWidget(btn_cancel)
        layout.addLayout(btns_layout)

        self.setStyleSheet("""
            QDialog { background-color: #2D3748; color: white; }
            QLabel { color: white; font-size: 13px; }
            QLineEdit, QComboBox {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton { border-radius: 4px; }
        """)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "اختر صورة الزوج", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if file_path:
            self.image_path = file_path
            self.lbl_img_path.setText(os.path.basename(file_path))

    def save_pair(self):
        pair_num = self.input_pair_num.text().strip()
        if not pair_num:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال رقم الزوج أولاً.")
            return

        male_ring = self.input_male_ring.text().strip()
        female_ring = self.input_female_ring.text().strip()

        saved_img_path = ""
        if self.image_path and os.path.exists(self.image_path):
            try:
                os.makedirs("media", exist_ok=True)
                ext = os.path.splitext(self.image_path)[1]
                saved_img_path = os.path.join("media", f"pair_{pair_num}{ext}")
                shutil.copy(self.image_path, saved_img_path)
            except Exception as e:
                print(f"Error saving image: {e}")

        male_color = self.combo_male_color.currentText()
        if male_color == "اختر اللون...":
            male_color = ""
            
        female_color = self.combo_female_color.currentText()
        if female_color == "اختر اللون...":
            female_color = ""

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pairs (
                    pair_number, male_ring, female_ring, male_color, female_color, status, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pair_num,
                male_ring,
                female_ring,
                male_color,
                female_color,
                self.combo_status.currentText(),
                saved_img_path
            ))

            # المزامنة مع قائمة الطيور بدون أخطاء القفل
            if male_ring:
                cursor.execute("SELECT id FROM individual_birds WHERE ring_number = ?", (male_ring,))
                if cursor.fetchone():
                    cursor.execute("UPDATE individual_birds SET gender='ذكر', color=?, status='في زوج', source=? WHERE ring_number=?", 
                                   (male_color, f"زوج برقم {pair_num}", male_ring))
                else:
                    cursor.execute("INSERT INTO individual_birds (ring_number, gender, color, status, source) VALUES (?, 'ذكر', ?, 'في زوج', ?)",
                                   (male_ring, male_color, f"زوج برقم {pair_num}"))

            if female_ring:
                cursor.execute("SELECT id FROM individual_birds WHERE ring_number = ?", (female_ring,))
                if cursor.fetchone():
                    cursor.execute("UPDATE individual_birds SET gender='أنثى', color=?, status='في زوج', source=? WHERE ring_number=?", 
                                   (female_color, f"زوج برقم {pair_num}", female_ring))
                else:
                    cursor.execute("INSERT INTO individual_birds (ring_number, gender, color, status, source) VALUES (?, 'أنثى', ?, 'في زوج', ?)",
                                   (female_ring, female_color, f"زوج برقم {pair_num}"))

            conn.commit()
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطأ", f"رقم الزوج ({pair_num}) موجود مسبقاً!")
        except Exception as err:
            QMessageBox.critical(self, "خطأ في الحفظ", f"حدث خطأ أثناء الحفظ:\n{str(err)}")
        finally:
            if conn:
                conn.close()


# --- نافذة تعديل بيانات زوج ---
class EditPairDialog(QDialog):
    def __init__(self, pair_data, parent=None):
        super().__init__(parent)
        self.pair_data = pair_data
        self.setWindowTitle(f"تعديل الزوج {pair_data['pair_number']}")
        self.setFixedSize(420, 520)
        self.setLayoutDirection(Qt.RightToLeft)
        self.image_path = pair_data['image_path'] if 'image_path' in pair_data.keys() and pair_data['image_path'] else ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        color_rows = get_settings_options_by_category('color')
        db_colors = [row['value'] for row in color_rows]
        colors_list = ["اختر اللون..."] + db_colors

        self.input_pair_num = QLineEdit(str(self.pair_data['pair_number']))
        self.input_male_ring = QLineEdit(str(self.pair_data['male_ring'] or ''))
        self.input_female_ring = QLineEdit(str(self.pair_data['female_ring'] or ''))
        
        self.combo_male_color = QComboBox()
        self.combo_male_color.addItems(colors_list)
        self.combo_male_color.setEditable(True)
        self.combo_male_color.setCurrentText(str(self.pair_data['male_color'] or ''))

        self.combo_female_color = QComboBox()
        self.combo_female_color.addItems(colors_list)
        self.combo_female_color.setEditable(True)
        self.combo_female_color.setCurrentText(str(self.pair_data['female_color'] or ''))

        self.combo_status = QComboBox()
        status_rows = get_settings_options_by_category('pair_status')
        db_statuses = [row['value'] for row in status_rows]
        if db_statuses:
            self.combo_status.addItems(db_statuses)
        else:
            self.combo_status.addItems(["إنتاج", "تجهيز", "راحة", "مستبعد"])
        self.combo_status.setCurrentText(str(self.pair_data['status'] or ''))

        form.addRow("رقم الزوج *:", self.input_pair_num)
        form.addRow("حجل الذكر:", self.input_male_ring)
        form.addRow("حجل الأنثى:", self.input_female_ring)
        form.addRow("لون الذكر:", self.combo_male_color)
        form.addRow("لون الأنثى:", self.combo_female_color)
        form.addRow("الحالة:", self.combo_status)

        layout.addLayout(form)

        btn_img_layout = QHBoxLayout()
        self.btn_select_img = QPushButton("تغيير الصورة")
        self.btn_select_img.clicked.connect(self.select_image)
        img_name = os.path.basename(self.image_path) if self.image_path else "لم يتم اختيار صورة"
        self.lbl_img_path = QLabel(img_name)
        self.lbl_img_path.setStyleSheet("color: #A0AEC0; font-size: 11px;")
        
        btn_img_layout.addWidget(self.btn_select_img)
        btn_img_layout.addWidget(self.lbl_img_path)
        layout.addLayout(btn_img_layout)

        btns_layout = QHBoxLayout()
        btn_save = QPushButton("تحديث البيانات")
        btn_save.setStyleSheet("background-color: #3182CE; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        btn_save.clicked.connect(self.update_pair)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setStyleSheet("background-color: #E53E3E; color: white; padding: 8px 15px; border-radius: 4px;")
        btn_cancel.clicked.connect(self.reject)

        btns_layout.addWidget(btn_save)
        btns_layout.addWidget(btn_cancel)
        layout.addLayout(btns_layout)

        self.setStyleSheet("""
            QDialog { background-color: #2D3748; color: white; }
            QLabel { color: white; font-size: 13px; }
            QLineEdit, QComboBox {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton { border-radius: 4px; }
        """)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "اختر صورة الزوج", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if file_path:
            self.image_path = file_path
            self.lbl_img_path.setText(os.path.basename(file_path))

    def update_pair(self):
        pair_num = self.input_pair_num.text().strip()
        if not pair_num:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال رقم الزوج.")
            return

        male_ring = self.input_male_ring.text().strip()
        female_ring = self.input_female_ring.text().strip()

        saved_img_path = self.image_path
        if self.image_path and os.path.exists(self.image_path) and self.image_path != self.pair_data.get('image_path'):
            try:
                os.makedirs("media", exist_ok=True)
                ext = os.path.splitext(self.image_path)[1]
                saved_img_path = os.path.join("media", f"pair_{pair_num}{ext}")
                shutil.copy(self.image_path, saved_img_path)
            except Exception as e:
                print(f"Error updating image: {e}")

        male_color = self.combo_male_color.currentText()
        if male_color == "اختر اللون...": male_color = ""
            
        female_color = self.combo_female_color.currentText()
        if female_color == "اختر اللون...": female_color = ""

        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pairs SET
                    pair_number = ?,
                    male_ring = ?,
                    female_ring = ?,
                    male_color = ?,
                    female_color = ?,
                    status = ?,
                    image_path = ?
                WHERE id = ?
            """, (
                pair_num,
                male_ring,
                female_ring,
                male_color,
                female_color,
                self.combo_status.currentText(),
                saved_img_path,
                self.pair_data['id']
            ))

            if male_ring:
                cursor.execute("SELECT id FROM individual_birds WHERE ring_number = ?", (male_ring,))
                if cursor.fetchone():
                    cursor.execute("UPDATE individual_birds SET gender='ذكر', color=?, status='في زوج', source=? WHERE ring_number=?", 
                                   (male_color, f"زوج برقم {pair_num}", male_ring))
                else:
                    cursor.execute("INSERT INTO individual_birds (ring_number, gender, color, status, source) VALUES (?, 'ذكر', ?, 'في زوج', ?)",
                                   (male_ring, male_color, f"زوج برقم {pair_num}"))

            if female_ring:
                cursor.execute("SELECT id FROM individual_birds WHERE ring_number = ?", (female_ring,))
                if cursor.fetchone():
                    cursor.execute("UPDATE individual_birds SET gender='أنثى', color=?, status='في زوج', source=? WHERE ring_number=?", 
                                   (female_color, f"زوج برقم {pair_num}", female_ring))
                else:
                    cursor.execute("INSERT INTO individual_birds (ring_number, gender, color, status, source) VALUES (?, 'أنثى', ?, 'في زوج', ?)",
                                   (female_ring, female_color, f"زوج برقم {pair_num}"))

            conn.commit()
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطأ", f"رقم الزوج ({pair_num}) مستخدم لزوج آخر!")
        except Exception as err:
            QMessageBox.critical(self, "خطأ في التحديث", f"حدث خطأ أثناء التحديث:\n{str(err)}")
        finally:
            if conn:
                conn.close()


# --- صفحة الأزواج الرئيسية ---
class PairsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title = QLabel("إدارة الأزواج")
        title.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: bold;")
        
        self.btn_add = QPushButton("+ إضافة زوج جديد")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #38A169;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2F855A; }
        """)
        self.btn_add.clicked.connect(self.open_add_pair)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)

        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 بحث برقم الزوج، حجل الذكر، حجل الأنثى، أو اللون...")
        self.txt_search.setStyleSheet("""
            QLineEdit {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3182CE;
            }
        """)
        self.txt_search.textChanged.connect(self.load_pairs)
        search_layout.addWidget(self.txt_search)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "id", "الصورة", "رقم الزوج", "حجل الذكر", "حجل الأنثى",
            "لون الذكر", "لون الأنثى", "عدد البطون", "عدد الفروخ",
            "الحالة", "ملاحظات", "إجراءات"
        ])
        
        self.table.hideColumn(0)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2D3748;
                color: #FFFFFF;
                gridline-color: #4A5568;
                border: none;
                border-radius: 8px;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #1A202C;
                color: #A0AEC0;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #4A5568;
            }
            QTableWidget::item {
                border-bottom: 1px solid #4A5568;
            }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(11, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 85)
        self.table.setColumnWidth(11, 140)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(10, QHeaderView.Stretch)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        self.load_pairs()

    def open_add_pair(self):
        dialog = AddPairDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_pairs()

    def edit_pair(self, pair_row):
        dialog = EditPairDialog(pair_row, self)
        if dialog.exec() == QDialog.Accepted:
            self.load_pairs()

    def load_pairs(self):
        search_query = self.txt_search.text().strip() if hasattr(self, 'txt_search') else ""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    p.id,
                    p.pair_number,
                    p.male_ring,
                    p.female_ring,
                    p.male_color,
                    p.female_color,
                    COUNT(pr.id) AS clutch_count,
                    COALESCE(SUM(pr.chicks_count), 0) AS chick_count,
                    p.status,
                    p.notes,
                    p.image_path
                FROM pairs p
                LEFT JOIN production pr ON p.pair_number = pr.pair_number
            """
            
            params = []
            if search_query:
                query += """
                    WHERE p.pair_number LIKE ? 
                       OR p.male_ring LIKE ? 
                       OR p.female_ring LIKE ? 
                       OR p.male_color LIKE ? 
                       OR p.female_color LIKE ?
                """
                pattern = f"%{search_query}%"
                params = [pattern, pattern, pattern, pattern, pattern]

            query += """
                GROUP BY p.id, p.pair_number, p.male_ring, p.female_ring, p.male_color, p.female_color, p.status, p.notes, p.image_path
                ORDER BY CAST(p.pair_number AS INTEGER) ASC, p.pair_number ASC
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
        except Exception as e:
            print(f"Error loading pairs: {e}")
            return
        finally:
            if conn:
                conn.close()

        self.table.setRowCount(0)
        
        for row_idx, row in enumerate(rows):
            self.table.insertRow(row_idx)
            self.table.setRowHeight(row_idx, 80)

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))

            img_container = QWidget()
            img_layout = QVBoxLayout(img_container)
            img_layout.setContentsMargins(2, 2, 2, 2)
            img_layout.setAlignment(Qt.AlignCenter)
            
            lbl_img = QLabel()
            lbl_img.setFixedSize(70, 70)
            lbl_img.setAlignment(Qt.AlignCenter)
            
            img_p = row['image_path'] if 'image_path' in row.keys() else ""
            if img_p and os.path.exists(img_p):
                pixmap = QPixmap(img_p)
                scaled_pix = pixmap.scaled(lbl_img.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl_img.setPixmap(scaled_pix)
            else:
                lbl_img.setText("لا صورة")
                lbl_img.setStyleSheet("color: #718096; font-size: 11px;")

            img_layout.addWidget(lbl_img)
            self.table.setCellWidget(row_idx, 1, img_container)

            get_val = lambda key, default='': str(row[key]) if key in row.keys() and row[key] is not None else default

            self.table.setItem(row_idx, 2, QTableWidgetItem(get_val('pair_number')))
            self.table.setItem(row_idx, 3, QTableWidgetItem(get_val('male_ring')))
            self.table.setItem(row_idx, 4, QTableWidgetItem(get_val('female_ring')))
            self.table.setItem(row_idx, 5, QTableWidgetItem(get_val('male_color')))
            self.table.setItem(row_idx, 6, QTableWidgetItem(get_val('female_color')))
            self.table.setItem(row_idx, 7, QTableWidgetItem(get_val('clutch_count', '0')))
            self.table.setItem(row_idx, 8, QTableWidgetItem(get_val('chick_count', '0')))
            self.table.setItem(row_idx, 9, QTableWidgetItem(get_val('status')))
            self.table.setItem(row_idx, 10, QTableWidgetItem(get_val('notes')))

            for col in range(2, 11):
                item = self.table.item(row_idx, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 0, 2, 0)
            actions_layout.setSpacing(4)

            btn_edit = QPushButton("تعديل")
            btn_edit.setStyleSheet("background-color: #3182CE; color: white; border-radius: 4px; padding: 4px 8px;")
            btn_edit.clicked.connect(lambda checked, r=row: self.edit_pair(r))

            btn_delete = QPushButton("حذف")
            btn_delete.setStyleSheet("background-color: #E53E3E; color: white; border-radius: 4px; padding: 4px 8px;")
            btn_delete.clicked.connect(lambda checked, r_id=row['id'], p_num=row['pair_number']: self.delete_pair(r_id, p_num))

            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_delete)
            self.table.setCellWidget(row_idx, 11, actions_widget)

    def delete_pair(self, pair_id, pair_number):
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل أنت متأكد من حذف الزوج رقم ({pair_number})؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM pairs WHERE id=?", (pair_id,))
                conn.commit()
            finally:
                if conn:
                    conn.close()
            self.load_pairs()