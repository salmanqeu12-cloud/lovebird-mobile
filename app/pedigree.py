import sqlite3
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QGridLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor
from app.database import get_connection

class BirdNodeWidget(QFrame):
    """مكون يعرض بطاقة طير واحدة داخل شجرة النسب"""
    def __init__(self, title, ring="", color="", photo_path=""):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #2D3748;
                border: 2px solid #4A5568;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(5, 5, 5, 5)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #3182CE; font-weight: bold; font-size: 11px;")
        lbl_title.setAlignment(Qt.AlignCenter)

        self.lbl_photo = QLabel()
        self.lbl_photo.setFixedSize(50, 50)
        self.lbl_photo.setStyleSheet("background-color: #1A202C; border-radius: 4px;")
        self.lbl_photo.setAlignment(Qt.AlignCenter)

        self.lbl_ring = QLabel(f"الحجل: {ring if ring else '-'}")
        self.lbl_ring.setStyleSheet("color: #FFFFFF; font-size: 11px; font-weight: bold;")
        self.lbl_ring.setAlignment(Qt.AlignCenter)

        self.lbl_color = QLabel(f"اللون: {color if color else '-'}")
        self.lbl_color.setStyleSheet("color: #A0AEC0; font-size: 10px;")
        self.lbl_color.setAlignment(Qt.AlignCenter)

        layout.addWidget(lbl_title)
        layout.addWidget(self.lbl_photo, alignment=Qt.AlignCenter)
        layout.addWidget(self.lbl_ring)
        layout.addWidget(self.lbl_color)

        self.update_data(ring, color, photo_path)

    def update_data(self, ring, color, photo_path):
        self.lbl_ring.setText(f"الحجل: {ring if ring else '-'}")
        self.lbl_color.setText(f"اللون: {color if color else '-'}")
        
        if photo_path and os.path.exists(photo_path):
            pix = QPixmap(photo_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_photo.setPixmap(pix)
        else:
            self.lbl_photo.setText("لا صورة")
            self.lbl_photo.setStyleSheet("color: #718096; font-size: 9px; background-color: #1A202C;")


class PedigreePage(QWidget):
    """صفحة شجرة النسب لعرض السلالة (الفرخ - الأبوين - الأجداد)"""
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.init_ui()
        self.load_chicks_list()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # الشريط العلوي لاختيار الفرخ
        header_layout = QHBoxLayout()
        title = QLabel("شجرة النسب (Pedigree)")
        title.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;")

        self.combo_chicks = QComboBox()
        self.combo_chicks.setMinimumWidth(250)
        self.combo_chicks.setStyleSheet("""
            QComboBox {
                background-color: #1A202C;
                color: white;
                border: 1px solid #4A5568;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
        """)
        self.combo_chicks.currentIndexChanged.connect(self.display_tree)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("اختر الفرخ:"))
        header_layout.addWidget(self.combo_chicks)
        layout.addLayout(header_layout)

        # شبكة عرض الشجرة (3 أجيال)
        tree_grid = QGridLayout()
        tree_grid.setSpacing(10)

        # الجيل 1: الفرخ
        self.node_target = BirdNodeWidget("الفرخ المستهدف")
        tree_grid.addWidget(self.node_target, 0, 1, 1, 2)

        # الجيل 2: الأب والأم
        self.node_father = BirdNodeWidget("الأب (الذكر)")
        self.node_mother = BirdNodeWidget("الأم (الأنثى)")
        tree_grid.addWidget(self.node_father, 1, 0, 1, 2)
        tree_grid.addWidget(self.node_mother, 1, 2, 1, 2)

        # الجيل 3: الأجداد (أب وأم الأب / أب وأم الأم)
        self.node_pat_gfather = BirdNodeWidget("جد (أب الأب)")
        self.node_pat_gmother = BirdNodeWidget("جدة (أم الأب)")
        self.node_mat_gfather = BirdNodeWidget("جد (أب الأم)")
        self.node_mat_gmother = BirdNodeWidget("جدة (أم الأم)")

        tree_grid.addWidget(self.node_pat_gfather, 2, 0)
        tree_grid.addWidget(self.node_pat_gmother, 2, 1)
        tree_grid.addWidget(self.node_mat_gfather, 2, 2)
        tree_grid.addWidget(self.node_mat_gmother, 2, 3)

        layout.addLayout(tree_grid)
        layout.addStretch()

    def load_chicks_list(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ring_number FROM chicks ORDER BY id DESC")
        rings = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.combo_chicks.clear()
        self.combo_chicks.addItems(rings)

    def fetch_bird_details(self, ring_number, conn):
        """البحث عن تفاصيل الطير برقم الحجل عبر جميع الجداول"""
        if not ring_number:
            return None

        cursor = conn.cursor()

        # 1. البحث في جدول الفروخ
        cursor.execute("SELECT ring_number, color, NULL as image_path, father_ring, mother_ring, pair_number FROM chicks WHERE ring_number = ?", (ring_number,))
        b = cursor.fetchone()
        if b: return dict(b)

        # 2. البحث في جدول جميع الطيور
        cursor.execute("SELECT ring_number, color, image_path, father_ring, mother_ring, NULL as pair_number FROM individual_birds WHERE ring_number = ?", (ring_number,))
        b = cursor.fetchone()
        if b: return dict(b)

        # 3. البحث كذكر في جدول الأزواج
        cursor.execute("SELECT male_ring as ring_number, male_color as color, image_path, NULL as father_ring, NULL as mother_ring, NULL as pair_number FROM pairs WHERE male_ring = ?", (ring_number,))
        b = cursor.fetchone()
        if b: return dict(b)

        # 4. البحث كأنثى في جدول الأزواج
        cursor.execute("SELECT female_ring as ring_number, female_color as color, NULL as image_path, NULL as father_ring, NULL as mother_ring, NULL as pair_number FROM pairs WHERE female_ring = ?", (ring_number,))
        b = cursor.fetchone()
        if b: return dict(b)

        return {"ring_number": ring_number, "color": "", "image_path": "", "father_ring": None, "mother_ring": None, "pair_number": None}

    def get_parents_rings(self, bird_info, conn):
        """استخراج رقم حجل الأب والأم المباشرين مع توفير آلية احتياطية برقم الزوج"""
        if not bird_info:
            return None, None

        father_ring = bird_info.get('father_ring')
        mother_ring = bird_info.get('mother_ring')

        # استخدام رقم الزوج كخيار احتياطي إذا لم يُحدد الأب والأم مباشرة
        if not father_ring and not mother_ring and bird_info.get('pair_number'):
            cursor = conn.cursor()
            cursor.execute("SELECT male_ring, female_ring FROM pairs WHERE pair_number = ?", (bird_info['pair_number'],))
            pair = cursor.fetchone()
            if pair:
                father_ring = pair['male_ring']
                mother_ring = pair['female_ring']

        return father_ring, mother_ring

    def display_tree(self):
        target_ring = self.combo_chicks.currentText()
        if not target_ring:
            self.reset_ancestors()
            return

        conn = get_connection()

        # الجيل 1: الفرخ المستهدف
        target_bird = self.fetch_bird_details(target_ring, conn)
        if target_bird:
            self.node_target.update_data(target_bird['ring_number'], target_bird['color'], target_bird.get('image_path'))

            # الجيل 2: الأب والأم
            f_ring, m_ring = self.get_parents_rings(target_bird, conn)

            father_bird = self.fetch_bird_details(f_ring, conn) if f_ring else None
            mother_bird = self.fetch_bird_details(m_ring, conn) if m_ring else None

            if father_bird:
                self.node_father.update_data(father_bird['ring_number'], father_bird['color'], father_bird.get('image_path'))
            else:
                self.node_father.update_data("", "", "")

            if mother_bird:
                self.node_mother.update_data(mother_bird['ring_number'], mother_bird['color'], mother_bird.get('image_path'))
            else:
                self.node_mother.update_data("", "", "")

            # الجيل 3: أجداد الأب
            pat_gfather_ring, pat_gmother_ring = self.get_parents_rings(father_bird, conn) if father_bird else (None, None)
            pat_gf = self.fetch_bird_details(pat_gfather_ring, conn) if pat_gfather_ring else None
            pat_gm = self.fetch_bird_details(pat_gmother_ring, conn) if pat_gmother_ring else None

            if pat_gf: self.node_pat_gfather.update_data(pat_gf['ring_number'], pat_gf['color'], pat_gf.get('image_path'))
            else: self.node_pat_gfather.update_data("", "", "")

            if pat_gm: self.node_pat_gmother.update_data(pat_gm['ring_number'], pat_gm['color'], pat_gm.get('image_path'))
            else: self.node_pat_gmother.update_data("", "", "")

            # الجيل 3: أجداد الأم
            mat_gfather_ring, mat_gmother_ring = self.get_parents_rings(mother_bird, conn) if mother_bird else (None, None)
            mat_gf = self.fetch_bird_details(mat_gfather_ring, conn) if mat_gfather_ring else None
            mat_gm = self.fetch_bird_details(mat_gmother_ring, conn) if mat_gmother_ring else None

            if mat_gf: self.node_mat_gfather.update_data(mat_gf['ring_number'], mat_gf['color'], mat_gf.get('image_path'))
            else: self.node_mat_gfather.update_data("", "", "")

            if mat_gm: self.node_mat_gmother.update_data(mat_gm['ring_number'], mat_gm['color'], mat_gm.get('image_path'))
            else: self.node_mat_gmother.update_data("", "", "")

        else:
            self.reset_ancestors()

        conn.close()

    def reset_ancestors(self):
        self.node_target.update_data("", "", "")
        self.node_father.update_data("", "", "")
        self.node_mother.update_data("", "", "")
        self.node_pat_gfather.update_data("", "", "")
        self.node_pat_gmother.update_data("", "", "")
        self.node_mat_gfather.update_data("", "", "")
        self.node_mat_gmother.update_data("", "", "")