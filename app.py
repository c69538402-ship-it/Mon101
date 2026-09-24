import os
import re
import math
from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo

import requests
import streamlit as st

st.set_page_config(
    page_title="Mon101",
    page_icon="📅",
    layout="wide",
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BANGKOK = ZoneInfo("Asia/Bangkok")
LOGO_PATH = os.path.join(APP_DIR, "logo.jpg")


def show_logo():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.warning("ไม่พบไฟล์ logo.jpg ในโฟลเดอร์เดียวกับ app.py")


THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
    "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
    "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

THAI_DAYS = [
    "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี",
    "ศุกร์", "เสาร์", "อาทิตย์",
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

LOTTO_TREE_URL = (
    "https://api.github.com/repos/"
    "vicha-w/thai-lotto-archive/git/trees/master?recursive=1"
)
LOTTO_RAW_BASE = (
    "https://raw.githubusercontent.com/"
    "vicha-w/thai-lotto-archive/master/"
)


def thai_date_text(dt):
    return (
        f"{dt.day} {THAI_MONTHS[dt.month - 1]} "
        f"{dt.year + 543}"
    )


def weekday_thai(dt):
    return THAI_DAYS[dt.weekday()]


def get_western_zodiac(year, month, day):
    try:
        import ephem

        local_dt = datetime(
            year, month, day, 12, tzinfo=BANGKOK
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
        "ชวด", "ฉลู", "ขาล", "เถาะ",
        "มะโรง", "มะเส็ง", "มะเมีย", "มะแม",
        "วอก", "ระกา", "จอ", "กุน",
    ]
    return animals[(year - 4) % 12]


@st.cache_data(ttl=86400, show_spinner=False)
def get_lottery_file_list():
    response = requests.get(
        LOTTO_TREE_URL,
        timeout=30,
        headers={"User-Agent": "Mon101"},
    )
    response.raise_for_status()

    data = response.json()

    paths = []
    for item in data.get("tree", []):
        path = item.get("path", "")
        if re.fullmatch(
            r"lottonumbers/\d{4}-\d{2}-\d{2}\.txt",
            path,
        ):
            paths.append(path)

    return sorted(paths, reverse=True)


def parse_lottery_text(text, filename):
    result = {
        "date": filename.replace(
            "lottonumbers/", ""
        ).replace(".txt", ""),
        "first": "",
        "front3": [],
        "back3": [],
        "back2": "",
    }

    labels = {
        "FIRST": "first",
        "THREE_FIRST": "front3",
        "THREE_LAST": "back3",
        "TWO": "back2",
    }

    for raw_line in text.splitlines():
        line = raw_line.strip()

        for label, key in labels.items():
            if line.startswith(label):
                values = re.findall(
                    r"\d{2,6}",
                    line[len(label):],
                )

                if key in ("front3", "back3"):
                    result[key].extend(values)
                elif values:
                    result[key] = values[0]

                break

    return result


@st.cache_data(ttl=86400, show_spinner=False)
def get_lottery_history(start_date, end_date):
    paths = get_lottery_file_list()
    selected = []

    for path in paths:
        filename = path.split("/")[-1]
        match = re.fullmatch(
            r"(\d{4})-(\d{2})-(\d{2})\.txt",
            filename,
        )

        if not match:
            continue

        y, m, d = map(int, match.groups())

        try:
            draw_date = date(y, m, d)
        except ValueError:
            continue

        if start_date <= draw_date <= end_date:
            selected.append((path, draw_date))

    rows = []

    for path, draw_date in selected:
        try:
            response = requests.get(
                LOTTO_RAW_BASE + path,
                timeout=20,
                headers={"User-Agent": "Mon101"},
            )
            response.raise_for_status()

            parsed = parse_lottery_text(
                response.text,
                path,
            )

            rows.append(
                {
                    "วันที่": draw_date.strftime("%d/%m/%Y"),
                    "พ.ศ.": str(draw_date.year + 543),
                    "รางวัลที่ 1": parsed["first"],
                    "เลขหน้า 3 ตัว": ", ".join(parsed["front3"]),
                    "เลขท้าย 3 ตัว": ", ".join(parsed["back3"]),
                    "เลขท้าย 2 ตัว": parsed["back2"],
                    "_date": draw_date,
                }
            )

        except Exception:
            continue

    rows.sort(
        key=lambda x: x["_date"],
        reverse=True,
    )
    return rows


FOREIGN_LOTTERY_URLS = {
    "lao": "https://lotto.thaiorc.com/lao/last3/stats-years1.php?pg={page}",
    "hanoi": "https://lotto.thaiorc.com/hanoi/stats/lottery-years1.php?pg={page}",
}


def _clean_number(value, width=None):
    text = str(value).strip()
    if text.lower() in ("nan", "none", ""):
        return ""
    text = re.sub(r"[^0-9]", "", text)
    if width and text:
        text = text.zfill(width)
    return text


def _find_result_table(html):
    try:
        tables = __import__("pandas").read_html(html)
    except Exception:
        return None

    for table in tables:
        columns = [str(c).strip() for c in table.columns]
        joined = " | ".join(columns)
        if "งวดวันที่" in joined and len(table) >= 5:
            table.columns = columns
            return table
    return None


def _parse_foreign_page(html, kind):
    table = _find_result_table(html)
    if table is None:
        return []

    rows = []
    for _, row in table.iterrows():
        data = {str(k).strip(): row[k] for k in table.columns}
        raw_date = str(data.get("งวดวันที่", ""))
        match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw_date)
        if not match:
            continue

        day, month, buddhist_year = map(int, match.groups())
        try:
            draw_date = date(buddhist_year - 543, month, day)
        except ValueError:
            continue

        if kind == "lao":
            rows.append({
                "วันที่": draw_date.strftime("%d/%m/%Y"),
                "พ.ศ.": str(draw_date.year + 543),
                "เลข 6 ตัว": _clean_number(data.get("เลข 6 ตัว", ""), 6),
                "เลข 3 ตัวบน": _clean_number(data.get("เลข 3 ตัวบน", ""), 3),
                "เลข 2 ตัวบน": _clean_number(data.get("เลข 2 ตัวบน", ""), 2),
                "เลข 2 ตัวล่าง": _clean_number(data.get("เลข 2 ตัวล่าง", ""), 2),
                "_date": draw_date,
            })
        else:
            rows.append({
                "วันที่": draw_date.strftime("%d/%m/%Y"),
                "พ.ศ.": str(draw_date.year + 543),
                "รางวัลพิเศษ": _clean_number(data.get("รางวัลพิเศษ", ""), 5),
                "รางวัลที่ 1": _clean_number(data.get("รางวัลที่ 1", ""), 5),
                "เลข 3 ตัวบน": _clean_number(data.get("เลข 3 ตัวบน", ""), 3),
                "เลข 2 ตัวล่าง": _clean_number(data.get("เลข 2 ตัวล่าง", ""), 2),
                "_date": draw_date,
            })

    return rows


@st.cache_data(ttl=3600, show_spinner=False)
def get_foreign_lottery_history(kind):
    today_date = datetime.now(BANGKOK).date()
    start_date = today_date - timedelta(days=365)
    all_rows = {}
    consecutive_empty = 0

    for page in range(1, 21):
        url = FOREIGN_LOTTERY_URLS[kind].format(page=page)
        try:
            response = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0 Mon101"
                },
            )
            response.raise_for_status()
            page_rows = _parse_foreign_page(response.text, kind)
        except Exception:
            page_rows = []

        if not page_rows:
            consecutive_empty += 1
            if consecutive_empty >= 2:
                break
            continue

        consecutive_empty = 0
        for row in page_rows:
            draw_date = row["_date"]
            if start_date <= draw_date <= today_date:
                all_rows[draw_date.isoformat()] = row

        oldest = min(row["_date"] for row in page_rows)
        if oldest < start_date:
            break

    rows = sorted(
        all_rows.values(),
        key=lambda x: x["_date"],
        reverse=True,
    )
    return rows


now = datetime.now(BANGKOK)

st.title("Mon101")
st.caption(
    "ปฏิทิน • จันทรคติ • นักษัตร • ราศี • เวลาโลก • "
    "อากาศ • ปฏิทิน • เปรียบเทียบวันที่ • Golden Ratio • "
    "เพลง • หวยรัฐบาล • หวยลาว • หวยฮานอย"
)

(
    tab1, tab2, tab3, tab4, tab5,
    tab6, tab7, tab8, tab9, tab10, tab11, tab12
) = st.tabs([
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
    "11 หวยลาว",
    "12 หวยฮานอย",
])


with tab1:
    show_logo()
    st.header("📅 วันที่")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("วัน", weekday_thai(now))

    with col2:
        st.metric("วันที่", str(now.day))

    with col3:
        st.metric("เวลา", now.strftime("%H:%M:%S"))

    st.divider()
    st.subheader("วันที่ปัจจุบัน")
    st.write(thai_date_text(now))
    st.write(f"ค.ศ. {now.year}")
    st.write(f"พ.ศ. {now.year + 543}")


with tab2:
    show_logo()
    st.header("🌙 จันทรคติ")

    try:
        from pythainlp.util import to_lunar_date

        lunar = to_lunar_date(now.date())

        st.subheader("วันที่จันทรคติ")
        st.write(lunar)

    except Exception as e:
        st.warning("ยังไม่สามารถอ่านข้อมูลจันทรคติได้")
        st.caption(str(e))


with tab3:
    show_logo()
    st.header("🐉 นักษัตร / ♈ ราศี")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("นักษัตร")
        st.metric(
            "ปีนักษัตร",
            get_chinese_zodiac(now.year),
        )
        st.write(f"พ.ศ. {now.year + 543}")

    with col2:
        st.subheader("ราศีตะวันตก")

        sign, degree = get_western_zodiac(
            now.year,
            now.month,
            now.day,
        )

        if sign:
            st.metric("ราศี", sign)
            st.write(
                f"ตำแหน่งดวงอาทิตย์ประมาณ {degree:.2f}°"
            )
        else:
            st.warning("ไม่สามารถคำนวณราศีได้")


with tab4:
    show_logo()
    st.header("🌍 เวลาโลก")

    now_utc = datetime.now(timezone.utc)
    rows = []

    for country, zone_name in WORLD_ZONES.items():
        local = now_utc.astimezone(
            ZoneInfo(zone_name)
        )

        rows.append({
            "สถานที่": country,
            "เขตเวลา": zone_name,
            "วันที่": local.strftime("%d/%m/%Y"),
            "เวลา": local.strftime("%H:%M:%S"),
        })

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )


with tab5:
    show_logo()
    st.header("☁️ อากาศ")

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
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": city,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
                timeout=15,
            )
            geo.raise_for_status()

            results = geo.json().get(
                "results", []
            )

            if not results:
                st.error("ไม่พบเมืองนี้")
            else:
                place = results[0]

                weather = requests.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": place["latitude"],
                        "longitude": place["longitude"],
                        "current": (
                            "temperature_2m,"
                            "relative_humidity_2m,"
                            "apparent_temperature,"
                            "wind_speed_10m,"
                            "weather_code"
                        ),
                        "timezone": "auto",
                    },
                    timeout=15,
                )
                weather.raise_for_status()

                current = weather.json().get(
                    "current", {}
                )

                st.subheader(
                    f"{place.get('name', city)}, "
                    f"{place.get('country', '')}"
                )

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        "อุณหภูมิ",
                        f"{current.get('temperature_2m', '-')} °C",
                    )

                with c2:
                    st.metric(
                        "รู้สึกเหมือน",
                        f"{current.get('apparent_temperature', '-')} °C",
                    )

                with c3:
                    st.metric(
                        "ความชื้น",
                        f"{current.get('relative_humidity_2m', '-')} %",
                    )

                st.write(
                    "ความเร็วลม: "
                    f"{current.get('wind_speed_10m', '-')} km/h"
                )

        except Exception as e:
            st.error("ดึงข้อมูลอากาศไม่สำเร็จ")
            st.caption(str(e))


with tab6:
    show_logo()
    st.header("🗓️ ปฏิทิน")

    selected = st.date_input(
        "เลือกวันที่",
        value=now.date(),
        key="calendar_date",
    )

    selected_dt = datetime(
        selected.year,
        selected.month,
        selected.day,
        tzinfo=BANGKOK,
    )

    st.subheader(thai_date_text(selected_dt))
    st.write(f"วัน{weekday_thai(selected_dt)}")
    st.write(f"ค.ศ. {selected.year}")
    st.write(f"พ.ศ. {selected.year + 543}")


with tab7:
    show_logo()
    st.header("🔎 เปรียบเทียบวันที่")

    date1 = st.date_input(
        "วันที่ 1",
        value=now.date(),
        key="compare_date_1",
    )

    date2 = st.date_input(
        "วันที่ 2",
        value=now.date(),
        key="compare_date_2",
    )

    difference = (date2 - date1).days

    st.metric(
        "จำนวนวันที่ต่างกัน",
        abs(difference),
    )

    if difference > 0:
        st.info(
            f"วันที่ 2 อยู่หลังวันที่ 1 {difference} วัน"
        )
    elif difference < 0:
        st.info(
            f"วันที่ 2 อยู่ก่อนวันที่ 1 {abs(difference)} วัน"
        )
    else:
        st.success("เป็นวันเดียวกัน")


with tab8:
    show_logo()
    st.header("🌀 Golden Ratio")

    phi = (1 + math.sqrt(5)) / 2

    st.metric(
        "φ (Phi)",
        f"{phi:.10f}",
    )

    st.write("ค่าโดยประมาณ: 1.618")
    st.write("สูตร φ = (1 + √5) / 2")

    st.divider()

    number = st.number_input(
        "ใส่ตัวเลข",
        value=100.0,
        key="golden_number",
    )

    c1, c2 = st.columns(2)

    with c1:
        st.write("คูณ Golden Ratio")
        st.success(
            f"{number * phi:.10f}"
        )

    with c2:
        st.write("หาร Golden Ratio")
        st.info(
            f"{number / phi:.10f}"
        )


with tab9:
    show_logo()
    st.header("🎵 เพลง")

    extensions = (
        ".mp3", ".wav", ".ogg",
        ".m4a", ".aac",
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
                music_files.append(filename)

    except Exception as e:
        st.error("ไม่สามารถอ่านไฟล์เพลงได้")
        st.caption(str(e))

    if music_files:
        st.success(
            f"พบไฟล์เพลง {len(music_files)} ไฟล์"
        )

        for filename in music_files:
            st.subheader(filename)

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
                st.caption(str(e))
    else:
        st.info(
            "ยังไม่พบไฟล์เพลง"
        )
        st.write(
            "วางไฟล์ .mp3 หรือ .wav "
            "ไว้โฟลเดอร์เดียวกับ app.py"
        )


with tab10:
    show_logo()
    st.header("🎟️ หวยรัฐบาล")

    st.subheader("📚 ผลรางวัลย้อนหลัง 12 ปี")

    current_date = now.date()
    first_date = date(
        current_date.year - 11,
        current_date.month,
        current_date.day,
    )

    st.caption(
        "ช่วงข้อมูล: "
        f"{first_date.strftime('%d/%m/%Y')} ถึง "
        f"{current_date.strftime('%d/%m/%Y')}"
    )

    try:
        paths = get_lottery_file_list()

        st.success(
            f"พบไฟล์ผลสลากในคลัง {len(paths):,} งวด"
        )

        years = sorted({
            int(p.split("/")[-1][:4])
            for p in paths
        }, reverse=True)

        available_years = [
            y for y in years
            if y >= first_date.year
        ]

        selected_year = st.selectbox(
            "เลือกปี พ.ศ.",
            available_years,
            format_func=lambda y: (
                f"พ.ศ. {y + 543} (ค.ศ. {y})"
            ),
            key="lottery_year",
        )

        year_start = date(
            selected_year, 1, 1
        )
        year_end = date(
            selected_year, 12, 31
        )

        rows = get_lottery_history(
            year_start,
            year_end,
        )

        if rows:
            display_rows = [
                {
                    k: v for k, v in row.items()
                    if k != "_date"
                }
                for row in rows
            ]

            st.success(
                f"พบผลรางวัล {len(display_rows)} งวด "
                f"ในปี ค.ศ. {selected_year}"
            )

            st.dataframe(
                display_rows,
                use_container_width=True,
                hide_index=True,
            )

            csv_data = (
                __import__("pandas")
                .DataFrame(display_rows)
                .to_csv(
                    index=False,
                    encoding="utf-8-sig",
                )
            )

            st.download_button(
                "ดาวน์โหลดข้อมูลปีนี้ CSV",
                data=csv_data,
    file_name=f"lottery_{selected_year}.csv",
                mime="text/csv",
            )

        else:
            st.warning(
                "ไม่พบข้อมูลสำหรับปีที่เลือก"
            )

    except Exception as e:
        st.error(
            "โหลดข้อมูลย้อนหลังไม่สำเร็จ"
        )
        st.code(str(e))

    st.divider()

    st.subheader("🔎 ค้นหาเลข")

    search_number = st.text_input(
        "กรอกเลข 6 หลัก",     
        max_chars=6,
        key="lottery_search_number",
    )

    if st.button(
        "ค้นหาจากข้อมูลย้อนหลัง",
        key="lottery_find_button",
    ):
        if not (
            search_number.isdigit()
            and len(search_number) == 6
        ):
            st.warning(
                "กรุณากรอกเลข 6 หลัก"
         )
        else:
            try:
                rows = get_lottery_history(
                    first_date,
                    current_date,
                )

                matches = []

                for row in rows:
                    if search_number == row["รางวัลที่ 1"]:
                        matches.append({
                            "วันที่": row["วันที่"],
                            "ประเภท": "รางวัลที่ 1",
                            "เลข": search_number,
                        })

                    if search_number[-2:] == row["เลขท้าย 2 ตัว"]:       
                       matches.append({
                            "วันที่": row["วันที่"],
                            "ประเภท": "เลขท้าย 2 ตัว",
                            "เลข": search_number[-2:],
                        })

                    if (
                        search_number[-3:]
                        in row["เลขท้าย 3 ตัว"].split(", ")
                    ):
                        matches.append({
                            "วันที่": row["วันที่"],
                            "ประเภท": "เลขท้าย 3 ตัว",
                            "เลข": search_number[-3:],
                        })

                    if ( 
                    
row["เลขหน้า 3 ตัว"].split(", ")
                    ):
                        matches.append({
                            "วันที่": row["วันที่"],
                            "ประเภท": "เลขหน้า 3 ตัว",
                            "เลข": search_number[:3],
                        })

                if matches:
                    st.success(
                        f"พบ {len(matches)} รายการ"
                    )
                    st.dataframe(
                        matches,
                        use_container_width=True,
                        hide_index=True,
    )
      else:
                    st.info(
                        "ไม่พบเลขนี้ในข้อมูลย้อนหลัง 12 ปี"
                    )

            except Exception as e:
                st.error(
                    "ค้นหาข้อมูลไม่สำเร็จ"
                )
                st.caption(str(e))

    st.divider()

    st.caption(
        "ข้อมูลย้อนหลังดึงจากคลัง thai-lotto-archive "
        "ซึ่งระบุว่าเก็บข้อมูลตั้งแต่ปี 2007 "
        "และระบุแหล่งที่มาของแต่ละงวดไว้ในไฟล์"
    )
    st.caption(
        "สำนักงานสลากกินแบ่งรัฐบาลมีชุดข้อมูลผลรางวัล "
        "และ API อย่างเป็นทางการเช่นกัน"
    )
    st.caption(
        "สถิติย้อนหลังเป็นข้อมูลในอดีต "
        "ไม่ใช่การทำนายผลรางวัลในอนาคต"
    )


with tab11:
    show_logo()
    st.header("🇱🇦 หวยลาว")
    st.subheader("📚 ผลหวยลาวย้อนหลัง 1 ปี")
    st.caption("ข้อมูลย้อนหลังประมาณ 365 วัน จากหน้าเผยแพร่สถิติของ ThaiORC; เป็นแหล่งข้อมูลภายนอก ไม่ใช่ API ทางการของรัฐบาลลาว")

    if st.button("โหลดผลหวยลาวย้อนหลัง 1 ปี", key="lao_load"):
        st.session_state["lao_loaded"] = True

    if st.session_state.get("lao_loaded", False):
        try:
            lao_rows = get_foreign_lottery_history("lao")
            if lao_rows:
                display = [
                    {k: v for k, v in row.items() if k != "_date"}
                    for row in lao_rows
                ]
                st.success(f"พบ {len(display):,} งวด")
                st.dataframe(display, use_container_width=True, hide_index=True)
                csv_data = __import__("pandas").DataFrame(display).to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    "ดาวน์โหลดหวยลาว CSV",
                    data=csv_data,
                    file_name="lao_lottery_1year.csv",
                    mime="text/csv",
                    key="lao_csv",
                )
            else:
                st.warning("ยังไม่พบข้อมูลหวยลาว หรือเว็บไซต์ต้นทางไม่ตอบสนอง")
        except Exception as e:
            st.error("โหลดข้อมูลหวยลาวไม่สำเร็จ")
            st.caption(str(e))


with tab12:
    show_logo()
    st.header("🇻🇳 หวยฮานอย")
    st.subheader("📚 ผลหวยฮานอยย้อนหลัง 1 ปี")
    st.caption("ข้อมูลย้อนหลังประมาณ 365 วัน จากหน้าเผยแพร่สถิติของ ThaiORC; เป็นแหล่งข้อมูลภายนอก ไม่ใช่ข้อมูลทางการของรัฐบาลเวียดนาม")

    if st.button("โหลดผลหวยฮานอยย้อนหลัง 1 ปี", key="hanoi_load"):
        st.session_state["hanoi_loaded"] = True

    if st.session_state.get("hanoi_loaded", False):
        try:
            hanoi_rows = get_foreign_lottery_history("hanoi")
            if hanoi_rows:
                display = [
                    {k: v for k, v in row.items() if k != "_date"}
                    for row in hanoi_rows
                ]
                st.success(f"พบ {len(display):,} งวด")
                st.dataframe(display, use_container_width=True, hide_index=True)
                csv_data = __import__("pandas").DataFrame(display).to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    "ดาวน์โหลดหวยฮานอย CSV",
                    data=csv_data,
                    file_name="hanoi_lottery_1year.csv",
                    mime="text/csv",
                    key="hanoi_csv",
                )
            else:
                st.warning("ยังไม่พบข้อมูลหวยฮานอย หรือเว็บไซต์ต้นทางไม่ตอบสนอง")
        except Exception as e:
            st.error("โหลดข้อมูลหวยฮานอยไม่สำเร็จ")
            st.caption(str(e))


st.divider()
st.caption("Mon101")
