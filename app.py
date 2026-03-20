import streamlit as st
import pandas as pd
import plotly.graph_objects as go 
import numpy as np

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="Home Energy Master (Debug Mode)", page_icon="🛠️", layout="wide")

st.title('🛠️ Home Energy Master: โหมดทดสอบหน้าเว็บ (ปิด AI ชั่วคราว)')
st.markdown("---")

# 2. แถบด้านข้าง (Sidebar)
st.sidebar.header('⚙️ ตั้งค่าระบบ')
unit_cost = st.sidebar.number_input('💰 ค่าไฟฟ้าต่อหน่วย (บาท)', value=4.0, step=0.1, min_value=0.0)
st.sidebar.markdown("---")
st.sidebar.subheader("📅 เลือกวันเพื่อดูข้อมูล")
selected_date = st.sidebar.date_input('เลือกวันที่ต้องการตรวจสอบ', 
                                    value=pd.to_datetime('2010-07-15'),
                                    min_value=pd.to_datetime('2010-01-01'),
                                    max_value=pd.to_datetime('2010-12-31'))

# 3. จำลองข้อมูล (เหมือนเดิมเป๊ะ)
@st.cache_data
def get_simulated_data(date, unit_cost):
    hours = np.arange(24)
    base_load = (np.sin((hours - 3) * np.pi / 12) * 0.4) + 0.8
    weekend_mult = 1.2 if date.dayofweek >= 5 else 1.0
    
    power_yesterday = (base_load * weekend_mult) + np.random.normal(0, 0.05, 24)
    df_yesterday = pd.DataFrame({'Hour': hours, 'Power_Yesterday': np.maximum(0.2, power_yesterday)})
    
    power_today = (base_load * weekend_mult) + np.random.normal(0, 0.08, 24)
    
    # จำลองไฟเกิน (วันที่หาร 3 ลงตัว) และไฟดับ (วันที่ 13)
    if date.day % 3 == 0: 
        power_today[14:19] += 2.1 
    if date.day == 13:
        power_today[20:23] = 0.05 
        
    df_today = pd.DataFrame({'Hour': hours, 'Power_Today': np.maximum(0.2, power_today)})
    return df_today, df_yesterday

df_today, df_yesterday = get_simulated_data(selected_date, unit_cost)

# 4. Dashboard สรุปภาพรวม
st.subheader(f"📊 สรุปภาพรวมพลังงานประจำวันที่ {selected_date.strftime('%d %B %Y')}")
total_power_today = df_today['Power_Today'].sum()
total_cost_today = total_power_today * unit_cost
power_diff = total_power_today - df_yesterday['Power_Yesterday'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("⚡ การใช้ไฟรวมวันนี้", f"{total_power_today:.2f} kWh", f"{power_diff:.2f} kWh vs เมื่อวาน")
col2.metric("💰 ประมาณการค่าไฟวันนี้", f"{total_cost_today:.2f} บาท", f"(คิดที่ {unit_cost} บาท/หน่วย)")
col3.metric("📉 การใช้ไฟเฉลี่ยรายชั่วโมง", f"{df_today['Power_Today'].mean():.2f} kW")
st.markdown("---")

# 5. กราฟเปรียบเทียบ (ไม่มีจุดแดงของ AI)
st.subheader("📈 กราฟเปรียบเทียบการใช้ไฟชั่วโมงต่อชั่วโมง (ทดสอบ UI)")
fig = go.Figure()

fig.add_trace(go.Scatter(x=df_yesterday['Hour'], y=df_yesterday['Power_Yesterday'], 
                         mode='lines', name='เมื่อวาน (Yesterday)', line=dict(color='gray', width=2, dash='dash')))
fig.add_trace(go.Scatter(x=df_today['Hour'], y=df_today['Power_Today'], 
                         mode='lines+markers', name='วันนี้ (Today)', line=dict(color='#1f77b4', width=3)))

fig.update_layout(title="เปรียบเทียบพฤติกรรมการใช้ไฟ (ปิดระบบแจ้งเตือน AI)", 
                  xaxis_title="ชั่วโมง (Hour)", yaxis_title="ปริมาณการใช้ไฟ (กิโลวัตต์)", 
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig, use_container_width=True)

st.success("✅ ถ้าคุณเห็นกล่องข้อความนี้และกราฟด้านบนแสดงผลได้ปกติ แปลว่าโค้ดหน้าเว็บ Streamlit ทำงานสมบูรณ์ 100% ครับ!")
