# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from itertools import product

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class Parent:
  base: str
  dark: int
  violet: int
  opaline: bool
  ino: bool
  cinnamon: bool
  pallid: bool
  orange_face: bool
  split_blue: bool
  split_aqua: bool
  split_turquoise: bool
  split_orange_face: bool
  split_opaline: bool
  split_ino: bool
  split_cinnamon: bool
  split_pallid: bool
  dominant_pied: int
  recessive_pied: int
  split_recessive_pied: bool


@dataclass(frozen=True)
class Result:
  sex: str
  base: str
  dark: int
  violet: int
  opaline: bool
  ino: bool
  cinnamon: bool
  pallid: bool
  orange_face: bool
  dominant_pied: bool
  recessive_pied: bool
  splits: tuple[str, ...]


class GeneticsCalculatorPage(QWidget):
  """حاسبة وراثة الروز - Green/Blue/Aqua/Turquoise + Dark/Violet +

  Opaline/Ino/Cinnamon/Pallid + Orange Face + Pied.
  """

  def __init__(self):
    super().__init__()
    self.setLayoutDirection(Qt.RightToLeft)
    self.init_ui()

  # ---------------- UI ----------------

  def init_ui(self):
    main = QVBoxLayout(self)
    main.setContentsMargins(20, 20, 20, 20)
    main.setSpacing(12)

    title = QLabel("🧬 حاسبة الوراثة والطفرات لطيور الروز")
    title.setStyleSheet("color:#FFF;font-size:23px;font-weight:bold;")
    main.addWidget(title)

    sub = QLabel(
        "اختر اللون الظاهر والطفرات والـ Split لكل أب، ثم احسب التركيبة"
        " الكاملة للفروخ."
    )
    sub.setStyleSheet("color:#A0AEC0;font-size:13px;")
    main.addWidget(sub)

    parents = QHBoxLayout()
    parents.setSpacing(15)
    self.male_card = self.create_parent_card("الذكر (1.0 ♂)", True)
    self.female_card = self.create_parent_card("الأنثى (0.1 ♀)", False)
    parents.addWidget(self.male_card)
    parents.addWidget(self.female_card)
    main.addLayout(parents)

    buttons = QHBoxLayout()
    self.btn_calc = QPushButton("⚡ حساب النتائج")
    self.btn_calc.setStyleSheet("""
            QPushButton{background:#38A169;color:white;font-weight:bold;
            font-size:15px;padding:12px;border-radius:7px;}
            QPushButton:hover{background:#2F855A;}
        """)
    self.btn_calc.clicked.connect(self.calculate_genetics)

    self.btn_clear = QPushButton("🗑️ مسح")
    self.btn_clear.setStyleSheet("""
            QPushButton{background:#4A5568;color:white;font-weight:bold;
            padding:12px 25px;border-radius:7px;}
            QPushButton:hover{background:#2D3748;}
        """)
    self.btn_clear.clicked.connect(self.clear_results)
    buttons.addWidget(self.btn_calc, 4)
    buttons.addWidget(self.btn_clear, 1)
    main.addLayout(buttons)

    self.results_frame = QFrame()
    self.results_frame.setStyleSheet(
        "QFrame{background:#2D3748;border-radius:9px;}"
    )
    self.results_layout = QVBoxLayout(self.results_frame)
    self.results_layout.setContentsMargins(16, 16, 16, 16)
    self.results_layout.setSpacing(7)
    self.show_placeholder()

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(self.results_frame)
    scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
    main.addWidget(scroll, 1)

  def create_parent_card(self, title, is_male):
    card = QFrame()
    card.setStyleSheet("""
            QFrame{background:#2D3748;border:1px solid #4A5568;border-radius:9px;}
            QLabel{color:#E2E8F0;font-size:12px;}
            QComboBox{background:#1A202C;color:white;border:1px solid #4A5568;
            border-radius:5px;padding:6px;min-height:18px;}
            QCheckBox{color:#CBD5E0;font-size:12px;spacing:6px;}
        """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(6)

    accent = "#3182CE" if is_male else "#ED64A6"
    header = QLabel(title)
    header.setStyleSheet(
        f"color:{accent};font-size:17px;font-weight:bold;"
        f"padding-bottom:6px;border-bottom:2px solid {accent};"
    )
    layout.addWidget(header)

    layout.addWidget(QLabel("🎨 السلسلة الأساسية:"))
    base = QComboBox()
    base.addItems([
        "أخضر (Green)",
        "أزرق (Blue)",
        "أكوا (Aqua)",
        "توركواز (Turquoise)",
        "أكوا توركواز (AquaTurquoise)",
    ])
    layout.addWidget(base)

    layout.addWidget(QLabel("🌑 عامل التغميق:"))
    dark = QComboBox()
    dark.addItems(["بدون (0D)", "سينجل دارك (1D)", "دبل دارك (2D)"])
    layout.addWidget(dark)

    layout.addWidget(QLabel("🟣 عامل البنفسجي:"))
    violet = QComboBox()
    violet.addItems(["بدون", "سينجل فيوليت", "دبل فيوليت"])
    layout.addWidget(violet)

    layout.addWidget(QLabel("🧬 الطفرات المرتبطة بالجنس - ظاهرة:"))
    opaline = QCheckBox("أوبلاين (Opaline)")
    ino = QCheckBox("إينو (Ino)")
    cinnamon = QCheckBox("سينامون (Cinnamon)")
    pallid = QCheckBox("باليد (Pallid)")
    for cb in (opaline, ino, cinnamon, pallid):
      layout.addWidget(cb)

    layout.addWidget(QLabel("🧬 الطفرات الأخرى:"))

    orange = QComboBox()
    orange.addItems(
        ["بدون Orange Face", "Orange Face ظاهر", "Split Orange Face"]
    )
    layout.addWidget(QLabel("🟠 Orange Face:"))
    layout.addWidget(orange)

    dpied = QComboBox()
    dpied.addItems([
        "بدون Dominant Pied",
        "Single Factor Dominant Pied",
        "Double Factor Dominant Pied",
    ])
    layout.addWidget(QLabel("🟡 Dominant Pied:"))
    layout.addWidget(dpied)

    rpied = QComboBox()
    rpied.addItems([
        "بدون Recessive Pied",
        "Recessive Pied ظاهر",
        "Split Recessive Pied",
    ])
    layout.addWidget(QLabel("⚪ Recessive Pied:"))
    layout.addWidget(rpied)

    layout.addWidget(QLabel("🔹 الـ Split:"))
    sp_blue = QCheckBox("Split Blue")
    sp_aqua = QCheckBox("Split Aqua")
    sp_turq = QCheckBox("Split Turquoise")
    for cb in (sp_blue, sp_aqua, sp_turq):
      layout.addWidget(cb)

    splits = {"blue": sp_blue, "aqua": sp_aqua, "turquoise": sp_turq}

    if is_male:
      sp_op = QCheckBox("Split Opaline")
      sp_ino = QCheckBox("Split Ino")
      sp_cin = QCheckBox("Split Cinnamon")
      sp_pal = QCheckBox("Split Pallid")
      for cb in (sp_op, sp_ino, sp_cin, sp_pal):
        layout.addWidget(cb)
      splits.update({
          "opaline": sp_op,
          "ino": sp_ino,
          "cinnamon": sp_cin,
          "pallid": sp_pal,
      })

    card.base = base
    card.dark = dark
    card.violet = violet
    card.opaline = opaline
    card.ino = ino
    card.cinnamon = cinnamon
    card.pallid = pallid
    card.orange = orange
    card.dpied = dpied
    card.rpied = rpied
    card.splits = splits
    card.is_male = is_male
    return card

  def read_parent(self, card):
    base = ["green", "blue", "aqua", "turquoise", "aqua_turquoise"][
        card.base.currentIndex()
    ]

    oi = card.orange.currentIndex()
    pi = card.rpied.currentIndex()

    return Parent(
        base=base,
        dark=card.dark.currentIndex(),
        violet=card.violet.currentIndex(),
        opaline=card.opaline.isChecked(),
        ino=card.ino.isChecked(),
        cinnamon=card.cinnamon.isChecked(),
        pallid=card.pallid.isChecked(),
        orange_face=(oi == 1),
        split_blue=card.splits["blue"].isChecked(),
        split_aqua=card.splits["aqua"].isChecked(),
        split_turquoise=card.splits["turquoise"].isChecked(),
        split_orange_face=(oi == 2),
        split_opaline=(
            card.splits["opaline"].isChecked()
            if "opaline" in card.splits
            else False
        ),
        split_ino=(
            card.splits["ino"].isChecked() if "ino" in card.splits else False
        ),
        split_cinnamon=(
            card.splits["cinnamon"].isChecked()
            if "cinnamon" in card.splits
            else False
        ),
        split_pallid=(
            card.splits["pallid"].isChecked()
            if "pallid" in card.splits
            else False
        ),
        dominant_pied=card.dpied.currentIndex(),
        recessive_pied=(1 if pi == 1 else 0),
        split_recessive_pied=(pi == 2),
    )

  # ---------------- genetic helpers ----------------

  @staticmethod
  def recessive_gametes(visible, split):
    if visible:
      return {"m": Fraction(1)}
    if split:
      return {"N": Fraction(1, 2), "m": Fraction(1, 2)}
    return {"N": Fraction(1)}

  @staticmethod
  def two_allele_gametes(kind, split=False):
    if kind == "mut":
      return {"m": Fraction(1)}
    if split:
      return {"N": Fraction(1, 2), "m": Fraction(1, 2)}
    return {"N": Fraction(1)}

  @staticmethod
  def dark_gametes(parent):
    if parent.dark == 0:
      return {"d": Fraction(1)}
    if parent.dark == 1:
      return {"D": Fraction(1, 2), "d": Fraction(1, 2)}
    return {"D": Fraction(1)}

  @staticmethod
  def violet_gametes(parent):
    if parent.violet == 0:
      return {"v": Fraction(1)}
    if parent.violet == 1:
      return {"V": Fraction(1, 2), "v": Fraction(1, 2)}
    return {"V": Fraction(1)}

  @staticmethod
  def blue_gametes(parent):
    if parent.base == "blue":
      return {"b": Fraction(1)}
    if parent.split_blue:
      return {"B": Fraction(1, 2), "b": Fraction(1, 2)}
    return {"B": Fraction(1)}

  @staticmethod
  def sex_gametes_male(parent):
    loci = []
    for visible, split in (
        (parent.opaline, parent.split_opaline),
        (parent.ino, parent.split_ino),
        (parent.cinnamon, parent.split_cinnamon),
        (parent.pallid, parent.split_pallid),
    ):
      if visible:
        loci.append([(True, Fraction(1))])
      elif split:
        loci.append([(False, Fraction(1, 2)), (True, Fraction(1, 2))])
      else:
        loci.append([(False, Fraction(1))])

    out = defaultdict(Fraction)
    for choices in product(*loci):
      flags = tuple(x[0] for x in choices)
      p = Fraction(1)
      for x in choices:
        p *= x[1]
      out[flags] += p
    return dict(out)

  @staticmethod
  def sex_gamete_female(parent):
    return {
        (
            parent.opaline,
            parent.ino,
            parent.cinnamon,
            parent.pallid,
        ): Fraction(1)
    }

  @staticmethod
  def simple_autosomal_gametes(visible, split):
    if visible:
      return {"m": Fraction(1)}
    if split:
      return {"N": Fraction(1, 2), "m": Fraction(1, 2)}
    return {"N": Fraction(1)}

  @staticmethod
  def dominant_pied_gametes(parent):
    if parent.dominant_pied == 0:
      return {"n": Fraction(1)}
    if parent.dominant_pied == 1:
      return {"n": Fraction(1, 2), "p": Fraction(1, 2)}
    return {"p": Fraction(1)}

  def series_gametes(self, parent):
    if parent.base == "blue":
      return {"blue": Fraction(1)}
    if parent.base == "aqua":
      return {"aqua": Fraction(1)}
    if parent.base == "turquoise":
      return {"turquoise": Fraction(1)}
    if parent.base == "aqua_turquoise":
      return {"aqua": Fraction(1, 2), "turquoise": Fraction(1, 2)}

    out = {"green": Fraction(1)}
    if parent.split_blue:
      out = self.mix(out, {"green": Fraction(1, 2), "blue": Fraction(1, 2)})
    if parent.split_aqua:
      out = self.mix(out, {"green": Fraction(1, 2), "aqua": Fraction(1, 2)})
    if parent.split_turquoise:
      out = self.mix(
          out, {"green": Fraction(1, 2), "turquoise": Fraction(1, 2)}
      )
    return out

  @staticmethod
  def mix(a, b):
    out = defaultdict(Fraction)
    for ka, pa in a.items():
      for kb, pb in b.items():
        key = tuple(sorted((ka, kb)))
        out[key] += pa * pb
    return {(k[0] if len(k) == 1 else "+".join(k)): p for k, p in out.items()}

  @staticmethod
  def resolve_series(a, b):
    if a == b:
      return a
    pair = {a, b}
    if pair == {"green", "blue"}:
      return "blue"
    if pair == {"green", "aqua"}:
      return "aqua"
    if pair == {"green", "turquoise"}:
      return "turquoise"
    if pair == {"aqua", "turquoise"}:
      return "aqua_turquoise"
    if pair == {"blue", "aqua"}:
      return "blue"
    if pair == {"blue", "turquoise"}:
      return "blue"
    return "green"

  @staticmethod
  def splits_for_male(mz, fz):
    mo, mi, mc, mp = mz
    fo, fi, fc, fp = fz
    splits = []
    if mo != fo:
      splits.append("Split Opaline")
    if mi != fi:
      splits.append("Split Ino")
    if mc != fc:
      splits.append("Split Cinnamon")
    if mp != fp:
      splits.append("Split Pallid")
    return splits

  # ---------------- calculation ----------------

  def calculate_genetics(self):
    self.clear_results()

    male = self.read_parent(self.male_card)
    female = self.read_parent(self.female_card)

    outcomes = defaultdict(Fraction)

    ms = self.series_gametes(male)
    fs = self.series_gametes(female)
    md = self.dark_gametes(male)
    fd = self.dark_gametes(female)
    mv = self.violet_gametes(male)
    fv = self.violet_gametes(female)

    mo = self.simple_autosomal_gametes(
        male.orange_face, male.split_orange_face
    )
    fo = self.simple_autosomal_gametes(
        female.orange_face, female.split_orange_face
    )

    mp = self.dominant_pied_gametes(male)
    fp = self.dominant_pied_gametes(female)

    mrp = self.simple_autosomal_gametes(
        bool(male.recessive_pied), male.split_recessive_pied
    )
    frp = self.simple_autosomal_gametes(
        bool(female.recessive_pied), female.split_recessive_pied
    )

    mz = self.sex_gametes_male(male)
    fz = self.sex_gamete_female(female)

    for a, pa in ms.items():
      for b, pb in fs.items():
        base = self.resolve_series(a, b)

        for d1, pd1 in md.items():
          for d2, pd2 in fd.items():
            dark = int(d1 == "D") + int(d2 == "D")

            for v1, pv1 in mv.items():
              for v2, pv2 in fv.items():
                violet = int(v1 == "V") + int(v2 == "V")

                for o1, po1 in mo.items():
                  for o2, po2 in fo.items():
                    orange = o1 == "m" and o2 == "m"

                    for p1, pp1 in mp.items():
                      for p2, pp2 in fp.items():
                        dom_pied = p1 == "p" or p2 == "p"

                        for r1, pr1 in mrp.items():
                          for r2, pr2 in frp.items():
                            rec_pied = r1 == "m" and r2 == "m"

                            auto_p = (
                                pa
                                * pb
                                * pd1
                                * pd2
                                * pv1
                                * pv2
                                * po1
                                * po2
                                * pp1
                                * pp2
                                * pr1
                                * pr2
                            )

                            if not auto_p:
                              continue

                            # Male chicks
                            for z1, pz1 in mz.items():
                              for z2, pz2 in fz.items():
                                op = z1[0] and z2[0]
                                ino = z1[1] and z2[1]
                                cin = z1[2] and z2[2]
                                pallid = z1[3] and z2[3]

                                splits = tuple(
                                    sorted(self.splits_for_male(z1, z2))
                                )

                                p = (
                                    auto_p
                                    * pz1
                                    * pz2
                                    * Fraction(1, 2)
                                )

                                result = Result(
                                    "male",
                                    base,
                                    dark,
                                    violet,
                                    op,
                                    ino,
                                    cin,
                                    pallid,
                                    orange,
                                    dom_pied,
                                    rec_pied,
                                    splits,
                                )
                                outcomes[result] += p

                            # Female chicks
                            for z1, pz1 in mz.items():
                              op = z1[0]
                              ino = z1[1]
                              cin = z1[2]
                              pallid = z1[3]

                              p = auto_p * pz1 * Fraction(1, 2)

                              result = Result(
                                  "female",
                                  base,
                                  dark,
                                  violet,
                                  op,
                                  ino,
                                  cin,
                                  pallid,
                                  orange,
                                  dom_pied,
                                  rec_pied,
                                  (),
                              )
                              outcomes[result] += p

    self.display_results(outcomes)

  # ---------------- display ----------------

  def display_results(self, outcomes):
    while self.results_layout.count():
      item = self.results_layout.takeAt(0)
      widget = item.widget()
      if widget:
        widget.deleteLater()

    if not outcomes:
      self.add_result("لا توجد نتائج محسوبة.", "#FC8181")
      return

    total = sum(outcomes.values())
    items = [
        (r, float(p / total * 100)) for r, p in outcomes.items() if p > 0
    ]
    items.sort(key=lambda x: x[1], reverse=True)

    title = QLabel("📊 النتائج الوراثية المتوقعة")
    title.setStyleSheet(
        "color:#68D391;font-size:20px;font-weight:bold;"
    )
    self.results_layout.addWidget(title)

    info = QLabel(
        "كل سطر يمثل تركيبة كاملة متوقعة، وليس نسبة طفرة منفصلة."
    )
    info.setStyleSheet("color:#A0AEC0;font-size:12px;")
    self.results_layout.addWidget(info)

    males = [(r, p) for r, p in items if r.sex == "male"]
    femates = [(r, p) for r, p in items if r.sex == "female"]

    if males:
      self.add_section("🐦 الذكور (1.0 ♂)", "#3182CE")
      for result, percent in males:
        self.add_outcome(result, percent)

    if femates:
      self.add_section("🐦 الإناث (0.1 ♀)", "#ED64A6")
      for result, percent in femates:
        self.add_outcome(result, percent)

    warning = QLabel(
        "⚠️ النسب احتمالات وراثية وليست ضمانًا لنفس النسب في كل بطن. Red"
        " Face / Red Suffusion غير محسوب كطفرة مندلية مستقلة."
    )
    warning.setWordWrap(True)
    warning.setStyleSheet("""
            QLabel{color:#F6AD55;background:#3A2E1F;
            border-radius:6px;padding:10px;margin-top:8px;}
        """)
    self.results_layout.addWidget(warning)

  @staticmethod
  def format_result(result):
    names = {
        "green": "جرين (Green)",
        "blue": "بلو (Blue)",
        "aqua": "أكوا (Aqua)",
        "turquoise": "توركواز (Turquoise)",
        "aqua_turquoise": "أكوا توركواز",
    }

    text = names.get(result.base, result.base)

    if result.dark == 1:
      text += " + 1D"
    elif result.dark == 2:
      text += " + 2D"

    if result.violet == 1:
      text += " + SF Violet"
    elif result.violet == 2:
      text += " + DF Violet"

    if result.ino:
      if result.base == "blue":
        text += " + Albino"
      elif result.base == "green":
        text += " + Lutino"
      else:
        text += " + Ino"

    if result.opaline:
      text += " + Opaline"
    if result.cinnamon:
      text += " + Cinnamon"
    if result.pallid:
      text += " + Pallid"
    if result.orange_face:
      text += " + Orange Face"
    if result.dominant_pied:
      text += " + Dominant Pied"
    if result.recessive_pied:
      text += " + Recessive Pied"

    if result.splits:
      text += " / " + " / ".join(result.splits)

    return text

  def add_section(self, text, color):
    label = QLabel(text)
    label.setStyleSheet(
        f"color:{color};font-size:16px;font-weight:bold;"
        "padding-top:10px;padding-bottom:5px;"
    )
    self.results_layout.addWidget(label)

  def add_outcome(self, result, percent):
    frame = QFrame()
    frame.setStyleSheet("""
            QFrame{background:#1A202C;border:1px solid #4A5568;
            border-radius:7px;}
        """)
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(12, 9, 12, 9)

    label = QLabel(self.format_result(result))
    label.setWordWrap(True)
    label.setStyleSheet(
        "color:#E2E8F0;font-size:13px;font-weight:bold;"
    )

    pct = QLabel(f"{percent:.2f}%")
    pct.setStyleSheet(
        "color:#68D391;font-size:14px;font-weight:bold;"
    )

    layout.addWidget(label, 1)
    layout.addWidget(pct)
    self.results_layout.addWidget(frame)

  def add_result(self, text, color="#E2E8F0"):
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet(
        f"color:{color};font-size:14px;padding:10px;"
    )
    self.results_layout.addWidget(label)

  def clear_results(self):
    while self.results_layout.count():
      item = self.results_layout.takeAt(0)
      widget = item.widget()
      if widget:
        widget.deleteLater()
    self.show_placeholder()

  def show_placeholder(self):
    label = QLabel(
        "اختر صفات الذكر والأنثى ثم اضغط «⚡ حساب النتائج»."
    )
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(
        "color:#A0AEC0;font-size:14px;padding:20px;"
    )
    self.results_layout.addWidget(label)