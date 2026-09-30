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

PHI = 1.618
LUNAR_CYCLE = 29.53

THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
    "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
    "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

THAI_DAYS = [
    "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี",
    "ศุกร์", "เสาร์", "อาทิตย์",
]

THAI_ZODIACS = [
    "ชวด", "ฉลู", "ขาล", "เถาะ",
    "มะโรง", "มะเส็ง", "มะเมีย", "มะแม",
    "วอก", "ระกา", "จอ", "กุน",
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

FOREIGN_LOTTERY_URLS = {
    "lao": [
        "https://lotto.thaiorc.com/lao/last3/stats-years1.php?pg={page}",
        "https://thaiorc.com/lotto/lao/last3/stats-years1.php?pg={page}",
    ],
    "hanoi": [
        "https://lotto.thaiorc.com/hanoi/stats/lottery-years1.php?pg={page}",
        "https://thaiorc.com/lotto/hanoi/stats/lottery-years1.php?pg={page}",
    ],
}


def show_logo():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.warning("ไม่พบไฟล์ logo.jpg ในโฟลเดอร์เดียวกับ app.py")


def thai_date_text(dt):
    return (
        f"{dt.day} {THAI_MONTHS[dt.month - 1]} "
        f"{dt.year + 543}"
    )


def weekday_thai(dt):
    return THAI_DAYS[dt.weekday()]


def get_chinese_zodiac(year):
    return THAI_ZODIACS[(year - 4) % 12]


def get_zodiac_number(year):
    return ((year - 4) % 12) + 1


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


def get_thai_lunar_info(target_date):
    try:
        from pythainlp.util import to_lunar_date

        lunar_text = to_lunar_date(target_date)

        match = re.search(
            r"(ขึ้น|แรม)\s+(\d+)\s+ค่ำ\s+เดือน\s+(\d+)",
            str(lunar_text),
        )

        if not match:
            return {
                "text": str(lunar_text),
                "phase": "",
                "day": None,
                "month": None,
                "error": "",
            }

        phase = match.group(1)
        lunar_day = int(match.group(2))
        lunar_month = int(match.group(3))

        return {
            "text": str(lunar_text),
            "phase": phase,
            "day": lunar_day,
            "month": lunar_month,
            "error": "",
        }

    except Exception as exc:
        return {
            "text": "",
            "phase": "",
            "day": None,
            "month": None,
            "error": str(exc),
        }


def calculate_digit(digit, phase, lunar_day):
    digit = int(digit)

    divided = digit / PHI
    multiplied = divided * LUNAR_CYCLE

    if phase == "ขึ้น":
        adjusted = multiplied - lunar_day
        operation = f"{multiplied:.6f} - {lunar_day}"
    elif phase == "แรม":
        adjusted = multiplied + lunar_day
        operation = f"{multiplied:.6f} + {lunar_day}"
    else:
        adjusted = multiplied
        operation = f"{multiplied:.6f}"

    return {
        "digit": digit,
        "divide": divided,
        "multiply": multiplied,
        "operation": operation,
        "adjusted": adjusted,
    }


def calculate_component(name, value, phase, lunar_day):
    digits = [int(x) for x in str(abs(int(value)))]

    details = []

    for position, digit in enumerate(digits, start=1):
        item = calculate_digit(
            digit,
            phase,
            lunar_day,
        )
        item["position"] = position
        details.append(item)

    total = sum(item["adjusted"] for item in details)

    return {
        "name": name,
        "value": int(value),
        "digits": digits,
        "details": details,
        "total": total,
    }


def run_lotto_formula(target_date):
    lunar = get_thai_lunar_info(target_date)

    if not lunar["phase"] or lunar["day"] is None:
        return {
            "ok": False,
            "error": lunar["error"] or "อ่านข้อมูลจันทรคติไม่ได้",
        }

    weekday_number = target_date.weekday() + 1
    month_number = target_date.month
    buddhist_year = target_date.year + 543
    zodiac_number = get_zodiac_number(target_date.year)

    components = [
        calculate_component(
            "วัน",
            weekday_number,
            lunar["phase"],
            lunar["day"],
        ),
        calculate_component(
            "เดือน",
            month_number,
            lunar["phase"],
            lunar["day"],
        ),
        calculate_component(
            "พ.ศ.",
            buddhist_year,
            lunar["phase"],
            lunar["day"],
        ),
        calculate_component(
            "นักษัตร",
            zodiac_number,
            lunar["phase"],
            lunar["day"],
        ),
    ]

    grand_total = sum(
        item["total"] for item in components
    )

    number_2 = int(round(abs(grand_total))) % 100
    number_3 = int(round(abs(grand_total))) % 1000
    number_6 = int(
        round(abs(grand_total) * 1000)
    ) % 1000000

    return {
        "ok": True,
        "date": target_date,
        "weekday": weekday_number,
        "weekday_name": THAI_DAYS[
            weekday_number - 1
        ],
        "month": month_number,
        "month_name": THAI_MONTHS[
            month_number - 1
        ],
        "buddhist_year": buddhist_year,
        "zodiac": THAI_ZODIACS[
            zodiac_number - 1
        ],
        "zodiac_number": zodiac_number,
        "lunar": lunar,
        "components": components,
        "grand_total": grand_total,
        "number_2": f"{number_2:02d}",
        "number_3": f"{number_3:03d}",
        "number_6": f"{number_6:06d}",
    }


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
                    "วันที่": draw_date.strftime(
                        "%d/%m/%Y"
                    ),
                    "พ.ศ.": str(
                        draw_date.year + 543
                    ),
                    "รางวัลที่ 1": parsed["first"],
                    "เลขหน้า 3 ตัว": ", ".join(
                        parsed["front3"]
                    ),
                    "เลขท้าย 3 ตัว": ", ".join(
                        parsed["back3"]
                    ),
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
def _clean_number(value, width=None):
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


def _parse_foreign_page(html, kind):
    text = _strip_html(html)
    rows = []

    if kind == "lao":
        pattern = re.compile(
            r"(\d{1,2}/\d{1,2}/\d{4})\s+"
            r"(\d{6})\s+(\d{3})\s+"
            r"(\d{2})\s+(\d{2})"
        )
    else:
        pattern = re.compile(
            r"(\d{1,2}/\d{1,2}/\d{4})\s+"
            r"(\d{5})\s+(\d{5})\s+"
            r"(\d{3})\s+(\d{2})"
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

        seen.add(draw_date.isoformat())

        if kind == "lao":
            six_digits, top3, top2, bottom2 = (
                match.groups()[1:]
            )

            rows.append(
                {
                    "วันที่": draw_date.strftime(
                        "%d/%m/%Y"
                    ),
                    "พ.ศ.": str(
                        draw_date.year + 543
                    ),
                    "เลข 6 ตัว": six_digits,
                    "เลข 3 ตัวบน": top3,
                    "เลข 2 ตัวบน": top2,
                    "เลข 2 ตัวล่าง": bottom2,
                    "_date": draw_date,
                }
            )

        else:
            special, first, top3, bottom2 = (
                match.groups()[1:]
            )

            rows.append(
                {
                    "วันที่": draw_date.strftime(
                        "%d/%m/%Y"
                    ),
                    "พ.ศ.": str(
                        draw_date.year + 543
                    ),
                    "รางวัลพิเศษ": special,
                    "รางวัลที่ 1": first,
                    "เลข 3 ตัวบน": top3,
                    "เลข 2 ตัวล่าง": bottom2,
                    "_date": draw_date,
                }
            )

    return rows


@st.cache_data(ttl=3600, show_spinner=False)
def get_foreign_lottery_history(kind):
    today_date = datetime.now(
        BANGKOK
    ).date()

    start_date = (
        today_date - timedelta(days=365)
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
                        "User-Agent": (
                            "Mozilla/5.0 "
                            "(Linux; Android 10) "
                            "AppleWebKit/537.36 "
                            "Chrome/128 Safari/537.36"
                        ),
                        "Accept-Language": (
                            "th-TH,th;q=0.9,en;q=0.8"
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

            if start_date <= draw_date <= today_date:
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


def normalize_result_numbers(text):
    if not text:
        return []

    return [
        x.strip().zfill(3)
        for x in str(text).split(",")
        if x.strip()
    ]


def compare_formula_to_result(calc, row):
    predicted2 = calc["number_2"]
    predicted3 = calc["number_3"]
    predicted6 = calc["number_6"]

    actual2 = str(
        row.get("เลขท้าย 2 ตัว", "")
    ).zfill(2)

    actual_front3 = (
        normalize_result_numbers(
            row.get(
                "เลขหน้า 3 ตัว",
                "",
            )
        )
    )

    actual_back3 = (
        normalize_result_numbers(
            row.get(
                "เลขท้าย 3 ตัว",
                "",
            )
        )
    )

    actual6 = str(
        row.get("รางวัลที่ 1", "")
    ).zfill(6)

    return {
        "2": predicted2 == actual2,
        "3": (
            predicted3 in actual_front3
            or predicted3 in actual_back3
        ),
        "6": predicted6 == actual6,
    }


def run_backtest(rows, limit):
    sample = rows[:limit]
    results = []

    hit2 = 0
    hit3 = 0
    hit6 = 0

    for row in sample:
        target_date = row["_date"]

        calc = run_lotto_formula(
            target_date
        )

        if not calc.get("ok"):
            continue

        compare = compare_formula_to_result(
            calc,
            row,
        )

        if compare["2"]:
            hit2 += 1

        if compare["3"]:
            hit3 += 1

        if compare["6"]:
            hit6 += 1

        results.append(
            {
                "วันที่": row["วันที่"],
                "สูตร 2 ตัว": calc["number_2"],
                "จริง 2 ตัว": row[
                    "เลขท้าย 2 ตัว"
                ],
                "2 ตัว": (
                    "ตรง"
                    if compare["2"]
                    else "-"
                ),
                "สูตร 3 ตัว": calc["number_3"],
                "จริง 3 ตัว": (
                    row["เลขหน้า 3 ตัว"]
                    + " / "
                    + row["เลขท้าย 3 ตัว"]
                ),
                "3 ตัว": (
                    "ตรง"
                    if compare["3"]
                    else "-"
                ),
                "สูตร 6 ตัว": calc["number_6"],
                "จริงรางวัลที่ 1": row[
                    "รางวัลที่ 1"
                ],
                "6 ตัว": (
                    "ตรง"
                    if compare["6"]
                    else "-"
                ),
            }
        )

    return {
        "rows": results,
        "count": len(results),
        "hit2": hit2,
        "hit3": hit3,
        "hit6": hit6,
    }


def render_formula_details(calc):
    st.markdown(
        "### 🔬 รายละเอียดทุกหลัก"
    )

    for component in calc["components"]:
        st.markdown(
            f"#### {component['name']} "
            f"= {component['value']}"
        )

        for item in component["details"]:
            digit = item["digit"]

            st.write(
                f"หลักที่ {item['position']} : "
                f"{digit}"
            )

            st.code(
                f"{digit} / {PHI} = "
                f"{item['divide']:.6f}\n"
                f"{item['divide']:.6f} × "
                f"{LUNAR_CYCLE} = "
                f"{item['multiply']:.6f}\n"
                f"{item['multiply']:.6f} "
                f"{'-' if calc['lunar']['phase'] == 'ขึ้น' else '+'} "
                f"{calc['lunar']['day']} = "
                f"{item['adjusted']:.6f}"
            )

        st.write(
            f"รวม {component['name']} = "
            f"{component['total']:.6f}"
        )

    st.divider()

    st.markdown(
        f"### Σ รวมทั้งหมด = "
        f"{calc['grand_total']:.6f}"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "ผลทดลอง 2 ตัว",
            calc["number_2"],
        )

    with c2:
        st.metric(
            "ผลทดลอง 3 ตัว",
            calc["number_3"],
        )

    with c3:
        st.metric(
            "ผลทดลอง 6 ตัว",
            calc["number_6"],
        )


st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(
            circle at top left,
            rgba(255, 0, 70, 0.14),
            transparent 32%
        ),
        radial-gradient(
            circle at top right,
            rgba(0, 100, 255, 0.14),
            transparent 32%
        ),
        #050505;
}

h1, h2, h3 {
    text-shadow:
        0 0 8px rgba(255, 0, 80, 0.45),
        0 0 16px rgba(0, 150, 255, 0.25);
}

div[data-testid="stMetric"] {
    border: 1px solid rgba(0, 220, 255, 0.35);
    border-radius: 12px;
    padding: 10px;
    background: rgba(10, 10, 20, 0.65);
}

.stButton > button {
    border-radius: 10px;
    font-weight: 700;
}

[data-testid="stTabs"] button {
    font-weight: 700;
}
</style>
""",
    unsafe_allow_html=True,
)


now = datetime.now(BANGKOK)

st.title("Mon101")

st.caption(
    "ปฏิทิน • จันทรคติ • นักษัตร • ราศี • "
    "เวลาโลก • อากาศ • ปฏิทิน • "
    "เปรียบเทียบวันที่ • Golden Ratio • "
    "เพลง • หวยรัฐบาล • หวยลาว • หวยฮานอย"
)

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
    tab11,
    tab12,
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
        "11 หวยลาว",
        "12 หวยฮานอย",
    ]
)


with tab1:
    show_logo()

    st.header("📅 วันที่")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "วัน",
            weekday_thai(now),
        )

    with c2:
        st.metric(
            "วันที่",
            str(now.day),
        )

    with c3:
        st.metric(
            "เวลา",
            now.strftime("%H:%M:%S"),
        )

    st.divider()

    st.subheader("วันที่ปัจจุบัน")
    st.write(thai_date_text(now))
    st.write(f"ค.ศ. {now.year}")
    st.write(f"พ.ศ. {now.year + 543}")


with tab2:
    show_logo()

    st.header("🌙 จันทรคติ")

    lunar_info = get_thai_lunar_info(
        now.date()
    )

    if lunar_info["text"]:
        st.subheader(
            "วันที่จันทรคติ"
        )
        st.success(
            lunar_info["text"]
        )
    else:
        st.warning(
            "ยังไม่สามารถอ่านข้อมูลจันทรคติได้"
        )


with tab3:
    show_logo()

    st.header(
        "🐉 นักษัตร / ♈ ราศี"
    )

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("นักษัตร")

        st.metric(
            "ปีนักษัตร",
            get_chinese_zodiac(
                now.year
            ),
        )

        st.write(
            f"หมายเลขนักษัตร "
            f"{get_zodiac_number(now.year)}"
        )

        st.write(
            f"พ.ศ. {now.year + 543}"
        )

    with c2:
        st.subheader(
            "ราศีตะวันตก"
        )

        sign, degree = (
            get_western_zodiac(
                now.year,
                now.month,
                now.day,
            )
        )

        if sign:
            st.metric(
                "ราศี",
                sign,
            )

            st.write(
                f"ตำแหน่งดวงอาทิตย์ "
                f"ประมาณ {degree:.2f}°"
            )
        else:
            st.warning(
                "ไม่สามารถคำนวณราศีได้"
            )


with tab4:
    show_logo()

    st.header("🌍 เวลาโลก")

    now_utc = datetime.now(
        timezone.utc
    )

    rows = []

    for country, zone_name in (
        WORLD_ZONES.items()
    ):
        local = now_utc.astimezone(
            ZoneInfo(zone_name)
        )

        rows.append(
            {
                "สถานที่": country,
                "เขตเวลา": zone_name,
                "วันที่": local.strftime(
                    "%d/%m/%Y"
                ),
                "เวลา": local.strftime(
                    "%H:%M:%S"
                ),
            }
        )

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
                "results",
                [],
            )

            if not results:
                st.error(
                    "ไม่พบเมืองนี้"
                )

            else:
                place = results[0]

                weather = requests.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": place[
                            "latitude"
                        ],
                        "longitude": place[
                            "longitude"
                        ],
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
                    "current",
                    {},
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
            st.error(
                "ดึงข้อมูลอากาศไม่สำเร็จ"
            )
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

    st.subheader(
        thai_date_text(selected_dt)
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

    lunar = get_thai_lunar_info(
        selected
    )

    if lunar["text"]:
        st.info(
            f"จันทรคติ: {lunar['text']}"
        )


with tab7:
    show_logo()

    st.header(
        "🔎 เปรียบเทียบวันที่"
    )

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

    difference = (
        date2 - date1
    ).days

    st.metric(
        "จำนวนวันที่ต่างกัน",
        abs(difference),
    )

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


with tab8:
    show_logo()

    st.header(
        "🌀 Golden Ratio"
    )

    phi = PHI

    st.metric(
        "φ (Phi)",
        f"{phi:.10f}",
    )

    st.write(
        "ค่าที่ใช้ในสูตร LOTTO LAB = 1.618"
    )

    st.write(
        "สูตรทางคณิตศาสตร์เต็ม "
        "φ = (1 + √5) / 2"
    )

    st.divider()

    number = st.number_input(
        "ใส่ตัวเลข",
        value=100.0,
        key="golden_number",
    )

    c1, c2 = st.columns(2)

    with c1:
        st.write(
            "คูณ Golden Ratio"
        )

        st.success(
            f"{number * phi:.10f}"
        )

    with c2:
        st.write(
            "หาร Golden Ratio"
        )

        st.info(
            f"{number / phi:.10f}"
        )


with tab9:
    show_logo()

    st.header("🎵 เพลง")

    st.caption(
        "เครื่องเล่นเพลงยังใช้ไฟล์เพลงในโฟลเดอร์เดียวกับ app.py"
    )

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
        st.caption(str(e))

    if music_files:
        st.success(
            f"พบไฟล์เพลง "
            f"{len(music_files)} ไฟล์"
        )

        for filename in music_files:
            st.subheader(
                f"🎧 {filename}"
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
                    f"เปิดเพลงไม่ได้: "
                    f"{filename}"
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

    st.header(
        "🎟️ หวยรัฐบาล"
    )

    st.markdown(
        """
        <div style="
            padding:16px;
            border-radius:14px;
            border:1px solid rgba(255,0,90,.45);
            background:linear-gradient(
                135deg,
                rgba(255,0,70,.12),
                rgba(0,120,255,.10),
                rgba(0,255,150,.08)
            );
        ">
        <h2 style="margin-top:0;">
        🧪 MON101 LOTTO LAB
        </h2>
        <p>
        ห้องทดลองสูตรตัวเลขจากข้อมูลวันที่จริง
        โดยใช้ 1.618 และ 29.53
        พร้อมคำนวณจันทรคติข้างขึ้น/ข้างแรม
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader(
        "📚 ผลรางวัลย้อนหลัง 12 ปี"
    )

    current_date = now.date()

    first_date = date(
        current_date.year - 12,
        1,
        1,
    )

    st.caption(
        "ช่วงข้อมูล: "
        f"{first_date.strftime('%d/%m/%Y')} ถึง "
        f"{current_date.strftime('%d/%m/%Y')}"
    )

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
                height=550,
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
                "ดาวน์โหลดหวยรัฐบาลย้อนหลัง CSV",
                data=csv_data,
                file_name=(
                    "thai_lottery_history.csv"
                ),
                mime="text/csv",
                key="thai_lottery_history_csv",
            )

        else:
            st.warning(
                "ยังไม่พบข้อมูลหวยรัฐบาล"
            )

    except Exception as e:
        st.error(
            "โหลดข้อมูลย้อนหลังไม่สำเร็จ"
        )
        st.code(str(e))

    st.divider()

    st.subheader(
        "🔬 ทดลองสูตรกับวันที่"
    )

    selected_lotto_date = st.date_input(
        "เลือกวันที่งวดที่ต้องการทดลอง",
        value=now.date(),
        key="lotto_formula_date",
    )

    calc = run_lotto_formula(
        selected_lotto_date
    )

    if calc.get("ok"):

        st.markdown(
            "### 📅 ค่าที่ป้อนเข้าสูตร"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "วัน",
                f"{calc['weekday']} "
                f"({calc['weekday_name']})",
            )

        with c2:
            st.metric(
                "เดือน",
                f"{calc['month']} "
                f"({calc['month_name']})",
            )

        with c3:
            st.metric(
                "พ.ศ.",
                calc["buddhist_year"],
            )

        with c4:
            st.metric(
                "นักษัตร",
                f"{calc['zodiac_number']} "
                f"({calc['zodiac']})",
            )

        lunar = calc["lunar"]

        st.markdown(
            "### 🌙 จันทรคติจริงของวันที่"
        )

        if lunar["phase"] == "ขึ้น":
            st.success(
                f"ข้างขึ้น {lunar['day']} ค่ำ "
                f"เดือน {lunar['month']}"
            )

        elif lunar["phase"] == "แรม":
            st.info(
                f"ข้างแรม {lunar['day']} ค่ำ "
                f"เดือน {lunar['month']}"
            )

        st.code(
            f"{lunar['text']}\n\n"
            f"กฎสูตร:\n"
            f"ข้างขึ้น -> ผล × 29.53 - วันค่ำ\n"
            f"ข้างแรม -> ผล × 29.53 + วันค่ำ"
        )

        st.divider()

        st.markdown(
            "### ⚙️ ค่าคงที่ของสูตร"
        )

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "Golden Ratio",
                "1.618",
            )

        with c2:
            st.metric(
                "Synodic Month",
                "29.53",
            )

        render_formula_details(
            calc
        )

        st.divider()

        st.markdown(
            "### 🎯 ตัวเลขจากการทดลอง"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(
                f"# `{calc['number_2']}`"
            )
            st.caption(
                "2 ตัว"
            )

        with c2:
            st.markdown(
                f"# `{calc['number_3']}`"
            )
            st.caption(
                "3 ตัว"
            )

        with c3:
            st.markdown(
                f"# `{calc['number_6']}`"
            )
            st.caption(
                "6 ตัว"
            )

    else:
        st.error(
            "คำนวณไม่ได้: "
            + calc.get(
                "error",
                "ไม่ทราบสาเหตุ",
            )
        )

    st.divider()
    st.subheader(
        "🔎 เปรียบเทียบกับผลจริงของงวด"
    )

    try:
        historical_rows = get_lottery_history(
            selected_lotto_date,
            selected_lotto_date,
        )

        if historical_rows and calc.get("ok"):
            actual = historical_rows[0]

            compare = (
                compare_formula_to_result(
                    calc,
                    actual,
                )
            )

            st.write(
                f"วันที่: "
                f"**{actual['วันที่']}**"
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.write(
                    "สูตร 2 ตัว"
                )
                st.code(
                    calc["number_2"]
                )
                st.write(
                    "ผลจริง: "
                    + actual[
                        "เลขท้าย 2 ตัว"
                    ]
                )

                if compare["2"]:
                    st.success(
                        "ตรง 2 ตัว"
                    )
                else:
                    st.info(
                        "ไม่ตรง"
                    )

            with c2:
                st.write(
                    "สูตร 3 ตัว"
                )
                st.code(
                    calc["number_3"]
                )
                st.write(
                    "หน้า 3: "
                    + actual[
                        "เลขหน้า 3 ตัว"
                    ]
                )
                st.write(
                    "ท้าย 3: "
                    + actual[
                        "เลขท้าย 3 ตัว"
                    ]
                )

                if compare["3"]:
                    st.success(
                        "ตรง 3 ตัว"
                    )
                else:
                    st.info(
                        "ไม่ตรง"
                    )

            with c3:
                st.write(
                    "สูตร 6 ตัว"
                )
                st.code(
                    calc["number_6"]
                )
                st.write(
                    "รางวัลที่ 1: "
                    + actual[
                        "รางวัลที่ 1"
                    ]
                )

                if compare["6"]:
                    st.success(
                        "ตรง 6 ตัว"
                    )
                else:
                    st.info(
                        "ไม่ตรง"
                    )

        else:
            st.warning(
                "ไม่พบผลจริงของวันที่เลือก "
                "หรือวันที่นั้นยังไม่มีข้อมูล"
            )

    except Exception as e:
        st.warning(
            "ไม่สามารถเปรียบเทียบผลจริงได้"
        )
        st.caption(str(e))

    st.divider()

    st.subheader(
        "📊 Backtest สูตรกับผลย้อนหลัง"
    )

    st.caption(
        "ส่วนนี้ใช้ตรวจสอบสูตรกับข้อมูลในอดีต "
        "ไม่ใช่การรับประกันหรือยืนยันผลในอนาคต"
    )

    backtest_count = st.selectbox(
        "จำนวนงวดที่ต้องการทดสอบ",
        [20, 50, 100, 200, 500],
        index=1,
        key="backtest_count",
    )

    if st.button(
        "🚀 เริ่ม Backtest",
        key="run_backtest_button",
    ):

        try:
            with st.spinner(
                "กำลังคำนวณย้อนหลัง..."
            ):
                backtest = run_backtest(
                    rows,
                    backtest_count,
                )

            if backtest["count"] == 0:
                st.warning(
                    "ไม่มีข้อมูลที่คำนวณได้"
                )

            else:
                c1, c2, c3, c4 = (
                    st.columns(4)
                )

                with c1:
                    st.metric(
                        "จำนวนงวด",
                        backtest["count"],
                    )

                with c2:
                    st.metric(
                        "ตรง 2 ตัว",
                        backtest["hit2"],
                    )

                with c3:
                    st.metric(
                        "ตรง 3 ตัว",
                        backtest["hit3"],
                    )

                with c4:
                    st.metric(
                        "ตรง 6 ตัว",
                        backtest["hit6"],
                    )

                result_df = (
                    __import__("pandas")
                    .DataFrame(
                        backtest["rows"]
                    )
                )

                st.dataframe(
                    result_df,
                    use_container_width=True,
                    hide_index=True,
                    height=600,
                )

                csv_backtest = (
                    result_df.to_csv(
                        index=False,
                        encoding="utf-8-sig",
                    )
                )

                st.download_button(
                    "ดาวน์โหลดผล Backtest CSV",
                    data=csv_backtest,
                    file_name=(
                        "mon101_lotto_backtest.csv"
                    ),
                    mime="text/csv",
                    key="backtest_csv",
                )

        except Exception as e:
            st.error(
                "Backtest ไม่สำเร็จ"
            )
            st.code(str(e))

    st.divider()

    st.subheader(
        "🔎 ค้นหาเลขจากข้อมูลย้อนหลัง"
    )

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
                matches = []

                for row in rows:
                    if (
                        search_number
                        == row["รางวัลที่ 1"]
                    ):
                        matches.append(
                            {
                                "วันที่": row[
                                    "วันที่"
                                ],
                                "ประเภท":
                                    "รางวัลที่ 1",
                                "เลข":
                                    search_number,
                            }
                        )

                    if (
                        search_number[-2:]
                        == row[
                            "เลขท้าย 2 ตัว"
                        ]
                    ):
                        matches.append(
                            {
                                "วันที่": row[
                                    "วันที่"
                                ],
                                "ประเภท":
                                    "เลขท้าย 2 ตัว",
                                "เลข":
                                    search_number[-2:],
                            }
                        )

                    if (
                        search_number[-3:]
                        in row[
                            "เลขท้าย 3 ตัว"
                        ].split(", ")
                    ):
                        matches.append(
                            {
                                "วันที่": row[
                                    "วันที่"
                                ],
                                "ประเภท":
                                    "เลขท้าย 3 ตัว",
                                "เลข":
                                    search_number[-3:],
                            }
                        )

                    if (
                        search_number[:3]
                        in row[
                            "เลขหน้า 3 ตัว"
                        ].split(", ")
                    ):
                        matches.append(
                            {
                                "วันที่": row[
                                    "วันที่"
                                ],
                                "ประเภท":
                                    "เลขหน้า 3 ตัว",
                                "เลข":
                                    search_number[:3],
                            }
                        )

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
                        "ไม่พบเลขนี้ในข้อมูลย้อนหลัง"
                    )

            except Exception as e:
                st.error(
                    "ค้นหาข้อมูลไม่สำเร็จ"
                )
                st.caption(str(e))


with tab11:
    show_logo()

    st.header("🇱🇦 หวยลาว")

    st.subheader(
        "📚 ผลหวยลาวย้อนหลัง 1 ปี"
    )

    st.caption(
        "ข้อมูลย้อนหลังประมาณ 365 วัน "
        "จากหน้าเผยแพร่สถิติภายนอก"
    )

    if st.button(
        "โหลดผลหวยลาวย้อนหลัง 1 ปี",
        key="lao_load",
    ):
        st.session_state[
            "lao_loaded"
        ] = True

    if st.session_state.get(
        "lao_loaded",
        False,
    ):
        try:
            lao_rows = (
                get_foreign_lottery_history(
                    "lao"
                )
            )

            if lao_rows:
                display = [
                    {
                        k: v
                        for k, v in row.items()
                        if k != "_date"
                    }
                    for row in lao_rows
                ]

                st.success(
                    f"พบ {len(display):,} งวด"
                )

                st.dataframe(
                    display,
                    use_container_width=True,
                    hide_index=True,
                )

                csv_data = (
                    __import__("pandas")
                    .DataFrame(display)
                    .to_csv(
                        index=False,
                        encoding="utf-8-sig",
                    )
                )

                st.download_button(
                    "ดาวน์โหลดหวยลาว CSV",
                    data=csv_data,
                    file_name=(
                        "lao_lottery_1year.csv"
                    ),
                    mime="text/csv",
                    key="lao_csv",
                )

            else:
                st.warning(
                    "ยังไม่พบข้อมูลหวยลาว "
                    "หรือเว็บไซต์ต้นทางไม่ตอบสนอง"
                )

        except Exception as e:
            st.error(
                "โหลดข้อมูลหวยลาวไม่สำเร็จ"
            )
            st.caption(str(e))


with tab12:
    show_logo()

    st.header("🇻🇳 หวยฮานอย")

    st.subheader(
        "📚 ผลหวยฮานอยย้อนหลัง 1 ปี"
    )

    st.caption(
        "ข้อมูลย้อนหลังประมาณ 365 วัน "
        "จากหน้าเผยแพร่สถิติภายนอก"
    )

    if st.button(
        "โหลดผลหวยฮานอยย้อนหลัง 1 ปี",
        key="hanoi_load",
    ):
        st.session_state[
            "hanoi_loaded"
        ] = True

    if st.session_state.get(
        "hanoi_loaded",
        False,
    ):
        try:
            hanoi_rows = (
                get_foreign_lottery_history(
                    "hanoi"
                )
            )

            if hanoi_rows:
                display = [
                    {
                        k: v
                        for k, v in row.items()
                        if k != "_date"
                    }
                    for row in hanoi_rows
                ]

                st.success(
                    f"พบ {len(display):,} งวด"
                )

                st.dataframe(
                    display,
                    use_container_width=True,
                    hide_index=True,
                )

                csv_data = (
                    __import__("pandas")
                    .DataFrame(display)
                    .to_csv(
                        index=False,
                        encoding="utf-8-sig",
                    )
                )

                st.download_button(
                    "ดาวน์โหลดหวยฮานอย CSV",
                    data=csv_data,
                    file_name=(
                        "hanoi_lottery_1year.csv"
                    ),
                    mime="text/csv",
                    key="hanoi_csv",
                )

            else:
                st.warning(
                    "ยังไม่พบข้อมูลหวยฮานอย "
                    "หรือเว็บไซต์ต้นทางไม่ตอบสนอง"
                )

        except Exception as e:
            st.error(
                "โหลดข้อมูลหวยฮานอยไม่สำเร็จ"
            )
            st.caption(str(e))


st.divider()

st.caption(
    "MON101 • Golden Ratio 1.618 • "
    "Lunar Synodic Period 29.53"
)

st.caption(
    "ห้องทดลองตัวเลขนี้เป็นการคำนวณเชิงสถิติ/ทดลอง "
    "จากข้อมูลวันที่และผลย้อนหลัง "
    "ไม่ใช่การรับประกันผลรางวัลในอนาคต"
)   
    
    
