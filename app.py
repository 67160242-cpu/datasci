import streamlit as st
import pandas as pd
import joblib
import datetime

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="Smart Home AI", page_icon="🏡", layout="wide")

# 2. โหลดสมอง AI และเกณฑ์การแจ้งเตือน
@st.cache_resource
def load_model_and_threshold():
    model = joblib.load('smart_home_xgb.pkl')
    threshold = joblib.load('smart_threshold.pkl')
    return model, threshold

model, threshold = load_model_and_threshold()

# 3. ส่วนหัวของเว็บ
st.title('🏡 ระบบ AI ผู้พิทักษ์บ้าน (Energy Anomaly Detector)')
st.write('วิเคราะห์ความผิดปกติและเปรียบเทียบการใช้ไฟฟ้าแบบ Real-time')
st.markdown("---")

# 4. Sidebar สำหรับรับข้อมูล
st.sidebar.header('⚙️ การตั้งค่าข้อมูล')
current_hour = st.sidebar.slider('ชั่วโมงปัจจุบัน (Hour)', 0, 23, 12)
day_of_week = st.sidebar.slider('วันในสัปดาห์ (0=จันทร์, 6=อาทิตย์)', 0, 6, 0)
is_weekend = 1 if day_of_week >= 5 else 0

st.sidebar.markdown("---")
st.sidebar.subheader("📊 ข้อมูลการใช้ไฟย้อนหลัง (kW)")
power_lag1 = st.sidebar.number_input('การใช้ไฟ 1 ชั่วโมงที่แล้ว', value=1.20, step=0.1)
power_lag24 = st.sidebar.number_input('การใช้ไฟเมื่อวานเวลานี้', value=1.10, step=0.1)

# 5. ส่วนหลัก: ตรวจสอบการใช้ไฟ
col_main, col_calc = st.columns([2, 1])

with col_main:
    st.subheader("⚡ ตรวจสอบการใช้ไฟ ณ ปัจจุบัน")
    current_power = st.number_input('กรอกปริมาณการใช้ไฟในชั่วโมงนี้ (kW):', value=1.50, step=0.1)

    # เตรียมข้อมูลส่งให้ AI
    input_data = pd.DataFrame({
        'Hour': [current_hour],
        'DayOfWeek': [day_of_week],
        'IsWeekend': [is_weekend],
        'Power_Lag1': [power_lag1],
        'Power_Lag24': [power_lag24]
    })

    if st.button('🔍 สแกนหาความผิดปกติ', type='primary'):
        expected_power = model.predict(input_data)[0]
        error = current_power - expected_power
        
        # --- ส่วนแสดงกราฟเปรียบเทียบ ---
        st.markdown("### 📊 เปรียบเทียบการใช้ไฟ (เมื่อวาน vs วันนี้)")
        chart_data = pd.DataFrame({
            'ช่วงเวลา': ['เมื่อวาน (เวลานี้)', 'วันนี้ (ปัจจุบัน)'],
            'ปริมาณไฟฟ้า (kW)': [power_lag24, current_power]
        }).set_index('ช่วงเวลา')
        
        st.bar_chart(chart_data)

        # ผลการวิเคราะห์แบบ Metric
        m1, m2, m3 = st.columns(3)
        m1.metric("ใช้จริง", f"{current_power:.2f} kW")
        m2.metric("AI คาดการณ์", f"{expected_power:.2f} kW")
        m3.metric("ส่วนต่าง", f"{error:.2f} kW", delta=f"{error:.2f}", delta_color="inverse")

        # Logic แจ้งเตือน
        if error > threshold:
            st.error(f'🚨 **แจ้งเตือน!** พบการใช้ไฟสูงผิดปกติ (เกินเกณฑ์ {threshold:.2f} kW)')
        elif error < -threshold:
            st.info(f'📉 **ข้อสังเกต:** การใช้ไฟน้อยกว่าปกติ')
        else:
            st.success(f'✅ **สถานะปกติ:** การใช้ไฟอยู่ในเกณฑ์มาตรฐาน')

with col_calc:
    # 6. ส่วนคำนวณค่าไฟรายเดือน (ประมาณการ)
    st.subheader("💰 ประมาณการค่าไฟ")
    unit_price = 4.42 # ค่าไฟเฉลี่ยต่อหน่วย (บาท) รวม FT
    
    # คำนวณเบื้องต้น: สมมติว่าใช้ไฟเรทนี้เฉลี่ยทั้งวัน (24 ชม.) เป็นเวลา 30 วัน
    daily_est = current_power * 24
    monthly_units = daily_est * 30
    monthly_cost = monthly_units * unit_price
    
    st.info(f"""
    **หากใช้ไฟระดับนี้ต่อเนื่อง:**
    - หน่วยไฟต่อเดือน: `{monthly_units:.2f}` Units
    - ค่าไฟประมาณการ: **`{monthly_cost:,.2;f}` บาท/เดือน**
    """)
    st.caption(f"*คำนวณจากอัตราเฉลี่ย {unit_price} บาท/หน่วย")

st.markdown("---")
st.caption(f"เกณฑ์ความผิดปกติ (Threshold): {threshold:.4f} kW")