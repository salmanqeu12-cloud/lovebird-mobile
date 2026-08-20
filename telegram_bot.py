from datetime import datetime, timedelta
from app.database import get_connection
import requests

# ================= الإعدادات =================
TELEGRAM_BOT_TOKEN = "8695434423:AAFZtqSizKRlTSfd0ZrRPNtolRuvlzYaw7c"
TELEGRAM_CHAT_ID = "1229934228"
# ============================================


def send_telegram_message(message: str):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "HTML",
  }
  try:
    response = requests.post(url, json=payload, timeout=10)
    if response.status_code == 200:
      print("✅ تم إرسال التنبيه إلى تيليجرام بنجاح!")
      return True
    else:
      print(f"⚠️ فشل الإرسال: {response.text}")
      return False
  except Exception as e:
    print(f"فشل الاتصال بتيليجرام: {e}")
    return False


def check_daily_alerts():
  today = datetime.now().date()
  conn = None
  clutches = []
  inventory_items = []

  try:
    conn = get_connection()
    cursor = conn.cursor()

    # 1. جلب بيانات الإنتاج
    cursor.execute("""
            SELECT pair_number, clutch_number, first_egg_date, eggs_count, chicks_count, notes
            FROM production 
            WHERE first_egg_date IS NOT NULL AND first_egg_date != ''
            ORDER BY first_egg_date DESC
        """)
    clutches = cursor.fetchall()

    # 2. جلب بيانات المخزون
    try:
      cursor.execute("""
                SELECT item_name, quantity, unit, min_quantity, expiry_date 
                FROM inventory
            """)
      inventory_items = cursor.fetchall()
    except Exception:
      pass

  except Exception as e:
    print(f"خطأ أثناء جلب البيانات: {e}")
    return
  finally:
    if conn:
      conn.close()

  alerts = []

  # فحص تنبيهات الإنتاج والبطون
  for c in clutches:
    try:
      first_egg_d = datetime.strptime(c["first_egg_date"], "%Y-%m-%d").date()
      candling_d = first_egg_d + timedelta(days=7)
      hatch_d = first_egg_d + timedelta(days=22)
      ring_d = first_egg_d + timedelta(days=30)
      wean_d = first_egg_d + timedelta(days=67)

      p_num = c["pair_number"]
      c_num = c["clutch_number"]
      eggs = c["eggs_count"] or 0

      # 1. تنبيه فحص تخصيب البيض
      if candling_d == today:
        alerts.append(
            f"🔦 <b>فحص التخصيب:</b> زوج رقم <b>[{p_num}]</b> (بطن"
            f" {c_num}) - حان موعد فحص البيض اليوم ({eggs} بيضات)."
        )

      # 2. تنبيه اقتراب الفقس أو الفقس اليوم
      days_to_hatch = (hatch_d - today).days
      if days_to_hatch == 1:
        alerts.append(
            f"⏳ <b>تجهيز الفقس:</b> زوج رقم <b>[{p_num}]</b> - متوقع أول فقس"
            " غداً!"
        )
      elif hatch_d == today:
        alerts.append(
            f"🐣 <b>موعد الفقس:</b> زوج رقم <b>[{p_num}]</b> (بطن {c_num}) -"
            " متوقع أول فقس اليوم!"
        )

      # 3. تنبيه موعد التحجيل
      if ring_d == today:
        alerts.append(
            f"💍 <b>تركيب الحجول:</b> زوج رقم <b>[{p_num}]</b> - حان موعد تحجيل"
            " الفروخ اليوم."
        )

      # 4. تنبيه موعد الفطام
      if wean_d == today:
        alerts.append(
            f"🌿 <b>فطام وعزل:</b> زوج رقم <b>[{p_num}]</b> - الفروخ جاهزة"
            " للفطام والعزل اليوم."
        )

    except Exception:
      continue

  # فحص تنبيهات المخزون والمستهلكات
  for inv in inventory_items:
    try:
      name = inv["item_name"]
      qty = float(inv["quantity"] or 0)
      min_q = float(inv["min_quantity"] or 0)
      unit = inv["unit"] or ""

      # تنبيه نقص الكمية
      if min_q > 0 and qty <= min_q:
        alerts.append(
            f"⚠️ <b>نقص مخزون:</b> مادة <b>[{name}]</b> شارفت على النفاد"
            f" (المتبقي: {qty:.1f} {unit})."
        )

      # تنبيه انتهاء الصلاحية
      if inv.get("expiry_date"):
        exp_d = datetime.strptime(str(inv["expiry_date"]), "%Y-%m-%d").date()
        days_exp = (exp_d - today).days
        if 0 <= days_exp <= 30:
          alerts.append(
              f"💊 <b>صلاحية دواء/مكمل:</b> صنف <b>[{name}]</b> ينتهي خلال"
              f" {days_exp} يوم ({exp_d})."
          )
        elif days_exp < 0:
          alerts.append(
              f"❌ <b>صلاحية منتهية:</b> صنف <b>[{name}]</b> منتهي الصلاحية"
              f" منذ {abs(days_exp)} يوم!"
          )
    except Exception:
      continue

  today_str = today.strftime("%Y-%m-%d")
  if alerts:
    message = (
        f"🦜 <b>صباح الخير يا سلمان!</b>\n"
        f"📅 <b>تنبيهات المزرعة والمخزون ليوم {today_str}:</b>\n\n"
        + "\n\n".join(alerts)
        + "\n\n<i>نتمنى لك يوماً سعيداً وإنتاجاً مباركاً! ✨</i>"
    )
  else:
    message = (
        f"🦜 <b>صباح الخير يا سلمان!</b>\n"
        f"📅 <b>تاريخ اليوم: {today_str}</b>\n\n"
        f"✅ <i>كل أمور المزرعة والمخزون مستقرة اليوم ولا توجد أي نواقص أو"
        f" مواعيد مستحقة! 🌿</i>"
    )

  send_telegram_message(message)


if __name__ == "__main__":
  check_daily_alerts()
