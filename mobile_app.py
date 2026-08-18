from datetime import datetime, timedelta
import pandas as pd
from app.database import get_connection
from app.services import compress_and_upload_image
import streamlit as st

# إعدادات الصفحة للجوال
st.set_page_config(
    page_title="Lovebird Manager", page_icon="🦜", layout="centered"
)

# ضبط التنسيق للغة العربية ودعم شاشات الجوال بدون التأثير على عناصر القائمة الداخلية
st.markdown(
    """
    <style>
    .stDataFrame {
        direction: rtl;
    }
    .alert-card {
        background-color: #2D3748;
        border-right: 6px solid #F6E05E;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🦜 Lovebird Manager - الجوال")

# استخدام label_visibility="collapsed" لمنع تكسر كلمة "القائمة" عمودياً في الجوال
menu = st.sidebar.selectbox(
    "القائمة",
    [
        "جمـيع الطيـور",
        "الأزواج",
        "💰 السجل المالي والمبيعات",
        "🚨 تنبيهات الحضن والفقس",
        "سجل الإنتاج والبطون",
        "معرض الصور والشهادات 🖼️",
        "🧬 حاسبة الطفرات والوراثة",
        "الفروخ",
        "إضافة طير جديد",
    ],
    label_visibility="collapsed",
)

conn = get_connection()

if menu == "جمـيع الطيـور":
    st.header("📋 قائمة جميع الطيور والشهادات")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ring_number, gender, color, mutations, status, source, COALESCE(dna_path, image_path) as photo
        FROM individual_birds 
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows)
        df.columns = [
            "رقم الحجل",
            "الجنس",
            "اللون",
            "الطفرات",
            "الحالة",
            "المصدر",
            "الشهادة / الصورة",
        ]
        st.dataframe(
            df,
            column_config={
                "الشهادة / الصورة": st.column_config.ImageColumn(
                    "الشهادة", help="انقر لتكبير صورة الشهادة"
                )
            },
            width="stretch",
        )
    else:
        st.info("لا توجد طيور مسجلة حالياً.")

elif menu == "الأزواج":
    st.header("👩‍❤️‍👨 قائمة الأزواج")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pair_number, male_ring, female_ring, male_color, female_color, status, image_path 
        FROM pairs 
        ORDER BY 
            CASE 
                WHEN pair_number ~ '^[0-9]+$' THEN CAST(pair_number AS INTEGER)
                ELSE 999999 
            END ASC, 
            pair_number ASC
    """)
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows)
        df.columns = [
            "رقم الزوج",
            "حجل الذكر",
            "حجل الأنثى",
            "لون الذكر",
            "لون الأنثى",
            "الحالة",
            "الصورة",
        ]
        st.dataframe(
            df,
            column_config={
                "الصورة": st.column_config.ImageColumn(
                    "الصورة", help="صورة الزوج المرفوعة سحابياً"
                )
            },
            width="stretch",
        )
    else:
        st.info("لا توجد أزواج مسجلة.")

elif menu == "💰 السجل المالي والمبيعات":
    st.header("💰 الحسابات والمبيعات (د.ب)")

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

    cursor.execute(
        "SELECT id, trans_type, category, amount, trans_date, description FROM"
        " finance_transactions ORDER BY trans_date DESC, id DESC"
    )
    fin_rows = cursor.fetchall()

    income = sum(
        float(r["amount"]) for r in fin_rows if r["trans_type"] == "income"
    )
    expense = sum(
        float(r["amount"]) for r in fin_rows if r["trans_type"] == "expense"
    )
    net = income - expense

    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي المبيعات", f"{income:.3f} د.ب")
    col2.metric("إجمالي المصروفات", f"{expense:.3f} د.ب")
    col3.metric("صافي الأرباح", f"{net:.3f} د.ب")

    tab1, tab2 = st.tabs(["📋 سجل العمليات", "➕ تسجيل معاملة"])

    with tab1:
        if fin_rows:
            df_fin = pd.DataFrame(fin_rows)
            df_fin["نوع المعاملة"] = df_fin["trans_type"].apply(
                lambda x: "إيراد / بيع 🟢" if x == "income" else "مصروف 🔴"
            )
            df_fin["amount"] = df_fin["amount"].apply(lambda x: f"{float(x):.3f} د.ب")
            df_display = df_fin[[
                "trans_date",
                "نوع المعاملة",
                "category",
                "amount",
                "description",
            ]]
            df_display.columns = [
                "التاريخ",
                "النوع",
                "التصنيف",
                "المبلغ",
                "الوصف",
            ]
            st.dataframe(df_display, width="stretch")
        else:
            st.info("لا توجد معاملات مسجلة.")

    with tab2:
        with st.form("add_finance_form"):
            t_type = st.selectbox(
                "نوع العملية *", ["إيراد / مبيعات", "مصروفات"]
            )
            t_cat = st.selectbox("التصنيف", [
                "بيع طير / فرخ",
                "بيع قفص / مستلزمات",
                "أعلاف وحبوب",
                "مكملات وفيتامينات وعلاج",
                "حجول وأدوات",
                "أخرى",
            ])
            t_amount = st.number_input(
                "المبلغ بالدينار البحريني (د.ب) *",
                min_value=0.001,
                value=5.000,
                step=0.500,
                format="%.3f",
            )
            t_date = st.date_input("التاريخ", value=datetime.now())
            t_desc = st.text_input("الوصف والملاحظات")

            save_fin = st.form_submit_button("حفظ المعاملة")

            if save_fin:
                try:
                    trans_val = "income" if t_type == "إيراد / مبيعات" else "expense"
                    cursor.execute(
                        """
                            INSERT INTO finance_transactions (trans_type, category, amount, trans_date, description)
                            VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            trans_val,
                            t_cat,
                            t_amount,
                            t_date.strftime("%Y-%m-%d"),
                            t_desc.strip(),
                        ),
                    )
                    conn.commit()
                    st.success("تم حفظ المعاملة المالية بنجاح!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء الحفظ: {e}")

elif menu == "🚨 تنبيهات الحضن والفقس":
    st.header("🚨 تنبيهات ومواعيد الإنتاج الحالية")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pair_number, clutch_number, first_egg_date, eggs_count, chicks_count, notes
        FROM production 
        WHERE (first_egg_date IS NOT NULL AND first_egg_date != '') 
          AND (chicks_count IS NULL OR chicks_count = 0)
        ORDER BY first_egg_date DESC
    """)
    active_clutches = cursor.fetchall()

    today = datetime.now().date()
    if active_clutches:
        for c in active_clutches:
            try:
                first_egg_d = datetime.strptime(
                    c["first_egg_date"], "%Y-%m-%d"
                ).date()
                candling_d = first_egg_d + timedelta(days=7)
                hatch_d = first_egg_d + timedelta(days=22)
                ring_d = first_egg_d + timedelta(days=30)
                wean_d = first_egg_d + timedelta(days=67)
                days_left = (hatch_d - today).days

                if days_left == 0:
                    status_tag = "🐣 متوقع أول فقس اليوم!"
                    border_color = "#48BB78"
                elif 0 < days_left <= 3:
                    status_tag = f"⚠️ اقترب الفقس جداً! (باقي {days_left} يوم)"
                    border_color = "#ECC94B"
                elif days_left > 3:
                    status_tag = f"⏳ في فترة الحضن (باقي {days_left} يوم على الفقس)"
                    border_color = "#4299E1"
                else:
                    status_tag = f"انتهت فترة الحضن منذ {abs(days_left)} يوم"
                    border_color = "#F56565"

                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color: #2D3748; border-right: 6px solid {border_color}; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;">
                            <h4 style="color: white; margin: 0 0 5px 0;">🦜 زوج رقم: {c['pair_number']} | بطن رقم: {c['clutch_number']}</h4>
                            <p style="color: #E2E8F0; font-weight: bold; margin: 0 0 5px 0;">{status_tag}</p>
                            <p style="color: #CBD5E0; font-size: 13px; margin: 0;">
                                🥚 <b>عدد البيض:</b> {c['eggs_count'] or 0} | 📅 <b>أول بيضة:</b> {c['first_egg_date']}<br>
                                🔦 <b>فحص التخصيب:</b> {candling_d.strftime('%Y-%m-%d')} | 🐣 <b>الفقس المتوقع:</b> {hatch_d.strftime('%Y-%m-%d')}<br>
                                💍 <b>التحجيل:</b> {ring_d.strftime('%Y-%m-%d')} | 🌿 <b>الفطام:</b> {wean_d.strftime('%Y-%m-%d')}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            except Exception:
                continue
    else:
        st.success("لا توجد بطون قيد الحضن حالياً.")

elif menu == "سجل الإنتاج والبطون":
    st.header("🥚 سجل الإنتاج والبطون")

    tab1, tab2 = st.tabs(["📋 استعراض البطون", "➕ تسجيل بطن جديد"])

    with tab1:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pair_number, clutch_number, eggs_count, chicks_count, first_egg_date, notes 
            FROM production 
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame(rows)
            df.columns = [
                "رقم الزوج",
                "رقم البطن",
                "عدد البيض",
                "عدد الفروخ",
                "تاريخ أول بيضة",
                "ملاحظات",
            ]
            st.dataframe(df, width="stretch")
        else:
            st.info("لا توجد بطون مسجلة بعد.")

    with tab2:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pair_number FROM pairs 
            ORDER BY 
                CASE 
                    WHEN pair_number ~ '^[0-9]+$' THEN CAST(pair_number AS INTEGER)
                    ELSE 999999 
                END ASC, 
                pair_number ASC
        """)
        pair_rows = cursor.fetchall()
        pairs_list = [
            str(list(r.values())[0] if isinstance(r, dict) else r[0])
            for r in pair_rows
        ]

        if not pairs_list:
            st.warning("يجب إضافة أزواج أولاً قبل تسجيل الإنتاج.")
        else:
            with st.form("add_clutch_form"):
                selected_p = st.selectbox("اختر رقم الزوج *", pairs_list)
                clutch_n = st.number_input(
                    "رقم البطن لهذا الزوج", min_value=1, max_value=50, value=1
                )
                eggs_n = st.number_input(
                    "عدد البيض", min_value=0, max_value=20, value=0
                )
                chicks_n = st.number_input(
                    "عدد الفروخ", min_value=0, max_value=20, value=0
                )
                first_egg_d = st.date_input("تاريخ أول بيضة", value=datetime.now())
                start_d = st.date_input("تاريخ وضع العش", value=datetime.now())
                notes = st.text_input("ملاحظات")

                save_clutch = st.form_submit_button("حفظ البطن وتفعيل التنبيهات")

                if save_clutch:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                                INSERT INTO production (pair_number, clutch_number, eggs_count, chicks_count, start_date, first_egg_date, notes)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                selected_p,
                                clutch_n,
                                eggs_n,
                                chicks_n,
                                start_d.strftime("%Y-%m-%d"),
                                first_egg_d.strftime("%Y-%m-%d"),
                                notes.strip(),
                            ),
                        )
                        conn.commit()
                        st.success(
                            f"تم حفظ البطن للزوج [{selected_p}] بنجاح وتفعيل جدول"
                            " التنبيهات!"
                        )
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء الحفظ: {e}")

elif menu == "معرض الصور والشهادات 🖼️":
    st.header("🖼️ استعراض الصور والشهادات بالحجم الكامل")

    tab1, tab2 = st.tabs(["🧬 شهادات DNA للطيور", "👩‍❤️‍👨 صور الأزواج"])

    with tab1:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ring_number, gender, color, dna_path, image_path 
            FROM individual_birds 
            WHERE (dna_path IS NOT NULL AND dna_path != '') 
               OR (image_path IS NOT NULL AND image_path != '')
            ORDER BY id DESC
        """)
        birds_with_media = cursor.fetchall()

        if birds_with_media:
            options = {
                f"طير حجل [{b['ring_number']}] - {b.get('color', '')} ({b.get('gender', '')})": (
                    b.get("dna_path") or b.get("image_path")
                )
                for b in birds_with_media
            }
            selected_bird = st.selectbox("اختر الطير لعرض شهادته:", list(options.keys()))
            img_url = options[selected_bird]

            if img_url:
                st.image(img_url, caption=selected_bird, width="stretch")
                st.markdown(f"[🔗 فتح الصورة برابط مباشر]({img_url})")
        else:
            st.info("لا توجد شهادات DNA مرفوعة للطيور بعد.")

    with tab2:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pair_number, male_ring, female_ring, image_path 
            FROM pairs 
            WHERE image_path IS NOT NULL AND image_path != ''
            ORDER BY 
                CASE 
                    WHEN pair_number ~ '^[0-9]+$' THEN CAST(pair_number AS INTEGER)
                    ELSE 999999 
                END ASC
        """)
        pairs_with_media = cursor.fetchall()

        if pairs_with_media:
            pair_options = {
                f"زوج رقم [{p['pair_number']}] - الذكر: {p.get('male_ring', '-')} / الأنثى: {p.get('female_ring', '-')}": (
                    p["image_path"]
                )
                for p in pairs_with_media
            }
            selected_pair = st.selectbox(
                "اختر الزوج لعرض صورته:", list(pair_options.keys())
            )
            pair_img_url = pair_options[selected_pair]

            if pair_img_url:
                st.image(pair_img_url, caption=selected_pair, width="stretch")
                st.markdown(f"[🔗 فتح الصورة برابط مباشر]({pair_img_url})")
        else:
            st.info("لا توجد صور مرفوعة للأزواج بعد.")

elif menu == "🧬 حاسبة الطفرات والوراثة":
    st.header("🧬 حاسبة طفرات وتوقعات إنتاج طيور الروز")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("الذكر (1.0 ♂)")
        m_opaline = st.checkbox("أوبلاين (Opaline)", key="m_op")
        m_ino = st.checkbox("لوتينو / إينو (Ino)", key="m_ino")
        m_cinnamon = st.checkbox("سينامون (Cinnamon)", key="m_cin")
        st.markdown("**طفرات سبليت للذكر (Split):**")
        m_sp_op = st.checkbox("سبليت أوبلاين (Split Opaline)")
        m_sp_ino = st.checkbox("سبليت إينو (Split Ino)")
        m_sp_cin = st.checkbox("سبليت سينامون (Split Cinnamon)")

    with col2:
        st.subheader("الأنثى (0.1 ♀)")
        f_opaline = st.checkbox("أوبلاين (Opaline)", key="f_op")
        f_ino = st.checkbox("لوتينو / إينو (Ino)", key="f_ino")
        f_cinnamon = st.checkbox("سينامون (Cinnamon)", key="f_cin")

    if st.button("⚡ حساب نتائج وتوقعات الفروخ"):
        st.markdown("---")
        st.subheader("📊 النتائج الوراثية المتوقعة:")

        st.markdown("#### 🐣 الفروخ الإناث (0.1 ♀):")
        f_res = []
        if m_opaline:
            f_res.append("100% إناث أوبلاين ظاهرياً")
        elif m_sp_op:
            f_res.append("50% إناث أوبلاين ظاهرياً / 50% عادية")

        if m_ino:
            f_res.append("100% إناث لوتينو/إينو ظاهرياً")
        elif m_sp_ino:
            f_res.append("50% إناث لوتينو/إينو ظاهرياً")

        if m_cinnamon:
            f_res.append("100% إناث سينامون ظاهرياً")
        elif m_sp_cin:
            f_res.append("50% إناث سينامون ظاهرياً")

        if not f_res:
            f_res.append("إناث عادية بنفس لون الأساس")
        for r in f_res:
            st.success(f"• {r}")

        st.markdown("#### 🐣 الفروخ الذكور (1.0 ♂):")
        m_res = []
        if m_opaline and f_opaline:
            m_res.append("100% ذكور أوبلاين ظاهرياً")
        elif m_opaline and not f_opaline:
            m_res.append("100% ذكور عادية ظاهرياً (Split Opaline)")
        elif m_sp_op and f_opaline:
            m_res.append(
                "50% ذكور أوبلاين ظاهرياً / 50% ذكور عادية (Split Opaline)"
            )
        elif f_opaline and not m_opaline:
            m_res.append("100% ذكور عادية ظاهرياً (Split Opaline)")

        if m_ino and f_ino:
            m_res.append("100% ذكور لوتينو/إينو ظاهرياً")
        elif (m_ino or m_sp_ino) and f_ino:
            m_res.append(
                "50% ذكور لوتينو/إينو ظاهرياً / 50% ذكور عادية (Split Ino)"
            )
        elif m_ino or f_ino or m_sp_ino:
            m_res.append("ذكور عادية ظاهرياً محتملة (Split Ino)")

        if not m_res:
            m_res.append("ذكور عادية بنفس لون الأساس")
        for r in m_res:
            st.info(f"• {r}")

elif menu == "الفروخ":
    st.header("🐣 قائمة الفروخ")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ring_number, pair_number, hatch_month, color, gender, status FROM"
        " chicks ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows)
        df.columns = [
            "رقم الحجل",
            "رقم الزوج",
            "شهر الفقس",
            "اللون",
            "الجنس",
            "الحالة",
        ]
        st.dataframe(df, width="stretch")
    else:
        st.info("لا توجد فروخ مسجلة.")

elif menu == "إضافة طير جديد":
    st.header("➕ إضافة طير جديد من الجوال")

    cursor = conn.cursor()
    cursor.execute(
        "SELECT value FROM settings_options WHERE category = 'color' ORDER BY"
        " value ASC"
    )
    color_rows = cursor.fetchall()
    db_colors = [
        list(r.values())[0] if isinstance(r, dict) else r[0] for r in color_rows
    ]
    colors_list = ["اختر اللون..."] + db_colors

    with st.form("add_bird_form"):
        ring_number = st.text_input("رقم الحجل *")
        gender = st.selectbox(
            "الجنس", ["ذكر", "أنثى", "بانتظار DNA", "غير معروف"]
        )
        selected_color = st.selectbox("اللون الأساسي", colors_list)
        custom_color = st.text_input("أو اكتب لوناً آخر (اختياري)")
        mutations = st.text_input("الطفرات / ملاحظات")
        status = st.selectbox(
            "الحالة", ["متاح", "مجهز للتزويج", "للبيع", "تم البيع", "نافق"]
        )
        source = st.text_input("المصدر", value="إنتاج محلي")
        uploaded_dna = st.file_uploader(
            "ارفق شهادة الـ DNA أو صورة الطير (اختياري)",
            type=["png", "jpg", "jpeg", "webp"],
        )

        submitted = st.form_submit_button("حفظ الطير")

        if submitted:
            final_color = (
                custom_color.strip()
                if custom_color.strip()
                else (
                    ""
                    if selected_color == "اختر اللون..."
                    else selected_color.strip()
                )
            )

            if not ring_number.strip():
                st.error("يرجى إدخال رقم الحجل.")
            else:
                try:
                    saved_cloud_url = ""
                    if uploaded_dna:
                        import tempfile

                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".jpg"
                        ) as tmp_file:
                            tmp_file.write(uploaded_dna.getvalue())
                            tmp_file_path = tmp_file.name

                        saved_cloud_url = compress_and_upload_image(
                            tmp_file_path, prefix=f"dna_{ring_number.strip()}"
                        )

                    cursor = conn.cursor()
                    cursor.execute(
                        """
                            INSERT INTO individual_birds (ring_number, gender, color, mutations, status, source, image_path, dna_path)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            ring_number.strip(),
                            gender,
                            final_color,
                            mutations.strip(),
                            status,
                            source.strip(),
                            saved_cloud_url,
                            saved_cloud_url,
                        ),
                    )
                    conn.commit()
                    st.success(
                        f"تم إضافة الطير صاحب الحجل [{ring_number}] بنجاح ورفع بياناته"
                        " سحابياً!"
                    )
                except Exception as e:
                    if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                        st.error(f"رقم الحجل ({ring_number}) مسجل مسبقاً!")
                    else:
                        st.error(f"حدث خطأ أثناء الحفظ: {e}")

conn.close()
