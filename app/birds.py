from datetime import datetime
import os
import shutil

from app.database import get_connection
from app.services import get_settings_options_by_category
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


# --- نافذة عرض وتصدير شهادة الـ DNA ---
class DnaCertificateDialog(QDialog):

  def __init__(self, bird_data, parent=None):
    super().__init__(parent)
    self.bird_data = bird_data
    self.setWindowTitle(
        f"شهادة DNA - الطير [{bird_data.get('ring_number', '')}]"
    )
    self.setFixedSize(480, 620)
    self.setLayoutDirection(Qt.RightToLeft)
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout(self)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)

    # البطاقة الرقمية المستهدفة بالتصدير
    self.cert_card = QFrame()
    self.cert_card.setObjectName('CertCard')
    self.cert_card.setStyleSheet("""
            QFrame#CertCard {
                background-color: #1A202C;
                border: 2px solid #38A169;
                border-radius: 10px;
                padding: 15px;
            }
            QLabel { color: white; }
        """)

    card_layout = QVBoxLayout(self.cert_card)
    card_layout.setSpacing(12)

    # العنوان
    header_lbl = QLabel('🧬 شهادة فحص DNA')
    header_lbl.setStyleSheet(
        'font-size: 20px; font-weight: bold; color: #38A169;'
        ' qproperty-alignment: AlignCenter;'
    )
    card_layout.addWidget(header_lbl)

    # عرض صورة الشهادة
    dna_img_lbl = QLabel()
    dna_img_lbl.setFixedSize(420, 240)
    dna_img_lbl.setStyleSheet(
        'border: 1px dashed #4A5568; border-radius: 8px; background-color:'
        ' #2D3748;'
    )
    dna_img_lbl.setAlignment(Qt.AlignCenter)

    dna_path = self.bird_data.get('dna_path', '') or self.bird_data.get(
        'image_path', ''
    )
    if dna_path and os.path.exists(dna_path):
      dna_img_lbl.setPixmap(
          QPixmap(dna_path).scaled(
              420, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation
          )
      )
    else:
      dna_img_lbl.setText('لم يتم إرفاق صورة شهادة DNA لهذا الطير')
      dna_img_lbl.setStyleSheet(
          'color: #A0AEC0; font-size: 13px; border: 1px dashed #4A5568;'
          ' background-color: #2D3748;'
      )

    card_layout.addWidget(dna_img_lbl)

    # جدول المعلومات الأساسية
    info_form = QFormLayout()
    info_form.setSpacing(8)

    get_v = lambda k: str(self.bird_data.get(k) or '-')

    info_form.addRow('رقم الحجل:', QLabel(f"<b>{get_v('ring_number')}</b>"))
    info_form.addRow('الجنس:', QLabel(f"<b>{get_v('gender')}</b>"))
    info_form.addRow('اللون الأساسي:', QLabel(get_v('color')))
    info_form.addRow('الطفرات:', QLabel(get_v('mutations')))
    info_form.addRow('الحالة:', QLabel(get_v('status')))
    info_form.addRow('المصدر:', QLabel(get_v('source')))

    card_layout.addLayout(info_form)
    layout.addWidget(self.cert_card)

    # أزرار الإجراءات
    btns_layout = QHBoxLayout()
    btn_export = QPushButton('📥 تصدير الشهادة كـ صورة (PNG)')
    btn_export.setStyleSheet(
        'background-color: #38A169; color: white; font-weight: bold; padding:'
        ' 10px; border-radius: 6px;'
    )
    btn_export.clicked.connect(self.export_as_image)

    btn_close = QPushButton('إغلاق')
    btn_close.setStyleSheet(
        'background-color: #E53E3E; color: white; padding: 10px;'
        ' border-radius: 6px;'
    )
    btn_close.clicked.connect(self.reject)

    btns_layout.addWidget(btn_export)
    btns_layout.addWidget(btn_close)
    layout.addLayout(btns_layout)

  def export_as_image(self):
    file_path, _ = QFileDialog.getSaveFileName(
        self,
        'حفظ شهادة DNA',
        f"DNA_{self.bird_data.get('ring_number', 'bird')}.png",
        'Images (*.png)',
    )
    if file_path:
      pixmap = self.cert_card.grab()
      pixmap.save(file_path, 'PNG')
      QMessageBox.information(
          self, 'تم التصدير', 'تم تصدير وتنزيل الشهادة بنجاح!'
      )


# --- نافذة إضافة طير جديد ---
class AddBirdDialog(QDialog):

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle('إضافة طير جديد')
    self.setFixedSize(420, 530)
    self.setLayoutDirection(Qt.RightToLeft)
    self.dna_path = ''
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout(self)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    form = QFormLayout()
    form.setSpacing(10)

    color_rows = get_settings_options_by_category('color')
    db_colors = [row['value'] for row in color_rows]
    colors_list = ['اختر اللون...'] + db_colors

    self.input_ring = QLineEdit()

    self.combo_gender = QComboBox()
    gender_rows = get_settings_options_by_category('gender')
    db_genders = [row['value'] for row in gender_rows]
    self.combo_gender.addItems(
        db_genders
        if db_genders
        else ['ذكر', 'أنثى', 'بانتظار DNA', 'غير معروف']
    )

    self.combo_color = QComboBox()
    self.combo_color.addItems(colors_list)
    self.combo_color.setEditable(True)

    self.input_mutations = QLineEdit()

    self.combo_status = QComboBox()
    self.combo_status.addItems(
        ['متاح', 'مجهز للتزويج', 'للبيع', 'تم البيع', 'نافق']
    )

    self.input_source = QLineEdit()
    self.input_source.setPlaceholderText('مثلاً: إنتاج محلي / شراء')

    form.addRow('رقم الحجل *:', self.input_ring)
    form.addRow('الجنس:', self.combo_gender)
    form.addRow('اللون الأساسي:', self.combo_color)
    form.addRow('الطفرات / ملاحظات:', self.input_mutations)
    form.addRow('الحالة:', self.combo_status)
    form.addRow('المصدر:', self.input_source)

    layout.addLayout(form)

    # اختيار شهادة DNA
    btn_dna_layout = QHBoxLayout()
    self.btn_select_dna = QPushButton('اختر صورة شهادة DNA')
    self.btn_select_dna.setStyleSheet(
        'background-color: #3182CE; color: white;'
    )
    self.btn_select_dna.clicked.connect(self.select_dna)
    self.lbl_dna_path = QLabel('لم تتم الإضافة')
    self.lbl_dna_path.setStyleSheet('color: #A0AEC0; font-size: 11px;')

    btn_dna_layout.addWidget(self.btn_select_dna)
    btn_dna_layout.addWidget(self.lbl_dna_path)
    layout.addLayout(btn_dna_layout)

    btns_layout = QHBoxLayout()
    btn_save = QPushButton('حفظ')
    btn_save.setStyleSheet(
        'background-color: #38A169; color: white; font-weight: bold; padding:'
        ' 8px 15px; border-radius: 4px;'
    )
    btn_save.clicked.connect(self.save_bird)

    btn_cancel = QPushButton('إلغاء')
    btn_cancel.setStyleSheet(
        'background-color: #E53E3E; color: white; padding: 8px 15px;'
        ' border-radius: 4px;'
    )
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
        """)

  def select_dna(self):
    file_path, _ = QFileDialog.getOpenFileName(
        self, 'اختر شهادة DNA', '', 'Images (*.png *.jpg *.jpeg *.webp)'
    )
    if file_path:
      self.dna_path = file_path
      self.lbl_dna_path.setText(os.path.basename(file_path))

  def save_bird(self):
    ring_num = self.input_ring.text().strip()
    if not ring_num:
      QMessageBox.warning(self, 'تنبيه', 'يرجى إدخال رقم الحجل أولاً.')
      return

    saved_dna_path = ''
    if self.dna_path and os.path.exists(self.dna_path):
      try:
        os.makedirs('media', exist_ok=True)
        ext = os.path.splitext(self.dna_path)[1]
        saved_dna_path = os.path.join('media', f'dna_{ring_num}{ext}')
        shutil.copy(self.dna_path, saved_dna_path)
      except Exception as e:
        print(f'Error saving DNA image: {e}')

    color_val = self.combo_color.currentText()
    if color_val == 'اختر اللون...':
      color_val = ''

    conn = None
    try:
      conn = get_connection()
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO individual_birds (
                    ring_number, gender, color, mutations, status, source, image_path, dna_path
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
          (
              ring_num,
              self.combo_gender.currentText(),
              color_val,
              self.input_mutations.text().strip(),
              self.combo_status.currentText(),
              self.input_source.text().strip(),
              saved_dna_path,
              saved_dna_path,
          ),
      )
      conn.commit()
      self.accept()
    except Exception as err:
      if 'unique' in str(err).lower() or 'duplicate' in str(err).lower():
        QMessageBox.warning(
            self, 'خطأ', f'رقم الحجل ({ring_num}) مسجل مسبقاً!'
        )
      else:
        QMessageBox.critical(
            self, 'خطأ في الحفظ', f'حدث خطأ أثناء الحفظ:\n{str(err)}'
        )
    finally:
      if conn:
        conn.close()


# --- نافذة تعديل بيانات طير ---
class EditBirdDialog(QDialog):

  def __init__(self, bird_data, parent=None):
    super().__init__(parent)
    self.bird_data = bird_data
    self.setWindowTitle(
        f"تعديل الطير ({bird_data.get('ring_number', '')})"
    )
    self.setFixedSize(420, 530)
    self.setLayoutDirection(Qt.RightToLeft)

    self.current_dna_path = (
        bird_data.get('dna_path') or bird_data.get('image_path') or ''
    )
    self.selected_new_file = ''
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout(self)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    form = QFormLayout()
    form.setSpacing(10)

    color_rows = get_settings_options_by_category('color')
    db_colors = [row['value'] for row in color_rows]
    colors_list = ['اختر اللون...'] + db_colors

    self.input_ring = QLineEdit(str(self.bird_data.get('ring_number', '')))

    self.combo_gender = QComboBox()
    gender_rows = get_settings_options_by_category('gender')
    db_genders = [row['value'] for row in gender_rows]
    self.combo_gender.addItems(
        db_genders
        if db_genders
        else ['ذكر', 'أنثى', 'بانتظار DNA', 'غير معروف']
    )
    self.combo_gender.setCurrentText(
        str(self.bird_data.get('gender') or 'غير معروف')
    )

    self.combo_color = QComboBox()
    self.combo_color.addItems(colors_list)
    self.combo_color.setEditable(True)
    self.combo_color.setCurrentText(str(self.bird_data.get('color') or ''))

    self.input_mutations = QLineEdit(
        str(self.bird_data.get('mutations') or '')
    )

    self.combo_status = QComboBox()
    self.combo_status.addItems(
        ['متاح', 'مجهز للتزويج', 'للبيع', 'تم البيع', 'نافق']
    )
    self.combo_status.setCurrentText(
        str(self.bird_data.get('status') or 'متاح')
    )

    self.input_source = QLineEdit(str(self.bird_data.get('source') or ''))

    form.addRow('رقم الحجل *:', self.input_ring)
    form.addRow('الجنس:', self.combo_gender)
    form.addRow('اللون الأساسي:', self.combo_color)
    form.addRow('الطفرات / ملاحظات:', self.input_mutations)
    form.addRow('الحالة:', self.combo_status)
    form.addRow('المصدر:', self.input_source)

    layout.addLayout(form)

    btn_dna_layout = QHBoxLayout()
    self.btn_select_dna = QPushButton('تغيير شهادة DNA')
    self.btn_select_dna.setStyleSheet(
        'background-color: #3182CE; color: white;'
    )
    self.btn_select_dna.clicked.connect(self.select_dna)

    dna_name = (
        os.path.basename(self.current_dna_path)
        if self.current_dna_path
        else 'لم تتم الإضافة'
    )
    self.lbl_dna_path = QLabel(dna_name)
    self.lbl_dna_path.setStyleSheet('color: #A0AEC0; font-size: 11px;')

    btn_dna_layout.addWidget(self.btn_select_dna)
    btn_dna_layout.addWidget(self.lbl_dna_path)
    layout.addLayout(btn_dna_layout)

    btns_layout = QHBoxLayout()
    btn_save = QPushButton('تحديث البيانات')
    btn_save.setStyleSheet(
        'background-color: #3182CE; color: white; font-weight: bold; padding:'
        ' 8px 15px; border-radius: 4px;'
    )
    btn_save.clicked.connect(self.update_bird)

    btn_cancel = QPushButton('إلغاء')
    btn_cancel.setStyleSheet(
        'background-color: #E53E3E; color: white; padding: 8px 15px;'
        ' border-radius: 4px;'
    )
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
        """)

  def select_dna(self):
    file_path, _ = QFileDialog.getOpenFileName(
        self, 'اختر شهادة DNA', '', 'Images (*.png *.jpg *.jpeg *.webp)'
    )
    if file_path:
      self.selected_new_file = file_path
      self.lbl_dna_path.setText(os.path.basename(file_path))

  def update_bird(self):
    ring_num = self.input_ring.text().strip()
    if not ring_num:
      QMessageBox.warning(self, 'تنبيه', 'يرجى إدخال رقم الحجل.')
      return

    final_path = self.current_dna_path

    if self.selected_new_file and os.path.exists(self.selected_new_file):
      try:
        os.makedirs('media', exist_ok=True)
        ext = os.path.splitext(self.selected_new_file)[1]
        final_path = os.path.join('media', f'dna_{ring_num}{ext}')
        shutil.copy(self.selected_new_file, final_path)
      except Exception as e:
        print(f'Error updating DNA image: {e}')

    color_val = self.combo_color.currentText()
    if color_val == 'اختر اللون...':
      color_val = ''

    conn = None
    try:
      conn = get_connection()
      cursor = conn.cursor()
      cursor.execute(
          """
                UPDATE individual_birds SET
                    ring_number = %s,
                    gender = %s,
                    color = %s,
                    mutations = %s,
                    status = %s,
                    source = %s,
                    image_path = %s,
                    dna_path = %s
                WHERE id = %s
            """,
          (
              ring_num,
              self.combo_gender.currentText(),
              color_val,
              self.input_mutations.text().strip(),
              self.combo_status.currentText(),
              self.input_source.text().strip(),
              final_path,
              final_path,
              self.bird_data['id'],
          ),
      )
      conn.commit()
      self.accept()
    except Exception as err:
      if 'unique' in str(err).lower() or 'duplicate' in str(err).lower():
        QMessageBox.warning(
            self, 'خطأ', f'رقم الحجل ({ring_num}) مستخدم لطير آخر!'
        )
      else:
        QMessageBox.critical(
            self, 'خطأ في التحديث', f'حدث خطأ أثناء التحديث:\n{str(err)}'
        )
    finally:
      if conn:
        conn.close()


# --- صفحة جميع الطيور ---
class BirdsPage(QWidget):

  def __init__(self):
    super().__init__()
    self.setLayoutDirection(Qt.RightToLeft)
    self.init_ui()
    self.load_filter_options()
    self.load_birds()

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
    title = QLabel('إدارة جميع الطيور والشهادات')
    title.setStyleSheet('color: #FFFFFF; font-size: 22px; font-weight: bold;')

    self.btn_add = QPushButton('+ إضافة طير جديد')
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
    self.btn_add.clicked.connect(self.open_add_bird)

    header_layout.addWidget(title)
    header_layout.addStretch()
    header_layout.addWidget(self.btn_add)
    layout.addLayout(header_layout)

    filter_layout = QHBoxLayout()
    filter_layout.setSpacing(10)

    self.txt_search = QLineEdit()
    self.txt_search.setPlaceholderText(
        '🔍 بحث برقم الحجل، اللون، الطفرات، أو المصدر...'
    )
    self.txt_search.setStyleSheet(self.input_style())
    self.txt_search.textChanged.connect(self.load_birds)

    self.combo_filter_gender = QComboBox()
    self.combo_filter_gender.setStyleSheet(self.input_style())
    self.combo_filter_gender.addItem('جميع الأجناس')
    self.combo_filter_gender.currentIndexChanged.connect(self.load_birds)

    self.combo_filter_status = QComboBox()
    self.combo_filter_status.setStyleSheet(self.input_style())
    self.combo_filter_status.addItem('جميع الحالات')
    self.combo_filter_status.currentIndexChanged.connect(self.load_birds)

    self.combo_filter_color = QComboBox()
    self.combo_filter_color.setStyleSheet(self.input_style())
    self.combo_filter_color.addItem('جميع الألوان')
    self.combo_filter_color.currentIndexChanged.connect(self.load_birds)

    filter_layout.addWidget(self.txt_search, 2)
    filter_layout.addWidget(self.combo_filter_gender, 1)
    filter_layout.addWidget(self.combo_filter_status, 1)
    filter_layout.addWidget(self.combo_filter_color, 1)

    layout.addLayout(filter_layout)

    self.table = QTableWidget()
    self.table.setColumnCount(9)
    self.table.setHorizontalHeaderLabels([
        'id',
        'شهادة DNA',
        'رقم الحجل',
        'الجنس',
        'اللون',
        'الطفرات',
        'الحالة',
        'المصدر',
        'إجراءات',
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
            }
            QTableWidget::item { padding: 6px; }
        """)

    header = self.table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Stretch)
    header.setSectionResizeMode(1, QHeaderView.Fixed)
    header.setSectionResizeMode(8, QHeaderView.Fixed)
    self.table.setColumnWidth(1, 85)
    self.table.setColumnWidth(8, 300)

    layout.addWidget(self.table)

  def load_filter_options(self):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT value FROM settings_options WHERE category = 'gender'"
    )
    rows = cursor.fetchall()
    genders = [
        list(r.values())[0] if isinstance(r, dict) else r[0] for r in rows
    ]
    if genders:
      self.combo_filter_gender.addItems(genders)
    else:
      self.combo_filter_gender.addItems(
          ['ذكر', 'أنثى', 'بانتظار DNA', 'غير معروف']
      )

    self.combo_filter_status.addItems(
        ['متاح', 'مجهز للتزويج', 'للبيع', 'تم البيع', 'نافق']
    )

    cursor.execute(
        "SELECT value FROM settings_options WHERE category = 'color'"
    )
    rows = cursor.fetchall()
    colors = [
        list(r.values())[0] if isinstance(r, dict) else r[0] for r in rows
    ]
    if colors:
      self.combo_filter_color.addItems(colors)

    conn.close()

  def open_add_bird(self):
    dialog = AddBirdDialog(self)
    if dialog.exec() == QDialog.Accepted:
      self.load_birds()

  def edit_bird(self, bird_data):
    dialog = EditBirdDialog(bird_data, self)
    if dialog.exec() == QDialog.Accepted:
      self.load_birds()

  def show_dna_certificate(self, bird_data):
    dialog = DnaCertificateDialog(bird_data, self)
    dialog.exec()

  def load_birds(self):
    search_text = (
        self.txt_search.text().strip() if hasattr(self, 'txt_search') else ''
    )
    selected_gender = (
        self.combo_filter_gender.currentText()
        if hasattr(self, 'combo_filter_gender')
        else 'جميع الأجناس'
    )
    selected_status = (
        self.combo_filter_status.currentText()
        if hasattr(self, 'combo_filter_status')
        else 'جميع الحالات'
    )
    selected_color = (
        self.combo_filter_color.currentText()
        if hasattr(self, 'combo_filter_color')
        else 'جميع الألوان'
    )

    conn = None
    try:
      conn = get_connection()
      cursor = conn.cursor()

      try:
        cursor.execute(
            'ALTER TABLE individual_birds ADD COLUMN IF NOT EXISTS dna_path TEXT'
        )
        conn.commit()
      except Exception:
        pass

      query = 'SELECT * FROM individual_birds WHERE 1=1'
      params = []

      if search_text:
        query += (
            ' AND (ring_number LIKE %s OR color LIKE %s OR mutations LIKE %s OR'
            ' source LIKE %s)'
        )
        pattern = f'%{search_text}%'
        params.extend([pattern, pattern, pattern, pattern])

      if selected_gender != 'جميع الأجناس':
        query += ' AND gender = %s'
        params.append(selected_gender)

      if selected_status != 'جميع الحالات':
        query += ' AND status = %s'
        params.append(selected_status)

      if selected_color != 'جميع الألوان':
        query += ' AND color = %s'
        params.append(selected_color)

      query += ' ORDER BY id DESC'

      cursor.execute(query, params)
      rows = cursor.fetchall()
    except Exception as e:
      print(f'Error loading birds: {e}')
      return
    finally:
      if conn:
        conn.close()

    self.table.setRowCount(0)
    for row_idx, row in enumerate(rows):
      bird_dict = dict(row)
      self.table.insertRow(row_idx)
      self.table.setRowHeight(row_idx, 75)

      self.table.setItem(
          row_idx, 0, QTableWidgetItem(str(bird_dict['id']))
      )

      img_container = QWidget()
      img_layout = QVBoxLayout(img_container)
      img_layout.setContentsMargins(2, 2, 2, 2)
      img_layout.setAlignment(Qt.AlignCenter)

      lbl_img = QLabel()
      lbl_img.setFixedSize(65, 65)
      lbl_img.setAlignment(Qt.AlignCenter)

      dna_p = (
          bird_dict.get('dna_path') or bird_dict.get('image_path') or ''
      )
      if dna_p and os.path.exists(dna_p):
        pixmap = QPixmap(dna_p)
        scaled_pix = pixmap.scaled(
            lbl_img.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        lbl_img.setPixmap(scaled_pix)
      else:
        lbl_img.setText('لا شهادة')
        lbl_img.setStyleSheet('color: #718096; font-size: 11px;')

      img_layout.addWidget(lbl_img)
      self.table.setCellWidget(row_idx, 1, img_container)

      self.table.setItem(
          row_idx, 2, QTableWidgetItem(str(bird_dict['ring_number']))
      )
      self.table.setItem(
          row_idx, 3, QTableWidgetItem(str(bird_dict.get('gender') or ''))
      )
      self.table.setItem(
          row_idx, 4, QTableWidgetItem(str(bird_dict.get('color') or ''))
      )
      self.table.setItem(
          row_idx, 5, QTableWidgetItem(str(bird_dict.get('mutations') or ''))
      )
      self.table.setItem(
          row_idx, 6, QTableWidgetItem(str(bird_dict.get('status') or ''))
      )
      self.table.setItem(
          row_idx, 7, QTableWidgetItem(str(bird_dict.get('source') or ''))
      )

      for col in range(2, 8):
        item = self.table.item(row_idx, col)
        if item:
          item.setTextAlignment(Qt.AlignCenter)

      btn_widget = QWidget()
      btn_layout = QHBoxLayout(btn_widget)
      btn_layout.setContentsMargins(4, 2, 4, 2)
      btn_layout.setSpacing(4)
      btn_layout.setAlignment(Qt.AlignCenter)

      btn_cert = QPushButton('شهادة DNA')
      btn_edit = QPushButton('تعديل')
      btn_archive = QPushButton('أرشفة')
      btn_delete = QPushButton('حذف')

      btn_cert.setStyleSheet("""
                QPushButton {
                    background-color: #38A169;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 6px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 65px;
                }
                QPushButton:hover { background-color: #2F855A; }
            """)

      btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #3182CE;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 6px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 45px;
                }
                QPushButton:hover { background-color: #2B6CB0; }
            """)

      btn_archive.setStyleSheet("""
                QPushButton {
                    background-color: #DD6B20;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 6px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 45px;
                }
                QPushButton:hover { background-color: #C05621; }
            """)

      btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #E53E3E;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 6px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 42px;
                }
                QPushButton:hover { background-color: #C53030; }
            """)

      btn_cert.clicked.connect(
          lambda checked, data=bird_dict: self.show_dna_certificate(data)
      )
      btn_edit.clicked.connect(
          lambda checked, data=bird_dict: self.edit_bird(data)
      )
      btn_archive.clicked.connect(
          lambda checked, ring=bird_dict['ring_number'], color=str(
              bird_dict.get('color') or ''
          ), gender=str(bird_dict.get('gender') or ''): self.archive_bird(
              ring, color, gender
          )
      )
      btn_delete.clicked.connect(
          lambda checked, b_id=bird_dict['id'], ring=bird_dict[
              'ring_number'
          ]: self.delete_bird(b_id, ring)
      )

      btn_layout.addWidget(btn_cert)
      btn_layout.addWidget(btn_edit)
      btn_layout.addWidget(btn_archive)
      btn_layout.addWidget(btn_delete)
      self.table.setCellWidget(row_idx, 8, btn_widget)

  def archive_bird(self, ring_number, color, gender):
    confirm = QMessageBox.question(
        self,
        'تأكيد الأرشفة',
        f'هل أنت متأكد من نقل الطير صاحب الحجل [{ring_number}] إلى الأرشيف؟',
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )

    if confirm == QMessageBox.Yes:
      reasons = ['بيع', 'نفوق', 'استبعاد', 'إهداء']
      reason, ok = QInputDialog.getItem(
          self, 'سبب الأرشفة', 'اختر سبب نقل الطير للأرشيف:', reasons, 0, False
      )

      if ok and reason:
        conn = None
        try:
          conn = get_connection()
          cursor = conn.cursor()

          today_str = datetime.now().strftime('%Y-%m-%d')

          cursor.execute(
              """
                            INSERT INTO archive (ring_number, color_mutations, gender, reason, archive_date, notes)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """,
              (
                  ring_number,
                  color,
                  gender,
                  reason,
                  today_str,
                  'تم النقل من قائمة الطيور',
              ),
          )

          cursor.execute(
              'DELETE FROM individual_birds WHERE ring_number = %s',
              (ring_number,),
          )
          cursor.execute(
              'DELETE FROM chicks WHERE ring_number = %s', (ring_number,)
          )

          conn.commit()
          QMessageBox.information(
              self,
              'تمت الأرشفة',
              f'تم نقل الطير [{ring_number}] بنجاح إلى صفحة الأرشيف.',
          )
        finally:
          if conn:
            conn.close()

        self.load_birds()

  def delete_bird(self, bird_id, ring_number):
    reply = QMessageBox.question(
        self,
        'تأكيد الحذف',
        f'هل أنت متأكد من حذف الطير رقم ({ring_number})؟',
        QMessageBox.Yes | QMessageBox.No,
    )
    if reply == QMessageBox.Yes:
      conn = None
      try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM individual_birds WHERE id=%s', (bird_id,)
        )
        conn.commit()
      finally:
        if conn:
          conn.close()
      self.load_birds()