from datetime import datetime, timedelta
import calendar
import os
import requests
import streamlit as st

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(
    page_title="แอปปฏิทินอเนกประสงค์ (Golden Ratio)", page_icon="📅", layout="wide"
)


# ฟังก์ชันแสดงโลโก้อย่างปลอดภัย
def show_logo():
  if os.path.exists("logo.jpg"):
    st.image("logo.jpg", width=80)


# ข้อมูลปีนักษัตรไทย
naksat_list = [
    "ปีชวด (หนู)",
    "ปีฉลู (วัว)",
    "ปีขาล (เสือ)",
    "ปีเถาะ (กระต่าย)",
    "ปีมะโรง (งูใหญ่)",
    "ปีมะเส็ง (งูเล็ก)",
    "ปีมะเมีย (ม้า)",
    "ปีมะแม (แพะ)",
    "ปีวอก (ลิง)",
    "ปีระกา (ไก่)",
    "ปีจอ (สุนัข)",
    "ปีกุน (หมู)",
]


def get_naksat(buddhist_year):
  base_year = 2503
  index = (buddhist_year - base_year) % 12
  return naksat_list[index]


# ฟังก์ชันคำนวณราศีตามสากล
def get_zodiac(day, month):
  zodiacs = [
      ((1, 20), (2, 18), "ราศีกุมภ์ (Aquarius)"),
      ((2, 19), (3, 20), "ราศีมีน (Pisces)"),
      ((3, 21), (4, 19), "ราศีเมษ (Aries)"),
      ((4, 20), (5, 20), "ราศีพฤษภ (Taurus)"),
      ((5, 21), (6, 20), "ราศีเมถุน (Gemini)"),
      ((6, 21), (7, 22), "ราศีกรกฎ (Cancer)"),
      ((7, 23), (8, 22), "ราศีสิงห์ (Leo)"),
      ((8, 23), (9, 22), "ราศีกันย์ (Virgo)"),
      ((9, 23), (10, 22), "ราศีตุลย์ (Libra)"),
      ((10, 23), (11, 21), "ราศีพิจิก (Scorpio)"),
      ((11, 22), (12, 21), "ราศีธนู (Sagittarius)"),
  ]
  for (s_m, s_d), (e_m, e_d), name in zodiacs:
    if (month == s_m and day >= s_d) or (month == e_m and day <= e_d):
      return name
  return "ราศีมังกร (Capricorn)"


# ฟังก์ชันจำลองข้างขึ้น-ข้างแรม
def get_lunar_phase(date_obj):
  known_new_moon = datetime(2026, 1, 18).date()
  diff = (date_obj - known_new_moon).days
  phase_day = diff % 29.53
  if phase_day < 1:
    return "วันเดือนมืด (แรม 15 ค่ำ / New Moon)"
  elif phase_day < 7.4:
    return f"ข้างขึ้น (ขึ้น {int(phase_day)} ค่ำ)"
  elif phase_day < 8.4:
    return "วันพระ / 8 ค่ำ (First Quarter)"
  elif phase_day < 15:
    return f"ข้างขึ้น (ขึ้น {int(phase_day)} ค่ำ)"
  elif phase_day < 16:
    return "วันเพ็ญ (ขึ้น 15 ค่ำ / Full Moon)"
  elif phase_day < 22.5:
    return f"ข้างแรม (แรม {int(phase_day - 15)} ค่ำ)"
  elif phase_day < 23.5:
    return "วันพระ / แรม 8 ค่ำ (Last Quarter)"
  else:
    return f"ข้างแรม (แรม {int(phase_day - 15)} ค่ำ)"


st.title("📅 แอปพลิเคชันปฏิทินอเนกประสงค์ (รองรับค่าสมดุล 1.618)")
st.write(
    "เลือกหัวข้อที่คุณต้องการตรวจสอบด้านล่างนี้ ทุกหัวข้อแสดงโลโก้และระบบคำนวณ"
    " Gold Ratio"
)

# สร้าง Tabs สำหรับแยกหัวข้อการใช้งาน (เพิ่ม 2 แท็บใหม่)
tabs = st.tabs([
    "🗓️ วันที่",
    "🌙 ข้างขึ้น/แรม & นักษัตร",
    "⭐ ราศี & พ.ศ./ค.ศ.",
    "🌍 เวลาโลก",
    "⛅ อากาศ",
    "⏪ ปฏิทินย้อนหลัง",
    "⚖️ เปรียบเทียบ 2 วัน",
    "✨ ค่าสมดุล 1.618",
])

days_th = {
    "Monday": "วันจันทร์",
    "Tuesday": "วันอังคาร",
    "Wednesday": "วันพุธ",
    "Thursday": "วันพฤหัสบดี",
    "Friday": "วันศุกร์",
    "Saturday": "วันเสาร์",
    "Sunday": "วันอาทิตย์",
}
months_th = {
    1: "มกราคม",
    2: "กุมภาพันธ์",
    3: "มีนาคม",
    4: "เมษายน",
    5: "พฤษภาคม",
    6: "มิถุนายน",
    7: "กรกฎาคม",
    8: "สิงหาคม",
    9: "กันยายน",
    10: "ตุลาคม",
    11: "พฤศจิกายน",
    12: "ธันวาคม",
}

# ----------------- TAB 1: ปฏิทิน & ข้อมูลวันที่ -----------------
with tabs[0]:
  show_logo()
  st.subheader("1-3. ข้อมูลวันที่ วัน และเดือน")
  selected_date = st.date_input(
      "เลือกวันที่ต้องการตรวจสอบ", datetime.today(), key="d1"
  )

  eng_day = selected_date.strftime("%A")
  day_name_th = days_th.get(eng_day, eng_day)
  month_name_th = months_th.get(selected_date.month)

  col1, col2, col3 = st.columns(3)
  col1.metric("1. วันที่", selected_date.day)
  col2.metric("2. วันในสัปดาห์", day_name_th)
  col3.metric("3. เดือน", month_name_th)

# ----------------- TAB 2: ข้างขึ้น-ข้างแรม & นักษัตร -----------------
with tabs[1]:
  show_logo()
  st.subheader("4-5. ข้างขึ้น-ข้างแรม และ ปีนักษัตร")
  b_year = selected_date.year + 543
  lunar = get_lunar_phase(selected_date)
  naksat = get_naksat(b_year)

  c1, c2 = st.columns(2)
  c1.info(f"**4. ข้างขึ้น / ข้างแรม:**\n\n {lunar}")
  c2.info(f"**5. ปีนักษัตร:**\n\n {naksat}")

# ----------------- TAB 3: ราศี & ปี พ.ศ./ค.ศ. -----------------
with tabs[2]:
  show_logo()
  st.subheader("6-7. ปี พ.ศ. / ค.ศ. และ ราศี")
  ce_year = selected_date.year
  be_year = ce_year + 543
  zodiac = get_zodiac(selected_date.day, selected_date.month)

  c1, c2, c3 = st.columns(3)
  c1.metric("6. ปี พ.ศ.", be_year)
  c2.metric("ปี ค.ศ.", ce_year)
  c3.metric("7. ราศี", zodiac)

# ----------------- TAB 4: นาฬิกาบอกเวลาโลกตามตำแหน่ง -----------------
with tabs[3]:
  show_logo()
  st.subheader("8. นาฬิกาบอกเวลาโลกตามตำแหน่งปัจจุบันของผู้ใช้")
  st.write("ระบบดึงพิกัดจากเบราว์เซอร์เพื่อแสดงเวลาท้องถิ่น")
  loc_html = """
    <div id="location-time" style="font-size: 18px; font-weight: bold; padding: 10px; background-color: #f0f2f6; border-radius: 8px;">
        กำลังค้นหาตำแหน่งของคุณ...
    </div>
    <script>
    function updateTime() {
        const now = new Date();
        document.getElementById('location-time').innerHTML = 
            "🕒 เวลาท้องถิ่น: " + now.toLocaleString() + "<br>" +
            "🌍 Timezone: " + Intl.DateTimeFormat().resolvedOptions().timeZone;
    }
    setInterval(updateTime, 1000);
    updateTime();
    </script>
    """
  st.components.v1.html(loc_html, height=100)

# ----------------- TAB 5: พยากรณ์อากาศ -----------------
with tabs[4]:
  show_logo()
  st.subheader("9. พยากรณ์อากาศ")
  city = st.text_input(
      "พิมพ์ชื่อเมืองหรือจังหวัด (ภาษาอังกฤษ เช่น Bangkok, Roi Et)",
      value="Bangkok",
  )

  if st.button("🔍 ค้นหาพยากรณ์อากาศ"):
    try:
      geo_url = (
          f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
      )
      geo_res = requests.get(geo_url).json()
      if "results" in geo_res:
        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]
        country = geo_res["results"][0].get("country", "")

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        w_res = requests.get(weather_url).json()
        current = w_res["current_weather"]

        st.success(
            f"📍 ตำแหน่ง: {city.capitalize()} ({country}) [Lat: {lat}, Lon:"
            f" {lon}]"
        )
        st.metric("🌡️ อุณหภูมิปัจจุบัน", f"{current['temperature']} °C")
        st.metric("💨 ความเร็วลม", f"{current['windspeed']} km/h")
      else:
        st.error("ไม่พบข้อมูลเมืองที่คุณค้นหา")
    except Exception as e:
      st.error(f"เกิดข้อผิดพลาด: {e}")

# ----------------- TAB 6: ดูปฏิทินย้อนหลัง / ล่วงหน้า -----------------
with tabs[5]:
  show_logo()
  st.subheader("10. ดูปฏิทินย้อนหลังและล่วงหน้า")
  col_y, col_m = st.columns(2)
  with col_y:
    target_year = st.number_input(
        "เลือกปี (ค.ศ.)",
        min_value=1900,
        max_value=2100,
        value=datetime.today().year,
    )
  with col_m:
    target_month = st.selectbox(
        "เลือกเดือน",
        range(1, 13),
        format_func=lambda x: months_th[x],
        index=datetime.today().month - 1,
    )

  st.write(f"### ปฏิทินเดือน {months_th[target_month]} พ.ศ. {target_year + 543}")
  cal_text = calendar.month(target_year, target_month)
  st.text(cal_text)

# ----------------- TAB 7: เปรียบเทียบ 2 วัน -----------------
with tabs[6]:
  show_logo()
  st.subheader("⚖️ หัวข้อใหม่: เปรียบเทียบรายละเอียด 2 วัน")
  col_d1, col_d2 = st.columns(2)
  with col_d1:
    date_a = st.date_input("เลือกวันที่ 1", datetime.today(), key="compare_a")
  with col_d2:
    date_b = st.date_input(
        "เลือกวันที่ 2",
        datetime.today() + timedelta(days=7),
        key="compare_b",
    )

  diff_days = abs((date_b - date_a).days)
  st.info(
      f"📌 ระยะเวลาห่างกันทั้งหมด: **{diff_days} วัน** (หรือประมาณ"
      f" {round(diff_days / 7, 1)} สัปดาห์)"
  )

  col_res1, col_res2 = st.columns(2)
  with col_res1:
    st.markdown(f"### วันที่ 1: {date_a.strftime('%d/%m/%Y')}")
    st.write(
        f"- **วัน:** {days_th.get(date_a.strftime('%A'))}"
        f" {months_th[date_a.month]} {date_a.year + 543}"
    )
    st.write(f"- **ข้างขึ้น/แรม:** {get_lunar_phase(date_a)}")
    st.write(f"- **ราศี:** {get_zodiac(date_a.day, date_a.month)}")
    st.write(f"- **นักษัตร:** {get_naksat(date_a.year + 543)}")

  with col_res2:
    st.markdown(f"### วันที่ 2: {date_b.strftime('%d/%m/%Y')}")
    st.write(
        f"- **วัน:** {days_th.get(date_b.strftime('%A'))}"
        f" {months_th[date_b.month]} {date_b.year + 543}"
    )
    st.write(f"- **ข้างขึ้น/แรม:** {get_lunar_phase(date_b)}")
    st.write(f"- **ราศี:** {get_zodiac(date_b.day, date_b.month)}")
    st.write(f"- **นักษัตร:** {get_naksat(date_b.year + 543)}")

# ----------------- TAB 8: ค่าสมดุลทองคำ (1.618) -----------------
with tabs[7]:
  show_logo()
  st.subheader("✨ หัวข้อใหม่: คำนวณค่าสมดุลของวันด้วยหลักการ 1.618 (Golden Ratio)")
  st.write(
      "ระบบจะนำวันที่เลือกมาคำนวณสัดส่วนความสมดุลตามสัดส่วนทองคำ (Golden Ratio:"
      " 1.618) เพื่อวิเคราะห์จุดกึ่งกลางและพลังงานสมดุลของรอบวัน"
  )

  golden_date = st.date_input(
      "เลือกวันที่ต้องการหาค่าสมดุล 1.618", datetime.today(), key="golden_d"
  )

  # คำนวณค่าสมดุล 1.618 จากลำดับวันในรอบปี (Day of Year)
  day_of_year = golden_date.timetuple().tm_yday
  total_days_in_year = (
      366 if calendar.isleap(golden_date.year) else 365
  )

  # ใช้สูตรสัดส่วนทองคำ 1.618 มาคำนวณจุดสมดุล
  golden_point = (day_of_year / 1.618) % total_days_in_year
  harmony_score = min(
      100,
      round(
          (1 - abs((day_of_year - (total_days_in_year / 1.618))) / 365) * 100,
          2,
      ),
  )

  st.metric(
      "📐 วันที่ในรอบปี (Day of Year)",
      f"{day_of_year} / {total_days_in_year}",
  )
  st.metric(
      "✨ ดัชนีความสมดุลทองคำ (Golden Harmony Score)", f"{harmony_score}%"
  )

  if harmony_score > 50:
    st.success(
        "🌟 วันนี้อยู่ในเกณฑ์สัดส่วนสมดุลตามหลัก 1.618 (มีความกลมกลืนและเสถียรสูง)"
    )
  else:
    st.warning("⚡ วันนี้อยู่ในช่วงการเปลี่ยนแปลงวัฏจักรตามสัดส่วน 1.618")

  st.markdown(
      "--- \n*หมายเหตุ: การคำนวณทั้งหมดในหัวข้อนี้อ้างอิงตัวเลขค่าคงที่สมดุล"
      " **1.618** เป็นหลักการหลัก*"
    )
    
