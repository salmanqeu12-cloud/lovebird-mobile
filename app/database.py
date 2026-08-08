import psycopg2
from psycopg2.extras import RealDictCursor

# بيانات الاتصال بقاعدة بيانات Supabase (Transaction pooler)
DB_HOST = "aws-0-ap-south-1.pooler.supabase.com"
DB_NAME = "postgres"
DB_USER = "postgres.vryzzhnokjxynoxsxspk"
DB_PASS = "A112211a@sqeu433786"
DB_PORT = "6543"


def get_connection():
    """إنشاء اتصال بقاعدة البيانات السحابية Supabase مع إرجاع الصفوف كـ Dictionary"""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        cursor_factory=RealDictCursor,
    )
    return conn


def init_db():
    """إنشاء الجداول والبيانات الافتراضية في Supabase تلقائياً عند أول تشغيل"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. جدول الإعدادات والقوائم المنسدلة
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings_options (
            id SERIAL PRIMARY KEY,
            category VARCHAR(50) NOT NULL,
            value VARCHAR(150) NOT NULL
        );
        """)

        # 2. جدول الأزواج
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pairs (
            id SERIAL PRIMARY KEY,
            pair_number VARCHAR(50) UNIQUE NOT NULL,
            male_ring VARCHAR(50),
            female_ring VARCHAR(50),
            male_color VARCHAR(100),
            female_color VARCHAR(100),
            status VARCHAR(50) DEFAULT 'إنتاج',
            notes TEXT,
            image_path TEXT
        );
        """)

        # 3. جدول سجل الإنتاج (البطون)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS production (
            id SERIAL PRIMARY KEY,
            pair_number VARCHAR(50) NOT NULL,
            clutch_number INTEGER NOT NULL,
            eggs_count INTEGER DEFAULT 0,
            chicks_count INTEGER DEFAULT 0,
            start_date VARCHAR(50),
            first_egg_date VARCHAR(50),
            notes TEXT,
            FOREIGN KEY(pair_number) REFERENCES pairs(pair_number) ON DELETE CASCADE
        );
        """)

        # 4. جدول الفروخ
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chicks (
            id SERIAL PRIMARY KEY,
            ring_number VARCHAR(50) UNIQUE NOT NULL,
            pair_number VARCHAR(50),
            hatch_month VARCHAR(50) NOT NULL,
            color VARCHAR(100),
            mutations TEXT,
            gender VARCHAR(50) DEFAULT 'بانتظار DNA',
            status VARCHAR(50) DEFAULT 'محتفظ به',
            notes TEXT,
            image_path TEXT,
            father_ring VARCHAR(50),
            mother_ring VARCHAR(50),
            FOREIGN KEY(pair_number) REFERENCES pairs(pair_number) ON DELETE SET NULL
        );
        """)

        # 5. جدول الأرشيف
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS archive (
            id SERIAL PRIMARY KEY,
            ring_number VARCHAR(50) NOT NULL,
            color_mutations TEXT,
            gender VARCHAR(50),
            reason VARCHAR(100) NOT NULL,
            archive_date VARCHAR(50) NOT NULL,
            notes TEXT
        );
        """)

        # 6. جدول الطيور الفردية (جميع الطيور والشهادات)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS individual_birds (
            id SERIAL PRIMARY KEY,
            ring_number VARCHAR(50) UNIQUE NOT NULL,
            gender VARCHAR(50) DEFAULT 'غير معروف',
            color VARCHAR(100),
            mutations TEXT,
            status VARCHAR(50) DEFAULT 'متاح',
            source VARCHAR(100) DEFAULT 'إنتاج محلي',
            notes TEXT,
            image_path TEXT,
            dna_path TEXT,
            father_ring VARCHAR(50),
            mother_ring VARCHAR(50)
        );
        """)

        # إضافة الألوان الخاصة بك تلقائياً إذا كان الجدول فارغاً
        cursor.execute(
            "SELECT COUNT(*) FROM settings_options WHERE category = 'color'"
        )
        if cursor.fetchone()['count'] == 0:
            custom_colors = [
                (
                    'color',
                    'لاتينو اورنج اوبلاين (Lutino Orange Opaline)',
                ),
                ('color', 'لاتينو اورنج فيس (Lutino Orange Face)'),
                ('color', 'لاتينو رد اوبلاين (Lutino Red Opaline)'),
                ('color', 'لاتينو رد فيس (Lutino Red Face)'),
                ('color', 'البينو (Albino)'),
                ('color', 'اينو(كريمينو) (Ino/Creamino)'),
                ('color', 'سينمون فيس (Cinnamon Face)'),
                ('color', 'سينمون اوبلاين (Cinnamon Opaline)'),
                ('color', 'قرين رد فيس (Green Red Face)'),
                ('color', 'قرين رد اوبلاين (Green Red Opaline)'),
                ('color', 'قرين اورنج اوبلاين (Green Orange Opaline)'),
                ('color', 'بلو اوبلاين (Blue Opaline)'),
                ('color', 'رصاصي فيس (Grey Face)'),
                ('color', 'رصاصي اوبلاين (Grey Opaline)'),
                ('color', 'بلو بايد (Blue Pied)'),
                ('color', 'باليد اوبلاين (Pied Opaline)'),
                ('color', 'بلو سبلت البينو (Blue Split Albino)'),
            ]
            cursor.executemany(
                "INSERT INTO settings_options (category, value) VALUES (%s, %s)",
                custom_colors,
            )

        # إضافة الخيارات الافتراضية للقطاعات الأخرى
        cursor.execute(
            "SELECT COUNT(*) FROM settings_options WHERE category != 'color'"
        )
        if cursor.fetchone()['count'] == 0:
            default_options = [
                ('pair_status', 'إنتاج'),
                ('pair_status', 'راحة'),
                ('pair_status', 'مباع'),
                ('pair_status', 'نافق'),
                ('chick_status', 'محتفظ به'),
                ('chick_status', 'للبيع'),
                ('chick_status', 'تم البيع'),
                ('chick_status', 'نافق'),
                ('gender', 'ذكر'),
                ('gender', 'أنثى'),
                ('gender', 'بانتظار DNA'),
                ('gender', 'غير معروف'),
                ('archive_reason', 'بيع'),
                ('archive_reason', 'نفوق'),
                ('archive_reason', 'استبعاد'),
            ]
            cursor.executemany(
                "INSERT INTO settings_options (category, value) VALUES (%s, %s)",
                default_options,
            )

        conn.commit()
        print("تم الاتصال بـ Supabase وإنشاء الجداول بنجاح!")
    except Exception as e:
        print(f"خطأ في الاتصال بالسحابة: {e}")
    finally:
        if conn:
            conn.close()


def get_pairs_with_counts():
    """جلب بيانات الأزواج مع حساب عدد البطون وإجمالي الفروخ تلقائياً"""
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
            COUNT(pr.id) AS clutches_count,
            COALESCE(SUM(pr.chicks_count), 0) AS total_chicks,
            p.status,
            p.notes,
            p.image_path
        FROM pairs p
        LEFT JOIN production pr ON p.pair_number = pr.pair_number
        GROUP BY p.id, p.pair_number, p.male_ring, p.female_ring, p.male_color, p.female_color, p.status, p.notes, p.image_path
        ORDER BY p.pair_number ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"Error in get_pairs_with_counts: {e}")
        return []
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    init_db()