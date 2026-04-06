import streamlit as st
import requests
import time
import pandas as pd
from twilio.rest import Client
from datetime import datetime

# --- 1. SETUP ---
try:
    OWM_API_KEY = st.secrets["OWM_API_KEY"]
    TWILIO_SID = st.secrets["TWILIO_SID"]
    TWILIO_TOKEN = st.secrets["TWILIO_TOKEN"]
    WHATSAPP_FROM = st.secrets["WHATSAPP_FROM"]
    WHATSAPP_TARGET = st.secrets["WHATSAPP_TARGET"]
except Exception as e:
    st.error("Secrets are not configured in Streamlit Cloud!")
    st.stop()


# Initialize Mixer
if 'mixer_init' not in st.session_state:
    pygame.mixer.init()
    st.session_state.mixer_init = True

# --- 2. STATE MANAGEMENT ---
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'worker_list' not in st.session_state:
    st.session_state.worker_list = []
if 'l_b' not in st.session_state: # Last Break tracker
    st.session_state.l_b = None

# --- 3. CORE FUNCTIONS ---

def log_event(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {msg}")

def send_whatsapp(text):
    """Sends the actual WhatsApp message via Twilio."""
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(body=text, from_=WHATSAPP_FROM, to=WHATSAPP_TARGET)
        log_event("📲 WhatsApp Notification Sent")
    except Exception as e:
        log_event(f"⚠️ WhatsApp Failed: {e}")

def trigger_alert(filename, label):
    """Sends WhatsApp and prepares audio for the browser."""
    log_event(f"🔊 Alert: {label}")
    send_whatsapp(f"Engro Safety Alert: {label}")
    
    # Store the latest alert in session state so the UI can show the audio player
    st.session_state.current_audio = filename
    st.session_state.audio_label = label

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Daharki&appid={OWM_API_KEY}&units=metric"
        res = requests.get(url).json()
        return res['main']['temp'], res['main']['humidity'], res['weather'][0]['main']
    except:
        return 28.0, 50, "Clear"

# --- 4. UI STYLING ---
st.set_page_config(page_title="Engro Safety Master", layout="wide")
st.markdown("""
    <style>
    /* Force a clean light background */
    .stApp {
        background-color: #FFFFFF !important;
    }

    /* Force ALL general text to Black */
    h1, h2, h3, h4, p, span, label {
        color: #000000 !important;
    }

    /* 1. THE GREEN BUTTONS (Add Worker & Start Shift) */
    /* This targets the first and third buttons appearing in the code */
    button[kind="secondary"], button[kind="primary"] {
        background-color: #28A745 !important; /* Industrial Green */
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        height: 3em !important;
        width: 100% !important;
    }

    /* 2. THE RED BUTTON (Stop Shift) */
    /* We target the 'Stop' button specifically by its position or type */
    div[data-testid="stHorizontalBlock"] div:nth-child(2) button {
        background-color: #DC3545 !important; /* Industrial Red */
        color: white !important;
    }

    /* 3. INPUT FIELD FIX */
    /* Making sure you can see what you type */
    input {
        background-color: #F8F9FA !important;
        color: #000000 !important;
        border: 2px solid #28A745 !important; /* Green border for input */
    }

    /* Metric Cards Fix */
    [data-testid="stMetric"] {
        background-color: #F8F9FA !important;
        border: 1px solid #EEEEEE !important;
        border-radius: 10px !important;
    }
    [data-testid="stMetricValue"] { color: #000000 !important; }
    [data-testid="stMetricLabel"] { color: #444444 !important; }

    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Engro Fertilizer: Safety Master")

temp, hum, cond = get_weather()

# Risk Logic
if temp < 28:
    risk_n, em, desc, col = "Low Risk", "🟢", "خطرہ کم ہے: کام جاری رکھیں۔", "#d4edda"
elif 28 <= temp <= 34:
    risk_n, em, desc, col = "Moderate Risk", "🟡", "درمیانہ خطرہ: احتیاط برتیں اور پانی پیئیں۔", "#fff3cd"
else:
    risk_n, em, desc, col = "High Risk", "🔴", "زیادہ خطرہ: سائے میں رہیں اور آرام کریں۔", "#f8d7da"

st.markdown(f"""<div style="background-color:{col}; padding:20px; border-radius:10px; border:2px solid rgba(0,0,0,0.1);">
    <h2 style="margin:0; color: black;">{em} {risk_n}</h2>
    <p style="font-size:18px; margin:0; font-weight:bold; color:black;">{desc}</p>
    </div>""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Live Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("Temp", f"{temp}°C")
    m2.metric("Humidity", f"{hum}%")
    m3.metric("Condition", cond)

    st.divider()
    st.subheader("👷 Worker Management")
    new_w = st.text_input("Enter Worker Name", key="w_input")
    if st.button("Add Worker"):
        if new_w:
            st.session_state.worker_list.append(new_w)
            st.rerun()

    if st.session_state.worker_list:
        st.info(f"Active Team: {', '.join(st.session_state.worker_list)}")

    # BUTTONS
    c1, c2, c3 = st.columns(3)
    if c1.button("🚀 START SHIFT", use_container_width=True):
        st.session_state.start_time = time.time()
        trigger_alert("welcome.mp3", f"Shift Started for {st.session_state.worker_list}")

    if c2.button("🍋 ORS LOG", use_container_width=True):
        trigger_alert("ors_log.mp3", "ORS Distribution Logged.")

    if c3.button("🛑 STOP SHIFT", use_container_width=True):
        trigger_alert("break.mp3", "Shift Ended/Break Time")
        st.session_state.start_time = None
        st.session_state.worker_list = []
        st.rerun()

with col2:
    st.subheader("🔔 Notification Log")
    with st.container(border=True, height=350):
        for log in reversed(st.session_state.logs):
            st.write(log)

if 'current_audio' in st.session_state and st.session_state.current_audio:
    with st.sidebar:
        st.markdown("### 📢 Active Alert")
        st.info(st.session_state.get('audio_label', 'Safety Alert'))
        # The actual player
        st.audio(st.session_state.current_audio, format="audio/mp3", autoplay=True)
        
        if st.button("🗑️ Clear Audio Player"):
            st.session_state.current_audio = None
            st.rerun()

# --- 5. AUTOMATED TIMERS & WEATHER ---
if st.session_state.start_time:
    elap = int((time.time() - st.session_state.start_time) // 60)
    st.write(f"⏱️ **Active Duration:** {elap} Minutes")

    # 15-Minute Water (water.mp3)
    if elap > 0 and elap % 15 == 0:
        if "l_w" not in st.session_state or st.session_state.l_w != elap:
            trigger_alert("water.mp3", "Scheduled Water Break")
            st.session_state.l_w = elap

        # 2-Hour Break Reminder (break.mp3)
    if elap > 0 and elap % 120 == 0:
        if "l_b" not in st.session_state or st.session_state.l_b != elap:
            trigger_alert("break.mp3", "2-Hour Work Cycle Completed: Mandatory Break")
            st.session_state.l_b = elap

    # Weather: Heat (heat_warning.mp3)
    if temp > 33:
        if "l_h" not in st.session_state or (time.time() - st.session_state.l_h > 1800):
            trigger_alert("heat_warning.mp3", f"Temperature Warning: {temp}°C")
            st.session_state.l_h = time.time()

    # Weather: Rain (rain_alert.mp3)
    if "Rain" in cond or "Drizzle" in cond:
        if "l_r" not in st.session_state or (time.time() - st.session_state.l_r > 1800):
            trigger_alert("rain_alert.mp3", "Rain Protection Protocol Activated")
            st.session_state.l_r = time.time()

    time.sleep(2)
    st.rerun()
