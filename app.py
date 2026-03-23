import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go 
import numpy as np
from datetime import datetime, timedelta
import calendar

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="Home Energy Master", page_icon="⚡", layout="wide")

# 🟢 ฟังก์ชัน: เดาชื่ออุปกรณ์จากค่าไฟที่เกินมา
def analyze_appliance(error_kw):
    if error_kw >= 3.0:
        return "🔥 **อันตรายมาก!** (เกิน 3.0 kW) น่าจะเป็นเครื่องทำน้ำอุ่นเปิดทิ้งไว้, เตาอบไฟฟ้า หรือ แอร์ขนาดใหญ่"
    elif error_kw >= 1.5:
        return "♨️ **ระดับกลาง** (1.5 - 3.0 kW) น่าจะเป็นเตารีด, หม้อต้มน้ำร้อน, ไมโครเวฟ หรือ แอร์ห้องนอน"
    elif error_kw >= 0.5:
        return "📺 **ระดับเริ่มต้น** (0.5 - 1.5 kW) น่าจะเป็นทีวีจอใหญ่, คอมพิวเตอร์ หรือตู้เย็นปิดไม่สนิท"
    else:
        return "💡 **เล็กน้อย** (ต่ำกว่า 0.5 kW) อาจจะลืมปิดพัดลม หรือหลอดไฟหลายดวง"

# 2. โหลดโมเดล AI
@st.cache_resource
def load_model_and_threshold():
    model = joblib.load('smart_home_xgb.pkl')
    threshold = joblib.load('smart_threshold.pkl')
    safe_threshold = abs(float(threshold))
    return model, safe_threshold

model, safe_threshold = load_model_and_threshold()

# 3. ส่วนหัวของเว็บ
st.title('⚡ Home Energy Master: ระบบบริหารจัดการพลังงานบ้านอัจฉริยะ')
st.markdown("---")

# 4. แถบด้านข้าง (Sidebar)
st.sidebar.header('⚙️ ตั้งค่าระบบ')
unit_cost = st.sidebar.number_input('💰 ค่าไฟฟ้าต่อหน่วย (บาท)', value=4.0, step=0.1, min_value=0.0)
st.sidebar.markdown("---")
st.sidebar.subheader("📅 เลือกวันเพื่อดูข้อมูล")

today = datetime.today()
selected_date = st.sidebar.date_input('เลือกวันที่ต้องการตรวจสอบ', value=today)

# 5. ฟังก์ชันจำลองข้อมูล (ปรับปรุงให้รองรับการสุ่มรายวันในเดือนนั้นๆ)
@st.cache_data
def get_simulated_data(date, unit_cost):
    # ใช้ Seed จากวันที่เพื่อให้ค่าคงที่สำหรับวันนั้นๆ
    np.random.seed(date.day + date.month * 100)
    hours = np.arange(24)
    base_load = (np.sin((hours - 3) * np.pi / 12) * 0.4) + 0.8
    weekend_mult = 1.2 if date.weekday() >= 5 else 1.0
    
    power = (base_load * weekend_mult) + np.random.normal(0, 0.08, 24)
    if date.day % 3 == 0: power[14:19] += 2.1 
    if date.day == 13: power[20:23] = 0.05 
    
    return pd.DataFrame({'Hour': hours, 'Power': np.maximum(0.2, power)})

# ดึงข้อมูลของวันนี้ และเมื่อวาน
df_today = get_simulated_data(selected_date, unit_cost)
df_yesterday = get_simulated_data(selected_date - timedelta(days=1), unit_cost)

# --- ส่วนคำนวณรายเดือน ---
# จำลองข้อมูลสะสมตั้งแต่วันที่ 1 ของเดือน จนถึงวันที่เลือก
total_month_kwh = 0
for d in range(1, selected_date.day + 1):
    sim_date = selected_date.replace(day=d)
    day_data = get_simulated_data(sim_date, unit_cost)
    total_month_kwh += day_data['Power'].sum()

last_day_of_month = calendar.monthrange(selected_date.year, selected_date.month)[1]
avg_daily_kwh = total_month_kwh / selected_date.day
forecast_month_kwh = avg_daily_kwh * last_day_of_month
# -----------------------

# 6. Dashboard ภาพรวม
st.subheader(f"📊 สรุปภาพรวมพลังงานประจำวันที่ {selected_date.strftime('%d %B %Y')}")

total_power_today = df_today['Power'].sum()
total_cost_today = total_power_today * unit_cost
power_diff = total_power_today - df_yesterday['Power'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("⚡ การใช้ไฟรวมวันนี้", f"{total_power_today:.2f} kWh", f"{power_diff:.2f} kWh vs เมื่อวาน")
col2.metric("💰 ประมาณการค่าไฟวันนี้", f"{total_cost_today:.2f} บาท")
col3.metric("📉 เฉลี่ยรายชั่วโมง", f"{df_today['Power'].mean():.2f} kW")

# ส่วนแสดงผลรายเดือน
st.info(f"📅 **ข้อมูลประจำเดือน {selected_date.strftime('%B %Y')}**")
m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("🗓️ สะสมต้นเดือน - ปัจจุบัน", f"{total_month_kwh:.2f} kWh")
m_col2.metric("💸 ค่าไฟสะสม ณ ตอนนี้", f"{total_month_kwh * unit_cost:,.2f} บาท")
m_col3.metric("🔮 AI คาดการณ์บิลสิ้นเดือน", f"{forecast_month_kwh * unit_cost:,.2f} บาท", help="คำนวณจากค่าเฉลี่ยการใช้ไฟรายวันของคุณในเดือนนี้")

st.markdown("---")

# 7. กราฟและการจับผิดโดย AI
st.subheader("📈 กราฟวิเคราะห์การใช้ไฟฟ้า")
fig = go.Figure()

fig.add_trace(go.Scatter(x=df_yesterday['Hour'], y=df_yesterday['Power'], 
                         mode='lines', name='เมื่อวาน', line=dict(color='gray', width=2, dash='dash')))
fig.add_trace(go.Scatter(x=df_today['Hour'], y=df_today['Power'], 
                         mode='lines+markers', name='วันนี้', line=dict(color='#1f77b4', width=3)))

# 🧠 AI Detection
expected_cols = ['Hour', 'DayOfWeek', 'IsWeekend', 'Power_Lag1', 'Power_Lag24']
final_input = pd.DataFrame(0.0, index=np.arange(24), columns=expected_cols)
final_input['Hour'] = df_today['Hour']
final_input['DayOfWeek'] = selected_date.weekday()
final_input['IsWeekend'] = 1 if selected_date.weekday() >= 5 else 0
final_input['Power_Lag1'] = df_today['Power'].shift(1).fillna(df_yesterday['Power'].iloc[-1]).values
final_input['Power_Lag24'] = df_yesterday['Power'].values

expected_powers = model.predict(final_input)
errors = df_today['Power'] - expected_powers
anomalies = np.abs(errors) > safe_threshold

# มาร์คจุดสีแดง
anomaly_hours = df_today[anomalies]
fig.add_trace(go.Scatter(x=anomaly_hours['Hour'], y=anomaly_hours['Power'], 
                         mode='markers', name='⚠️ ผิดปกติ!', marker=dict(color='red', size=12, symbol='x')))

fig.update_layout(xaxis_title="ชั่วโมง (Hour)", yaxis_title="กิโลวัตต์ (kW)", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig, use_container_width=True)

# 8. สรุปความผิดปกติ
st.subheader("🚨 รายงานจาก AI")
if any(anomalies):
    for idx, is_anomaly in enumerate(anomalies):
        if is_anomaly:
            error_val = errors.iloc[idx]
            if error_val > 0:
                st.warning(f"🕒 {idx:02d}:00 น. : ใช้ไฟเกินคาดการณ์ {error_val:.2f} kW -> {analyze_appliance(error_val)}")
            else:
                st.info(f"🕒 {idx:02d}:00 น. : ใช้ไฟต่ำกว่าปกติ {abs(error_val):.2f} kW (อาจมีไฟดับหรือไม่มีคนอยู่บ้าน)")
else:
    st.success("✅ วันนี้พฤติกรรมการใช้ไฟเป็นปกติ")

st.markdown("---")
st.caption("Developed by ธนพล แสงนวล | ข้อมูลรายเดือนเป็นการจำลองเพื่อประกอบการวิเคราะห์แนวโน้มค่าใช้จ่าย")
