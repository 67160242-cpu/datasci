import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go # ใช้ Plotly วาดกราฟสวยๆ
import numpy as np

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="Home Energy Master", page_icon="⚡", layout="wide")

# 2. โหลดสมอง AI และเกณฑ์การแจ้งเตือน
@st.cache_resource
def load_model_and_threshold():
    model = joblib.load('smart_home_xgb.pkl')
    threshold = joblib.load('smart_threshold.pkl')
    return model, threshold

model, threshold = load_model_and_threshold()

# 3. ส่วนหัวของเว็บ
st.title('⚡ Home Energy Master: ระบบบริหารจัดการพลังงานบ้านอัจฉริยะ')
st.markdown("---")

# 4. แถบด้านข้าง (Sidebar) - เน้นตั้งค่าค่าไฟ
st.sidebar.header('⚙️ ตั้งค่าระบบ')
unit_cost = st.sidebar.number_input('💰 ค่าไฟฟ้าต่อหน่วย (บาท)', value=4.0, step=0.1, min_value=0.0)
st.sidebar.markdown("---")
st.sidebar.subheader("📅 เลือกวันเพื่อดูข้อมูล")
# ในแอปจริงจุดนี้จะดึงวันปัจจุบัน แต่ตอนนี้เราจำลองข้อมูล ให้ผู้ใช้เลือกวันในปี 2010
selected_date = st.sidebar.date_input('เลือกวันที่ต้องการตรวจสอบ (ข้อมูลจำลองปี 2010)', 
                                    value=pd.to_datetime('2010-07-15'),
                                    min_value=pd.to_datetime('2010-01-01'),
                                    max_value=pd.to_datetime('2010-12-31'))

# 5. ฟังก์ชันจำลองข้อมูลการใช้ไฟของ "วันนี้" และ "เมื่อวาน" (Simulated Database)
@st.cache_data
def get_simulated_data(date, unit_cost):
    # ในแอปจริงจุดนี้จะดึงข้อมูลจาก Database/Sensor
    # แต่ตอนนี้เราใช้สมการคณิตศาสตร์จำลองพฤติกรรมให้ดูสมจริง
    
    date_str = date.strftime('%Y-%m-%d')
    yesterday_str = (date - pd.to_timedelta(1, unit='D')).strftime('%Y-%m-%d')
    hours = np.arange(24)
    
    # พฤติกรรมพื้นฐาน (sin wave)
    base_load = np.sin((hours - 3) * np.pi / 12) + 1.8
    weekend_mult = 1.3 if date.dayofweek >= 5 else 1.0
    month_mult = 1.2 if date.month in [4, 5] else 1.0
    
    # ข้อมูลเมื่อวาน (Yesterday) - ปกติเรียบร้อย
    power_yesterday = (base_load * weekend_mult * month_mult) + np.random.normal(0, 0.05, 24)
    df_yesterday = pd.DataFrame({'Hour': hours, 'Power_Yesterday': np.maximum(0.2, power_yesterday)})
    
    # ข้อมูลวันนี้ (Today) - แอบใส่ความผิดปกติ (ลืมปิดแอร์ตอนบ่าย)
    power_today = (base_load * weekend_mult * month_mult) + np.random.normal(0, 0.08, 24)
    
    # สถานการณ์จำลอง: ลืมปิดแอร์ตัวใหญ่ตอนบ่าย (14:00 - 18:00)
    if date.day % 3 == 0: # จำลองให้เกิดขึ้นทุกๆ 3 วัน
        power_today[14:19] += 2.8 
        
    df_today = pd.DataFrame({'Hour': hours, 'Power_Today': np.maximum(0.2, power_today)})
    
    return df_today, df_yesterday

df_today, df_yesterday = get_simulated_data(selected_date, unit_cost)

# 6. ส่วนหลักของเว็บ: Dashboard สรุปค่าไฟ
st.subheader(f"📊 สรุปภาพรวมพลังงานประจำวันที่ {selected_date.strftime('%d %B %Y')}")

# คำนวณสถิติ
total_power_today = df_today['Power_Today'].sum()
total_power_yesterday = df_yesterday['Power_Yesterday'].sum()
total_cost_today = total_power_today * unit_cost
power_diff = total_power_today - total_power_yesterday

# แสดง Metric สวยๆ
col1, col2, col3 = st.columns(3)
col1.metric("⚡ การใช้ไฟรวมวันนี้", f"{total_power_today:.2f} kWh", f"{power_diff:.2f} kWh vs เมื่อวาน")
col2.metric("💰 ประมาณการค่าไฟวันนี้", f"{total_cost_today:.2f} บาท", f"(คิดที่ {unit_cost} บาท/หน่วย)")
col3.metric("📉 การใช้ไฟเฉลี่ยรายชั่วโมง", f"{df_today['Power_Today'].mean():.2f} kW")

st.markdown("---")

# 7. กราฟเปรียบเทียบการใช้ไฟ (วันนี้ vs เมื่อวาน)
st.subheader("📈 กราฟเปรียบเทียบการใช้ไฟชั่วโมงต่อชั่วโมง")

fig = go.Figure()

# เส้นเมื่อวาน (สีเทา)
fig.add_trace(go.Scatter(x=df_yesterday['Hour'], y=df_yesterday['Power_Yesterday'],
                        mode='lines', name='เมื่อวาน (Yesterday)',
                        line=dict(color='gray', width=2, dash='dash')))

# เส้นวันนี้ (สีฟ้า)
fig.add_trace(go.Scatter(x=df_today['Hour'], y=df_today['Power_Today'],
                        mode='lines+markers', name='วันนี้ (Today)',
                        line=dict(color='#1f77b4', width=3)))

# 💡 ส่วนจับผิด (Anomaly Detection) โดย AI
# เตรียมข้อมูลส่งให้ AI
input_data = pd.DataFrame({
    'Hour': df_today['Hour'],
    'DayOfWeek': [selected_date.dayofweek] * 24,
    'IsWeekend': [1 if selected_date.dayofweek >= 5 else 0] * 24,
    # Lag1: ใช้ค่าชั่วโมงก่อนหน้า (สำหรับชั่วโมงแรกสุดให้ใช้ค่าชั่วโมงสุดท้ายของเมื่อวาน)
    'Power_Lag1': df_today['Power_Today'].shift(1).fillna(df_yesterday['Power_Yesterday'].iloc[-1]).values,
    # Lag24: ใช้ค่าของเมื่อวานเวลานี้เป๊ะๆ
    'Power_Lag24': df_yesterday['Power_Yesterday'].values
})

# ให้ AI ทายค่าปกติ
expected_powers = model.predict(input_data)
# คำนวณ Error และหาจุดที่ผิดปกติ
anomalies = (df_today['Power_Today'] - expected_powers) > threshold

# พล็อตจุดแดงแจ้งเตือนเฉพาะจุดที่ผิดปกติ
anomaly_hours = df_today[anomalies]
fig.add_trace(go.Scatter(x=anomaly_hours['Hour'], y=anomaly_hours['Power_Today'],
                        mode='markers', name='⚠️ แจ้งเตือนไฟผิดปกติ!',
                        marker=dict(color='red', size=12, symbol='x')))

fig.update_layout(title=f"เปรียบเทียบพฤติกรรมการใช้ไฟ (Threshold AI = {threshold:.2f} kW)",
                  xaxis_title="ชั่วโมง (Hour)",
                  yaxis_title="ปริมาณการใช้ไฟ (กิโลวัตต์)",
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

st.plotly_chart(fig, use_container_width=True)

st.info("💡 ทริค: ลองเลือกวันที่หารด้วย 3 ลงตัว (เช่น วันที่ 15, 18, 21) ใน Sidebar เพื่อดูสถานการณ์จำลอง 'ลืมปิดแอร์ตอนบ่าย' ที่ AI จะเด้งจุดสีแดงแจ้งเตือนครับ!")