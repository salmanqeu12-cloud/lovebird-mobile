from datetime import datetime
from app.database import get_connection
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
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


class AddTransactionDialog(QDialog):
  """نافذة إضافة معاملة مالية (مبيعات / مصروفات)"""

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setWindowTitle("تسجيل معاملة مالية جديدة")
    self.setMinimumWidth(400)
    self.setLayoutDirection(Qt.RightToLeft)
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout(self)
    layout.setSpacing(12)
    layout.setContentsMargins(20, 20, 20, 20)

    form = QFormLayout()
    form.setSpacing(10)

    self.combo_type = QComboBox()
    self.combo_type.addItems(["إيراد / مبيعات (Income)", "مصروفات (Expense)"])

    self.combo_category = QComboBox()
    self.combo_category.addItems([
        "بيع طير / فرخ",
        "بيع قفص / مستلزمات",
        "أعلاف وحبوب",
        "مكملات وفيتامينات وعلاج",
        "حجول وأدوات",
        "أخرى",
    ])

    self.spin_amount = QDoubleSpinBox()
    self.spin_amount.setRange(0.001, 100000.0)
    self.spin_amount.setDecimals(3)
    self.spin_amount.setSuffix(" د.ب")
    self.spin_amount.setValue(10.000)
    self.spin_amount.setAlignment(Qt.AlignCenter)

    self.date_trans = QDateEdit()
    self.date_trans.setCalendarPopup(True)
    self.date_trans.setDate(QDate.currentDate())
    self.date_trans.setDisplayFormat("yyyy-MM-dd")
    self.date_trans.setAlignment(Qt.AlignCenter)

    self.txt_desc = QLineEdit()
    self.txt_desc.setPlaceholderText("مثال: بيع فرخ حجل 2026-05 أو كيس مشكل")

    form.addRow("نوع المعاملة *:", self.combo_type)
    form.addRow("التصنيف:", self.combo_category)
    form.addRow("المبلغ (د.ب) *:", self.spin_amount)
    form.addRow("التاريخ:", self.date_trans)
    form.addRow("الوصف والتفاصيل:", self.txt_desc)

    layout.addLayout(form)

    btn_layout = QHBoxLayout()
    self.btn_save = QPushButton("حفظ المعاملة")
    self.btn_cancel = QPushButton("إلغاء")

    self.btn_save.setStyleSheet(
        "background-color: #38A169; color: white; padding: 8px 16px;"
        " border-radius: 4px; font-weight: bold;"
    )
    self.btn_cancel.setStyleSheet(
        "background-color: #E53E3E; color: white; padding: 8px 16px;"
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
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 2px;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #4A5568;
            }
        """)

  def get_data(self):
    trans_type = (
        "income"
        if self.combo_type.currentIndex() == 0
        else "expense"
    )
    return {
        "trans_type": trans_type,
        "category": self.combo_category.currentText(),
        "amount": self.spin_amount.value(),
        "trans_date": self.date_trans.date().toString("yyyy-MM-dd"),
        "description": self.txt_desc.text().strip(),
    }


class FinancePage(QWidget):
  """صفحة الحسابات والسجل المالي"""

  def __init__(self):
    super().__init__()
    self.setLayoutDirection(Qt.RightToLeft)
    self.ensure_table_exists()
    self.init_ui()
    self.load_transactions()

  def ensure_table_exists(self):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS finance_transactions (
                id SERIAL PRIMARY KEY,
                trans_type VARCHAR(20) NOT NULL,
                category VARCHAR(100),
                amount NUMERIC(10, 3) NOT NULL,
                trans_date DATE NOT NULL,
                description TEXT
            );
        """)
    conn.commit()
    conn.close()

  def init_ui(self):
    layout = QVBoxLayout(self)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    header_layout = QHBoxLayout()
    title = QLabel("💰 السجل المالي والمبيعات (بالدينار البحريني)")
    title.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: bold;")

    self.btn_add = QPushButton("+ تسجيل معاملة جديدة")
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
    self.btn_add.clicked.connect(self.add_transaction)

    header_layout.addWidget(title)
    header_layout.addStretch()
    header_layout.addWidget(self.btn_add)
    layout.addLayout(header_layout)

    summary_layout = QHBoxLayout()
    summary_layout.setSpacing(15)

    self.card_income = self.create_stat_card("إجمالي المبيعات / الإيراد", "0.000 د.ب", "#48BB78")
    self.card_expense = self.create_stat_card("إجمالي المصروفات", "0.000 د.ب", "#F56565")
    self.card_net = self.create_stat_card("صافي الأرباح", "0.000 د.ب", "#4299E1")

    summary_layout.addWidget(self.card_income)
    summary_layout.addWidget(self.card_expense)
    summary_layout.addWidget(self.card_net)
    layout.addLayout(summary_layout)

    self.table = QTableWidget()
    self.table.setColumnCount(6)
    self.table.setHorizontalHeaderLabels([
        "التاريخ",
        "النوع",
        "التصنيف",
        "المبلغ (د.ب)",
        "الوصف والملاحظات",
        "إجراءات",
    ])

    header = self.table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Stretch)
    header.setSectionResizeMode(5, QHeaderView.Fixed)
    self.table.setColumnWidth(5, 90)

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
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item { padding: 6px; }
        """)
    layout.addWidget(self.table)

  def create_stat_card(self, title, default_val, color_hex):
    card = QFrame()
    card.setStyleSheet(f"""
            QFrame {{
                background-color: #2D3748;
                border-radius: 8px;
                border-right: 6px solid {color_hex};
                padding: 12px 16px;
            }}
            QLabel {{ color: white; }}
        """)
    lay = QVBoxLayout(card)
    lay.setSpacing(4)

    t_lbl = QLabel(title)
    t_lbl.setStyleSheet("color: #A0AEC0; font-size: 12px; font-weight: bold;")
    v_lbl = QLabel(default_val)
    v_lbl.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: bold;")

    lay.addWidget(t_lbl)
    lay.addWidget(v_lbl)
    card.val_lbl = v_lbl
    return card

  def load_transactions(self):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
            SELECT id, trans_type, category, amount, trans_date, description 
            FROM finance_transactions 
            ORDER BY trans_date DESC, id DESC
        """)
    rows = cursor.fetchall()
    conn.close()

    total_income = 0.0
    total_expense = 0.0

    self.table.setRowCount(0)
    for r_idx, r in enumerate(rows):
      self.table.insertRow(r_idx)

      amt = float(r["amount"])
      is_income = r["trans_type"] == "income"
      if is_income:
        total_income += amt
        type_str = "إيراد / بيع 🟢"
      else:
        total_expense += amt
        type_str = "مصروف 🔴"

      self.table.setItem(r_idx, 0, QTableWidgetItem(str(r["trans_date"])))
      self.table.setItem(r_idx, 1, QTableWidgetItem(type_str))
      self.table.setItem(r_idx, 2, QTableWidgetItem(str(r["category"] or "-")))

      item_amt = QTableWidgetItem(f"{amt:.3f} د.ب")
      item_amt.setForeground(Qt.GlobalColor.green if is_income else Qt.GlobalColor.red)
      self.table.setItem(r_idx, 3, item_amt)

      self.table.setItem(r_idx, 4, QTableWidgetItem(str(r["description"] or "")))

      for col in range(5):
        it = self.table.item(r_idx, col)
        if it:
          it.setTextAlignment(Qt.AlignCenter)

      btn_del = QPushButton("حذف")
      btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #E53E3E;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #C53030; }
            """)
      btn_del.clicked.connect(lambda checked, t_id=r["id"]: self.delete_transaction(t_id))
      self.table.setCellWidget(r_idx, 5, btn_del)

    net_profit = total_income - total_expense
    self.card_income.val_lbl.setText(f"{total_income:.3f} د.ب")
    self.card_expense.val_lbl.setText(f"{total_expense:.3f} د.ب")
    self.card_net.val_lbl.setText(f"{net_profit:.3f} د.ب")
    self.card_net.val_lbl.setStyleSheet(
        f"color: {'#48BB78' if net_profit >= 0 else '#F56565'}; font-size: 22px; font-weight: bold;"
    )

  def add_transaction(self):
    dlg = AddTransactionDialog(self)
    if dlg.exec() == QDialog.Accepted:
      data = dlg.get_data()
      try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
                    INSERT INTO finance_transactions (trans_type, category, amount, trans_date, description)
                    VALUES (%s, %s, %s, %s, %s)
                """,
            (
                data["trans_type"],
                data["category"],
                data["amount"],
                data["trans_date"],
                data["description"],
            ),
        )
        conn.commit()
        conn.close()
        self.load_transactions()
      except Exception as e:
        QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {e}")

  def delete_transaction(self, t_id):
    reply = QMessageBox.question(
        self,
        "تأكيد الحذف",
        "هل أنت متأكد من حذف هذه المعاملة؟",
        QMessageBox.Yes | QMessageBox.No,
    )
    if reply == QMessageBox.Yes:
      conn = get_connection()
      cursor = conn.cursor()
      cursor.execute("DELETE FROM finance_transactions WHERE id = %s", (t_id,))
      conn.commit()
      conn.close()
      self.load_transactions()