import streamlit as st
import pandas as pd
from app.database import get_connection

# إعدادات الصفحة للجوال
st.set_page_config(page_title="Lovebird Manager", page_icon="🦜", layout="centered")

st.title("🦜 Lovebird Manager - الجوال")

menu = st.sidebar.selectbox("القائمة", ["جمـيع الطيـور", "الأزواج", "الفروخ", "إضافة طير جديد"])

conn = get_connection()

if menu == "جمـيع الطيـور":
    st.header("📋 قائمة جميع الطيور")
    cursor = conn.cursor()
    cursor.execute("SELECT ring_number, gender, color, mutations, status, source FROM individual_birds ORDER BY id DESC")
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows)
        df.columns = ["رقم الحجل", "الجنس", "اللون", "الطفرات", "الحالة", "المصدر"]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("لا توجد طيور مسجلة حالياً.")

elif menu == "الأزواج":
    st.header("👩‍❤️‍👨 قائمة الأزواج")
    cursor = conn.cursor()
    cursor.execute("SELECT pair_number, male_ring, female_ring, male_color, female_color, status FROM pairs ORDER BY id DESC")
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows)
        df.columns = ["رقم الزوج", "حجل الذكر", "حجل الأنثى", "لون الذكر", "لون الأنثى", "الحالة"]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("لا توجد أزواج مسجلة.")

elif menu == "الفروخ":
    st.header("🐣 قائمة الفروخ")
    cursor = conn.cursor()
    cursor.execute("SELECT ring_number, pair_number, hatch_month, color, gender, status FROM chicks ORDER BY id DESC")
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows)
        df.columns = ["رقم الحجل", "رقم الزوج", "شهر الفقس", "اللون", "الجنس", "الحالة"]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("لا توجد فروخ مسجلة.")

elif menu == "إضافة طير جديد":
    st.header("➕ إضافة طير جديد من الجوال")
    with st.form("add_bird_form"):
        ring_number = st.text_input("رقم الحجل *")
        gender = st.selectbox("الجنس", ["ذكر", "أنثى", "بانتظار DNA", "غير معروف"])
        color = st.text_input("اللون الأساسي")
        mutations = st.text_input("الطفرات / ملاحظات")
        status = st.selectbox("الحالة", ["متاح", "مجهز للتزويج", "للبيع", "تم البيع", "نافق"])
        source = st.text_input("المصدر", value="إنتاج محلي")
        
        submitted = st.form_submit_button("حفظ الطير")
        
        if submitted:
            if not ring_number.strip():
                st.error("يرجى إدخال رقم الحجل.")
            else:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO individual_birds (ring_number, gender, color, mutations, status, source)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (ring_number.strip(), gender, color.strip(), mutations.strip(), status, source.strip()))
                    conn.commit()
                    st.success(f"تم إضافة الطير صاحب الحجل [{ring_number}] بنجاح!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء الحفظ: {e}")

conn.close()