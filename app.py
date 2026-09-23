import os
import math
import calendar
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
import streamlit as st
import ephem

from pythainlp.util import to_lunar_date, th_zodiac


# =========================================================
# CONFIG
# =========================================================

APP_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="Mon101",
    page_icon="📅",
    layout="wide"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        font-size: 18px;
        opacity: 0.75;
        margin-bottom: 25px;
    }

    .big-number {
        font-size: 38px;
        font-weight: 700;
        text-align: center;
    }

    .info-box {
        padding: 18px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 15px;
    }

    .song-box {
        padding: 12px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# LOGO
# =========================================================

def show_logo():
    logo_path = os.path.join(APP_DIR, "logo.jpg")

    if os.path.exists(logo_path):
        st.image(logo_path, width=180)


# =========================================================
# THAI DATE
# =========================================================

thai_weekdays = {
    0: "วันจันทร์",
    1: "วันอังคาร",
    2: "วันพุธ",
    3: "วันพฤหัสบดี",
    4: "วันศุกร์",
    5: "วันเสาร์",
    6: "วันอาทิตย์",
}

thai_months = {
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


# =========================================================
# THAI LUNAR CALENDAR
# =========================================================

def get_thai_lunar_date(date_obj):
    """
    แปลงวันที่สากลเป็นวันที่จันทรคติไทย
    โดยใช้ PyThaiNLP
    """

    try:
        return to_lunar_date(date_obj)

    except (ValueError, NotImplementedError) as e:
        return f"ไม่สามารถคำนวณวันจันทรคติสำหรับวันที่นี้ได้: {e}"

    except Exception as e:
        return f"เกิดข้อผิดพลาดในการคำนวณวันจันทรคติ: {e}"


# =========================================================
# THAI ZODIAC
# =========================================================

def get_thai_zodiac(year):
    """
    นักษัตรไทยจากปี ค.ศ.
    """

    try:
        return th_zodiac(year, output_type=1)

    except Exception as e:
        return f"ไม่สามารถคำนวณนักษัตรได้: {e}"


# =========================================================
# WESTERN ZODIAC
# =========================================================

western_zodiac = [
    ("เมษ", "Aries"),
    ("พฤษภ", "Taurus"),
    ("เมถุน", "Gemini"),
    ("กรกฎ", "Cancer"),
    ("สิงห์", "Leo"),
    ("กันย์", "Virgo"),
    ("ตุลย์", "Libra"),
    ("พิจิก", "Scorpio"),
    ("ธนู", "Sagittarius"),
    ("มังกร", "Capricorn"),
    ("กุมภ์", "Aquarius"),
    ("มีน", "Pisces"),
]


def get_western_zodiac(date_obj):
    """
    คำนวณราศีจากตำแหน่งดวงอาทิตย์
    โดยใช้ PyEphem แทนการกำหนดช่วงวันที่ตายตัว
    """

    try:
        # ใช้เวลาเที่ยงของประเทศไทยเป็นจุดอ้างอิง
        bangkok = ZoneInfo("Asia/Bangkok")

        local_dt = datetime(
            date_obj.year,
            date_obj.month,
            date_obj.day,
            12,
            0,
            0,
            tzinfo=bangkok
        )

        # แปลงเป็น UTC
        utc_dt = local_dt.astimezone(timezone.utc).replace(tzinfo=None)

        # คำนวณตำแหน่งดวงอาทิตย์
        sun = ephem.Sun(utc_dt)

        # แปลงเป็นพิกัดสุริยวิถี
        ecliptic = ephem.Ecliptic(sun)

        longitude_deg = math.degrees(float(ecliptic.lon))
        longitude_deg %= 360

        index = int(longitude_deg // 30)

        thai_name, english_name = western_zodiac[index]

        degree_in_sign = longitude_deg % 30

        return {
            "thai": thai_name,
            "english": english_name,
            "longitude": longitude_deg,
            "degree": degree_in_sign,
        }

    except Exception as e:
        return {
            "thai": "ไม่ทราบ",
            "english": "Unknown",
            "longitude": None,
            "degree": None,
            "error": str(e),
        }


# =========================================================
# BUDDHIST / CHRISTIAN ERA
# =========================================================

def get_be_ce(date_obj):

    ce = date_obj.year
    be = ce + 543

    return ce, be


# =========================================================
# GOLDEN RATIO
# =========================================================

PHI = (1 + math.sqrt(5)) / 2


def golden_ratio_info(date_obj):

    year = date_obj.year

    start = date(year, 1, 1)
    end = date(year + 1, 1, 1)

    total_days = (end - start).days

    day_number = (date_obj - start).days + 1

    # จุดแบ่ง Golden Section
    golden_position = total_days / PHI

    distance = abs(day_number - golden_position)

    nearest_day = round(golden_position)

    golden_date = start + timedelta(days=nearest_day - 1)

    return {
        "phi": PHI,
        "total_days": total_days,
        "day_number": day_number,
        "golden_position": golden_position,
        "distance": distance,
        "golden_date": golden_date,
    }


# =========================================================
# WEATHER
# =========================================================

@st.cache_data(ttl=600)
def get_weather(city):

    try:

        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        geo_params = {
            "name": city,
            "count": 1,
            "language": "th",
            "format": "json",
        }

        geo_response = requests.get(
            geo_url,
            params=geo_params,
            timeout=10
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        if not geo_data.get("results"):
            return None

        location = geo_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "timezone": "Asia/Bangkok",
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()

        return {
            "location": location,
            "current": weather_data.get("current", {}),
        }

    except Exception as e:
        return {
            "error": str(e)
        }


def weather_description(code):

    weather_codes = {
        0: "ท้องฟ้าแจ่มใส",
        1: "แจ่มใสเป็นส่วนใหญ่",
        2: "มีเมฆบางส่วน",
        3: "มีเมฆมาก",
        45: "มีหมอก",
        48: "มีหมอกจับตัวเป็นน้ำค้างแข็ง",
        51: "ฝนละอองเล็กน้อย",
        53: "ฝนละออง",
        55: "ฝนละอองหนาแน่น",
        61: "ฝนเล็กน้อย",
        63: "ฝนปานกลาง",
        65: "ฝนตกหนัก",
        71: "หิมะตกเล็กน้อย",
        73: "หิมะตกปานกลาง",
        75: "หิมะตกหนัก",
        80: "ฝนตกเป็นช่วง",
        81: "ฝนตกเป็นช่วงปานกลาง",
        82: "ฝนตกหนักเป็นช่วง",
        95: "พายุฝนฟ้าคะนอง",
        96: "พายุฝนฟ้าคะนองและลูกเห็บ",
        99: "พายุฝนฟ้าคะนองและลูกเห็บหนัก",
    }

    return weather_codes.get(code, "ไม่ทราบสภาพอากาศ")


# =========================================================
# MUSIC
# =========================================================

def get_music_files():

    extensions = (
        ".mp3",
        ".wav",
        ".ogg",
        ".m4a",
        ".aac",
    )

    files = []

    try:
        for filename in os.listdir(APP_DIR):

            full_path = os.path.join(APP_DIR, filename)

            if (
                os.path.isfile(full_path)
                and filename.lower().endswith(extensions)
            ):
                files.append(filename)

    except Exception:
        pass

    return sorted(files, key=str.lower)


# =========================================================
# HEADER
# =========================================================

show_logo()

st.markdown(
    '<div class="main-title">Mon101</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">ปฏิทิน • จันทรคติ • นักษัตร • ดาราศาสตร์ • เวลา • อากาศ • เพลง</div>',
    unsafe_allow_html=True
)


# =========================================================
# MAIN DATE
# =========================================================

today = date.today()

selected_date = st.date_input(
    "เลือกวันที่",
    value=today
)


# =========================================================
# TABS
# =========================================================

tabs = st.tabs([
    "📅 วันที่",
    "🌙 จันทรคติ",
    "🐉 นักษัตร / ราศี",
    "🌍 เวลาโลก",
    "🌦️ อากาศ",
    "🗓️ ปฏิทิน",
    "🔄 เปรียบเทียบวันที่",
    "🟡 Golden Ratio",
    "🎵 เพลง",
])


# =========================================================
# TAB 1 : DATE
# =========================================================

with tabs[0]:

    ce, be = get_be_ce(selected_date)

    weekday = thai_weekdays[selected_date.weekday()]
    month_name = thai_months[selected_date.month]

    st.markdown(
        f"""
        <div class="info-box">
            <div class="big-number">
                {selected_date.day} {month_name} {be}
            </div>
            <div style="text-align:center;font-size:20px;">
                {weekday}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("ค.ศ.", ce)

    with col2:
        st.metric("พ.ศ.", be)

    with col3:
        st.metric(
            "วันที่ของปี",
            selected_date.timetuple().tm_yday
        )


# =========================================================
# TAB 2 : THAI LUNAR
# =========================================================

with tabs[1]:

    st.subheader("🌙 ปฏิทินจันทรคติไทย")

    lunar_date = get_thai_lunar_date(selected_date)

    st.markdown(
        f"""
        <div class="info-box">
            <div style="font-size:30px;font-weight:700;text-align:center;">
                {lunar_date}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "ส่วนนี้ไม่ได้ใช้สูตรจำลองรอบดวงจันทร์แบบกำหนดเอง "
        "แต่ใช้ตัวแปลงปฏิทินจันทรคติไทยจาก PyThaiNLP"
    )


# =========================================================
# TAB 3 : ZODIAC
# =========================================================

with tabs[2]:

    st.subheader("🐉 นักษัตรและราศี")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 🐉 นักษัตร")

        zodiac = get_thai_zodiac(selected_date.year)

        st.markdown(
            f"""
            <div class="info-box">
                <div class="big-number">
                    {zodiac}
                </div>
                <div style="text-align:center;">
                    ปี ค.ศ. {selected_date.year}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.caption(
            "นักษัตรส่วนนี้อ้างอิงปี ค.ศ. ตามฟังก์ชัน Thai Zodiac ของ PyThaiNLP"
        )

    with col2:

        st.markdown("### ☀️ ราศีตะวันตก")

        western = get_western_zodiac(selected_date)

        st.markdown(
            f"""
            <div class="info-box">
                <div class="big-number">
                    {western["thai"]}
                </div>
                <div style="text-align:center;font-size:20px;">
                    {western["english"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if western["degree"] is not None:

            st.write(
                f"ตำแหน่งดวงอาทิตย์ประมาณ "
                f"{western['degree']:.2f}° "
                f"ภายในราศี"
            )

            st.caption(
                f"Ecliptic longitude ≈ {western['longitude']:.4f}°"
            )


# =========================================================
# TAB 4 : WORLD TIME
# =========================================================

with tabs[3]:

    st.subheader("🌍 เวลาท้องถิ่นของอุปกรณ์")

    st.info(
        "เวลาส่วนนี้อ่านจากเวลาของอุปกรณ์/เบราว์เซอร์ของคุณ "
        "จึงไม่ใช่เวลาที่จำลองขึ้นจากค่าเริ่มต้นของโปรแกรม"
    )

    st.components.v1.html(
        """
        <div id="clock"
             style="
                font-size:42px;
                font-weight:bold;
                text-align:center;
                padding:30px;
             ">
        </div>

        <div id="zone"
             style="
                text-align:center;
                font-size:18px;
                opacity:0.7;
             ">
        </div>

        <script>

        function updateClock() {

            const now = new Date();

            document.getElementById("clock").innerHTML =
                now.toLocaleString("th-TH", {
                    weekday: "long",
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit"
                });

            document.getElementById("zone").innerHTML =
                "Timezone: " +
                Intl.DateTimeFormat().resolvedOptions().timeZone;
        }

        updateClock();

        setInterval(updateClock, 1000);

        </script>
        """,
        height=150
    )


# =========================================================
# TAB 5 : WEATHER
# =========================================================

with tabs[4]:

    st.subheader("🌦️ สภาพอากาศ")

    city = st.text_input(
        "ค้นหาเมือง",
        value="อุดรธานี"
    )

    if st.button("🔍 ตรวจสอบอากาศ"):

        weather = get_weather(city)

        if weather is None:

            st.warning("ไม่พบเมืองที่ค้นหา")

        elif "error" in weather:

            st.error(
                f"เกิดข้อผิดพลาด: {weather['error']}"
            )

        else:

            location = weather["location"]
            current = weather["current"]

            st.success(
                f"{location.get('name', city)}, "
                f"{location.get('country', '')}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "อุณหภูมิ",
                    f"{current.get('temperature_2m', '-')}"
                    f" {current.get('units', {}).get('temperature_2m', '°C')}"
                )

            with col2:
                st.metric(
                    "ความชื้น",
                    f"{current.get('relative_humidity_2m', '-')}%"
                )

            with col3:
                st.metric(
                    "ลม",
                    f"{current.get('wind_speed_10m', '-')} km/h"
                )

            code = current.get("weather_code")

            st.write(
                f"**สภาพอากาศ:** {weather_description(code)}"
            )

            st.write(
                f"อุณหภูมิที่รู้สึกได้: "
                f"{current.get('apparent_temperature', '-')} °C"
            )


# =========================================================
# TAB 6 : CALENDAR
# =========================================================

with tabs[5]:

    st.subheader("🗓️ ปฏิทินรายเดือน")

    year = st.number_input(
        "ปี ค.ศ.",
        min_value=1,
        max_value=9999,
        value=selected_date.year,
        step=1
    )

    month = st.number_input(
        "เดือน",
        min_value=1,
        max_value=12,
        value=selected_date.month,
        step=1
    )

    cal = calendar.month(
        int(year),
        int(month)
    )

    st.code(
        cal,
        language=None
    )


# =========================================================
# TAB 7 : COMPARE DATES
# =========================================================

with tabs[6]:

    st.subheader("🔄 เปรียบเทียบวันที่")

    col1, col2 = st.columns(2)

    with col1:

        date_a = st.date_input(
            "วันที่ A",
            value=selected_date,
            key="date_a"
        )

    with col2:

        date_b = st.date_input(
            "วันที่ B",
            value=today,
            key="date_b"
        )

    difference = abs(
        (date_b - date_a).days
    )

    st.markdown(
        f"""
        <div class="info-box">
            <div class="big-number">
                {difference:,}
            </div>
            <div style="text-align:center;font-size:20px;">
                วัน
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# TAB 8 : GOLDEN RATIO
# =========================================================

with tabs[7]:

    st.subheader("🟡 Golden Ratio")

    info = golden_ratio_info(selected_date)

    st.write(
        f"ค่า Golden Ratio (φ) = **{info['phi']:.12f}**"
    )

    st.write(
        f"ปีนี้มี **{info['total_days']} วัน**"
    )

    st.write(
        f"วันที่เลือกคือวันที่ **{info['day_number']}** ของปี"
    )

    st.write(
        f"ตำแหน่ง Golden Section ของปี ≈ "
        f"วันที่ {info['golden_position']:.2f}"
    )

    st.write(
        f"วันที่ใกล้จุด Golden Section ที่สุดคือ "
        f"**{info['golden_date'].strftime('%d/%m/%Y')}**"
    )

    st.write(
        f"วันที่เลือกห่างจากจุดนั้นประมาณ "
        f"**{info['distance']:.2f} วัน**"
    )

    st.info(
        "ส่วนนี้เป็นคณิตศาสตร์ของ Golden Ratio เท่านั้น "
        "ไม่ได้ตีความเป็นพลังงาน โชค หรือคะแนนชีวิต"
    )


# =========================================================
# TAB 9 : MUSIC
# =========================================================

with tabs[8]:

    st.subheader("🎵 เครื่องเล่นเพลง")

    st.write(
        "วางไฟล์เพลงไว้ในโฟลเดอร์เดียวกับ app.py"
    )

    st.code(
        """
Mon101/
├── app.py
├── logo.jpg
├── requirements.txt
├── README.md
├── 4ทิศ.mp3
├── เพลงของฉัน.mp3
└── เพลงอีกเพลง.mp3
        """,
        language=None
    )

    if st.button("🔄 สแกนเพลงใหม่"):

        st.rerun()

    music_files = get_music_files()

    if not music_files:

        st.warning(
            "ยังไม่พบไฟล์เพลงในโฟลเดอร์เดียวกับ app.py"
        )

    else:

        st.success(
            f"พบเพลง {len(music_files)} ไฟล์"
        )

        song_options = {
            os.path.splitext(filename)[0]: filename
            for filename in music_files
        }

        selected_song_name = st.selectbox(
            "เลือกเพลง",
            list(song_options.keys())
        )

        selected_song = song_options[selected_song_name]

        song_path = os.path.join(
            APP_DIR,
            selected_song
        )

        st.markdown(
            f"### 🎶 {selected_song_name}"
        )

        st.audio(song_path)


# =========================================================
# FOOTER
# ========================================================
