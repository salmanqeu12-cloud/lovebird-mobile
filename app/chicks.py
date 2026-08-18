from datetime import datetime
import os

from app.database import get_connection
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class AddEditChickDialog(QDialog):

  def __init__(self, parent=None, chick_data=None):
    super().__init__(parent)
    self.chick_data = chick_data
    self.setWindowTitle(
        "تعديل بيانات فرخ" if chick_data else "إضافة فرخ جديد"
    )
    self.setMinimumWidth(400)
    self.setLayoutDirection(Qt.RightToLeft)

    self.init_ui()
    self.load_options()
    if chick_data:
      self.populate_data()

  def init_ui(self):
    layout = QVBoxLayout(self)
    form_layout = QFormLayout()
    form_layout.setSpacing(12)

    self.txt_ring_num = QLineEdit()
    self.combo_pair_num = QComboBox()
    self.txt_hatch_month = QLineEdit()
    self.txt_hatch_month.setPlaceholderText(
        "MM-YYYY أو YYYY-MM (مثال: 6-2026)"
    )

    self.combo_color = QComboBox()
    self.combo_color.setEditable(True)

    self.txt_mutations = QLineEdit()
    self.combo_gender = QComboBox()
    self.combo_status = QComboBox()
    self.txt_notes = QLineEdit()

    form_layout.addRow("رقم الحجل *:", self.txt_ring_num)
    form_layout.addRow("رقم الزوج:", self.combo_pair_num)
    form_layout.addRow("شهر الفقس *:", self.txt_hatch_month)
    form_layout.addRow("اللون:", self.combo_color)
    form_layout.addRow("الطفرات:", self.txt_mutations)
    form_layout.addRow("الجنس:", self.combo_gender)
    form_layout.addRow("الحالة:", self.combo_status)
    form_layout.addRow("ملاحظات:", self.txt_notes)

    layout.addLayout(form_layout)

    btn_layout = QHBoxLayout()
    self.btn_save = QPushButton("حفظ")
    self.btn_cancel = QPushButton("إلغاء")

    self.btn_save.setStyleSheet(
        "background-color: #3182CE; color: white; padding: 8px 16px;"
        " border-radius: 4px;"
    )
    self.btn_cancel.setStyleSheet(
        "background-color: #E2E8F0; color: #2D3748; padding: 8px 16px;"
        " border-radius: 4px;"
    )

    self.btn_save.clicked.connect(self.accept)
    self.btn_cancel.clicked.connect(self.reject)

    btn_layout.addWidget(self.btn_save)
    btn_layout.addWidget(self.btn_cancel)
    layout.addLayout(btn_layout)

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

  def load_options(self):
    conn = None
    try:
      conn = get_connection()
      cursor = conn.cursor()

      cursor.execute(
          "SELECT pair_number FROM pairs ORDER BY CASE WHEN pair_number ~"
          " '^[0-9]+$' THEN CAST(pair_number AS INTEGER) ELSE 999999 END ASC,"
          " pair_number ASC"
      )
      rows = cursor.fetchall()
      pairs = [
          list(row.values())[0] if isinstance(row, dict) else row[0]
          for row in rows
      ]
      self.combo_pair_num.addItems(["بدون"] + pairs)

      cursor.execute(
          "SELECT value FROM settings_options WHERE category = 'color'"
      )
      rows = cursor.fetchall()
      colors = [
          list(row.values())[0] if isinstance(row, dict) else row[0]
          for row in rows
      ]
      self.combo_color.addItems(colors)

      cursor.execute(
          "SELECT value FROM settings_options WHERE category = 'gender'"
      )
      rows = cursor.fetchall()
      genders = [
          list(row.values())[0] if isinstance(row, dict) else row[0]
          for row in rows
      ]
      self.combo_gender.addItems(
          genders if genders else ["ذكر", "أنثى", "بانتظار DNA"]
      )

      cursor.execute(
          "SELECT value FROM settings_options WHERE category = 'chick_status'"
      )
      rows = cursor.fetchall()
      statuses = [
          list(row.values())[0] if isinstance(row, dict) else row[0]
          for row in rows
      ]
      self.combo_status.addItems(
          statuses if statuses else ["محتفظ به", "للبيع", "تم البيع", "نافق"]
      )
    finally:
      if conn:
        conn.close()

  def populate_data(self):
    self.txt_ring_num.setText(str(self.chick_data["ring_number"]))
    self.txt_ring_num.setReadOnly(False)

    p_idx = self.combo_pair_num.findText(
        self.chick_data["pair_number"] or "بدون"
    )
    if p_idx >= 0:
      self.combo_pair_num.setCurrentIndex(p_idx)

    self.txt_hatch_month.setText(str(self.chick_data["hatch_month"] or ""))

    self.combo_color.setCurrentText(self.chick_data["color"] or "")
    self.txt_mutations.setText(self.chick_data["mutations"] or "")

    g_idx = self.combo_gender.findText(self.chick_data["gender"] or "")
    if g_idx >= 0:
      self.combo_gender.setCurrentIndex(g_idx)

    s_idx = self.combo_status.findText(self.chick_data["status"] or "")
    if s_idx >= 0:
      self.combo_status.setCurrentIndex(s_idx)

    self.txt_notes.setText(self.chick_data["notes"] or "")

  def get_data(self):
    pair_val = self.combo_pair_num.currentText()
    return {
        "ring_number": self.txt_ring_num.text().strip(),
        "pair_number": None if pair_val == "بدون" else pair_val,
        "hatch_month": self.txt_hatch_month.text().strip(),
        "color": self.combo_color.currentText(),
        "mutations": self.txt_mutations.text().strip(),
        "gender": self.combo_gender.currentText(),
        "status": self.combo_status.currentText(),
        "notes": self.txt_notes.text().strip(),
    }


class ChicksPage(QWidget):

  def __init__(self):
    super().__init__()
    self.setLayoutDirection(Qt.RightToLeft)
    self.init_ui()
    self.load_filter_options()
    self.load_chicks()

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
    title = QLabel("إدارة الفروخ")
    title.setStyleSheet(
        "color: #FFFFFF; font-size: 20px; font-weight: bold;"
    )

    self.btn_add = QPushButton("+ إضافة فرخ جديد")
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
    self.btn_add.clicked.connect(self.add_chick)

    header_layout.addWidget(title)
    header_layout.addStretch()
    header_layout.addWidget(self.btn_add)
    layout.addLayout(header_layout)

    filter_layout = QHBoxLayout()
    filter_layout.setSpacing(10)

    self.txt_search = QLineEdit()
    self.txt_search.setPlaceholderText(
        "🔍 بحث برقم الحجل أو رقم الزوج..."
    )
    self.txt_search.setStyleSheet(self.input_style())
    self.txt_search.textChanged.connect(self.load_chicks)

    self.combo_filter_gender = QComboBox()
    self.combo_filter_gender.setStyleSheet(self.input_style())
    self.combo_filter_gender.addItem("جميع الأجناس")
    self.combo_filter_gender.currentIndexChanged.connect(self.load_chicks)

    self.combo_filter_status = QComboBox()
    self.combo_filter_status.setStyleSheet(self.input_style())
    self.combo_filter_status.addItem("جميع الحالات")
    self.combo_filter_status.currentIndexChanged.connect(self.load_chicks)

    self.combo_filter_color = QComboBox()
    self.combo_filter_color.setStyleSheet(self.input_style())
    self.combo_filter_color.addItem("جميع الألوان")
    self.combo_filter_color.currentIndexChanged.connect(self.load_chicks)

    filter_layout.addWidget(self.txt_search, 2)
    filter_layout.addWidget(self.combo_filter_gender, 1)
    filter_layout.addWidget(self.combo_filter_status, 1)
    filter_layout.addWidget(self.combo_filter_color, 1)

    layout.addLayout(filter_layout)

    self.table = QTableWidget()
    self.table.setColumnCount(10)
    self.table.setHorizontalHeaderLabels([
        "رقم الحجل",
        "رقم الزوج",
        "شهر الفقس",
        "العمر الحالي",
        "اللون",
        "الطفرات",
        "الجنس",
        "الحالة",
        "ملاحظات",
        "إجراءات",
    ])

    header = self.table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Stretch)
    header.setSectionResizeMode(9, QHeaderView.Fixed)
    self.table.setColumnWidth(9, 160)

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
    conn = None
    try:
      conn = get_connection()
      cursor = conn.cursor()

      cursor.execute(
          "SELECT value FROM settings_options WHERE category = 'gender'"
      )
      rows = cursor.fetchall()
      genders = [
          list(row.values())[0] if isinstance(row, dict) else row[0]
          for row in rows
      ]
      if genders:
        self.combo_filter_gender.addItems(genders)
      else:
        self.combo_filter_gender.addItems(["ذكر", "أنثى", "بانتظار DNA"])

      cursor.execute(
          "SELECT value FROM settings_options WHERE category = 'chick_status'"
      )
      rows = cursor.fetchall()
      statuses = [
          list(row.values())[0] if isinstance(row, dict) else row[0]
          for row in rows
      ]
      if statuses:
        self.combo_filter_status.addItems(statuses)
      else:
        self.combo_filter_status.addItems(
            ["محتفظ به", "للبيع", "تم البيع", "نافق"]
        )

      cursor.execute(
          "SELECT value FROM settings_options WHERE category = 'color'"
      )
      rows = cursor.fetchall()
      colors = [
          list(row.values())[0] if isinstance(row, dict) else row[0]
          for row in rows
      ]
      if colors:
        self.combo_filter_color.addItems(colors)
    finally:
      if conn:
        conn.close()

  def calculate_age(self, hatch_month_str):
    if not hatch_month_str:
      return "غير محدد"

    try:
      clean_str = str(hatch_month_str).replace("/", "-").strip()
      parts = clean_str.split("-")

      if len(parts) == 2:
        if len(parts[0]) == 4:
          year, month = int(parts[0]), int(parts[1])
        else:
          month, year = int(parts[0]), int(parts[1])

        now = datetime.now()
        diff_months = (now.year - year) * 12 + (now.month - month)

        if diff_months < 0:
          return "مستقبلي"
        elif diff_months == 0:
          return "أقل من شهر"
        elif diff_months == 1:
          return "شهر واحد"
        elif diff_months == 2:
          return "شهرين"
        elif 3 <= diff_months <= 10:
          return f"{diff_months} أشهر"
        elif diff_months < 12:
          return f"{diff_months} شهر"
        else:
          years = diff_months // 12
          rem_months = diff_months % 12

          year_str = (
              "سنة"
              if years == 1
              else ("سنتين" if years == 2 else f"{years} سنوات")
          )
          if rem_months == 0:
            return year_str
          return f"{year_str} و{rem_months} شهر"
    except Exception:
      pass

    return "غير محدد"

  def load_chicks(self):
    search_text = (
        self.txt_search.text().strip() if hasattr(self, "txt_search") else ""
    )
    selected_gender = (
        self.combo_filter_gender.currentText()
        if hasattr(self, "combo_filter_gender")
        else "جميع الأجناس"
    )
    selected_status = (
        self.combo_filter_status.currentText()
        if hasattr(self, "combo_filter_status")
        else "جميع الحالات"
    )
    selected_color = (
        self.combo_filter_color.currentText()
        if hasattr(self, "combo_filter_color")
        else "جميع الألوان"
    )

    conn = None
    try:
      conn = get_connection()
      cursor = conn.cursor()

      query = (
          "SELECT ring_number, pair_number, hatch_month, color, mutations,"
          " gender, status, notes FROM chicks WHERE 1=1"
      )
      params = []

      if search_text:
        query += " AND (ring_number LIKE %s OR pair_number LIKE %s)"
        params.extend([f"%{search_text}%", f"%{search_text}%"])

      if selected_gender != "جميع الأجناس":
        query += " AND gender = %s"
        params.append(selected_gender)

      if selected_status != "جميع الحالات":
        query += " AND status = %s"
        params.append(selected_status)

      if selected_color != "جميع الألوان":
        query += " AND color = %s"
        params.append(selected_color)

      query += " ORDER BY id DESC"

      cursor.execute(query, params)
      rows = cursor.fetchall()
    finally:
      if conn:
        conn.close()

    self.table.setRowCount(0)
    for row_idx, row in enumerate(rows):
      self.table.insertRow(row_idx)

      age_text = self.calculate_age(row["hatch_month"])

      self.table.setItem(
          row_idx, 0, QTableWidgetItem(str(row["ring_number"]))
      )
      self.table.setItem(
          row_idx, 1, QTableWidgetItem(str(row["pair_number"] or "بدون"))
      )
      self.table.setItem(
          row_idx, 2, QTableWidgetItem(str(row["hatch_month"] or ""))
      )
      self.table.setItem(row_idx, 3, QTableWidgetItem(age_text))
      self.table.setItem(
          row_idx, 4, QTableWidgetItem(str(row["color"] or ""))
      )
      self.table.setItem(
          row_idx, 5, QTableWidgetItem(str(row["mutations"] or ""))
      )
      self.table.setItem(
          row_idx, 6, QTableWidgetItem(str(row["gender"] or ""))
      )
      self.table.setItem(
          row_idx, 7, QTableWidgetItem(str(row["status"] or ""))
      )
      self.table.setItem(
          row_idx, 8, QTableWidgetItem(str(row["notes"] or ""))
      )

      for col in range(9):
        item = self.table.item(row_idx, col)
        if item:
          item.setTextAlignment(Qt.AlignCenter)

      btn_widget = QWidget()
      btn_layout = QHBoxLayout(btn_widget)
      btn_layout.setContentsMargins(4, 2, 4, 2)
      btn_layout.setSpacing(6)
      btn_layout.setAlignment(Qt.AlignCenter)

      btn_edit = QPushButton("تعديل")
      btn_delete = QPushButton("حذف")

      btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #3182CE;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 50px;
                }
                QPushButton:hover { background-color: #2B6CB0; }
            """)
      btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #E53E3E;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 50px;
                }
                QPushButton:hover { background-color: #C53030; }
            """)

      chick_data = dict(row)
      btn_edit.clicked.connect(
          lambda checked, data=chick_data: self.edit_chick(data)
      )
      btn_delete.clicked.connect(
          lambda checked, r_num=row["ring_number"]: self.delete_chick(r_num)
      )

      btn_layout.addWidget(btn_edit)
      btn_layout.addWidget(btn_delete)
      self.table.setCellWidget(row_idx, 9, btn_widget)

  def add_chick(self):
    dialog = AddEditChickDialog(self)
    if dialog.exec() == QDialog.Accepted:
      data = dialog.get_data()
      if not data["ring_number"] or not data["hatch_month"]:
        QMessageBox.warning(
            self, "خطأ", "يجب إدخال رقم الحجل وشهر الفقس!"
        )
        return

      conn = None
      try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. إدخال الفرخ في جدول الفروخ
        cursor.execute(
            """
                    INSERT INTO chicks (ring_number, pair_number, hatch_month, color, mutations, gender, status, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
            (
                data["ring_number"],
                data["pair_number"],
                data["hatch_month"],
                data["color"],
                data["mutations"],
                data["gender"],
                data["status"],
                data["notes"],
            ),
        )

        # 2. المزامنة التلقائية مع قائمة جميع الطيور
        source_text = (
            f"إنتاج الزوج {data['pair_number']}"
            if data["pair_number"]
            else "إنتاج فرخ"
        )
        cursor.execute(
            """
                    INSERT INTO individual_birds (ring_number, gender, color, mutations, status, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT(ring_number) DO UPDATE SET
                        gender = EXCLUDED.gender,
                        color = EXCLUDED.color,
                        mutations = EXCLUDED.mutations,
                        status = EXCLUDED.status,
                        source = EXCLUDED.source
                """,
            (
                data["ring_number"],
                data["gender"],
                data["color"],
                data["mutations"],
                data["status"],
                source_text,
            ),
        )

        conn.commit()
        self.load_chicks()
      except Exception as err:
        if "unique" in str(err).lower() or "duplicate" in str(err).lower():
          QMessageBox.critical(self, "خطأ", "رقم الحجل موجود مسبقاً!")
        else:
          QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ:\n{err}")
      finally:
        if conn:
          conn.close()

  def edit_chick(self, chick_data):
    dialog = AddEditChickDialog(self, chick_data)
    if dialog.exec() == QDialog.Accepted:
      data = dialog.get_data()
      if not data["ring_number"] or not data["hatch_month"]:
        QMessageBox.warning(
            self, "خطأ", "يجب إدخال رقم الحجل وشهر الفقس!"
        )
        return

      old_ring = str(chick_data.get("ring_number") or "").strip()
      new_ring = data["ring_number"]

      conn = None
      try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. تحديث الفرخ في جدول الفروخ
        cursor.execute(
            """
                    UPDATE chicks 
                    SET ring_number=%s, pair_number=%s, hatch_month=%s, color=%s, mutations=%s, gender=%s, status=%s, notes=%s
                    WHERE ring_number=%s
                """,
            (
                new_ring,
                data["pair_number"],
                data["hatch_month"],
                data["color"],
                data["mutations"],
                data["gender"],
                data["status"],
                data["notes"],
                old_ring,
            ),
        )

        # 2. المزامنة الذكية مع جدول جميع الطيور وتحديث رقم الحجل القديم
        source_text = (
            f"إنتاج الزوج {data['pair_number']}"
            if data["pair_number"]
            else "إنتاج فرخ"
        )
        if old_ring and old_ring != new_ring:
          cursor.execute(
              "SELECT id FROM individual_birds WHERE ring_number = %s",
              (old_ring,),
          )
          if cursor.fetchone():
            cursor.execute(
                """
                            UPDATE individual_birds 
                            SET ring_number = %s, gender = %s, color = %s, mutations = %s, status = %s, source = %s
                            WHERE ring_number = %s
                        """,
                (
                    new_ring,
                    data["gender"],
                    data["color"],
                    data["mutations"],
                    data["status"],
                    source_text,
                    old_ring,
                ),
            )
          else:
            cursor.execute(
                """
                            INSERT INTO individual_birds (ring_number, gender, color, mutations, status, source)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT(ring_number) DO UPDATE SET
                                gender = EXCLUDED.gender,
                                color = EXCLUDED.color,
                                mutations = EXCLUDED.mutations,
                                status = EXCLUDED.status,
                                source = EXCLUDED.source
                        """,
                (
                    new_ring,
                    data["gender"],
                    data["color"],
                    data["mutations"],
                    data["status"],
                    source_text,
                ),
            )
        else:
          cursor.execute(
              """
                        INSERT INTO individual_birds (ring_number, gender, color, mutations, status, source)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT(ring_number) DO UPDATE SET
                            gender = EXCLUDED.gender,
                            color = EXCLUDED.color,
                            mutations = EXCLUDED.mutations,
                            status = EXCLUDED.status,
                            source = EXCLUDED.source
                    """,
              (
                  new_ring,
                  data["gender"],
                  data["color"],
                  data["mutations"],
                  data["status"],
                  source_text,
              ),
          )

        conn.commit()
        self.load_chicks()
      except Exception as err:
        if "unique" in str(err).lower() or "duplicate" in str(err).lower():
          QMessageBox.critical(
              self, "خطأ", f"رقم الحجل ({new_ring}) مسجل لطائر آخر!"
          )
        else:
          QMessageBox.critical(
              self, "خطأ", f"حدث خطأ أثناء التحديث:\n{err}"
          )
      finally:
        if conn:
          conn.close()

  def delete_chick(self, ring_number):
    reply = QMessageBox.question(
        self,
        "تأكيد الحذف",
        f"هل أنت متأكد من حذف الفرخ صاحب الحجل {ring_number}؟",
        QMessageBox.Yes | QMessageBox.No,
    )
    if reply == QMessageBox.Yes:
      conn = None
      try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chicks WHERE ring_number=%s", (ring_number,)
        )
        conn.commit()
        self.load_chicks()
      finally:
        if conn:
          conn.close()