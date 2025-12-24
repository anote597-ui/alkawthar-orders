import streamlit as st
import google.generativeai as genai
import pandas as pd
from PIL import Image

st.set_page_config(page_title="مدير طلبيات الكوثر", layout="centered")

# --- إدخال المفتاح ---
api_key = st.text_input("أدخل مفتاح Google API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"خطأ في إعداد المفتاح: {e}")

st.title("📸 ماسح الطلبيات (نسخة الفحص)")

# --- الكاميرا ---
img_file = st.camera_input("التقط صورة الوصل")

if 'orders' not in st.session_state:
    st.session_state.orders = []

def analyze_image(image):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    استخرج البيانات من صورة الطلب:
    1. المصدر (فيسبوك/انستكرام)
    2. المحافظة
    3. المبلغ الصافي (المبلغ الكلي - 5000)
    
    الصيغة المطلوبة بالضبط:
    المصدر|المحافظة|المبلغ_الصافي
    """
    
    try:
        response = model.generate_content([prompt, image])
        return response.text.strip()
    except Exception as e:
        # هنا سنعيد رسالة الخطأ الحقيقية
        return f"Error Details: {str(e)}"

if img_file is not None:
    image = Image.open(img_file)
    
    if api_key:
        with st.spinner('جاري التحليل...'):
            result_text = analyze_image(image)
            
            # --- منطقة كشف الخطأ ---
            if "Error Details" in result_text:
                st.error("🛑 حدث خطأ تقني من المصدر:")
                st.code(result_text, language="text") # سيعرض لك سبب الخطأ باللغة الانجليزية
                st.info("قم بتصوير هذه الرسالة وأرسلها لي (لـ Gemini) لأشرح لك الحل.")
                
            elif "|" not in result_text:
                st.warning("⚠️ الذكاء الاصطناعي لم يفهم الصورة جيداً أو لم يلتزم بالصيغة.")
                st.write("ما قاله الذكاء الاصطناعي:")
                st.code(result_text)
                
            else:
                # نجاح العملية
                try:
                    source, city, net_price = result_text.split('|')
                    st.success(f"تم! {source} - {city} - {net_price}")
                    st.session_state.orders.append({
                        "المصدر": source, "المحافظة": city, "الصافي": net_price
                    })
                except:
                    st.error("خطأ في تقسيم البيانات رغم نجاح القراءة.")
    else:
        st.warning("الرجاء إدخال المفتاح أولاً.")

# عرض الجدول
if st.session_state.orders:
    st.dataframe(pd.DataFrame(st.session_state.orders))
