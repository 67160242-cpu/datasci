import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go 
import numpy as np
from datetime import datetime, timedelta
import calendar

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="Home Energy Master", page_icon="⚡", layout="wide")

# 🟢 ฟังก์ชัน: วิเคราะห์อุปกรณ์เมื่อพบความผิดปกติ
def analyze_appliance(error_kw):
    if error_kw >= 3.0:
        return "🔥 **อันตรายมาก!** (เกิน 3.0 kW) น่าจะเป็นเครื่องทำน้ำอุ่นเปิดทิ้งไว้, เตาอบไฟฟ้า หรือ แอร์ขนาดใหญ่"
    elif error_kw >= 1.5:
        return "♨️ **ระดับกลาง** (1.5 - 3.0 kW) น่าจะเป็นเตารีด, หม้อต้มน้ำร้อน, ไมโครเวฟ หรือ แอร์ห้องนอน"
    elif error_kw >= 0.5:
        return "📺 **ระดับเริ่มต้น** (0.5 - 1.5 kW) น่าจะเป็นทีวีจอใหญ่, คอมพิวเตอร์ หรือตู้เย็นปิดไม่สนิท"
    else:
        return "💡 **เล็กน้อย** (ต่ำกว่า 0.5 kW) อาจจะลืมปิดพัดลม หรือหลอดไฟหลายดวง"

# 2. โหลดโมเดล AI และค่า Threshold
@st.cache_resource
def load_model_and_threshold():
    # ตรวจสอบให้แน่ใจว่ามีไฟล์ .pkl อยู่ในโฟลเดอร์เดียวกับ app.py
    model = joblib.load('smart_home_xgb.pkl')
    threshold = joblib.load('smart_threshold.pkl')
    safe_threshold = abs(float(threshold))
    return model, safe_threshold

try:
    model, safe_threshold = load_model_and_threshold()
except Exception as e:
    st.error(f"❌ ไม่สามารถโหลดโมเดลได้: {e}")
    st.stop()

# 3. ส่วนหัวของเว็บ
st.title('⚡ Home Energy Master: ระบบบริหารจัดการพลังงานบ้านอัจฉริยะ')
st.markdown(f"**ผู้พัฒนา:** คุณอรรณพ ศีผ่อง | วิชา: Data Science")
st.markdown("---")

# 4. แถบด้านข้าง (Sidebar)
st.sidebar.header('⚙️ ตั้งค่าระบบ')
unit_cost = st.sidebar.number_input('💰 ค่าไฟฟ้าต่อหน่วย (บาท)', value=4.0, step=0.1, min_value=0.0)
st.sidebar.markdown("---")
st.sidebar.subheader("📅 เลือกวันเพื่อดูข้อมูล")

today = datetime.today()
selected_date = st.sidebar.date_input('เลือกวันที่ต้องการตรวจสอบ', value=today)

# 5. ฟังก์ชันจำลองข้อมูล (พร้อมระบบ Test Cases)
@st.cache_data
def get_simulated_data(date):
    # ล็อค Seed ตามวันที่เพื่อให้ข้อมูลคงที่เมื่อเลือกวันเดิม
    np.random.seed(date.day + date.month * 100)
    
    hours = np.arange(24)
    base_load = (np.sin((hours - 3) * np.pi / 12) * 0.4) + 0.8
    
    # คิดค่าพลังงานพื้นฐานตามวันหยุด/วันธรรมดา
    weekend_mult = 1.2 if date.weekday() >= 5 else 1.0
    power = (base_load * weekend_mult) + np.random.normal(0, 0.08, 24)
    
    # --- 🧪 ระบบทดสอบ (Easter Eggs) ---
    if date.day % 3 == 0:  # เคส: ลืมปิดไฟ
        power[14:19] += 2.1 
    if date.day == 13:      # เคส: ไฟดับ
        power[20:23] = 0.05 
    
    return pd.DataFrame({'Hour': hours, 'Power': np.maximum(0.2, power)})

# ดึงข้อมูลของวันนี้ และข้อมูลของเมื่อวาน (เพื่อใช้ทำ Power_Lag24)
df_today = get_simulated_data(selected_date)
df_yesterday = get_simulated_data(selected_date - timedelta(days=1))

# --- 💰 ส่วนคำนวณรายเดือน ---
total_month_kwh = 0
for d in range(1, selected_date.day + 1):
    sim_date = selected_date.replace(day=d)
    day_data = get_simulated_data(sim_date)
    total_month_kwh += day_data['Power'].sum()

last_day_of_month = calendar.monthrange(selected_date.year, selected_date.month)[1]
avg_daily_kwh = total_month_kwh / selected_date.day
forecast_month_kwh = avg_daily_kwh * last_day_of_month

# 6. Dashboard แสดงตัวเลข
st.subheader(f"📊 สรุปภาพรวมประจำวันที่ {selected_date.strftime('%d %B %Y')}")

# แถวที่ 1: รายวัน
t_col1, t_col2, t_col3 = st.columns(3)
total_power_today = df_today['Power'].sum()
t_col1.metric("⚡ ใช้ไฟรวมวันนี้", f"{total_power_today:.2f} kWh")
t_col2.metric("💰 ค่าไฟวันนี้", f"{total_power_today * unit_cost:.2f} บาท")
t_col3.metric("📉 เฉลี่ย kW/ชม.", f"{df_today['Power'].mean():.2f}")

# แถวที่ 2: รายเดือน
st.info(f"📅 **สถานะบิลค่าไฟเดือน {selected_date.strftime('%B %Y')}**")
m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("🗓️ สะสมต้นเดือน-ปัจจุบัน", f"{total_month_kwh:.2f} kWh")
m_col2.metric("💸 ค่าไฟสะสมขณะนี้", f"{total_month_kwh * unit_cost:,.2f} บาท")
m_col3.metric("🔮 AI คาดการณ์บิลสิ้นเดือน", f"{forecast_month_kwh * unit_cost:,.2f} บาท", help="คำนวณจากพฤติกรรมการใช้ไฟเฉลี่ยในเดือนนี้")

st.markdown("---")

# 7. กราฟและการจับผิดโดย AI (แก้ไขลำดับการพล็อตเพื่อป้องกัน NameError)
st.subheader("📈 วิเคราะห์พฤติกรรมการใช้ไฟฟ้าด้วย AI")

# --- 🧠 ขั้นตอน AI: คำนวณค่าคาดการณ์ก่อนวาดกราฟ ---
expected_cols = ['Hour', 'DayOfWeek', 'IsWeekend', 'Power_Lag1', 'Power_Lag24']
final_input = pd.DataFrame(0.0, index=np.arange(24), columns=expected_cols)
final_input['Hour'] = df_today['Hour']
final_input['DayOfWeek'] = selected_date.weekday()
final_input['IsWeekend'] = 1 if selected_date.weekday() >= 5 else 0
# คำนวณ Lag 1 (ชั่วโมงก่อนหน้า) และ Lag 24 (เวลาเดียวกันเมื่อวาน)
final_input['Power_Lag1'] = df_today['Power'].shift(1).fillna(df_yesterday['Power'].iloc[-1]).values
final_input['Power_Lag24'] = df_yesterday['Power'].values

# ทำนายผลด้วยโมเดล XGBoost
expected_powers = model.predict(final_input)
errors = df_today['Power'] - expected_powers
anomalies = np.abs(errors) > safe_threshold

# --- 📊 ขั้นตอนการพล็อตกราฟ ---
fig = go.Figure()

# 1. เส้นเมื่อวาน (เส้นประสีเทา)
fig.add_trace(go.Scatter(x=df_yesterday['Hour'], y=df_yesterday['Power'], 
                         mode='lines', name='เมื่อวาน (Yesterday)', 
                         line=dict(color='gray', width=1, dash='dash')))

# 2. เส้นที่ AI คาดการณ์ (เส้นสีเขียวโปร่งแสง)
fig.add_trace(go.Scatter(x=df_today['Hour'], y=expected_powers, 
                         mode='lines', name='AI คาดการณ์ (Expected)', 
                         line=dict(color='rgba(46, 204, 113, 0.4)', width=2)))

# 3. เส้นจริงวันนี้ (เส้นสีน้ำเงิน)
fig.add_trace(go.Scatter(x=df_today['Hour'], y=df_today['Power'], 
                         mode='lines+markers', name='วันนี้ (Actual Today)', 
                         line=dict(color='#1f77b4', width=3)))

# 4. จุดความผิดปกติ (สีแดง)
anomaly_hours = df_today[anomalies]
fig.add_trace(go.Scatter(x=anomaly_hours['Hour'], y=anomaly_hours['Power'], 
                         mode='markers', name='⚠️ แจ้งเตือนผิดปกติ!', 
                         marker=dict(color='red', size=12, symbol='x')))

fig.update_layout(
    xaxis_title="ชั่วโมง (Hour)", 
    yaxis_title="กิโลวัตต์ (kW)", 
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# 8. สรุปรายงานและการแนะนำจาก AI
st.markdown("---")
st.subheader("🚨 รายงานจากระบบ AI")

if any(anomalies):
    for idx, is_anomaly in enumerate(anomalies):
        if is_anomaly:
            diff = errors[idx]
            if diff > 0:
                st.warning(f"⏰ **{idx:02d}:00 น.** : พบการใช้ไฟเกินมา {diff:.2f} kW | {analyze_appliance(diff)}")
            else:
                st.info(f"⏰ **{idx:02d}:00 น.** : การใช้ไฟต่ำผิดปกติ {abs(diff):.2f} kW (อาจเกิดจากไฟดับหรือไม่มีคนอยู่บ้าน)")
else:
    st.success(f"✅ วันนี้ไม่มีความผิดปกติ สบายใจได้ครับ!")

# วิธีทดสอบระบบ
with st.expander("💡 วิธีทดสอบระบบ (Easter Eggs)"):
    st.write("""
    - **ทดสอบลืมปิดเครื่องใช้ไฟฟ้า:** เลือกวันที่หารด้วย 3 ลงตัว (เช่น 15, 18, 21...) กราฟจะพุ่งช่วงบ่าย
    - **ทดสอบเคสไฟดับ:** เลือกวันที่ 13 ของเดือน กราฟจะดิ่งลงช่วงดึก
    - **ทดสอบวันปกติ:** เลือกวันที่อื่นๆ เพื่อดูการทำงานมาตรฐาน
    """)

st.caption("Developed by อรรณพ ศรีผ่อง | Data Science Project")
