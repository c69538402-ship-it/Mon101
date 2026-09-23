```python
from datetime import date, datetime, timedelta
import calendar
import os
import requests
import streamlit as st


# =========================================================
# ตั้งค่าหน้าเว็บ
# =========================================================

st.set_page_config(
    page_title="แอปปฏิทินอเนกประสงค์",
    page_icon="📅",
    layout="wide",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #666;
        margin-bottom: 20px;
    }

    .music-box {
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# โลโก้
# =========================================================

def show_logo():
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=80)


# =========================================================
# วัน / เดือน ภาษาไทย
# =========================================================

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


# =========================================================
# ปีนักษัตร
# =========================================================

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
    """
    คำนวณปีนักษัตรจาก พ.ศ.
    หมายเหตุ: ใช้รอบ 12 ปี ไม่ใช่การคำนวณวันขึ้นปีใหม่จีนแบบละเอียด
    """
    base_year = 2503
    index = (buddhist_year - base_year) % 12
    return naksat_list[index]


# =========================================================
# ราศีสากล
# =========================================================

def get_zodiac(day, month):

    zodiac_ranges = [
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

    for (sm, sd), (em, ed), name in zodiac_ranges:

        if (
            (month == sm and day >= sd)
            or
            (month == em and day <= ed)
        ):
            return name

    return "ราศีมังกร (Capricorn)"


# =========================================================
# ข้างขึ้น / ข้างแรม
# =========================================================

def get_lunar_phase(date_obj):
    """
    เวอร์ชันนี้ยังเป็นการประมาณจากรอบจันทร์ 29.53 วัน
    ไม่ใช่ข้อมูลจันทรคติจริง
    """

    known_new_moon = date(2026, 1, 18)

    diff = (date_obj - known_new_moon).days

    phase_day = diff % 29.530588

    if phase_day < 1:
        return "🌑 เดือนมืด / New Moon"

    elif phase_day < 7.4:
        return f"🌒 ข้างขึ้น ประมาณ {int(phase_day)} ค่ำ"

    elif phase_day < 8.4:
        return "🌓 ประมาณ 8 ค่ำ / First Quarter"

    elif phase_day < 14.8:
        return f"🌔 ข้างขึ้น ประมาณ {int(phase_day)} ค่ำ"

    elif phase_day < 15.8:
        return "🌕 วันเพ็ญ / Full Moon"

    elif phase_day < 22.1:
        return f"🌖 ข้างแรม ประมาณ {int(phase_day - 15)} ค่ำ"

    elif phase_day < 23.1:
        return "🌗 ประมาณแรม 8 ค่ำ / Last Quarter"

    else:
        return f"🌘 ข้างแรม ประมาณ {int(phase_day - 15)} ค่ำ"


# =========================================================
# เครื่องเล่นเพลง
# =========================================================

MUSIC_FOLDER = "music"


def get_music_files():
    """
    อ่านไฟล์เพลงจากโฟลเดอร์ music
    รองรับ mp3 / wav / ogg / m4a
    """

    if not os.path.exists(MUSIC_FOLDER):
        os.makedirs(MUSIC_FOLDER)

    supported = (
        ".mp3",
        ".wav",
        ".ogg",
        ".m4a",
    )

    files = []

    for filename in os.listdir(MUSIC_FOLDER):

        if filename.lower().endswith(supported):
            files.append(filename)

    return sorted(files)


def music_player():
    """
    เครื่องเล่นเพลงจากไฟล์ในโฟลเดอร์ music
    """

    st.subheader("🎵 เครื่องเล่นเพลง")

    music_files = get_music_files()

    if not music_files:

        st.info(
            "ยังไม่มีเพลงในระบบ\n\n"
            "ให้นำไฟล์ .mp3 ไปใส่ในโฟลเดอร์ music "
            "ที่อยู่ข้าง ๆ app.py"
        )

        return

    selected_song = st.selectbox(
        "เลือกเพลง",
        music_files,
        key="music_select",
    )

    song_path = os.path.join(
        MUSIC_FOLDER,
        selected_song,
    )

    st.audio(
        song_path,
        format="audio/mpeg",
    )

    st.caption(
        f"🎶 กำลังเลือกเพลง: {selected_song}"
    )


# =========================================================
# หน้าแรก
# =========================================================

st.markdown(
    '<div class="main-title">📅 แอปปฏิทินอเนกประสงค์</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-title">'
    "ระบบปฏิทิน • วัน • เดือน • นักษัตร • ราศี • อากาศ • เพลง"
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# Tabs
# =========================================================

tabs = st.tabs(
    [
        "🗓️ วันที่",
        "🌙 ข้างขึ้น/แรม & นักษัตร",
        "⭐ ราศี & พ.ศ./ค.ศ.",
        "🌍 เวลาโลก",
        "⛅ อากาศ",
        "⏪ ปฏิทินย้อนหลัง",
        "⚖️ เปรียบเทียบ 2 วัน",
        "✨ ค่าสมดุล 1.618",
        "🎵 เพลง",
    ]
)


# =========================================================
# TAB 1
# =========================================================

with tabs[0]:

    show_logo()

    st.subheader("1–3. ข้อมูลวันที่")

    selected_date = st.date_input(
        "เลือกวันที่",
        date.today(),
        key="main_date",
    )

    eng_day = selected_date.strftime("%A")

    day_name_th = days_th.get(
        eng_day,
        eng_day,
    )

    month_name_th = months_th[
        selected_date.month
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "1. วันที่",
        selected_date.day,
    )

    col2.metric(
        "2. วัน",
        day_name_th,
    )

    col3.metric(
        "3. เดือน",
        month_name_th,
    )


# =========================================================
# TAB 2
# =========================================================

with tabs[1]:

    show_logo()

    st.subheader(
        "4–5. ข้างขึ้น/ข้างแรม และปีนักษัตร"
    )

    b_year = selected_date.year + 543

    lunar = get_lunar_phase(
        selected_date
    )

    naksat = get_naksat(
        b_year
    )

    c1, c2 = st.columns(2)

    c1.info(
        f"**4. ข้างขึ้น / ข้างแรม**\n\n{lunar}"
    )

    c2.info(
        f"**5. ปีนักษัตร**\n\n{naksat}"
    )


# =========================================================
# TAB 3
# =========================================================

with tabs[2]:

    show_logo()

    st.subheader(
        "6–7. ปี พ.ศ. / ค.ศ. และราศี"
    )

    ce_year = selected_date.year

    be_year = ce_year + 543

    zodiac = get_zodiac(
        selected_date.day,
        selected_date.month,
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "6. ปี พ.ศ.",
        be_year,
    )

    c2.metric(
        "ปี ค.ศ.",
        ce_year,
    )

    c3.metric(
        "7. ราศี",
        zodiac,
    )


# =========================================================
# TAB 4
# =========================================================

with tabs[3]:

    show_logo()

    st.subheader(
        "8. เวลาท้องถิ่นของเครื่อง"
    )

    st.write(
        "เวลานี้อ่านจากเบราว์เซอร์ของผู้ใช้ "
        "จึงเป็นเวลาของอุปกรณ์ที่เปิดเว็บไซต์"
    )

    loc_html = """
    <div id="location-time"
         style="
         font-size:18px;
         font-weight:bold;
         padding:15px;
         background:#f0f2f6;
         border-radius:10px;
         ">
    </div>

    <script>

    function updateTime() {

        const now = new Date();

        const timeText =
            now.toLocaleString(
                'th-TH',
                {
                    dateStyle: 'full',
                    timeStyle: 'medium'
                }
            );

        const timezone =
            Intl.DateTimeFormat()
            .resolvedOptions()
            .timeZone;

        document.getElementById(
            'location-time'
        ).innerHTML =
            "🕒 " + timeText +
            "<br>🌍 Timezone: " +
            timezone;
    }

    updateTime();

    setInterval(
        updateTime,
        1000
    );

    </script>
    """

    st.components.v1.html(
        loc_html,
        height=100,
    )


# =========================================================
# TAB 5 — WEATHER
# =========================================================

with tabs[4]:

    show_logo()

    st.subheader(
        "9. พยากรณ์อากาศ"
    )

    city = st.text_input(
        "ชื่อเมืองหรือจังหวัด เช่น Bangkok หรือ Roi Et",
        value="Bangkok",
        key="weather_city",
    )

    if st.button(
        "🔍 ค้นหาอากาศ",
        key="weather_button",
    ):

        try:

            geo_url = (
                "https://geocoding-api.open-meteo.com/"
                f"v1/search?name={city}"
                "&count=1"
                "&language=th"
                "&format=json"
            )

            geo_res = requests.get(
                geo_url,
                timeout=10,
            )

            geo_res.raise_for_status()

            geo_data = geo_res.json()

            if not geo_data.get("results"):

                st.error(
                    "ไม่พบเมืองที่ค้นหา"
                )

            else:

                location = geo_data[
                    "results"
                ][0]

                lat = location[
                    "latitude"
                ]

                lon = location[
                    "longitude"
                ]

                country = location.get(
                    "country",
                    "",
                )

                weather_url = (
                    "https://api.open-meteo.com/"
                    "v1/forecast?"
                    f"latitude={lat}"
                    f"&longitude={lon}"
                    "&current=temperature_2m,"
                    "relative_humidity_2m,"
                    "wind_speed_10m,"
                    "weather_code"
                    "&timezone=auto"
                )

                weather_res = requests.get(
                    weather_url,
                    timeout=10,
                )

                weather_res.raise_for_status()

                weather_data = (
                    weather_res.json()
                )

                current = weather_data[
                    "current"
                ]

                st.success(
                    f"📍 {location.get('name', city)} "
                    f"({country})"
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "🌡️ อุณหภูมิ",
                    f"{current['temperature_2m']} °C",
                )

                c2.metric(
                    "💧 ความชื้น",
                    f"{current['relative_humidity_2m']} %",
                )

                c3.metric(
                    "💨 ความเร็วลม",
                    f"{current['wind_speed_10m']} km/h",
                )

                st.caption(
                    f"พิกัด: {lat}, {lon}"
                )

        except requests.RequestException as e:

            st.error(
                f"เชื่อมต่อบริการอากาศไม่ได้: {e}"
            )

        except Exception as e:

            st.error(
                f"เกิดข้อผิดพลาด: {e}"
            )


# =========================================================
# TAB 6
# =========================================================

with tabs[5]:

    show_logo()

    st.subheader(
        "10. ปฏิทินย้อนหลัง / ล่วงหน้า"
    )

    col_y, col_m = st.columns(2)

    with col_y:

        target_year = st.number_input(
            "เลือกปี ค.ศ.",
            min_value=1900,
            max_value=2100,
            value=date.today().year,
            step=1,
        )

    with col_m:

        target_month = st.selectbox(
            "เลือกเดือน",
            range(1, 13),
            format_func=lambda x:
                months_th[x],
            index=date.today().month - 1,
        )

    st.write(
        f"### {months_th[target_month]} "
        f"พ.ศ. {target_year + 543}"
    )

    cal_text = calendar.month(
        target_year,
        target_month,
    )

    st.code(
        cal_text,
        language="text",
    )


# =========================================================
# TAB 7 — เปรียบเทียบ 2 วัน
# =========================================================

with tabs[6]:

    show_logo()

    st.subheader(
        "⚖️ เปรียบเทียบรายละเอียด 2 วัน"
    )

    col_d1, col_d2 = st.columns(2)

    with col_d1:

        date_a = st.date_input(
            "เลือกวันที่ 1",
            date.today(),
            key="compare_a",
        )

    with col_d2:

        date_b = st.date_input(
            "เลือกวันที่ 2",
            date.today() + timedelta(days=7),
            key="compare_b",
        )

    diff_days = abs(
        (date_b - date_a).days
    )

    st.info(
        f"📌 ห่างกัน **{diff_days} วัน** "
        f"หรือประมาณ "
        f"**{round(diff_days / 7, 1)} สัปดาห์**"
    )

    col_res1, col_res2 = st.columns(2)

    for col, selected, label in [
        (col_res1, date_a, "วันที่ 1"),
        (col_res2, date_b, "วันที่ 2"),
    ]:

        with col:

            st.markdown(
                f"### {label}: "
                f"{selected.strftime('%d/%m/%Y')}"
            )

            st.write(
                f"**วัน:** "
                f"{days_th[selected.strftime('%A')]} "
                f"{months_th[selected.month]} "
                f"{selected.year + 543}"
            )

            st.write(
                f"**ข้างขึ้น/แรม:** "
                f"{get_lunar_phase(selected)}"
            )

            st.write(
                f"**ราศี:** "
                f"{get_zodiac(selected.day, selected.month)}"
            )

            st.write(
                f"**นักษัตร:** "
                f"{get_naksat(selected.year + 543)}"
            )


# =========================================================
# TAB 8 — GOLDEN RATIO
# =========================================================

with tabs[7]:

    show_logo()

    st.subheader(
        "✨ ค่าสัดส่วน 1.618"
    )

    st.warning(
        "หมายเหตุ: ส่วนนี้เป็นการคำนวณเชิงคณิตศาสตร์ "
        "ที่สร้างขึ้นจากเลข 1.618 ไม่ใช่เครื่องมือทางวิทยาศาสตร์ "
        "สำหรับวัดพลังงาน โชค หรือความกลมกลืนของชีวิต"
    )

    golden_date = st.date_input(
        "เลือกวันที่",
        date.today(),
        key="golden_date",
    )

    day_of_year = (
        golden_date.timetuple().tm_yday
    )

    total_days = (
        366
        if calendar.isleap(
            golden_date.year
        )
        else 365
    )

    golden_ratio = 1.618033988749895

    golden_position = (
        total_days / golden_ratio
    )

    distance = abs(
        day_of_year - golden_position
    )

    harmony_score = max(
        0,
        100 - (
            distance / total_days * 100
        ),
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "📅 วันที่ในรอบปี",
        f"{day_of_year}/{total_days}",
    )

    c2.metric(
        "📐 Golden Ratio",
        "1.6180339887",
    )

    c3.metric(
        "📊 ตำแหน่ง 1.618 ของปี",
        f"{golden_position:.2f}",
    )

    st.metric(
        "✨ ค่าความใกล้เคียงเชิงคณิตศาสตร์",
        f"{harmony_score:.2f}%",
    )


# =========================================================
# TAB 9 — MUSIC PLAYER
# =========================================================

with tabs[8]:

    show_logo()

    st.subheader(
        "🎵 เครื่องเล่นเพลง"
    )

    st.write(
        "เพลงจะถูกอ่านจากโฟลเดอร์ `music` "
        "ที่อยู่ระดับเดียวกับ `app.py`"
    )

    music_player()

    st.markdown("---")

    st.caption(
        "รองรับไฟล์ .mp3, .wav, .ogg และ .m4a"
    )
```

### โครงสร้างโฟลเดอร์

ให้จัดไฟล์ประมาณนี้ครับ

```text
โปรเจกต์/
│
├── app.py
├── logo.jpg
│
└── music/
    ├── เพลงที่หนึ่ง.mp3
    ├── เพลงที่สอง.mp3
    ├── เพลงที่สาม.mp3
    └── เพลงที่สี่.mp3
```

จากนั้นรัน:

```bash
streamlit run app.py
```

แล้วเข้าแท็บ **🎵 เพลง** ก็จะเห็นรายชื่อเพลงที่อยู่ใน `music/` และกดเล่นได้ทันที

**ส่วนสำคัญ:** เครื่องเล่นนี้ไม่ได้ดึงเพลงจาก YouTube หรือเว็บภายนอก แต่ **ดึงไฟล์เพลงจากโฟลเดอร์ `music` ในโปรเจกต์โดยตรง** ซึ่งเหมาะกับการทำแอปส่วนตัวและไม่ต้องพึ่ง API เพลงครับ

ถ้าคุณหมายถึง **“ให้หน้า `app.py` ดึงเพลงจากหน้า `.py` อีกไฟล์หนึ่ง”** เช่นมี `music.py` ที่เก็บรายชื่อ/ข้อมูลเพลง หรืออยากให้ **ค้นหาเพลงจากอินเทอร์เน็ตแล้วเล่นในแอป** แบบนั้นโครงสร้างจะต่างออกไปเล็กน้อยครับ
    
