import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go 
import numpy as np

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="Home Energy Master", page_icon="⚡", layout="wide")

# 🟢 ฟังก์ชัน: เดาชื่ออุปกรณ์จากค่าไฟที่เกินมา (สำหรับกรณีใช้ไฟเกิน)
def analyze_appliance(error_kw):
    if error_kw >= 3.0:
        return "🔥 **อันตรายมาก!** (เกิน 3.0 kW) น่าจะเป็นเครื่องทำน้ำอุ่นเปิดทิ้งไว้, เตาอบไฟฟ้า หรือ แอร์ขนาดใหญ่"
    elif error_kw >= 1.5:
        return "♨️ **ระดับกลาง** (1.5 - 3.0 kW) น่าจะเป็นเตารีด, หม้อต้มน้ำร้อน, ไมโครเวฟ หรือ แอร์ห้องนอน"
    elif error_kw >= 0.5:
        return "📺 **ระดับเริ่มต้น** (0.5 - 1.5 kW) น่าจะเป็นทีวีจอใหญ่, คอมพิวเตอร์ หรือตู้เย็นปิดไม่สนิท"
    else:
        return "💡 **เล็กน้อย** (ต่ำกว่า 0.5 kW) อาจจะลืมปิดพัดลม หรือหลอดไฟหลายดวง"

# 2. โหลดโมเดล AI "ของแท้" ที่คุณเทรนมา
@st.cache_resource
def load_model_and_threshold():
    model = joblib.load('smart_home_xgb.pkl')
    threshold = joblib.load('smart_threshold.pkl')
    # บังคับให้ Threshold เป็นค่าบวกเสมอ ป้องกันบั๊กกราฟมุดลงดิน
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
selected_date = st.sidebar.date_input('เลือกวันที่ต้องการตรวจสอบ (ข้อมูลจำลองปี 2010)', 
                                    value=pd.to_datetime('2010-07-15'),
                                    min_value=pd.to_datetime('2010-01-01'),
                                    max_value=pd.to_datetime('2010-12-31'))

# 5. จำลองข้อมูลให้เนียนไปกับสมอง AI ของจริง
@st.cache_data
def get_simulated_data(date, unit_cost):
    hours = np.arange(24)
    
    # ปรับ Base Load ให้ลดลงมาใกล้เคียงของจริง (ประมาณ 0.5 - 1.2 kW)
    base_load = (np.sin((hours - 3) * np.pi / 12) * 0.4) + 0.8
    weekend_mult = 1.2 if date.dayofweek >= 5 else 1.0
    
    # ข้อมูลเมื่อวาน (ปกติ)
    power_yesterday = (base_load * weekend_mult) + np.random.normal(0, 0.05, 24)
    df_yesterday = pd.DataFrame({'Hour': hours, 'Power_Yesterday': np.maximum(0.2, power_yesterday)})
    
    # ข้อมูลวันนี้
    power_today = (base_load * weekend_mult) + np.random.normal(0, 0.08, 24)
    
    # สถานการณ์จำลอง: ถ้าเลือกวันที่หารด้วย 3 ลงตัว จะมีไฟรั่วตอนบ่าย
    if date.day % 3 == 0: 
        power_today[14:19] += 2.1 # แอบบวกไฟเพิ่ม 2.1 kW (จำลองเปิดแอร์ทิ้งไว้)
    
    # สถานการณ์จำลอง: ถ้าเลือกวันที่ 13 จะจำลองไฟดับตอน 2 ทุ่ม
    if date.day == 13:
        power_today[20:23] = 0.05 
        
    df_today = pd.DataFrame({'Hour': hours, 'Power_Today': np.maximum(0.2, power_today)})
    return df_today, df_yesterday

df_today, df_yesterday = get_simulated_data(selected_date, unit_cost)

# 6. Dashboard สรุปภาพรวม
st.subheader(f"📊 สรุปภาพรวมพลังงานประจำวันที่ {selected_date.strftime('%d %B %Y')}")
total_power_today = df_today['Power_Today'].sum()
total_cost_today = total_power_today * unit_cost
power_diff = total_power_today - df_yesterday['Power_Yesterday'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("⚡ การใช้ไฟรวมวันนี้", f"{total_power_today:.2f} kWh", f"{power_diff:.2f} kWh vs เมื่อวาน")
col2.metric("💰 ประมาณการค่าไฟวันนี้", f"{total_cost_today:.2f} บาท", f"(คิดที่ {unit_cost} บาท/หน่วย)")
col3.metric("📉 การใช้ไฟเฉลี่ยรายชั่วโมง", f"{df_today['Power_Today'].mean():.2f} kW")
st.markdown("---")

# 7. กราฟเปรียบเทียบและการใช้ AI จับผิด
st.subheader("📈 กราฟเปรียบเทียบการใช้ไฟชั่วโมงต่อชั่วโมง")
fig = go.Figure()

# วาดเส้นกราฟเมื่อวาน และ วันนี้
fig.add_trace(go.Scatter(x=df_yesterday['Hour'], y=df_yesterday['Power_Yesterday'], 
                         mode='lines', name='เมื่อวาน (Yesterday)', line=dict(color='gray', width=2, dash='dash')))
fig.add_trace(go.Scatter(x=df_today['Hour'], y=df_today['Power_Today'], 
                         mode='lines+markers', name='วันนี้ (Today)', line=dict(color='#1f77b4', width=3)))

# เตรียมข้อมูลให้ AI ทาย
# 1. เตรียมข้อมูลพื้นฐานเท่าที่เรามี
temp_data = pd.DataFrame({
    'Hour': df_today['Hour'],
    'DayOfWeek': [selected_date.dayofweek] * 24,
    'IsWeekend': [1 if selected_date.dayofweek >= 5 else 0] * 24,
    'Power_Lag1': df_today['Power_Today'].shift(1).fillna(df_yesterday['Power_Yesterday'].iloc[-1]).values,
    'Power_Lag24': df_yesterday['Power_Yesterday'].values
})

# 2. ถามโมเดลว่าต้องการคอลัมน์ชื่ออะไรบ้าง
try:
    expected_features = model.feature_names_in_
except AttributeError:
    expected_features = model.get_booster().feature_names

# 3. ไฮไลท์สำคัญ!: คอลัมน์ไหนที่ AI อยากได้แต่เราไม่มี ให้สร้างขึ้นมาแล้วใส่เลข 0
for col in expected_features:
    if col not in temp_data.columns:
        temp_data[col] = 0

# 4. จัดเรียงคอลัมน์ให้ตรงใจโมเดลเป๊ะๆ
input_data = temp_data[expected_features]

# 5. ให้ AI ทายค่าปกติ และหา Error
expected_powers = model.predict(input_data)
errors = df_today['Power_Today'] - expected_powers

# ผิดปกติ = ค่าความคลาดเคลื่อนมีขนาดใหญ่กว่า safe_threshold
anomalies = np.abs(errors) > safe_threshold

# ==========================================