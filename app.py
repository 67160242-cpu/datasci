import streamlit as st
import pandas as pd
import joblib
import datetime

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="Smart Home AI", page_icon="🏡", layout="centered")

# 2. โหลดสมอง AI และเกณฑ์การแจ้งเตือน
@st.cache_resource # ใช้ Cache เพื่อไม่ให้เว็บโหลดโมเดลใหม่ทุกครั้งที่ขยับเมาส์
def load_model_and_threshold():
    model = joblib.load('smart_home_xgb.pkl')
    threshold = joblib.load('smart_threshold.pkl')
    return model, threshold

model, threshold = load_model_and_threshold()

# 3. ส่วนหัวของเว็บ
st.title('🏡 ระบบ AI ผู้พิทักษ์บ้าน (Energy Anomaly Detector)')
st.write('แอปพลิเคชันนี้จะช่วยตรวจสอบว่า **"การใช้ไฟของคุณในชั่วโมงนี้ ผิดปกติหรือไม่?"** (มีไฟรั่ว หรือลืมปิดแอร์หรือเปล่า) โดยให้ AI เปรียบเทียบกับพฤติกรรมการใช้ไฟในอดีตของคุณ')
st.markdown("---")

# 4. แถบด้านข้างสำหรับรับข้อมูล (Sidebar)
st.sidebar.header('⚙️ ข้อมูลจำเพาะของชั่วโมงนี้')

# จำลองการดึงเวลาปัจจุบัน (หรือให้ผู้ใช้เลือกเอง)
current_hour = st.sidebar.slider('ชั่วโมงปัจจุบัน (Hour)', 0, 23, 12)
day_of_week = st.sidebar.slider('วันในสัปดาห์ (0=จันทร์, 6=อาทิตย์)', 0, 6, 0)
is_weekend = 1 if day_of_week >= 5 else 0
st.sidebar.info(f"วันหยุดสุดสัปดาห์: {'ใช่ (1)' if is_weekend else 'ไม่ใช่ (0)'}")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 ข้อมูลการใช้ไฟย้อนหลัง (kW)")
power_lag1 = st.sidebar.number_input('การใช้ไฟ 1 ชั่วโมงที่แล้ว', value=1.20, step=0.1)
power_lag24 = st.sidebar.number_input('การใช้ไฟเมื่อวานเวลานี้', value=1.10, step=0.1)

# 5. ส่วนหลักของเว็บ: กรอกค่าไฟปัจจุบันเพื่อตรวจสอบ
st.subheader("⚡ ตรวจสอบการใช้ไฟ ณ ปัจจุบัน")
current_power = st.number_input('กรอกปริมาณการใช้ไฟในชั่วโมงนี้ (กิโลวัตต์) เพื่อให้ AI ตรวจสอบ:', value=1.50, step=0.1)

# 6. เตรียมข้อมูลส่งให้ AI
input_data = pd.DataFrame({
    'Hour': [current_hour],
    'DayOfWeek': [day_of_week],
    'IsWeekend': [is_weekend],
    'Power_Lag1': [power_lag1],
    'Power_Lag24': [power_lag24]
})

# 7. ปุ่มกดตรวจสอบ
if st.button('🔍 สแกนหาความผิดปกติ', type='primary'):
    with st.spinner('AI กำลังวิเคราะห์พฤติกรรม...'):
        
        # ให้ AI ทายว่าชั่วโมงนี้ "ควรจะ" ใช้ไฟเท่าไหร่
        expected_power = model.predict(input_data)[0]
        
        # คำนวณความต่าง (ส่วนเกิน)
        error = current_power - expected_power
        
        st.markdown("### 📊 ผลการวิเคราะห์:")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("การใช้ไฟจริง", f"{current_power:.2f} kW")
        col2.metric("ค่าที่ AI คาดการณ์", f"{expected_power:.2f} kW")
        col3.metric("ส่วนเกิน (Error)", f"{error:.2f} kW", delta_color="inverse")
        
        st.markdown("---")
        
        # 🚨 ระบบตัดสินใจ (Logic)
        if error > threshold:
            st.error(f'🚨 **แจ้งเตือนอันตราย!** พบการใช้ไฟสูงผิดปกติ (เกินเกณฑ์ {threshold:.2f} kW)')
            st.warning('👉 คำแนะนำ: โปรดตรวจสอบว่าคุณลืมปิดแอร์ เครื่องทำน้ำอุ่น หรือมีกระแสไฟฟ้ารั่วภายในบ้านหรือไม่!')
        elif error < -threshold:
            st.info(f'📉 **ข้อสังเกต:** การใช้ไฟน้อยกว่าปกติมาก (อาจเกิดจากไฟดับ หรือไม่อยู่บ้าน)')
        else:
            st.success(f'✅ **สถานะปกติ:** การใช้ไฟของคุณอยู่ในเกณฑ์มาตรฐานของบ้านหลังนี้ครับ')

st.caption(f"หมายเหตุ: ระบบตั้งค่าเกณฑ์ความผิดปกติ (Threshold) ไว้ที่ส่วนเกิน {threshold:.4f} กิโลวัตต์")