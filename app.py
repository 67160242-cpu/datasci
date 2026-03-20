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

# ==========================================
# เตรียมข้อมูลให้ AI ทาย (เวอร์ชันจัดให้ตามคำขอ 13 คอลัมน์ แก้ปัญหา feature_names mismatch)
# ==========================================

# ลิสต์รายชื่อคอลัมน์ทั้ง 13 ตัวที่ AI จำมาจากตอนเทรน
expected_cols = [
    'Datetime', 'Global_active_power', 'Global_reactive_power', 
    'Voltage', 'Global_intensity', 'Sub_metering_1', 
    'Sub_metering_2', 'Sub_metering_3', 'Power_Lag1', 
    'Power_Lag24', 'Hour', 'DayOfWeek', 'IsWeekend'
]

# สร้างกระดาษคำตอบที่มี 13 ช่อง (ใส่เลข 0 ไว้ก่อน)
final_input = pd.DataFrame(0, index=np.arange(24), columns=expected_cols)

# หยอดข้อมูล 5 ตัวที่เรามีจริงๆ ลงไป
final_input['Hour'] = df_today['Hour']
final_input['DayOfWeek'] = selected_date.dayofweek
final_input['IsWeekend'] = 1 if selected_date.dayofweek >= 5 else 0
final_input['Power_Lag1'] = df_today['Power_Today'].shift(1).fillna(df_yesterday['Power_Yesterday'].iloc[-1]).values
final_input['Power_Lag24'] = df_yesterday['Power_Yesterday'].values

# ให้ AI ทายค่าปกติ และหา Error
expected_powers = model.predict(final_input)
errors = df_today['Power_Today'] - expected_powers

# ผิดปกติ = ค่าความคลาดเคลื่อนมีขนาดใหญ่กว่า safe_threshold
anomalies = np.abs(errors) > safe_threshold
# ==========================================

# พล็อตจุดกากบาทสีแดงบนกราฟ
anomaly_hours = df_today[anomalies]
fig.add_trace(go.Scatter(x=anomaly_hours['Hour'], y=anomaly_hours['Power_Today'], 
                         mode='markers', name='⚠️ แจ้งเตือนไฟผิดปกติ!', marker=dict(color='red', size=12, symbol='x')))

fig.update_layout(title=f"เปรียบเทียบพฤติกรรมการใช้ไฟ (เกณฑ์แจ้งเตือน AI = ±{safe_threshold:.2f} kW)", 
                  xaxis_title="ชั่วโมง (Hour)", yaxis_title="ปริมาณการใช้ไฟ (กิโลวัตต์)", 
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig, use_container_width=True)

# 8. สรุปการแจ้งเตือน (แยกแยะ ไฟรั่ว vs ไฟดับ)
st.markdown("---")
st.subheader("🚨 รายงานความผิดปกติและคำแนะนำจาก AI")

if any(anomalies):
    for idx, is_anomaly in enumerate(anomalies):
        if is_anomaly:
            hour = df_today['Hour'].iloc[idx]
            actual_power = df_today['Power_Today'].iloc[idx]
            expected_power = expected_powers[idx]
            error_val = errors.iloc[idx]
            
            # กรณีที่ 1: ใช้ไฟเกิน (ไฟรั่ว / ลืมปิดอุปกรณ์)
            if error_val > 0:
                with st.expander(f"📈 พบการใช้ไฟสูงผิดปกติเวลา {hour:02d}:00 น. (ใช้ไฟเกินไป {error_val:.2f} kW)", expanded=True):
                    st.write(f"- **การใช้ไฟจริง:** {actual_power:.2f} kW | **AI คาดการณ์:** {expected_power:.2f} kW")
                    st.warning(f"🔍 **AI ประเมินว่า:** {analyze_appliance(error_val)}")
            
            # กรณีที่ 2: ใช้ไฟน้อยผิดปกติ (ไฟดับ / ไม่อยู่บ้าน / เซ็นเซอร์พัง)
            else:
                with st.expander(f"📉 พบการใช้ไฟต่ำผิดปกติเวลา {hour:02d}:00 น. (ไฟหายไป {abs(error_val):.2f} kW)", expanded=True):
                    st.write(f"- **การใช้ไฟจริง:** {actual_power:.2f} kW | **AI คาดการณ์:** {expected_power:.2f} kW")
                    st.info(f"💡 **AI ประเมินว่า:** การใช้ไฟน้อยกว่าปกติมาก อาจเกิดจาก **ไฟดับในพื้นที่, ไม่อยู่บ้าน, หรือเซ็นเซอร์ขัดข้อง**")
else:
    st.success("✅ **เยี่ยมมาก!** วันนี้ไม่มีการใช้ไฟที่ผิดปกติ การใช้พลังงานของคุณอยู่ในเกณฑ์มาตรฐานครับ")

# ทริคสำหรับเทสระบบ
st.info("💡 ทริคทดสอบระบบ: \n- เลือกวันที่หารด้วย 3 ลงตัว (เช่น 15, 18, 21) เพื่อดู AI จับผิด **'การลืมปิดอุปกรณ์'** 📈\n- เลือกวันที่ 13 เพื่อดู AI จับผิดสถานการณ์ **'ไฟดับตอนกลางคืน'** 📉")