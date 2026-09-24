import os
import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import streamlit as st
import requests


# =========================================================
# Mon101
# =========================================================

st.set_page_config(
    page_title="Mon101",
    page_icon="📅",
    layout="wide",
)


# =========================================================
# CONFIG
# =========================================================

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BANGKOK = ZoneInfo("Asia/Bangkok")

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

WORLD_ZONES = {
    "ประเทศไทย": "Asia/Bangkok",
    "ญี่ปุ่น": "Asia/Tokyo",
    "จีน": "Asia/Shanghai",
    "สิงคโปร์": "Asia/Singapore",
    "อินเดีย": "Asia/Kolkata",
    "อังกฤษ": "Europe/London",
    "ฝรั่งเศส": "Europe/Paris",
    "นิวยอร์ก": "America/New_York",
    "ลอสแอนเจลิส": "America/Los_Angeles",
}


# =========================================================
# FUNCTIONS
# =========================================================

def thai_date_text(dt):
    month = THAI_MONTHS[dt.month - 1]
    year = dt.year + 543
    return f"{dt.day} {month} {year}"


def weekday_thai(dt):
    return THAI_DAYS[dt.weekday()]


def get_western_zodiac(year, month, day):
    try:
        import ephem

        local_dt = datetime(
            year,
            month,
            day,
            12,
            tzinfo=BANGKOK,
        )

        utc_dt = local_dt.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

        sun = ephem.Sun(utc_dt)
        ecliptic = ephem.Ecliptic(sun)

        longitude = (
            math.degrees(float(ecliptic.lon)) % 360
        )

        signs = [
            ("เมษ", 0, 30),
            ("พฤษภ", 30, 60),
            ("เมถุน", 60, 90),
            ("กรกฎ", 90, 120),
            ("สิงห์", 120, 150),
            ("กันย์", 150, 180),
            ("ตุล", 180, 210),
            ("พิจิก", 210, 240),
            ("ธนู", 240, 270),
            ("มังกร", 270, 300),
            ("กุมภ์", 300, 330),
            ("มีน", 330, 360),
        ]

        for name, low, high in signs:
            if low <= longitude < high:
                return name, longitude

        return "มีน", longitude

    except Exception:
        return None, None


def get_chinese_zodiac(year):
    animals = [
        "ชวด",
        "ฉลู",
        "ขาล",
        "เถาะ",
        "มะโรง",
        "มะเส็ง",
        "มะเมีย",
        "มะแม",
        "วอก",
        "ระกา",
        "จอ",
        "กุน",
    ]

    return animals[(year - 4) % 12]


# =========================================================
# HEADER
# =========================================================

st.title("Mon101")

st.caption(
    "ปฏิทิน • จันทรคติ • นักษัตร • ราศี • เวลาโลก • "
    "อากาศ • ปฏิทิน • เปรียบเทียบวันที่ • "
    "Golden Ratio • เพลง • หวยรัฐบาล"
)


# =========================================================
# TABS
# =========================================================

(
    tab1,
    tab2,
    tab3,
    tab4,
    tab5,
    tab6,
    tab7,
    tab8,
    tab9,
    tab10,
) = st.tabs(
    [
        "1 วันที่",
        "2 จันทรคติ",
        "3 นักษัตร / ราศี",
        "4 เวลาโลก",
        "5 อากาศ",
        "6 ปฏิทิน",
        "7 เปรียบเทียบวันที่",
        "8 Golden Ratio",
        "9 เพลง",
        "10 หวยรัฐบาล",
    ]
)


# =========================================================
# TAB 1 : วันที่
# =========================================================

with tab1:

    st.header("📅 วันที่")

    now = datetime.now(BANGKOK)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "วัน",
            weekday_thai(now),
        )

    with col2:
        st.metric(
            "วันที่",
            str(now.day),
        )

    with col3:
        st.metric(
            "เวลา",
            now.strftime("%H:%M:%S"),
        )

    st.divider()

    st.subheader("วันที่ปัจจุบัน")

    st.write(
        thai_date_text(now)
    )

    st.write(
        f"ค.ศ. {now.year}"
    )

    st.write(
        f"พ.ศ. {now.year + 543}"
    )

    st.caption(
        now.strftime(
            "%d/%m/%Y %H:%M:%S"
        )
    )


# =========================================================
# TAB 2 : จันทรคติ
# =========================================================

with tab2:

    st.header("🌙 จันทรคติ")

    now = datetime.now(BANGKOK)

    try:

        from pythainlp.util import to_lunar_date

        lunar = to_lunar_date(
            now.date()
        )

        st.subheader(
            "วันที่จันทรคติ"
        )

        st.write(lunar)

        st.caption(
            "ข้อมูลจันทรคติจาก PyThaiNLP"
        )

    except Exception as e:

        st.warning(
            "ยังไม่สามารถอ่านข้อมูลจันทรคติได้"
        )

        st.caption(
            str(e)
        )


# =========================================================
# TAB 3 : นักษัตร / ราศี
# =========================================================

with tab3:

    st.header("🐉 นักษัตร / ♈ ราศี")

    now = datetime.now(BANGKOK)

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "นักษัตร"
        )

        animal = get_chinese_zodiac(
            now.year
        )

        st.metric(
            "ปีนักษัตร",
            animal
        )

        st.write(
            f"พ.ศ. {now.year + 543}"
        )

    with col2:

        st.subheader(
            "ราศีตะวันตก"
        )

        sign, degree = get_western_zodiac(
            now.year,
            now.month,
            now.day,
        )

        if sign:

            st.metric(
                "ราศี",
                sign
            )

            st.write(
                f"ตำแหน่งดวงอาทิตย์ประมาณ "
                f"{degree:.2f}°"
            )

        else:

            st.warning(
                "ไม่สามารถคำนวณราศีตะวันตกได้"
            )


# =========================================================
# TAB 4 : เวลาโลก
# =========================================================

with tab4:

    st.header("🌍 เวลาโลก")

    now_utc = datetime.now(
        timezone.utc
    )

    rows = []

    for country, zone_name in WORLD_ZONES.items():

        local = now_utc.astimezone(
            ZoneInfo(zone_name)
        )

        rows.append(
            {
                "สถานที่": country,
                "เขตเวลา": zone_name,
                "เวลา": local.strftime(
                    "%H:%M:%S"
                ),
                "วันที่": local.strftime(
                    "%d/%m/%Y"
                ),
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# TAB 5 : อากาศ
# =========================================================

with tab5:

    st.header("☁️ อากาศ")

    st.write(
        "ค้นหาเมืองเพื่อดูข้อมูลอากาศ"
    )

    city = st.text_input(
        "ชื่อเมือง",
        value="Udon Thani",
        key="weather_city",
    )

    if st.button(
        "ตรวจอากาศ",
        key="weather_button",
    ):

        try:

            geo_url = (
                "https://geocoding-api.open-meteo.com/v1/search"
            )

            geo_params = {
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json",
            }

            geo_response = requests.get(
                geo_url,
                params=geo_params,
                timeout=15,
            )

            geo_response.raise_for_status()

            geo_data = geo_response.json()

            results = geo_data.get(
                "results",
                []
            )

            if not results:

                st.error(
                    "ไม่พบเมืองนี้"
                )

            else:

                place = results[0]

                latitude = place[
                    "latitude"
                ]

                longitude = place[
                    "longitude"
                ]

                place_name = place.get(
                    "name",
                    city
                )

                country = place.get(
                    "country",
                    ""
                )

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
                        "wind_speed_10m,"
                        "weather_code"
                    ),
                    "timezone": "auto",
                }

                weather_response = requests.get(
                    weather_url,
                    params=weather_params,
                    timeout=15,
                )

                weather_response.raise_for_status()

                weather_data = (
                    weather_response.json()
                )

                current = weather_data.get(
                    "current",
                    {}
                )

                st.subheader(
                    f"{place_name}, {country}"
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "อุณหภูมิ",
                        f"{current.get('temperature_2m', '-')} °C",
                    )

                with col2:
                    st.metric(
                        "รู้สึกเหมือน",
                        f"{current.get('apparent_temperature', '-')} °C",
                    )

                with col3:
                    st.metric(
                        "ความชื้น",
                        f"{current.get('relative_humidity_2m', '-')} %",
                    )

                st.write(
                    "ความเร็วลม: "
                    f"{current.get('wind_speed_10m', '-')} km/h"
                )

                st.caption(
                    "อัปเดต: "
                    f"{current.get('time', '-')}"
                )

        except Exception as e:

            st.error(
                "ดึงข้อมูลอากาศไม่สำเร็จ"
            )

            st.caption(
                str(e)
            )


# =========================================================
# TAB 6 : ปฏิทิน
# =========================================================

with tab6:

    st.header("🗓️ ปฏิทิน")

    selected = st.date_input(
        "เลือกวันที่",
        value=datetime.now(
            BANGKOK
        ).date(),
        key="calendar_date",
    )

    selected_dt = datetime(
        selected.year,
        selected.month,
        selected.day,
        tzinfo=BANGKOK,
    )

    st.subheader(
        thai_date_text(
            selected_dt
        )
    )

    st.write(
        f"วัน{weekday_thai(selected_dt)}"
    )

    st.write(
        f"ค.ศ. {selected.year}"
    )

    st.write(
        f"พ.ศ. {selected.year + 543}"
    )


# =========================================================
# TAB 7 : เปรียบเทียบวันที่
# =========================================================

with tab7:

    st.header("🔎 เปรียบเทียบวันที่")

    today = datetime.now(
        BANGKOK
    ).date()

    date1 = st.date_input(
        "วันที่ 1",
        value=today,
        key="compare_date_1",
    )

    date2 = st.date_input(
        "วันที่ 2",
        value=today,
        key="compare_date_2",
    )

    difference = (
        date2 - date1
    ).days

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "วันที่ 1",
            thai_date_text(
                datetime(
                    date1.year,
                    date1.month,
                    date1.day,
                )
            ),
        )

    with col2:

        st.metric(
            "วันที่ 2",
            thai_date_text(
                datetime(
                    date2.year,
                    date2.month,
                    date2.day,
                )
            ),
        )

    with col3:

        st.metric(
            "จำนวนวัน",
            str(abs(difference)),
        )

    st.divider()

    if difference > 0:

        st.info(
            f"วันที่ 2 อยู่หลังวันที่ 1 "
            f"{difference} วัน"
        )

    elif difference < 0:

        st.info(
            f"วันที่ 2 อยู่ก่อนวันที่ 1 "
            f"{abs(difference)} วัน"
        )

    else:

        st.success(
            "เป็นวันเดียวกัน"
        )


# =========================================================
# TAB 8 : GOLDEN RATIO
# =========================================================

with tab8:

    st.header("🌀 Golden Ratio")

    phi = (
        1 + math.sqrt(5)
    ) / 2

    st.subheader(
        "ค่ามาตรฐาน Golden Ratio"
    )

    st.metric(
        "φ (Phi)",
        f"{phi:.10f}",
    )

    st.write(
        "ค่าประมาณ: 1.618"
    )

    st.divider()

    number = st.number_input(
        "ใส่ตัวเลข",
        value=100.0,
        key="golden_number",
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            "คูณ Golden Ratio"
        )

        st.success(
            f"{number * phi:.10f}"
        )

    with col2:

        st.write(
            "หาร Golden Ratio"
        )

        st.info(
            f"{number / phi:.10f}"
        )

    st.divider()

    st.write(
        "Golden Ratio = 1.6180339887..."
    )

    st.write(
        "สูตร φ = (1 + √5) / 2"
    )


# =========================================================
# TAB 9 : เพลง
# =========================================================

with tab9:

    st.header("🎵 เพลง")

    extensions = (
        ".mp3",
        ".wav",
        ".ogg",
        ".m4a",
        ".aac",
    )

    music_files = []

    try:

        for filename in sorted(
            os.listdir(APP_DIR)
        ):

            full_path = os.path.join(
                APP_DIR,
                filename,
            )

            if (
                os.path.isfile(full_path)
                and filename.lower().endswith(
                    extensions
                )
            ):

                music_files.append(
                    filename
                )

    except Exception as e:

        st.error(
            "ไม่สามารถอ่านไฟล์เพลงได้"
        )

        st.caption(
            str(e)
        )

    if music_files:

        st.success(
            f"พบไฟล์เพลง {len(music_files)} ไฟล์"
        )

        for index, filename in enumerate(
            music_files,
            start=1,
        ):

            st.subheader(
                f"{index}. {filename}"
            )

            try:

                with open(
                    os.path.join(
                        APP_DIR,
                        filename,
                    ),
                    "rb",
                ) as audio_file:

                    st.audio(
                        audio_file.read()
                    )

            except Exception as e:

                st.warning(
                    f"เปิดเพลงไม่ได้: {filename}"
                )

                st.caption(
                    str(e)
                )

    else:

        st.info(
            "ยังไม่พบไฟล์เพลง"
        )

        st.write(
            "ให้นำไฟล์ .mp3 หรือ .wav "
            "มาไว้โฟลเดอร์เดียวกับ app.py"
        )

        st.code(
            "app.py\n"
            "4ทิศ.mp3\n"
            "เพลงอื่น.mp3"
        )


# =========================================================
# TAB 10 : หวยรัฐบาล
# =========================================================

# =========================================================
# TAB 10 : หวยรัฐบาล
# =========================================================

with tab10:

    st.header("🎟️ หวยรัฐบาล")

    st.subheader("📊 ผลสลากกินแบ่งรัฐบาล")

    st.write(
        "ค้นหาผลรางวัลย้อนหลังจากข้อมูลของสำนักงานสลากกินแบ่งรัฐบาล"
    )

    st.divider()

    # -----------------------------------------------------
    # เลือกวันที่
    # -----------------------------------------------------

    lottery_date = st.date_input(
        "เลือกวันที่ออกรางวัล",
        value=datetime.now(BANGKOK).date(),
        key="lottery_date",
    )

    date_text = lottery_date.strftime("%Y-%m-%d")

    if st.button(
        "🔎 ค้นหาผลรางวัล",
        key="lottery_search_button",
        use_container_width=True,
    ):

        st.info(
            f"กำลังค้นหาผลรางวัลวันที่ {lottery_date.strftime('%d/%m/%Y')}"
        )

        # -------------------------------------------------
        # GLO API
        # -------------------------------------------------

        api_urls = [
            "https://api.glo.or.th/utility/lottery-result",
            "https://www.glo.or.th/api/lottery/getLotteryResult",
        ]

        result = None
        last_error = ""

        for api_url in api_urls:

            try:

                response = requests.get(
                    api_url,
                    params={
                        "date": date_text
                    },
                    timeout=15,
                    headers={
                        "User-Agent": "Mozilla/5.0"
                    },
                )

                if response.status_code == 200:

                    try:
                        result = response.json()
                    except Exception:
                        result = response.text

                    break

                last_error = (
                    f"{response.status_code} "
                    f"จาก {api_url}"
                )

            except Exception as e:

                last_error = str(e)

        # -------------------------------------------------
        # แสดงผล
        # -------------------------------------------------

        if result is not None:

            st.success(
                "พบข้อมูลจากระบบ GLO"
            )

            if isinstance(result, dict):

                st.json(result)

            elif isinstance(result, list):

                st.dataframe(
                    result,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.code(
                    str(result)
                )

        else:

            st.warning(
                "ระบบ API ของ GLO ไม่ตอบข้อมูลโดยตรงในขณะนี้"
            )

            st.caption(
                f"รายละเอียด: {last_error}"
            )

            st.info(
                "สามารถตรวจสอบข้อมูลผลรางวัลจากฐานข้อมูล "
                "สำนักงานสลากกินแบ่งรัฐบาลได้โดยตรง"
            )

    # -----------------------------------------------------
    # ข้อมูลย้อนหลัง
    # -----------------------------------------------------

    st.divider()

    st.subheader("📚 ผลย้อนหลัง 12 ปี")

    current_year = datetime.now(
        BANGKOK
    ).year

    start_year = current_year - 12

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "เริ่มต้น",
            f"พ.ศ. {start_year + 543}",
        )

    with col2:

        st.metric(
            "ถึงปัจจุบัน",
            f"พ.ศ. {current_year + 543}",
        )

    st.write(
        "สำนักงานสลากกินแบ่งรัฐบาลมีชุดข้อมูล "
        "ผลการออกรางวัลและข้อมูลสถิติย้อนหลัง"
    )

    st.link_button(
        "🏛️ เปิดฐานข้อมูล GLO",
        "https://gdcatalog.glo.or.th/th/dataset/dataset_c4-9_01",
        use_container_width=True,
    )

    st.divider()

    # -----------------------------------------------------
    # สถิติเลขรางวัล
    # -----------------------------------------------------

    st.subheader("🔢 ตรวจเลขสลาก")

    lottery_number = st.text_input(
        "กรอกเลขสลาก 6 หลัก",
        max_chars=6,
        key="lottery_number",
    )

    if lottery_number:

        if (
            lottery_number.isdigit()
            and len(lottery_number) == 6
        ):

            st.write(
                f"เลขที่กรอก: **{lottery_number}**"
            )

            st.write(
                "ระบบสามารถนำเลขนี้ไปตรวจย้อนหลัง "
                "เมื่อเชื่อมต่อฐานข้อมูลผลรางวัลได้"
            )

        else:

            st.warning(
                "กรุณากรอกตัวเลข 6 หลัก"
            )

    st.divider()

    st.caption(
        "แหล่งข้อมูลหลัก: สำนักงานสลากกินแบ่งรัฐบาล"
    )

    st.caption(
        "ข้อมูลย้อนหลังใช้สำหรับตรวจสอบผลในอดีต "
        "ไม่ใช่การทำนายผลรางวัลในอนาคต"
            )

        

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Mon101 | ปฏิทินและข้อมูลวันที่"
            )
