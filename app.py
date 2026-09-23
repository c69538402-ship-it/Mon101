import os
import math
import calendar
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
import pandas as pd
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

    try:
        return th_zodiac(
            year,
            output_type=1
        )

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

    try:

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

        utc_dt = local_dt.astimezone(
            timezone.utc
        ).replace(
            tzinfo=None
        )

        sun = ephem.Sun(utc_dt)

        ecliptic = ephem.Ecliptic(sun)

        longitude_deg = math.degrees(
            float(ecliptic.lon)
        )

        longitude_deg %= 360

        index = int(
            longitude_deg // 30
        )

        thai_name, english_name = (
            western_zodiac[index]
        )

        degree_in_sign = (
            longitude_deg % 30
        )

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
# BE / CE
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

    start = date(
        year,
        1,
        1
    )

    end = date(
        year + 1,
        1,
        1
    )

    total_days = (
        end - start
    ).days

    day_number = (
        date_obj - start
    ).days + 1

    golden_position = (
        total_days / PHI
    )

    distance = abs(
        day_number - golden_position
    )

    nearest_day = round(
        golden_position
    )

    golden_date = (
        start
        + timedelta(
            days=nearest_day - 1
        )
    )

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

        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search"
        )

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

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
        )

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
            "current": weather_data.get(
                "current",
                {}
            ),
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

    return weather_codes.get(
        code,
        "ไม่ทราบสภาพอากาศ"
    )


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

            full_path = os.path.join(
                APP_DIR,
                filename
            )

            if (
                os.path.isfile(full_path)
                and filename.lower().endswith(
                    extensions
                )
            ):
                files.append(filename)

    except Exception:
        pass

    return sorted(
        files,
        key=str.lower
    )


# =========================================================
# LOTTERY - GLO
# =========================================================

GLO_API_URL = (
    "https://www.glo.or.th/api/lottery/getLotteryResult"
)


def normalize_lottery_number(value):

    if value is None:
        return ""

    return str(value).strip()


def extract_numbers(obj):

    results = []

    if obj is None:
        return results

    if isinstance(obj, list):

        for item in obj:
            results.extend(
                extract_numbers(item)
            )

    elif isinstance(obj, dict):

        for key in [
            "number",
            "numbers",
            "lottery_number",
            "lottery_numbers",
            "value",
        ]:

            if key in obj:

                results.extend(
                    extract_numbers(
                        obj[key]
                    )
                )

    elif isinstance(obj, str):

        text = obj.strip()

        if text:
            results.append(text)

    elif isinstance(obj, int):

        results.append(
            str(obj)
        )

    return results


def find_prize_numbers(
    data,
    keywords
):

    found = []

    def walk(obj):

        if isinstance(obj, dict):

            label_parts = []

            for key in [
                "name",
                "title",
                "label",
                "lottery_type",
                "reward_type",
                "type",
                "description",
            ]:

                if key in obj:

                    label_parts.append(
                        str(
                            obj[key]
                        ).lower()
                    )

            label = " ".join(
                label_parts
            )

            if any(
                keyword.lower() in label
                for keyword in keywords
            ):

                for key in [
                    "number",
                    "numbers",
                    "lottery_number",
                    "lottery_numbers",
                    "value",
                    "result",
                ]:

                    if key in obj:

                        nums = extract_numbers(
                            obj[key]
                        )

                        found.extend(
                            nums
                        )

            for value in obj.values():
                walk(value)

        elif isinstance(obj, list):

            for item in obj:
                walk(item)

    walk(data)

    unique = []

    for number in found:

        number = normalize_lottery_number(
            number
        )

        if (
            number
            and number not in unique
        ):
            unique.append(number)

    return unique


@st.cache_data(ttl=86400)
def get_lottery_by_date(
    draw_date
):

    date_string = draw_date.strftime(
        "%Y-%m-%d"
    )

    try:

        response = requests.get(
            GLO_API_URL,
            params={
                "date": date_string
            },
            timeout=15,
            headers={
                "User-Agent": "Mon101/1.0"
            }
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        return {
            "_error": str(e),
            "_date": date_string
        }


def parse_lottery_result(
    data,
    draw_date
):

    if not data:
        return None

    if isinstance(data, dict):

        if "_error" in data:

            return {
                "วันที่": draw_date,
                "รางวัลที่ 1": "",
                "เลขหน้า 3 ตัว": "",
                "เลขท้าย 3 ตัว": "",
                "เลขท้าย 2 ตัว": "",
                "_error": data["_error"],
            }

    first_prize = find_prize_numbers(
        data,
        [
            "รางวัลที่ 1",
            "รางวัลที่หนึ่ง",
            "first prize",
        ]
    )

    front_three = find_prize_numbers(
        data,
        [
            "เลขหน้า 3 ตัว",
            "เลขหน้า3ตัว",
            "front 3",
        ]
    )

    last_three = find_prize_numbers(
        data,
        [
            "เลขท้าย 3 ตัว",
            "เลขท้าย3ตัว",
            "last 3",
        ]
    )

    last_two = find_prize_numbers(
        data,
        [
            "เลขท้าย 2 ตัว",
            "เลขท้าย2ตัว",
            "last 2",
        ]
    )

    return {
        "วันที่": draw_date,
        "รางวัลที่ 1": " ".join(
            first_prize
        ),
        "เลขหน้า 3 ตัว": " ".join(
            front_three
        ),
        "เลขท้าย 3 ตัว": " ".join(
            last_three
        ),
        "เลขท้าย 2 ตัว": " ".join(
            last_two
        ),
    }


def generate_possible_draw_dates(year):

    dates = []

    for month in range(1, 13):

        dates.append(
            date(
                year,
                month,
                1
            )
        )

        dates.append(
            date(
                year,
                month,
                16
            )
        )

    return dates


def get_lottery_year(year):

    rows = []

    possible_dates = (
        generate_possible_draw_dates(
            year
        )
    )

    progress = st.progress(
        0,
        text=(
            f"กำลังตรวจสอบข้อมูลปี "
            f"{year + 543}"
        )
    )

    total = len(
        possible_dates
    )

    for index, draw_date in enumerate(
        possible_dates
    ):

        data = get_lottery_by_date(
            draw_date
        )

        result = parse_lottery_result(
            data,
            draw_date
        )

        if result:

            if (
                result.get("รางวัลที่ 1")
                or result.get("เลขท้าย 2 ตัว")
                or result.get("เลขหน้า 3 ตัว")
                or result.get("เลขท้าย 3 ตัว")
            ):

                rows.append(
                    result
                )

        progress.progress(
            int(
                (
                    (index + 1)
                    / total
                ) * 100
            ),
            text=(
                f"กำลังตรวจสอบ "
                f"{draw_date.strftime('%d/%m/%Y')}"
            )
        )

    progress.empty()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(
        rows
    )

    df = df.sort_values(
        "วันที่",
        ascending=False
    )

    df["วันที่"] = df[
        "วันที่"
    ].apply(
        lambda x:
        x.strftime(
            "%d/%m/%Y"
        )
    )

    return df.reset_index(
        drop=True
    )


# =========================================================
# HEADER
# =========================================================

show_logo()

st.markdown(
    '<div class="main-title">Mon101</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'ปฏิทิน • จันทรคติ • นักษัตร • '
    'ดาราศาสตร์ • เวลา • อากาศ • หวย • เพลง'
    '</div>',
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
# TAB 1 - DATE
# =========================================================

with tabs[0]:

    ce, be = get_be_ce(
        selected_date
    )

    weekday = thai_weekdays[
        selected_date.weekday()
    ]

    month_name = thai_months[
        selected_date.month
    ]

    st.markdown(
        f"""
        <div class="info-box">
            <div class="big-number">
                {selected_date.day}
                {month_name}
                {be}
            </div>

            <div style="
                text-align:center;
                font-size:20px;
            ">
                {weekday}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        3
    )

    with col1:

        st.metric(
            "ค.ศ.",
            ce
        )

    with col2:

        st.metric(
            "พ.ศ.",
            be
        )

    with col3:

        st.metric(
            "วันที่ของปี",
            selected_date.timetuple().tm_yday
        )


# =========================================================
# TAB 2 - LUNAR
# =========================================================

with tabs[1]:

    st.subheader(
        "🌙 ปฏิทินจันทรคติไทย"
    )

    lunar_date = (
        get_thai_lunar_date(
            selected_date
        )
    )

    st.markdown(
        f"""
        <div class="info-box">
            <div style="
                font-size:30px;
                font-weight:700;
                text-align:center;
            ">
                {lunar_date}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "คำนวณจากระบบปฏิทินจันทรคติไทย "
        "ผ่าน PyThaiNLP ไม่ใช้สูตรจำลองรอบดวงจันทร์"
    )


# =========================================================
# TAB 3 - ZODIAC
# =========================================================

with tabs[2]:

    st.subheader(
        "🐉 นักษัตรและราศี"
    )

    col1, col2 = st.columns(
        2
    )

    with col1:

        st.markdown(
            "### 🐉 นักษัตร"
        )

        zodiac = get_thai_zodiac(
            selected_date.year
        )

        st.markdown(
            f"""
            <div class="info-box">
                <div class="big-number">
                    {zodiac}
                </div>

                <div style="
                    text-align:center;
                ">
                    ปี ค.ศ.
                    {selected_date.year}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.caption(
            "ใช้ฟังก์ชัน Thai Zodiac "
            "ของ PyThaiNLP"
        )

    with col2:

        st.markdown(
            "### ☀️ ราศีตะวันตก"
        )

        western = get_western_zodiac(
            selected_date
        )

        western_thai = western.get(
            "thai",
            "ไม่ทราบ"
        )

        western_english = western.get(
            "english",
            "Unknown"
        )

        western_longitude = western.get(
            "longitude"
        )

        western_degree = western.get(
    
