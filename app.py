import os
import math
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
import pandas as pd
import streamlit as st

# Optional libraries
try:
import ephem    
except Exception:
    ephem = None

try:
    from pythainlp.util import to_lunar_date
except Exception:
    to_lunar_date = None

try:
    from pythainlp.corpus import th_zodiac
except Exception:
    th_zodiac = None


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Mon101",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BANGKOK_TZ = ZoneInfo("Asia/Bangkok")


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #fafafa;
    }

    .hero {
        padding: 25px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            #111827,
            #312e81
        );
        color: white;
        margin-bottom: 20px;
    }

    .hero h1 {
        margin: 0;
        font-size: 42px;
    }

    .hero p {
        margin-top: 8px;
        font-size: 17px;
        opacity: 0.9;
    }

    .info-box {
        padding: 20px;
        border-radius: 18px;
        background: white;
        border: 1px solid #e5e7eb;
        margin-bottom: 15px;
    }

    .big-number {
        font-size: 38px;
        font-weight: 700;
        text-align: center;
    }

    .small-label {
        text-align: center;
        color: #6b7280;
        font-size: 14px;
    }

    .result-card {
        padding: 18px;
        border-radius: 16px;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }

    .music-card {
        padding: 15px;
        border-radius: 15px;
        background: #f3f4f6;
        margin-bottom: 10px;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

THAI_MONTHS = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]

THAI_DAYS = [
    "จันทร์",
    "อังคาร",
    "พุธ",
    "พฤหัสบดี",
    "ศุกร์",
    "เสาร์",
    "อาทิตย์",
]

THAI_WEATHER = {
    0: "ท้องฟ้าแจ่มใส",
    1: "มีเมฆเล็กน้อย",
    2: "มีเมฆเป็นบางส่วน",
    3: "มีเมฆมาก",
    45: "มีหมอก",
    48: "มีหมอกจับตัว",
    51: "ฝนปรอยเล็กน้อย",
    53: "ฝนปรอย",
    55: "ฝนปรอยหนัก",
    61: "ฝนเล็กน้อย",
    63: "ฝนปานกลาง",
    65: "ฝนตกหนัก",
    71: "หิมะตกเล็กน้อย",
    73: "หิมะตกปานกลาง",
    75: "หิมะตกหนัก",
    80: "ฝนซู่เล็กน้อย",
    81: "ฝนซู่",
    82: "ฝนซู่หนัก",
    95: "พายุฝนฟ้าคะนอง",
    96: "พายุฝนฟ้าคะนองและลูกเห็บ",
    99: "พายุฝนฟ้าคะนองรุนแรง",
}


def thai_date_string(d):
    """แสดงวันที่ภาษาไทย"""
    weekday = THAI_DAYS[d.weekday()]
    month = THAI_MONTHS[d.month - 1]
    year = d.year + 543

    return f"วัน{weekday}ที่ {d.day} {month} พ.ศ. {year}"


def western_zodiac_from_longitude(longitude):
    """คำนวณราศีตะวันตกจากองศาสุริยวิถี"""
    signs = [
        ("เมษ", "Aries"),
        ("พฤษภ", "Taurus"),
        ("เมถุน", "Gemini"),
        ("กรกฎ", "Cancer"),
        ("สิงห์", "Leo"),
        ("กันย์", "Virgo"),
        ("ตุล", "Libra"),
        ("พิจิก", "Scorpio"),
        ("ธนู", "Sagittarius"),
        ("มังกร", "Capricorn"),
        ("กุมภ์", "Aquarius"),
        ("มีน", "Pisces"),
    ]

    index = int(longitude // 30) % 12
    degree_in_sign = longitude % 30

    return {
        "thai": signs[index][0],
        "english": signs[index][1],
        "degree": degree_in_sign,
        "longitude": longitude,
    }


def calculate_western_zodiac(d):
    """
    ใช้ ephem คำนวณตำแหน่งดวงอาทิตย์บน ecliptic
    โดยใช้เวลาเที่ยงของประเทศไทยเป็นจุดอ้างอิง
    """
    if ephem is None:
        return None

    try:
        local_dt = datetime(
            d.year,
            d.month,
            d.day,
            12,
            0,
            0,
            tzinfo=BANGKOK_TZ,
        )

        utc_dt = local_dt.astimezone(timezone.utc)
        utc_naive = utc_dt.replace(tzinfo=None)

        sun = ephem.Sun(utc_naive)
        ecliptic = ephem.Ecliptic(sun)

        longitude = math.degrees(float(ecliptic.lon))
        longitude = longitude % 360

        return western_zodiac_from_longitude(longitude)

    except Exception:
        return None


def get_thai_lunar_date(d):
    """แปลงวันที่สากลเป็นข้อมูลจันทรคติไทย"""
    if to_lunar_date is None:
        return None

    try:
        lunar = to_lunar_date(d.year, d.month, d.day)
        return lunar
    except Exception:
        return None


def get_thai_zodiac(year):
    """เรียกข้อมูลนักษัตรจาก PyThaiNLP"""
    if th_zodiac is None:
        return None

    try:
        return th_zodiac(year, output_type=1)
    except Exception:
        try:
            return th_zodiac(year)
        except Exception:
            return None


def golden_ratio():
    """อัตราส่วนทองคำทางคณิตศาสตร์"""
    return (1 + math.sqrt(5)) / 2


def format_seconds(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# =========================================================
# WEATHER
# =========================================================

@st.cache_data(ttl=1800)
def geocode_city(city):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 1,
        "language": "th",
        "format": "json",
    }

    response = requests.get(
        url,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    if not results:
        return None

    item = results[0]

    return {
        "name": item.get("name", city),
        "country": item.get("country", ""),
        "latitude": item["latitude"],
        "longitude": item["longitude"],
        "timezone": item.get("timezone", "Asia/Bangkok"),
    }


@st.cache_data(ttl=1800)
def get_weather(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
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
        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max,"
            "sunrise,"
            "sunset"
        ),
        "forecast_days": 7,
        "timezone": "auto",
    }

    response = requests.get(
        url,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


# =========================================================
# LOTTERY
# =========================================================

GLO_API_URL = "https://www.glo.or.th/api/lottery/getLotteryResult"


@st.cache_data(ttl=86400)
def get_lottery_result(draw_date):
    """
    เรียก API ผลสลากกินแบ่งรัฐบาลของสำนักงานสลากกินแบ่งรัฐบาล

    API อาจเปลี่ยนโครงสร้างในอนาคต จึงแยก parser
    ออกจากส่วน UI เพื่อให้แก้ได้ง่าย
    """
    payload = {
        "date": draw_date.strftime("%Y-%m-%d")
    }

    try:
        response = requests.post(
            GLO_API_URL,
            json=payload,
            timeout=20,
        )

        response.raise_for_status()

        return response.json()

    except Exception as exc:
        return {
            "_error": str(exc)
        }


def flatten_lottery_data(data):
    """
    พยายามดึงข้อมูลรางวัลออกจาก JSON แบบทั่วไป
    เพราะ schema ของ API อาจเปลี่ยนได้
    """
    rows = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else str(key)

                if isinstance(value, (dict, list)):
                    walk(value, new_path)
                else:
                    rows.append(
                        {
                            "รายการ": new_path,
                            "ค่า": value,
                        }
                    )

        elif isinstance(obj, list):
            for index, value in enumerate(obj):
                new_path = f"{path}[{index}]"

                if isinstance(value, (dict, list)):
                    walk(value, new_path)
                else:
                    rows.append(
                        {
                            "รายการ": new_path,
                            "ค่า": value,
                        }
                    )

    walk(data)

    return rows


# =========================================================
# MUSIC
# =========================================================

def find_music_files():
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
                files.append(full_path)

    except Exception:
        return []

    return sorted(files)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <h1>🌙 Mon101</h1>
        <p>
            ปฏิทิน • เวลา • จันทรคติ • ราศี • อากาศ • เพลง • หวย
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CURRENT DATE
# =========================================================

today = datetime.now(BANGKOK_TZ).date()

st.caption(
    f"วันที่ระบบประเทศไทย: {thai_date_string(today)}"
)


# =========================================================
# TABS
# =========================================================

tabs = st.tabs(
    [
        "📅 วันที่",
        "🌙 จันทรคติ",
        "🐉 นักษัตร / ราศี",
        "🌍 เวลาโลก",
        "🌦️ อากาศ",
        "🗓️ ปฏิทิน",
        "🔄 เปรียบเทียบวันที่",
        "🟡 Golden Ratio",
        "🎵 เพลง",
        "🎰 หวยรัฐบาล",
    ]
)


# =========================================================
# TAB 1 : DATE
# =========================================================

with tabs[0]:
    st.subheader("📅 วันที่")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "วัน",
            f"{today.day}",
        )

    with col2:
        st.metric(
            "เดือน",
            THAI_MONTHS[today.month - 1],
        )

    with col3:
        st.metric(
            "พ.ศ.",
            str(today.year + 543),
        )

    st.markdown(
        f"""
        <div class="info-box">
            <div class="big-number">
                {thai_date_string(today)}
            </div>
            <div class="small-label">
                ค.ศ. {today.year}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        f"วันในสัปดาห์: **วัน{THAI_DAYS[today.weekday()]}**"
    )

    st.write(
        f"วันที่แบบ ISO: **{today.isoformat()}**"
    )


# =========================================================
# TAB 2 : LUNAR
# =========================================================

with tabs[1]:
    st.subheader("🌙 ปฏิทินจันทรคติไทย")

    lunar_date = get_thai_lunar_date(today)

    if lunar_date is None:
        st.warning(
            "ไม่สามารถอ่านข้อมูลจันทรคติจาก PyThaiNLP ได้ "
            "ตรวจสอบ requirements.txt ว่าติดตั้ง pythainlp แล้ว"
        )
    else:
        st.write("วันที่สากล")
        st.info(thai_date_string(today))

        st.write("ข้อมูลจันทรคติ")

        st.code(
            str(lunar_date),
            language="text",
        )

        st.caption(
            "หมายเหตุ: การแปลงนี้เป็นปฏิทินจันทรคติตามข้อมูลของไลบรารี "
            "ไม่ใช่การสังเกตดวงจันทร์จริง ณ สถานที่"
        )


# =========================================================
# TAB 3 : ZODIAC
# =========================================================

with tabs[2]:
    st.subheader("🐉 นักษัตรและราศีตะวันตก")

    zodiac_year = today.year

    thai_zodiac = get_thai_zodiac(zodiac_year)
    western = calculate_western_zodiac(today)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="info-box">
                <h3>🐉 นักษัตร</h3>
            """,
            unsafe_allow_html=True,
        )

        if thai_zodiac is None:
            st.warning(
                "ไม่สามารถอ่านข้อมูลนักษัตรจาก PyThaiNLP ได้"
            )
        else:
            st.markdown(
                f"""
                <div class="big-number">
                    {thai_zodiac}
                </div>
                <div class="small-label">
                    ปี ค.ศ. {zodiac_year}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            """
            <div class="info-box">
                <h3>♈ ราศีตะวันตก</h3>
            """,
            unsafe_allow_html=True,
        )

        if western is None:
            st.warning(
                "ไม่สามารถคำนวณราศีตะวันตกได้ "
                "ตรวจสอบว่าได้ติดตั้ง ephem แล้ว"
            )
        else:
            st.markdown(
                f"""
                <div class="big-number">
                    {western["thai"]}
                </div>
                <div class="small-label">
                    {western["english"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(
                f"องศาสุริยวิถี: "
                f"**{western['longitude']:.4f}°**"
            )

            st.write(
                f"องศาภายในราศี: "
                f"**{western['degree']:.4f}°**"
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        "ราศีตะวันตกในหน้านี้คำนวณจากตำแหน่งดวงอาทิตย์ "
        "ไม่ใช่การสุ่มหรือคะแนนจำลอง"
    )


# =========================================================
# TAB 4 : WORLD CLOCK
# =========================================================

with tabs[3]:
    st.subheader("🌍 เวลาโลก")

    cities = {
        "🇹🇭 กรุงเทพฯ": "Asia/Bangkok",
        "🇯🇵 โตเกียว": "Asia/Tokyo",
        "🇰🇷 โซล": "Asia/Seoul",
        "🇨🇳 เซี่ยงไฮ้": "Asia/Shanghai",
        "🇸🇬 สิงคโปร์": "Asia/Singapore",
        "🇮🇳 นิวเดลี": "Asia/Kolkata",
        "🇦🇪 ดูไบ": "Asia/Dubai",
        "🇬🇧 ลอนดอน": "Europe/London",
        "🇫🇷 ปารีส": "Europe/Paris",
        "🇺🇸 นิวยอร์ก": "America/New_York",
        "🇺🇸 ลอสแอนเจลิส": "America/Los_Angeles",
        "🇦🇺 ซิดนีย์": "Australia/Sydney",
    }

    cols = st.columns(3)

    now_utc = datetime.now(timezone.utc)

    for index, (city, tz_name) in enumerate(cities.items()):
        with cols[index % 3]:
            try:
                local_time = now_utc.astimezone(
                    ZoneInfo(tz_name)
                )

                st.markdown(
                    f"""
                    <div class="info-box">
                        <h4>{city}</h4>
                        <div class="big-number">
                            {local_time.strftime("%H:%M")}
                        </div>
                        <div class="small-label">
                            {local_time.strftime("%d/%m/%Y")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            except Exception:
                st.error(
                    f"ไม่สามารถอ่านเขตเวลา {tz_name}"
                )


# =========================================================
# TAB 5 : WEATHER
# =========================================================

with tabs[4]:
    st.subheader("🌦️ สภาพอากาศ")

    city = st.text_input(
        "พิมพ์ชื่อเมือง",
        value="Udon Thani",
        key="weather_city",
    )

    if st.button(
        "🔎 ตรวจอากาศ",
        key="weather_button",
    ):
        if not city.strip():
            st.warning("กรุณาระบุชื่อเมือง")
        else:
            with st.spinner("กำลังค้นหาสถานที่..."):
                try:
                    location = geocode_city(city)

                    if location is None:
                        st.error(
                            "ไม่พบสถานที่นี้"
                        )
                    else:
                        weather = get_weather(
                            location["latitude"],
                            location["longitude"],
                        )

                        current = weather.get(
                            "current",
                            {},
                        )

                        code = current.get(
                            "weather_code"
                        )

                        description = THAI_WEATHER.get(
                            code,
                            f"รหัสสภาพอากาศ {code}",
                        )

                        st.success(
                            f"{location['name']}, "
                            f"{location['country']}"
                        )

                        c1, c2, c3 = st.columns(3)

                        with c1:
                            st.metric(
                                "อุณหภูมิ",
                                f"{current.get('temperature_2m', '-') } °C",
                            )

                        with c2:
                            st.metric(
                                "ความรู้สึก",
                                f"{current.get('apparent_temperature', '-') } °C",
                            )

                        with c3:
                            st.metric(
                                "ความชื้น",
                                f"{current.get('relative_humidity_2m', '-')} %",
                            )

                        st.info(
                            f"สภาพอากาศ: **{description}**"
                        )

                        st.write(
                            "ฝนขณะนี้: "
                            f"**{current.get('precipitation', '-')} mm**"
                        )

                        st.write(
                            "ความเร็วลม: "
                            f"**{current.get('wind_speed_10m', '-')} km/h**"
                        )

                        daily = weather.get(
                            "daily",
                            {},
                        )

                        if daily:
                            rows = []

                            times = daily.get(
                                "time",
                                [],
                            )

                            max_temp = daily.get(
                                "temperature_2m_max",
                                [],
                            )

                            min_temp = daily.get(
                                "temperature_2m_min",
                                [],
                            )

                            rain_prob = daily.get(
                                "precipitation_probability_ma
