from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QFrame, QGridLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from app.database import get_connection

class StatCard(QFrame):
    def __init__(self, title, value, color_hex):
        super().__init__()
        self.setObjectName("StatCard")
        self.setStyleSheet(f"""
            QFrame#StatCard {{
                background-color: #2D3748;
                border-radius: 12px;
                border-right: 6px solid {color_hex};
                padding: 15px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #A0AEC0; font-size: 14px; font-weight: bold;")
        
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: bold;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header = QLabel("الرئيسية - نظرة عامة وإحصائيات الإنتاج")
        header.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: bold;")
        main_layout.addWidget(header)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # البطاقات الإحصائية الست
        self.card_pairs = StatCard("عدد الأزواج", 0, "#3182CE")
        self.card_chicks = StatCard("إجمالي الفروخ", 0, "#38A169")
        self.card_kept = StatCard("المحتفظ بهم", 0, "#DD6B20")
        self.card_month_prod = StatCard("فروخ هذا الشهر", 0, "#805AD5")
        self.card_hatch_rate = StatCard("نسبة الفقس الإجمالية", "0%", "#E53E3E")
        self.card_for_sale = StatCard("متاح للبيع", 0, "#D69E2E")

        grid_layout.addWidget(self.card_pairs, 0, 0)
        grid_layout.addWidget(self.card_chicks, 0, 1)
        grid_layout.addWidget(self.card_month_prod, 0, 2)
        grid_layout.addWidget(self.card_kept, 1, 0)
        grid_layout.addWidget(self.card_for_sale, 1, 1)
        grid_layout.addWidget(self.card_hatch_rate, 1, 2)

        main_layout.addLayout(grid_layout)
        main_layout.addStretch()

    def load_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        # 1. عدد الأزواج
        cursor.execute("SELECT COUNT(*) FROM pairs")
        pairs_count = cursor.fetchone()[0]

        # 2. إجمالي الفروخ
        cursor.execute("SELECT COUNT(*) FROM chicks")
        chicks_count = cursor.fetchone()[0]

        # 3. الفروخ المحتفظ بها
        cursor.execute("SELECT COUNT(*) FROM chicks WHERE status = 'محتفظ به'")
        kept_count = cursor.fetchone()[0]

        # 4. فروخ الشهر الحالي (يدعم صيغ مثل 2026-08 و 8-2026)
        now = datetime.now()
        current_ym = now.strftime("%Y-%m")
        current_my = f"{now.month}-{now.year}"
        current_my_padded = f"{now.month:02d}-{now.year}"

        cursor.execute("""
            SELECT COUNT(*) FROM chicks 
            WHERE hatch_month = ? OR hatch_month = ? OR hatch_month = ?
        """, (current_ym, current_my, current_my_padded))
        month_prod_count = cursor.fetchone()[0]

        # 5. حساب نسبة الفقس الإجمالية (إجمالي الفروخ ÷ إجمالي البيض)
        cursor.execute("SELECT COALESCE(SUM(eggs_count), 0), COALESCE(SUM(chicks_count), 0) FROM production")
        total_eggs, total_hatched_chicks = cursor.fetchone()

        if total_eggs > 0:
            hatch_rate = round((total_hatched_chicks / total_eggs) * 100, 1)
            hatch_rate_str = f"{hatch_rate}%"
        else:
            hatch_rate_str = "0%"

        # 6. المتاح للبيع (من جدول الفروخ وجدول جميع الطيور)
        cursor.execute("SELECT COUNT(*) FROM chicks WHERE status = 'للبيع'")
        chicks_for_sale = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM individual_birds WHERE status = 'للبيع'")
        birds_for_sale = cursor.fetchone()[0]

        total_for_sale = chicks_for_sale + birds_for_sale

        conn.close()

        # تحديث قيم البطاقات
        self.card_pairs.set_value(pairs_count)
        self.card_chicks.set_value(chicks_count)
        self.card_kept.set_value(kept_count)
        self.card_month_prod.set_value(month_prod_count)
        self.card_hatch_rate.set_value(hatch_rate_str)
        self.card_for_sale.set_value(total_for_sale)