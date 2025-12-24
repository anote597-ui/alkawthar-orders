import streamlit as st
import google.generativeai as genai
import pandas as pd
from PIL import Image

# --- إعدادات التطبيق ---
st.set_page_config(page_title="مدير طلبيات الكوثر", layout="centered")

# --- تهيئة الذكاء الاصطناعي (تحتاج مفتاح API خاص بك) ---
# يمكنك الحصول على مفتاح مجاني من Google AI Studio
api_key = st.text_input("أدخل مفتاح Google API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)

# --- واجهة المستخدم ---
st.title("📸 ماسح الطلبيات الذكي")
st.write("التقط صورة لورقة الملاحظات وسأقوم بالحسابات تلقائياً.")

# تشغيل الكاميرا
img_file = st.camera_input("التقط صورة الوصل")

# --- المتغيرات لتخزين البيانات (session state) ---
if 'orders' not in st.session_state:
    st.session_state.orders = []
if 'customer_count' not in st.session_state:
    st.session_state.customer_count = 1

def analyze_image(image):
    """دالة ترسل الصورة للذكاء الاصطناعي لاستخراج البيانات"""
    model = genai.GenerativeModel('gemini-1.5-flash') # نستخدم موديل سريع
    
    prompt = """
    أنت مساعد ذكي لإدارة المبيعات. أمامك صورة لورقة ملاحظات مكتوبة بخط اليد لطلب زبون.
    المطلوب منك استخراج البيانات التالية بدقة، والقيام بعملية حسابية:
    
    1. **المصدر**: (فيسبوك أو انستكرام).
    2. **المحافظة**: استخرج اسم المحافظة.
    3. **المبلغ الصافي**: ابحث عن "المبلغ الكلي" في الورقة، وقم بطرح 5000 دينار منه (أجور التوصيل). الناتج هو مبلغ الطلبية.
       - مثال: اذا كان المبلغ في الورقة 30000، الناتج يجب أن يكون 25000.
    
    تجاهل رقم الهاتف تماماً.
    تجاهل اسم الزبون المكتوب.
    
    أرجع النتيجة بصيغة نصية بسيطة جداً بهذا الشكل بالضبط:
    المصدر|المحافظة|المبلغ_الصافي
    مثال:
    فيسبوك|بغداد|25000
    """
    
    try:
        response = model.generate_content([prompt, image])
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

# --- معالجة الصورة عند الالتقاط ---
if img_file is not None:
    # عرض الصورة للتاكيد
    image = Image.open(img_file)
    
    with st.spinner('جاري قراءة خط اليد وحساب الصافي...'):
        if api_key:
            result_text = analyze_image(image)
            
            # التحقق من أن النتيجة صحيحة وليست خطأ
            if "|" in result_text and "Error" not in result_text:
                try:
                    source, city, net_price = result_text.split('|')
                    
                    # إنشاء اسم الزبون المشفر
                    cust_name = f"زبون {st.session_state.customer_count}"
                    
                    # حفظ البيانات
                    new_order = {
                        "كود الزبون": cust_name,
                        "جهة المراسلة": source.strip(),
                        "مبلغ الطلبية (الصافي)": net_price.strip(),
                        "المحافظة": city.strip()
                    }
                    
                    st.session_state.orders.append(new_order)
                    st.session_state.customer_count += 1
                    
                    st.success(f"تمت الإضافة: {cust_name} - الصافي: {net_price}")
                    
                except ValueError:
                    st.error("لم أتمكن من فهم البيانات بدقة، حاول تصوير الورقة بشكل أوضح.")
            else:
                 st.error("حدث خطأ في قراءة الصورة أو مفتاح API غير صحيح.")
        else:
            st.warning("يرجى إدخال مفتاح API أولاً.")

# --- عرض الجدول النهائي ---
st.divider()
st.subheader("📋 سجل الطلبيات")

if st.session_state.orders:
    df = pd.DataFrame(st.session_state.orders)
    st.dataframe(df, use_container_width=True)
    
    # زر لتحميل البيانات كملف Excel/CSV
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "تحميل السجل (CSV)",
        csv,
        "orders_list.csv",
        "text/csv",
        key='download-csv'
    )
else:
    st.info("لا توجد طلبيات مسجلة بعد.")
