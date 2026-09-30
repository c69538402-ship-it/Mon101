import os
import re
import math
from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo

import requests
import streamlit as st


# =========================================================
# MON101
# =========================================================

st.set_page_config(
    page_title="Mon101",
    page_icon="📅",
    layout="wide",
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BANGKOK = ZoneInfo("Asia/Bangkok")
LOGO_PATH = os.path.join(APP_DIR, "logo.jpg")


# =========================================================
# LOGO
# =========================================================

def show_logo():
    if os.path.exists(LOGO_PATH):
        st.image(
            LOGO_PATH,
            use_container_width=True,
        )
    else:
        st.warning(
            "ไม่พบไฟล์ logo.jpg ในโฟลเดอร์เดียวกับ app.py"
        )


# =========================================================
# ภาษา / วันที่
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
# หวยรัฐบาล
# =========================================================

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
        f"{dt.day} "
        f"{THAI_MONTHS[dt.month - 1]} "
        f"{dt.year + 543}"
    )


def weekday_thai(dt):
    return THAI_DAYS[dt.weekday()]


# =========================================================
# ราศีตะวันตก
# =========================================================

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

        utc_dt = (
            local_dt
            .astimezone(timezone.utc)
            .replace(tzinfo=None)
        )

        sun = ephem.Sun(utc_dt)
        ecliptic = ephem.Ecliptic(sun)

        longitude = (
            math.degrees(
                float(ecliptic.lon)
            )
            % 360
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


# =========================================================
# นักษัตร
# =========================================================

CHINESE_ZODIACS = [
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


def get_chinese_zodiac(year):
    return CHINESE_ZODIACS[
        (year - 4) % 12
    ]


def get_zodiac_number(year):
    return ((year - 4) % 12) + 1


# =========================================================
# โหลดรายชื่อไฟล์หวยรัฐบาล
# =========================================================

@st.cache_data(
    ttl=86400,
    show_spinner=False,
)
def get_lottery_file_list():

    response = requests.get(
        LOTTO_TREE_URL,
        timeout=30,
        headers={
            "User-Agent": "Mon101"
        },
    )

    response.raise_for_status()

    data = response.json()

    paths = []

    for item in data.get("tree", []):

        path = item.get(
            "path",
            "",
        )

        if re.fullmatch(
            r"lottonumbers/\d{4}-\d{2}-\d{2}\.txt",
            path,
        ):
            paths.append(path)

    return sorted(
        paths,
        reverse=True,
    )


# =========================================================
# แปลงข้อมูลหวยรัฐบาล
# =========================================================

def parse_lottery_text(
    text,
    filename,
):

    result = {
        "date": (
            filename
            .replace(
                "lottonumbers/",
                "",
            )
            .replace(
                ".txt",
                "",
            )
        ),
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

                if key in (
                    "front3",
                    "back3",
                ):
                    result[key].extend(
                        values
                    )

                elif values:
                    result[key] = values[0]

                break

    return result


# =========================================================
# ประวัติหวยรัฐบาล
# =========================================================

@st.cache_data(
    ttl=86400,
    show_spinner=False,
)
def get_lottery_history(
    start_date,
    end_date,
):

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

        y, m, d = map(
            int,
            match.groups(),
        )

        try:
            draw_date = date(
                y,
                m,
                d,
            )

        except ValueError:
            continue

        if (
            start_date
            <= draw_date
            <= end_date
        ):
            selected.append(
                (
                    path,
                    draw_date,
                )
            )

    rows = []

    for path, draw_date in selected:

        try:

            response = requests.get(
                LOTTO_RAW_BASE + path,
                timeout=20,
                headers={
                    "User-Agent": "Mon101"
                },
            )

            response.raise_for_status()

            parsed = parse_lottery_text(
                response.text,
                path,
            )

            rows.append(
                {
                    "วันที่":
                        draw_date.strftime(
                            "%d/%m/%Y"
                        ),
                    "พ.ศ.":
                        str(
                            draw_date.year
                            + 543
                        ),
                    "รางวัลที่ 1":
                        parsed["first"],
                    "เลขหน้า 3 ตัว":
                        ", ".join(
                            parsed["front3"]
                        ),
                    "เลขท้าย 3 ตัว":
                        ", ".join(
                            parsed["back3"]
                        ),
                    "เลขท้าย 2 ตัว":
                        parsed["back2"],
                    "_date":
                        draw_date,
                }
            )

        except Exception:
            continue

    rows.sort(
        key=lambda x: x["_date"],
        reverse=True,
    )

    return rows


# =========================================================
# หวยลาว / ฮานอย
# =========================================================

FOREIGN_LOTTERY_URLS = {

    "lao": [
        "https://lotto.thaiorc.com/"
        "lao/last3/stats-years1.php?pg={page}",

        "https://thaiorc.com/"
        "lotto/lao/last3/stats-years1.php?pg={page}",
    ],

    "hanoi": [
        "https://lotto.thaiorc.com/"
        "hanoi/stats/lottery-years1.php?pg={page}",

        "https://thaiorc.com/"
        "lotto/hanoi/stats/lottery-years1.php?pg={page}",
    ],
}


def _clean_number(
    value,
    width=None,
):

    text = str(value).strip()

    if text.lower() in (
        "nan",
        "none",
        "",
    ):
        return ""

    text = re.sub(
        r"[^0-9]",
        "",
        text,
    )

    if width and text:
        text = text.zfill(width)

    return text


def _strip_html(html):

    html = re.sub(
        r"<script[\s\S]*?</script>",
        " ",
        html,
        flags=re.I,
    )

    html = re.sub(
        r"<style[\s\S]*?</style>",
        " ",
        html,
        flags=re.I,
    )

    html = re.sub(
        r"<[^>]+>",
        " ",
        html,
    )

    html = html.replace(
        "&nbsp;",
        " ",
    )

    html = html.replace(
        "&amp;",
        "&",
    )

    html = re.sub(
        r"\s+",
        " ",
        html,
    )

    return html.strip()


def _parse_foreign_page(
    html,
    kind,
):

    text = _strip_html(html)

    rows = []

    if kind == "lao":

        pattern = re.compile(
            r"(\d{1,2}/\d{1,2}/\d{4})\s+"
            r"(\d{6})\s+"
            r"(\d{3})\s+"
            r"(\d{2})\s+"
            r"(\d{2})"
        )

    else:

        pattern = re.compile(
            r"(\d{1,2}/\d{1,2}/\d{4})\s+"
            r"(\d{5})\s+"
            r"(\d{5})\s+"
            r"(\d{3})\s+"
            r"(\d{2})"
        )

    seen = set()

    for match in pattern.finditer(text):

        date_text = match.group(1)

        day, month, buddhist_year = map(
            int,
            date_text.split("/"),
        )

        try:

            draw_date = date(
                buddhist_year - 543,
                month,
                day,
            )

        except ValueError:
            continue

        if draw_date.isoformat() in seen:
            continue

        seen.add(
            draw_date.isoformat()
        )

        if kind == "lao":

            (
                six_digits,
                top3,
                top2,
                bottom2,
            ) = match.groups()[1:]

            rows.append(
                {
                    "วันที่":
                        draw_date.strftime(
                            "%d/%m/%Y"
                        ),
                    "พ.ศ.":
                        str(
                            draw_date.year
                            + 543
                        ),
                    "เลข 6 ตัว":
                        six_digits,
                    "เลข 3 ตัวบน":
                        top3,
                    "เลข 2 ตัวบน":
                        top2,
                    "เลข 2 ตัวล่าง":
                        bottom2,
                    "_date":
                        draw_date,
                }
            )

        else:

            (
                special,
                first,
                top3,
                bottom2,
            ) = match.groups()[1:]

            rows.append(
                {
                    "วันที่":
                        draw_date.strftime(
                            "%d/%m/%Y"
                        ),
                    "พ.ศ.":
                        str(
                            draw_date.year
                            + 543
                        ),
                    "รางวัลพิเศษ":
                        special,
                    "รางวัลที่ 1":
                        first,
                    "เลข 3 ตัวบน":
                        top3,
                    "เลข 2 ตัวล่าง":
                        bottom2,
                    "_date":
                        draw_date,
                }
            )

    return rows


@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def get_foreign_lottery_history(
    kind,
):

    today_date = datetime.now(
        BANGKOK
    ).date()

    start_date = (
        today_date
        - timedelta(days=365)
    )

    all_rows = {}

    for page in range(1, 25):

        page_rows = []

        for url_template in (
            FOREIGN_LOTTERY_URLS[kind]
        ):

            url = url_template.format(
                page=page
            )

            try:

                response = requests.get(
                    url,
                    timeout=30,
                    headers={
                        "User-Agent":
                            (
                                "Mozilla/5.0 "
                                "(Linux; Android 10) "
                                "AppleWebKit/537.36 "
                                "Chrome/128 "
                                "Safari/537.36"
                            ),
                        "Accept-Language":
                            "th-TH,th;q=0.9,en;q=0.8",
                        "Accept":
                            (
                                "text/html,"
                                "application/xhtml+xml,"
                                "application/xml;q=0.9,"
                                "*/*;q=0.8"
                            ),
                    },
                )

                response.raise_for_status()

                page_rows = _parse_foreign_page(
                    response.text,
                    kind,
                )

                if page_rows:
                    break

            except Exception:
                continue

        if not page_rows:

            if page >= 3:
                break

            continue

        for row in page_rows:

            draw_date = row["_date"]

            if (
                start_date
                <= draw_date
                <= today_date
            ):

                all_rows[
                    draw_date.isoformat()
                ] = row

        oldest = min(
            row["_date"]
            for row in page_rows
        )

        if oldest < start_date:
            break

    return sorted(
        all_rows.values(),
        key=lambda x: x["_date"],
        reverse=True,
    )


# =========================================================
# MON101 LOTTO LAB
# =========================================================

LOTTO_PHI = 1.618
LUNAR_CYCLE = 29.53


def get_thai_lunar_info(
    target_date,
):

    try:

        from pythainlp.util import (
            to_lunar_date
        )

        lunar_value = to_lunar_date(
            target_date
        )

        lunar_text = str(
            lunar_value
        )

        match = re.search(
            r"(ขึ้น|แรม)\s*"
            r"(\d+)\s*ค่ำ"
            r"(?:\s*เดือน\s*([0-9]+))?",
            lunar_text,
        )

        if not match:

            return {
                "text": lunar_text,
                "phase": "",
                "lunar_day": 0,
                "lunar_month": "",
            }

        phase = match.group(1)

        lunar_day = int(
            match.group(2)
        )

        lunar_month = (
            match.group(3)
            or ""
        )

        return {
            "text": lunar_text,
            "phase": phase,
            "lunar_day": lunar_day,
            "lunar_month":
                lunar_month,
        }

    except Exception as e:

        return {
            "text": "",
            "phase": "",
            "lunar_day": 0,
            "lunar_month": "",
            "error": str(e),
        }


def split_digits(number):

    return [
        int(x)
        for x in str(
            abs(int(number))
        )
    ]


def calculate_digit_formula(
    digit,
    phase,
    lunar_day,
):

    divided = (
        digit
        / LOTTO_PHI
    )

    multiplied = (
        divided
        * LUNAR_CYCLE
    )

    if phase == "ขึ้น":

        adjusted = (
            multiplied
            - lunar_day
        )

        operation = (
            f"{multiplied:.6f}"
            f" - {lunar_day}"
        )

    elif phase == "แรม":

        adjusted = (
            multiplied
            + lunar_day
        )

        operation = (
            f"{multiplied:.6f}"
            f" + {lunar_day}"
        )

    else:

        adjusted = multiplied

        operation = (
            f"{multiplied:.6f}"
        )

    return {
        "digit": digit,
        "divided": divided,
        "multiplied": multiplied,
        "adjusted": adjusted,
        "operation": operation,
    }


def calculate_component(
    name,
    value,
    phase,
    lunar_day,
):

    digits = split_digits(
        value
    )

    details = []

    for digit in digits:

        details.append(
            calculate_digit_formula(
                digit,
                phase,
                lunar_day,
            )
        )

    total = sum(
        item["adjusted"]
        for item in details
    )

    return {
        "name": name,
        "value": value,
        "digits": digits,
        "details": details,
        "total": total,
    }


def run_lotto_formula(
    target_date,
):

    lunar = get_thai_lunar_info(
        target_date
    )

    weekday_number = (
        target_date.weekday()
        + 1
    )

    month_number = (
        target_date.month
    )

    buddhist_year = (
        target_date.year
        + 543
    )

    zodiac_number = (
        get_zodiac_number(
            target_date.year
        )
    )

    phase = lunar.get(
        "phase",
        "",
    )

    lunar_day = lunar.get(
        "lunar_day",
        0,
    )

    components = [

        calculate_component(
            "วันที่",
            target_date.day,
            phase,
            lunar_day,
        ),

        calculate_component(
            "วันในสัปดาห์",
            weekday_number,
            phase,
            lunar_day,
        ),

        calculate_component(
            "เดือน",
            month_number,
            phase,
            lunar_day,
        ),

        calculate_component(
            "พ.ศ.",
            buddhist_year,
            phase,
            lunar_day,
        ),

        calculate_component(
            "นักษัตร",
            zodiac_number,
            phase,
            lunar_day,
        ),
    ]

    grand_total = sum(
        item["total"]
        for item in components
    )

    absolute_total = abs(
        grand_total
    )

    # -----------------------------------------------------
    # ค่าตัวเลขสำหรับการทดลอง
    # -----------------------------------------------------

    number_2 = (
        int(
            round(
                absolute_total
            )
        )
        % 100
    )

    number_3 = (
        int(
            round(
                absolute_total
            )
        )
        % 1000
    )

    number_6 = (
        int(
            round(
                absolute_total
                * 1000
            )
        )
        % 1000000
    )

    return {
        "date": target_date,
        "lunar": lunar,
        "weekday_number":
            weekday_number,
        "month_number":
            month_number,
        "buddhist_year":
            buddhist_year,
        "zodiac_number":
            zodiac_number,
        "zodi
# =========================================================
# TAB 10 - หวยรัฐบาล / MON101 LOTTO LAB
# =========================================================

with tab10:

    show_logo()

    st.markdown(
        """
        <div class="lotto-title">

            <h1>🎟️ MON101 LOTTO LAB</h1>

            <div class="white-neon"
                 style="font-size:18px;">

                🔴 1.618
                &nbsp; × &nbsp;
                🟠 29.53
                &nbsp; × &nbsp;
                🌙 จันทรคติ

            </div>

            <div style="margin-top:8px;">

                ห้องทดลองสูตรจากวันที่จริง
                และข้อมูลหวยย้อนหลัง

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # =====================================================
    # ประวัติ 12 ปี
    # =====================================================

    st.subheader(
        "📚 ผลรางวัลย้อนหลัง 12 ปี"
    )

    current_date = now.date()

    first_date = date(
        current_date.year - 12,
        10,
        1,
    )

    st.caption(
        "ช่วงข้อมูล 12 ปี: "
        f"{first_date.strftime('%d/%m/%Y')} "
        "ถึง "
        f"{current_date.strftime('%d/%m/%Y')}"
    )

    rows = []

    try:

        rows = get_lottery_history(
            first_date,
            current_date,
        )

        display_rows = [

            {
                k: v
                for k, v in row.items()
                if k != "_date"
            }

            for row in rows
        ]

        if display_rows:

            st.success(
                f"พบผลรางวัล "
                f"{len(display_rows):,} งวด"
            )

            st.dataframe(
                display_rows,
                use_container_width=True,
                hide_index=True,
                height=500,
            )

            csv_data = (
                __import__("pandas")
                .DataFrame(
                    display_rows
                )
                .to_csv(
                    index=False,
                    encoding="utf-8-sig",
                )
            )

            st.download_button(
                "⬇️ ดาวน์โหลดหวยย้อนหลัง 12 ปี CSV",
                data=csv_data,
                file_name=(
                    "thai_lottery_12years.csv"
                ),
                mime="text/csv",
                key="thai_lottery_12y_csv_new",
            )

        else:

            st.warning(
                "ยังไม่พบข้อมูลหวยรัฐบาลย้อนหลัง 12 ปี"
            )

    except Exception as e:

        st.error(
            "โหลดข้อมูลย้อนหลังไม่สำเร็จ"
        )

        st.code(
            str(e)
        )


    # =====================================================
    # ห้องทดลอง
    # =====================================================

    st.divider()

    st.markdown(
        """
        <div class="neon-card">

            <h2>🔬 ห้องทดลองสูตร 1.618</h2>

            <div class="white-neon">

                เลือกงวดจริงจากข้อมูลย้อนหลัง
                แล้วให้ Mon101 คำนวณทีละหลัก

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    if rows:

        available_dates = [

            row["_date"]

            for row in rows

            if row.get("_date")

        ]

        selected_lotto_date = (
            st.selectbox(
                "📅 เลือกงวดที่ต้องการทดลอง",
                available_dates,
                format_func=lambda x:
                    x.strftime(
                        "%d/%m/%Y"
                    ),
                key="lotto_lab_date",
            )
        )

        selected_row = next(
            (
                row
                for row in rows
                if row["_date"]
                == selected_lotto_date
            ),
            None,
        )


        if selected_row:

            calc = run_lotto_formula(
                selected_lotto_date
            )

            lunar = calc[
                "lunar"
            ]


            # =================================================
            # ข้อมูลตั้งต้น
            # =================================================

            st.markdown(
                "### 🧭 ข้อมูลตั้งต้น"
            )

            info1, info2, info3, info4, info5 = (
                st.columns(5)
            )

            with info1:

                st.metric(
                    "วันที่",
                    selected_lotto_date.day,
                )

            with info2:

                st.metric(
                    "วัน",
                    calc[
                        "weekday_number"
                    ],
                )

            with info3:

                st.metric(
                    "เดือน",
                    calc[
                        "month_number"
                    ],
                )

            with info4:

                st.metric(
                    "พ.ศ.",
                    calc[
                        "buddhist_year"
                    ],
                )

            with info5:

                st.metric(
                    "นักษัตร",
                    (
                        f"{calc['zodiac_number']} "
                        f"{calc['zodiac_name']}"
                    ),
                )


            # =================================================
            # จันทรคติ
            # =================================================

            st.markdown(
                f"""
                <div class="formula-card">

                    <b class="orange-neon">
                        🌙 จันทรคติจริง
                    </b>

                    <br><br>

                    <span style="font-size:22px;">
                        {lunar.get(
                            "text",
                            "ไม่พบข้อมูล"
                        )}
                    </span>

                </div>
                """,
                unsafe_allow_html=True,
            )


            phase = lunar.get(
                "phase",
                "",
            )

            lunar_day = lunar.get(
                "lunar_day",
                0,
            )


            if phase == "ขึ้น":

                st.info(
                    f"🌒 ข้างขึ้น "
                    f"{lunar_day} ค่ำ "
                    f"→ สูตรใช้ − {lunar_day}"
                )

            elif phase == "แรม":

                st.success(
                    f"🌘 ข้างแรม "
                    f"{lunar_day} ค่ำ "
                    f"→ สูตรใช้ + {lunar_day}"
                )

            else:

                st.warning(
                    "ไม่สามารถระบุข้างขึ้น/ข้างแรมได้"
                )


            # =================================================
            # สูตร
            # =================================================

            st.divider()

            st.markdown(
                "### 🧮 ขั้นตอนการคำนวณ"
            )

            st.caption(
                "สูตรทดลองของ Mon101:"
            )

            st.code(
                "ตัวเลข ÷ 1.618"
                " → × 29.53"
                " → ปรับด้วยข้างขึ้น/ข้างแรม",
                language="text",
            )


            for component in (
                calc["components"]
            ):

                st.markdown(
                    f"""
                    <div class="neon-card">

                        <h3>
                            🔹 {component['name']}
                            = {component['value']}
                        </h3>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


                for index, detail in enumerate(
                    component["details"],
                    start=1,
                ):

                    digit = detail[
                        "digit"
                    ]


                    st.markdown(
                        f"""
                        <div class="formula-card">

                            <b class="white-neon">
                                หลักที่ {index}
                                → ตัวเลข {digit}
                            </b>

                            <br><br>

                            <span class="blue-neon">

                                {digit}
                                ÷
                                {LOTTO_PHI}

                                =
                                {detail['divided']:.6f}

                            </span>

                            <br><br>

                            <span class="purple-neon">

                                {detail['divided']:.6f}
                                ×
                                {LUNAR_CYCLE}

                                =
                                {detail['multiplied']:.6f}

                            </span>

                            <br><br>

                            <span class="green-neon">

                                {detail['operation']}
                                =
                                {detail['adjusted']:.6f}

                            </span>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


                st.write(
                    f"**รวม {component['name']} "
                    f"= {component['total']:.6f}**"
                )


            # =================================================
            # ผลรวม
            # =================================================

            st.divider()

            st.markdown(
                "### ⚡ ผลรวมสูตร"
            )

            st.markdown(
                f"""
                <div class="lotto-title">

                    <div>
                        ผลรวมทั้งหมด
                    </div>

                    <div class="result-number green-neon">

                        {calc['grand_total']:.6f}

                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


            # =================================================
            # เลขทดลอง
            # =================================================

            n1, n2, n3 = st.columns(3)


            with n1:

                st.markdown(
                    "### 🔴 เลขทดลอง 2 ตัว"
                )

                st.markdown(
                    f"""
                    <div class="result-number red-neon">

                        {calc['number_2']}

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


            with n2:

                st.markdown(
                    "### 🔵 เลขทดลอง 3 ตัว"
                )

                st.markdown(
                    f"""
                    <div class="result-number blue-neon">

                        {calc['number_3']}

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


            with n3:

                st.markdown(
                    "### 🟣 ค่า 6 หลักทดลอง"
                )

                st.markdown(
                    f"""
                    <div class="result-number purple-neon">

                        {calc['number_6']}

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


            st.caption(
                "ค่าด้านบนเป็นผลจากสูตรทดลอง "
                "ไม่ใช่การรับประกันผลรางวัล"
            )


            # =================================================
            # ผลจริง
            # =================================================

            st.divider()

            st.markdown(
                "### 🎯 ผลรางวัลจริง"
            )

            r1, r2, r3 = (
                st.columns(3)
            )


            with r1:

                st.metric(
                    "รางวัลที่ 1",
                    selected_row.get(
                        "รางวัลที่ 1",
                        "-",
                    ),
                )


            with r2:

                st.metric(
                    "เลขท้าย 2 ตัว",
                    selected_row.get(
                        "เลขท้าย 2 ตัว",
                        "-",
                    ),
                )


            with r3:

                st.metric(
                    "เลขท้าย 3 ตัว",
                    selected_row.get(
                        "เลขท้าย 3 ตัว",
                        "-",
                    ),
                )


            # =================================================
            # เปรียบเทียบ
            # =================================================

            comparison = (
                compare_formula_with_result(
                    calc,
                    selected_row,
                )
            )

            st.divider()

            st.markdown(
                "### 🔎 เปรียบเทียบสูตรกับผลจริง"
            )

            comparison_rows = [

                {
                    "รายการ": key,
                    "ค่า": value,
                }

                for key, value
                in comparison.items()

            ]

            st.dataframe(
                comparison_rows,
                use_container_width=True,
                hide_index=True,
            )


    else:

        st.warning(
            "ยังไม่มีข้อมูลหวยสำหรับห้องทดลอง"
        )


    # =====================================================
    # BACKTEST
    # =====================================================

    st.divider()

    st.markdown(
        """
        <div class="neon-card">

            <h2>📊 ทดลองสูตรย้อนหลัง</h2>

            <div class="white-neon">

                ให้สูตรทำงานกับหลายงวด
                แล้วดูผลที่เกิดขึ้นจริง

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    if rows:

        backtest_count = (
            st.selectbox(
                "จำนวนงวดที่ต้องการทดลอง",
                [
                    20,
                    50,
                    100,
                    200,
                    500,
                ],
                index=2,
                key="lotto_backtest_count",
            )
        )


        if st.button(
            "🚀 เริ่มทดลองย้อนหลัง",
            key="lotto_backtest_button",
        ):

            test_rows = rows[
                :min(
                    backtest_count,
                    len(rows),
                )
            ]


            results = []

            progress = st.progress(
                0
            )


            for index, row in enumerate(
                test_rows,
                start=1,
            ):

                try:

                    calc = (
                        run_lotto_formula(
                            row["_date"]
                        )
                    )

                    result = (
                        compare_formula_with_result(
                            calc,
                            row,
                        )
                    )


                    results.append(
                        {
                            "วันที่":
                                row["_date"].strftime(
                                    "%d/%m/%Y"
                                ),

                            "เลขทดลอง 2 ตัว":
                                calc["number_2"],

                            "เลขจริง 2 ตัว":
                                row.get(
                                    "เลขท้าย 2 ตัว",
                                    "",
                                ),

                            "ตรง 2 ตัว":
                                result[
                                    "ตรง 2 ตัว"
                                ],

                            "เลขทดลอง 3 ตัว":
                                calc["number_3"],

                            "ตรงท้าย 3 ตัว":
                                result[
                                    "ตรงท้าย 3 ตัว"
                                ],

                            "ตรงหน้า 3 ตัว":
                                result[
                                    "ตรงหน้า 3 ตัว"
                                ],

                            "เลขทดลอง 6 ตัว":
                                calc["number_6"],

                            "ตรงรางวัลที่ 1":
                                result[
                                    "ตรงรางวัลที่ 1"
                                ],
                        }
                    )


                except Exception:
                    pass


                progress.progress(
                    index / len(test_rows)
                )


            if results:

                import pandas as pd

                df_test = pd.DataFrame(
                    results
                )

                count_total = len(
                    df_test
                )

                hit_2 = int(
                    df_test[
                        "ตรง 2 ตัว"
                    ].sum()
                )

                hit_back3 = int(
                    df_test[
                        "ตรงท้าย 3 ตัว"
                    ].sum()
                )

                hit_front3 = int(
                    df_test[
                        "ตรงหน้า 3 ตัว"
                    ].sum()
                )

                hit_first = int(
                    df_test[
                        "ตรงรางวัลที่ 1"
                    ].sum()
                )


                st.success(
                    f"ทดลองสำเร็จ "
                    f"{count_total:,} งวด"
                )


                c1, c2, c3, c4 = (
                    st.columns(4)
                )


                with c1:

                    st.metric(
                        "ตรง 2 ตัว",
                        f"{hit_2:,}",
                    )


                with c2:

                    st.metric(
                        "ตรงท้าย 3 ตัว",
                        f"{hit_back3:,}",
                    )


                with c3:

                    st.metric(
                        "ตรงหน้า 3 ตัว",
                        f"{hit_front3:,}",
                    )


                with c4:

                    st.metric(
                        "ตรงรางวัลที่ 1",
                        f"{hit_first:,}",
                    )


                st.dataframe(
                    df_test,
                    use_container_width=True,
                    hide_index=True,
                    height=550,
                )


                csv_test = (
                    df_test.to_csv(
                        index=False,
                        encoding="utf-8-sig",
                    )
                )


                st.download_button(
                    "⬇️ ดาวน์โหลดผลการทดลองย้อนหลัง",
                    data=csv_test,
                    file_name=(
                        "mon101_lotto_backtest.csv"
                    ),
                    mime="text/csv",
                    key="lotto_backtest_csv",
                )


                st.caption(
                    "Backtest เป็นการวัดจากข้อมูลในอดีต "
                    "ไม่ใช่หลักฐานว่าผลสูตรสามารถทำนายงวดถัดไปได้"
                )


    # =====================================================
    # ค้นหาเลข
    # =====================================================

    st.divider()

    st.subheader(
        "🔎 ค้นหาเลขในข้อมูลย้อนหลัง"
    )


    search_number = st.text_input(
        "กรอกเลข 6 หลัก",
        max_chars=6,
        key="lottery_search_number_new",
    )


    if st.button(
        "ค้นหาจากข้อมูลย้อนหลัง",
        key="lottery_find_button_new",
    ):

        if not (
            search_number.isdigit()
                  
    
