# ⚡ Home Energy Master: ระบบบริหารจัดการพลังงานบ้านอัจฉริยะ

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-172434?style=for-the-badge&logo=xgboost&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-239120?style=for-the-badge&logo=plotly&logoColor=white)

โปรเจกต์แอปพลิเคชันสำหรับติดตาม เปรียบเทียบ และวิเคราะห์การใช้พลังงานไฟฟ้าภายในบ้าน (Smart Home) ทำงานร่วมกับโมเดล AI ในการตรวจจับความผิดปกติแบบเรียลไทม์ 
แอปพลิเคชันนี้ถูกพัฒนาขึ้นเพื่อช่วยเจ้าของบ้านวิเคราะห์พฤติกรรมการใช้ไฟ และใช้ Machine Learning ตรวจจับเหตุการณ์ผิดปกติ (Anomaly Detection) เช่น **"การลืมเปิดเครื่องใช้ไฟฟ้าทิ้งไว้"** หรือ **"เหตุการณ์ไฟตก/ไฟดับ"** พร้อมระบบประเมินว่าความผิดปกตินั้นน่าจะเกิดจากอุปกรณ์ชนิดใด เพื่อลดความสูญเสียและเพิ่มความปลอดภัย

## 🚀 เทคโนโลยีที่ใช้ (Tech Stack)

* **Language:** Python
* **Framework:** Streamlit
* **Machine Learning:** * **XGBoost Regressor:** โมเดลหลักที่ใช้ในการเรียนรู้พฤติกรรมการใช้ไฟและทำนายแนวโน้ม (Expected Power) ล่วงหน้า
* **Data Processing:** Pandas, NumPy
* **Visualization:** Plotly (สำหรับการแสดงกราฟเปรียบเทียบพฤติกรรมแบบ Interactive)

## 🛠️ วิธีการติดตั้งและใช้งาน (Installation & Setup)

1. **Clone Repository:**
   ```bash
   git clone [https://github.com/67160337-lab/HomeEnergyMaster.git](https://github.com/67160337-lab/HomeEnergyMaster.git)
   cd HomeEnergyMaster
2. ติดตั้ง Library ที่จำเป็น
   - pip install -r requirements.txt
3. รันแอปพลิเคชัน
   - streamlit run app.py
# 🧠 กระบวนการพัฒนา (Methodology)
Data Simulation: จำลองพฤติกรรมการใช้ไฟฟ้ารายวัน โดยอิงจาก Base Load และเพิ่มตัวคูณสำหรับวันหยุดสุดสัปดาห์ (Weekend Multiplier)
Feature Engineering: ดึงข้อมูลที่สำคัญ 5 ปัจจัย (Features) เพื่อให้ AI ใช้ตัดสินใจ ได้แก่:
Hour: เวลาปัจจุบัน
DayOfWeek: วันในสัปดาห์
IsWeekend: เป็นวันหยุดสุดสัปดาห์หรือไม่
Power_Lag1: การใช้ไฟในชั่วโมงที่แล้ว
Power_Lag24: การใช้ไฟในเวลาเดียวกันของเมื่อวาน
Anomaly Detection Logic: ใช้โมเดล XGBoost ทำนายค่าการใช้ไฟที่ควรจะเป็น หากค่าการใช้ไฟจริง (Actual) แตกต่างจากค่าที่ทำนาย (Expected) เกินกว่าค่า Threshold (เช่น ±0.5 kW) ระบบจะมาร์กจุดเป็นความผิดปกติทันที

#📊 ฟีเจอร์หลัก (Key Features)
Interactive Dashboard: แสดงผลสรุปการใช้ไฟฟ้ารายวัน (kWh), ค่าไฟประมาณการ (บาท) และกราฟเปรียบเทียบชั่วโมงต่อชั่วโมง
Smart Anomaly Alerts: มาร์กจุดสีแดง (⚠️) บนกราฟอัตโนมัติเมื่อ AI พบการใช้ไฟที่ผิดปกติ
Appliance Analysis: ระบบช่วยวิเคราะห์ขนาดของกระแสไฟที่ผิดปกติ เพื่อเดาว่าน่าจะเกิดจากอุปกรณ์ใด (เช่น แอร์, เครื่องทำน้ำอุ่น, ทีวี)

#💡 วิธีการทดสอบระบบ (Usage & Testing)
ระบบนี้ถูกออกแบบมาให้มี Easter Egg สำหรับทดสอบการทำงานของ AI ดังนี้:
วันปกติ ✅: เลือกวันที่ใดก็ได้ (ที่หาร 3 ไม่ลงตัว และไม่ใช่วันที่ 13) เพื่อดูกราฟพฤติกรรมการใช้ไฟปกติ
ทดสอบเคส "ลืมปิดเครื่องใช้ไฟฟ้า" 📈: เลือกวันที่ที่ หารด้วย 3 ลงตัว (เช่น 15, 18, 21) ระบบจะจำลองไฟกระชากในช่วงบ่าย AI จะจับผิดและแจ้งเตือนไฟรั่ว
ทดสอบเคส "ไฟตก/ไฟดับ" 📉: เลือก วันที่ 13 ของเดือน ระบบจะจำลองเหตุการณ์ไฟดับในช่วงกลางคืน AI จะแจ้งเตือนการใช้ไฟที่ต่ำผิดปกติ

#⚠️ ข้อควรระวัง (Disclaimer):
แบบจำลองและข้อมูลในแอปพลิเคชันนี้เป็นการจำลอง (Simulation) เพื่อการศึกษาในวิชา Data Science และการนำ Machine Learning มาประยุกต์ใช้กับระบบ Smart Home เบื้องต้นเท่านั้น

#👤 จัดทำโดย
67160242 อรรณพ ศรีผ่อง วิชาData Science
