import os
import math
from import import datetime, date, timezone
from zoneinfo import ZoneInfo

import requests
import pandas as pd
import streamlit as st

try:
    import ephem
except ImportError:
    ephem = None

try:
    from pythainlp.util import to_lunar_date
except ImportError:
    to_lunar_date = None

try:
    from pythainlp.corpus import th_zodiac
except ImportError:
    th_zodiac = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BANGKOK = ZoneInfo("Asia/Bangkok")

st.set_page_config(page_title="Mon101", page_icon="📅", layout="wide")
st.title("Mon101")
st.caption("ปฏิทิน • จันทรคติ • นักษัตร • ราศี • เวลาโลก • อากาศ • Golden Ratio • เพลง • หวย")

def thai_date(dt):
    months = ["มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน",
              "กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"]
    return f"{dt.day} {months[dt.month - 1]} {dt.year + 543}"

def western_zodiac(dt):
    if ephem is None:
        return {"name": "ไม่พร้อมใช้งาน", "degree": None}
    local_dt = datetime(dt.year, dt.month, dt.day, 12, tzinfo=BANGKOK)
    utc_dt = local_dt.astimezone(timezone.utc).replace(tzinfo=None)
    sun = ephem.Sun(utc_dt)
    longitude = math.degrees(float(ephem.Ecliptic(sun).lon)) % 360.0
    signs = [
        ("เมษ",0,30),("พฤษภ",30,60),("เมถุน",60,90),("กรกฎ",90,120),
        ("สิงห์",120,150),("กันย์",150,180),("ตุล",180,210),("พิจิก",210,240),
        ("ธนู",240,270),("มังกร",270,300),("กุมภ์",300,330),("มีน",330,360)
    ]
    for name, start, end in signs:
        if start <= longitude < end:
            return {"name": name, "degree": longitude - start, "longitude": longitude}
    return {"name": "ไม่ทราบ", "degree": None, "longitude": longitude}

def lunar_date_text(dt):
    if to_lunar_date is None:
        return "ติดตั้ง PyThaiNLP เพื่อแสดงจันทรคติ"
    try:
        return str(to_lunar_date(dt))
    except Exception as exc:
        return f"อ่านจันทรคติไม่ได้: {exc}"

def thai_zodiac_text(dt):
    if th_zodiac is None:
        return "ติดตั้ง PyThaiNLP เพื่อแสดงนักษัตร"
    try:
        return str(th_zodiac(dt.year))
    except Exception as exc:
        return f"อ่านนักษัตรไม่ได้: {exc}"

def weather_code_text(code):
    mapping = {
        0:"ท้องฟ้าแจ่มใส",1:"มีเมฆเล็กน้อย",2:"มีเมฆบางส่วน",3:"มีเมฆมาก",
        45:"มีหมอก",48:"มีหมอกจับตัว",51:"ฝนปรอยเล็กน้อย",53:"ฝนปรอย",
        55:"ฝนปรอยหนัก",61:"ฝนเล็กน้อย",63:"ฝนปานกลาง",65:"ฝนหนัก",
        71:"หิมะเล็กน้อย",73:"หิมะปานกลาง",75:"หิมะหนัก",80:"ฝนซู่เล็กน้อย",
        81:"ฝนซู่ปานกลาง",82:"ฝนซู่หนัก",95:"พายุฝนฟ้าคะนอง",
        96:"พายุฝนฟ้าคะนองและลูกเห็บ",99:"พายุฝนฟ้าคะนองและลูกเห็บหนัก"
    }
    return mapping.get(code, f"รหัสอากาศ {code}")

@st.cache_data(ttl=1800)
def geocode_city(city):
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name":city,"count":1,"language":"th","format":"json"},
        timeout=15
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None

@st.cache_data(ttl=900)
def get_weather(latitude, longitude):
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude":latitude, "longitude":longitude,
            "current":"temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
            "timezone":"Asia/Bangkok"
        },
        timeout=15
    )
    r.raise_for_status()
    return r.json()

def discover_music():
    extensions = (".mp3",".wav",".ogg",".m4a",".aac")
    return sorted(
        os.path.join(APP_DIR, name)
        for name in os.listdir(APP_DIR)
        if os.path.isfile(os.path.join(APP_DIR, name)) and name.lower().endswith(extensions)
    )

def golden_ratio_info(a, b):
    phi = (1 + math.sqrt(5)) / 2
    ratio = a / b
    return {
        "ratio": ratio,
        "phi": phi,
        "difference": abs(ratio - phi),
        "percent_difference": abs(ratio - phi) / phi * 100
    }

def lottery_api():
    try:
        r = requests.post("https://www.glo.or.th/api/lottery/getLotteryResult",
                          json={}, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}

now = datetime.now(BANGKOK)
today = now.date()

tabs = st.tabs([
    "1 วันที่","2 จันทรคติ","3 นักษัตร / ราศี","4 เวลาโลก","5 อากาศ",
    "6 ปฏิทิน","7 เปรียบเทียบวันที่","8 Golden Ratio","9 เพลง","10 หวยรัฐบาล"
])

with tabs[0]:
    st.header("วันที่")
    st.metric("วันที่วันนี้", thai_date(now))
    st.write("วัน:", now.strftime("%A"))
    st.write("เวลา:", now.strftime("%H:%M:%S"))
    st.write("วันที่สากล:", now.strftime("%Y-%m-%d"))

with tabs[1]:
    st.header("จันทรคติ")
    st.write("วันที่:", thai_date(now))
    st.info(lunar_date_text(today))

with tabs[2]:
    st.header("นักษัตร / ราศี")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("นักษัตรไทย")
        st.write(thai_zodiac_text(today))
    with c2:
        st.subheader("ราศีตะวันตก")
        western = western_zodiac(today)
        st.write("ราศี:", western.get("name"))
        if western.get("degree") is not None:
            st.write(f"องศาในราศี: {western['degree']:.2f}°")
            st.write(f"ลองจิจูดดวงอาทิตย์: {western['longitude']:.2f}°")

with tabs[3]:
    st.header("เวลาโลก")
    zones = {
        "ประเทศไทย":"Asia/Bangkok","ญี่ปุ่น":"Asia/Tokyo","จีน":"Asia/Shanghai",
        "สิงคโปร์":"Asia/Singapore","อินเดีย":"Asia/Kolkata","อังกฤษ":"Europe/London",
        "ฝรั่งเศส":"Europe/Paris","นิวยอร์ก":"America/New_York","ลอสแอนเจลิส":"America/Los_Angeles"
    }
    cols = st.columns(3)
    for i, (label, zone_name) in enumerate(zones.items()):
        local = datetime.now(ZoneInfo(zone_name))
        with cols[i % 3]:
            st.metric(label, local.strftime("%H:%M:%S"))
            st.caption(local.strftime("%Y-%m-%d"))

with tabs[4]:
    st.header("อากาศ")
    city = st.text_input("ระบุเมือง", value="Udon Thani", key="weather_city")
    if st.button("ดูอากาศ", key="weather_button"):
        try:
            place = geocode_city(city)
            if not place:
                st.error("ไม่พบเมืองนี้")
            else:
                data = get_weather(place["latitude"], place["longitude"])
                current = data.get("current", {})
                st.subheader(f"{place.get('name', city)}, {place.get('country', '')}")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("อุณหภูมิ", f"{current.get('temperature_2m','-')} °C")
                with c2:
                    st.metric("ความรู้สึก", f"{current.get('apparent_temperature','-')} °C")
                with c3:
                    st.metric("ความชื้น", f"{current.get('relative_humidity_2m','-')} %")
                st.write("สภาพอากาศ:", weather_code_text(current.get("weather_code")))
                st.write("ลม:", f"{current.get('wind_speed_10m','-')} km/h")
        except Exception as exc:
            st.error(f"โหลดข้อมูลอากาศไม่สำเร็จ: {exc}")

with tabs[5]:
    st.header("ปฏิทิน")
    selected_date = st.date_input("เลือกวันที่", value=today, key="calendar_date")
    selected_dt = datetime.combine(selected_date, datetime.min.time(), tzinfo=BANGKOK)
    st.write("วันที่เลือก:", thai_date(selected_dt))
    st.write("วัน:", selected_dt.strftime("%A"))
    st.write("ISO:", selected_date.isoformat())

with tabs[6]:
    st.header("เปรียบเทียบวันที่")
    c1, c2 = st.columns(2)
    with c1:
        date1 = st.date_input("วันที่ 1", value=today, key="compare_date_1")
    with c2:
        date2 = st.date_input("วันที่ 2", value=today, key="compare_date_2")
    difference = (date2 - date1).days
    st.metric("จำนวนวันต่างกัน", f"{abs(difference):,} วัน")
    if difference > 0:
        st.info(f"วันที่ 2 อยู่หลังวันที่ 1 จำนวน {difference:,} วัน")
    elif difference < 0:
        st.info(f"วันที่ 2 อยู่ก่อนวันที่ 1 จำนวน {abs(difference):,} วัน")
    else:
        st.info("เป็นวันเดียวกัน")

with tabs[7]:
    st.header("Golden Ratio")
    st.write("φ (Phi) =", f"{(1 + math.sqrt(5)) / 2:.12f}")
    c1, c2 = st.columns(2)
    with c1:
        a = st.number_input("ค่าที่ 1", value=1.0, format="%.6f", key="golden_a")
    with c2:
        b = st.number_input("ค่าที่ 2", value=1.0, format="%.6f", key="golden_b")
    if b == 0:
        st.error("ค่าที่ 2 ต้องไม่เป็นศูนย์")
    else:
        info = golden_ratio_info(a, b)
        st.metric("อัตราส่วน", f"{info['ratio']:.8f}")
        st.write("ความต่างจาก φ:", f"{info['difference']:.8f}")
        st.write("ความต่างเชิงเปอร์เซ็นต์:", f"{info['percent_difference']:.4f}%")

with tabs[8]:
    st.header("เพลง")
    music_files = discover_music()
    if not music_files:
        st.warning("ยังไม่พบไฟล์เพลง กรุณาวางไฟล์ .mp3/.wav/.ogg/.m4a/.aac ไว้ในโฟลเดอร์เดียวกับ app.py")
    else:
        st.success(f"พบเพลง {len(music_files)} ไฟล์")
        for path in music_files:
            st.write(f"🎵 {os.path.basename(path)}")
            with open(path, "rb") as audio_file:
                st.audio(audio_file.read())

with tabs[9]:
    st.header("หวยรัฐบาล")
    st.warning("ข้อมูลหวยย้อนหลังควรใช้ข้อมูลจากสำนักงานสลากกินแบ่งรัฐบาล และไม่ควรใช้สถิติย้อนหลังเป็นการทำนายงวดถัดไป")
    if st.button("ดึงผลล่าสุดจาก GLO", key="lottery_button"):
        result = lottery_api()
        if isinstance(result, dict) and result.get("error"):
            st.error(f"ดึงข้อมูลไม่สำเร็จ: {result['error']}")
        else:
            st.json(result)
    st.subheader("หมายเหตุเรื่องย้อนหลัง 12 ปี")
    st.write("ส่วนนี้เตรียมพื้นที่สำหรับข้อมูลผลสลากย้อนหลัง แต่จะไม่สร้างข้อมูลขึ้นมาเอง หากแหล่งข้อมูลที่เชื่อถือได้ไม่ส่งข้อมูลมา")

st.divider()
st.caption(f"Mon101 • {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
