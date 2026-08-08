import sqlite3
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QGraphicsDropShadowEffect,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from app.database import get_connection

class StatBox(QFrame):
    def __init__(self, title, value, subtext="", color_hex="#3182CE"):
        super().__init__()
        self.setObjectName("StatBox")
        self.setStyleSheet(f"""
            QFrame#StatBox {{
                background-color: #2D3748;
                border-radius: 10px;
                border-top: 4px solid {color_hex};
                padding: 15px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #A0AEC0; font-size: 13px; font-weight: bold;")
        
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: bold;")

        self.sub_lbl = QLabel(subtext)
        self.sub_lbl.setStyleSheet("color: #718096; font-size: 11px;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.val_lbl)
        layout.addWidget(self.sub_lbl)

    def update_value(self, value, subtext=""):
        self.val_lbl.setText(str(value))
        if subtext:
            self.sub_lbl.setText(subtext)


class StatisticsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header = QLabel("الإحصائيات وتقارير الكفاءة")
        header.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: bold;")
        layout.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(15)

        self.box_pairs = StatBox("إجمالي الأزواج", "0", "جميع الأزواج المسجلة", "#3182CE")
        self.box_chicks = StatBox("إجمالي الفروخ", "0", "جميع الفروخ المسجلة", "#38A169")
        self.box_kept = StatBox("المحتفظ بهم", "0", "فروخ في المزرعة", "#DD6B20")
        self.box_hatch_rate = StatBox("نسبة الفقس العامة", "0%", "معدل تفريخ البيض", "#E53E3E")
        self.box_sold_chicks = StatBox("الفروخ المباعة", "0", "تم بيعها", "#319795")
        self.box_best_pair = StatBox("أعلى زوج إنتاجاً", "-", "أعلى عدد فروخ", "#805AD5")

        grid.addWidget(self.box_pairs, 0, 0)
        grid.addWidget(self.box_chicks, 0, 1)
        grid.addWidget(self.box_kept, 0, 2)
        
        grid.addWidget(self.box_hatch_rate, 1, 0)
        grid.addWidget(self.box_sold_chicks, 1, 1)
        grid.addWidget(self.box_best_pair, 1, 2)

        layout.addLayout(grid)

        # جدول تقرير كفاءة الأزواج
        tbl_title = QLabel("تقرير كفاءة وأداء الأزواج التفصيلي")
        tbl_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(tbl_title)

        self.table_performance = QTableWidget()
        self.table_performance.setColumnCount(6)
        self.table_performance.setHorizontalHeaderLabels([
            "رقم الزوج", "عدد البطون", "إجمالي البيض", "إجمالي الفروخ", "نسبة الفقس", "حالة الزوج"
        ])
        
        self.table_performance.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_performance.setStyleSheet("""
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
        layout.addWidget(self.table_performance)

    def load_statistics(self):
        conn = get_connection()
        cursor = conn.cursor()

        # الإحصائيات العامة
        cursor.execute("SELECT COUNT(*) FROM pairs")
        pairs_cnt = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chicks")
        chicks_cnt = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chicks WHERE status = 'محتفظ به'")
        kept_cnt = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chicks WHERE status = 'تم البيع'")
        sold_chicks_cnt = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(eggs_count), 0), COALESCE(SUM(chicks_count), 0) FROM production")
        total_eggs, total_hatched = cursor.fetchone()
        
        hatch_rate_gen = round((total_hatched / total_eggs) * 100, 1) if total_eggs > 0 else 0

        # أكثر زوج إنتاجاً
        cursor.execute("""
            SELECT pair_number, SUM(chicks_count) as total_c 
            FROM production 
            GROUP BY pair_number 
            ORDER BY total_c DESC 
            LIMIT 1
        """)
        best_pair_row = cursor.fetchone()
        best_pair_str = f"زوج {best_pair_row[0]}" if best_pair_row else "لا يوجد"
        best_pair_sub = f"إنتاج: {best_pair_row[1]} فرخ" if best_pair_row else ""

        self.box_pairs.update_value(pairs_cnt)
        self.box_chicks.update_value(chicks_cnt)
        self.box_kept.update_value(kept_cnt)
        self.box_hatch_rate.update_value(f"{hatch_rate_gen}%", f"بيض: {total_eggs} | فروخ: {total_hatched}")
        self.box_sold_chicks.update_value(sold_chicks_cnt)
        self.box_best_pair.update_value(best_pair_str, best_pair_sub)

        # تحميل جدول تقرير كفاءة الأزواج
        query = """
            SELECT 
                p.pair_number,
                p.status,
                COUNT(pr.id) as clutch_count,
                COALESCE(SUM(pr.eggs_count), 0) as total_eggs,
                COALESCE(SUM(pr.chicks_count), 0) as total_chicks
            FROM pairs p
            LEFT JOIN production pr ON p.pair_number = pr.pair_number
            GROUP BY p.pair_number, p.status
            ORDER BY total_chicks DESC, total_eggs DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        self.table_performance.setRowCount(0)
        for row_idx, row in enumerate(rows):
            self.table_performance.insertRow(row_idx)

            p_num = str(row['pair_number'])
            c_cnt = str(row['clutch_count'])
            e_cnt = row['total_eggs']
            ch_cnt = row['total_chicks']
            p_status = str(row['status'] or '-')

            rate = round((ch_cnt / e_cnt) * 100, 1) if e_cnt > 0 else 0.0
            rate_str = f"{rate}%"

            self.table_performance.setItem(row_idx, 0, QTableWidgetItem(p_num))
            self.table_performance.setItem(row_idx, 1, QTableWidgetItem(c_cnt))
            self.table_performance.setItem(row_idx, 2, QTableWidgetItem(str(e_cnt)))
            self.table_performance.setItem(row_idx, 3, QTableWidgetItem(str(ch_cnt)))
            self.table_performance.setItem(row_idx, 4, QTableWidgetItem(rate_str))
            self.table_performance.setItem(row_idx, 5, QTableWidgetItem(p_status))

            for col in range(6):
                item = self.table_performance.item(row_idx, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)