from datetime import datetime, timedelta
import calendar
import requests
import streamlit as st

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(
    page_title="แอปปฏิทินอเนกประสงค์", page_icon="📅", layout="wide"
)

# ข้อมูลปีนักษัตรไทย (เริ่มนับปีชวดตามรอบ 12 ปี โดยอิงปี พ.ศ. 2503 เป็นปีชวดตั้งต้น)
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


# ฟังก์ชันจำลองข้างขึ้น-ข้างแรม (แก้ไขให้รองรับชนิดข้อมูล date)
def get_lunar_phase(date_obj):
  known_new_moon = datetime(2026, 1, 18).date()  # แปลงเป็น .date() เพื่อให้ตรงกัน
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


st.title("📅 แอปพลิเคชันปฏิทินอเนกประสงค์ครบวงจร")
st.write(
    "เลือกหัวข้อที่คุณต้องการตรวจสอบด้านล่างนี้ สามารถดูข้อมูลย้อนหลังและดูตามตำแหน่งปัจจุบันได้"
)

# สร้าง Tabs สำหรับแยกหัวข้อการใช้งาน
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🗓️ ปฏิทิน & ข้อมูลวันที่",
    "🌙 ข้างขึ้น-ข้างแรม & นักษัตร",
    "⭐ ราศี & พ.ศ./ค.ศ.",
    "🌍 นาฬิกาบอกเวลาโลก (ตามตำแหน่ง)",
    "⛅ พยากรณ์อากาศ",
    "⏪ ปฏิทินย้อนหลัง / ล่วงหน้า",
])

# ----------------- TAB 1: ปฏิทิน & ข้อมูลวันที่ -----------------
with tab1:
  st.subheader("ข้อมูลวันที่ วัน และเดือนปัจจุบัน/ที่เลือก")
  selected_date = st.date_input("เลือกวันที่ต้องการตรวจสอบ", datetime.today())

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

  eng_day = selected_date.strftime("%A")
  day_name_th = days_th.get(eng_day, eng_day)
  month_name_th = months_th.get(selected_date.month)

  col1, col2, col3 = st.columns(3)
  col1.metric("1. วันที่", selected_date.day)
  col2.metric("2. วันในสัปดาห์", day_name_th)
  col3.metric("3. เดือน", month_name_th)

# ----------------- TAB 2: ข้างขึ้น-ข้างแรม & นักษัตร -----------------
with tab2:
  st.subheader("ข้างขึ้น-ข้างแรม และ ปีนักษัตร")
  b_year = selected_date.year + 543
  lunar = get_lunar_phase(selected_date)
  naksat = get_naksat(b_year)

  c1, c2 = st.columns(2)
  c1.info(f"**4. ข้างขึ้น / ข้างแรม:**\n\n {lunar}")
  c2.info(f"**5. ปีนักษัตร:**\n\n {naksat}")

# ----------------- TAB 3: ราศี & ปี พ.ศ./ค.ศ. -----------------
with tab3:
  st.subheader("ปี พ.ศ. / ค.ศ. และ ราศี")
  ce_year = selected_date.year
  be_year = ce_year + 543
  zodiac = get_zodiac(selected_date.day, selected_date.month)

  c1, c2, c3 = st.columns(3)
  c1.metric("6. ปี พ.ศ.", be_year)
  c2.metric("ปี ค.ศ.", ce_year)
  c3.metric("7. ราศี", zodiac)

# ----------------- TAB 4: นาฬิกาบอกเวลาโลกตามตำแหน่ง -----------------
with tab4:
  st.subheader(
      "8. นาฬิกาบอกเวลาโลกตามตำแหน่งปัจจุบันของผู้ใช้ (Geolocated Time)"
  )
  st.write(
      "ระบบจะดึงพิกัดจากเบราว์เซอร์ของคุณเพื่อแสดงเวลาท้องถิ่นและ Timezone"
      " ที่คุณอยู่"
  )

  loc_html = """
    <div id="location-time" style="font-size: 20px; font-weight: bold; padding: 10px; background-color: #f0f2f6; border-radius: 8px;">
        กำลังค้นหาตำแหน่งของคุณ...
    </div>
    <script>
    function updateTime() {
        const now = new Date();
        document.getElementById('location-time').innerHTML = 
            "🕒 เวลาท้องถิ่นตามอุปกรณ์: " + now.toLocaleString() + "<br>" +
            "🌍 Timezone: " + Intl.DateTimeFormat().resolvedOptions().timeZone;
    }
    setInterval(updateTime, 1000);
    updateTime();
    </script>
    """
  st.components.v1.html(loc_html, height=100)

# ----------------- TAB 5: พยากรณ์อากาศ -----------------
with tab5:
  st.subheader("9. พยากรณ์อากาศ")
  city = st.text_input(
      "พิมพ์ชื่อเมืองหรือจังหวัด (ภาษาอังกฤษ เช่น Bangkok, Roi Et)", value="Bangkok"
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
        st.error("ไม่พบข้อมูลเมืองที่คุณค้นหา กรุณาลองใหม่อีกครั้ง")
    except Exception as e:
      st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลอากาศ: {e}")

# ----------------- TAB 6: ดูปฏิทินย้อนหลัง / ล่วงหน้า -----------------
with tab6:
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
    
