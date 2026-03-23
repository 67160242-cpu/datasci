import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go 
import numpy as np
from datetime import datetime, timedelta
import calendar

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="Home Energy Master", page_icon="⚡", layout="wide")

# 🟢 ฟังก์ชัน: วิเคราะห์อุปกรณ์ (ปรับช่วงตามผลวิเคราะห์ใหม่)
def analyze_appliance(error_kw):
    if error_kw >= 3.0:
        return "🔥 **อันตรายมาก!** (เกิน 3.0 kW) น่าจะเป็นเครื่องทำน้ำอุ่นเปิดทิ้งไว้ หรือเตาอบไฟฟ้า"
    elif error_kw >= 1.5:
        return f"♨️ **ระดับสูง** ({error_kw:.2f} kW) ใกล้เคียงจุดผิดปกติที่ AI ตรวจพบ อาจเป็นแอร์ขนาดใหญ่หรือเตารีด"
    elif error_kw >= 0.5:
        return "📺 **ระดับทั่วไป** (0.5 - 1.5 kW) น่าจะเป็นไมโครเวฟ, คอมพิวเตอร์เล่นเกม หรือตู้เย็นปิดไม่สนิท"
    else:
        return "💡 **เล็กน้อย** (ต่ำกว่า 0.5 kW) อาจจะลืมปิดพัดลม หรือหลอดไฟทิ้งไว้"

# 2. โหลดโมเดล AI (ปรับชื่อไฟล์ให้ตรงกับที่เรา Save ล่าสุด)
@st.cache_resource
def load_all_assets():
    # โหลดโมเดล Tuned XGBoost
    model = joblib.load('power_model.pkl') 
    # โหลดรายชื่อ Features (เพื่อให้ลำดับข้อมูลถูกต้อง)
    features_list = joblib.load('model_features.pkl')
    # โหลดค่า Smart Threshold (1.5642)
    threshold_data = joblib.load('threshold_config.pkl')
    safe_threshold = float(threshold_data['smart_threshold'])
    return model, features_list, safe_threshold

try:
    model, features_list, safe_threshold = load_all_assets()
except Exception as e:
    st.error(f"❌ ไม่พบไฟล์โมเดล กรุณาตรวจสอบว่ามีไฟล์ .pkl ครบถ้วน (Error: {e})")
    st.stop()

# 3. ส่วนหัวของเว็บ
st.title('⚡ Home Energy Master: ระบบบริหารจัดการพลังงานบ้านอัจฉริยะ')
st.markdown(f"**ผู้พัฒนา:** คุณอรรณพ ศรีผ่อง (AI-Powered Anomaly Detection)")
st.markdown("---")

# 4. แถบด้านข้าง (Sidebar)
st.sidebar.header('⚙️ ตั้งค่าระบบ')
unit_cost = st.sidebar.number_input('💰 ค่าไฟฟ้าต่อหน่วย (บาท)', value=4.5, step=0.1, min_value=0.0)
st.sidebar.markdown("---")
st.sidebar.subheader("📅 เลือกวันเพื่อดูข้อมูล")

today = datetime.today()
selected_date = st.sidebar.date_input('เลือกวันที่ต้องการตรวจสอบ', value=today)

# 5. ฟังก์ชันจำลองข้อมูล (Simulated Data)
@st.cache_data
def get_simulated_data(date):
    np.random.seed(date.day + date.month * 100)
    hours = np.arange(24)
    # สร้างเส้นฐานพฤติกรรม (Base Load)
    base_load = (np.sin((hours - 3) * np.pi / 12) * 0.5) + 0.9
    weekend_mult = 1.3 if date.weekday() >= 5 else 1.0
    power = (base_load * weekend_mult) + np.random.normal(0, 0.1, 24)
    
    # 🧪 --- ระบบเทส (Easter Eggs) เพื่อโชว์ Anomaly ---
    if date.day % 3 == 0: # ทุกวันที่หาร 3 ลงตัว จะมี Error พุ่งสูง (1.5 kW+)
        power[14:18] += 1.8 # จำลองการลืมปิดอุปกรณ์ใหญ่
    if date.day == 13: # เคสไฟตก/ไม่อยู่บ้าน
        power[10:15] = 0.1
        
    return pd.DataFrame({'Hour': hours, 'Power': np.maximum(0.1, power)})

df_today = get_simulated_data(selected_date)
df_yesterday = get_simulated_data(selected_date - timedelta(days=1))

# --- คำนวณรายเดือน ---
total_month_kwh = 0
for d in range(1, selected_date.day + 1):
    sim_date = selected_date.replace(day=d)
    total_month_kwh += get_simulated_data(sim_date)['Power'].sum()

last_day = calendar.monthrange(selected_date.year, selected_date.month)[1]
forecast_month_kwh = (total_month_kwh / selected_date.day) * last_day

# 6. Dashboard Metrics
st.subheader(f"📊 สรุปภาพรวมประจำวันที่ {selected_date.strftime('%d %B %Y')}")
m1, m2, m3 = st.columns(3)
m1.metric("⚡ ใช้ไฟรวมวันนี้", f"{df_today['Power'].sum():.2f} kWh")
m2.metric("💰 ค่าไฟวันนี้", f"{df_today['Power'].sum() * unit_cost:.2f} บาท")
m3.metric("🔮 คาดการณ์บิลสิ้นเดือน", f"{forecast_month_kwh * unit_cost:,.2f} บาท")
st.markdown("---")

# 7. กราฟและการจับผิดโดย AI (ใช้ Features ของ Tuned XGBoost)
st.subheader("📈 วิเคราะห์ความผิดปกติด้วย AI (Anomaly Detection)")

# เตรียม Input สำหรับ AI ให้ตรงกับ Features ที่เทรนมา
# features_list = ['Hour', 'DayOfWeek', 'Month', 'IsWeekend', 'Power_Lag1', 'Power_Lag24']
input_df = pd.DataFrame(index=np.arange(24))
input_df['Hour'] = df_today['Hour']
input_df['DayOfWeek'] = selected_date.weekday()
input_df['Month'] = selected_date.month
input_df['IsWeekend'] = 1 if selected_date.weekday() >= 5 else 0
input_df['Power_Lag1'] = df_today['Power'].shift(1).fillna(df_yesterday['Power'].iloc[-1]).values
input_df['Power_Lag24'] = df_yesterday['Power'].values

# ให้ AI ทำนายค่าที่ "ควรจะเป็น" (Baseline)
expected_powers = model.predict(input_df[features_list])
errors = df_today['Power'] - expected_powers
anomalies = errors > safe_threshold # แจ้งเตือนเมื่อใช้ไฟเกินเกณฑ์ที่วิเคราะห์ไว้ (1.5642)

# วาดกราฟ Plotly
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_today['Hour'], y=df_today['Power'], name='การใช้ไฟจริง', line=dict(color='#1f77b4', width=3)))
fig.add_trace(go.Scatter(x=df_today['Hour'], y=expected_powers, name='AI Baseline (ปกติ)', line=dict(color='#2ecc71', dash='dot')))

# เพิ่มจุดสีแดงเมื่อเจอ Anomaly
anomaly_data = df_today[anomalies]
if not anomaly_data.empty:
    fig.add_trace(go.Scatter(x=anomaly_data['Hour'], y=anomaly_data['Power'], mode='markers', 
                             name='⚠️ ผิดปกติ!', marker=dict(color='red', size=12, symbol='x')))

fig.update_layout(hovermode="x unified", title=f"เกณฑ์การตรวจจับความผิดปกติ (Threshold): {safe_threshold:.2f} kW")
st.plotly_chart(fig, use_container_width=True)

# 8. รายงานสรุปจาก AI
st.markdown("---")
st.subheader("🚨 รายงานสถานะจาก AI")

if any(anomalies):
    st.error(f"⚠️ ตรวจพบความผิดปกติทั้งหมด {sum(anomalies)} ช่วงเวลา!")
    for hr, is_a in enumerate(anomalies):
        if is_a:
            diff = errors[hr]
            st.warning(f"⏰ **{hr:02d}:00 น.** : ใช้ไฟเกินเกณฑ์ปกติมา {diff:.2f} kW | {analyze_appliance(diff)}")
else:
    st.success("✅ พฤติกรรมการใช้ไฟวันนี้เป็นปกติ ไม่พบสัญญาณการลืมปิดอุปกรณ์ครับ")

with st.expander("📘 ข้อมูลทางเทคนิค"):
    st.write(f"โมเดลที่ใช้งาน: Tuned XGBoost | Smart Threshold: {safe_threshold} kW")
    st.write("ระบบวิเคราะห์จากส่วนต่างระหว่างพฤติกรรมในอดีต (Lag) และการใช้งานจริง ณ ปัจจุบัน")
