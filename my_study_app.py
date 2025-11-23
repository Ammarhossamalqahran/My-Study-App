import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import docx
import json
import pandas as pd # عشان الرسوم البيانية والإحصائيات

# --- 1. إعداد الصفحة ---
st.set_page_config(page_title="المدرس الشامل (Pro)", page_icon="🎓", layout="wide")

# --- 2. إعداد المفتاح ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "AIzaSyDDvLq3YjF9IrgWY51mD2RCHU2b7JF75Tk" 

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. دوال مساعدة ---
def get_pdf_text(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def get_docx_text(uploaded_file):
    doc = docx.Document(uploaded_file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# دالة تنظيف الـ JSON (عشان الذكاء الاصطناعي ساعات بيحط رموز زيادة)
def clean_json_string(json_str):
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0]
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0]
    return json_str.strip()

# --- 4. تهيئة المتغيرات (Session State) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_content" not in st.session_state:
    st.session_state.file_content = ""
if "exam_history" not in st.session_state:
    st.session_state.exam_history = [] # لتخزين درجات الامتحانات السابقة
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = None

# --- 5. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.header("🎓 لوحة التحكم")
    
    # اختيار الوضع
    mode = st.radio("اختار عايز تعمل إيه:", ["💬 المذاكرة والشات", "📝 اختبار ومراجعة", "📊 تقييم مستواك"])
    
    st.divider()
    st.subheader("📂 المادة العلمية")
    uploaded_file = st.file_uploader("ارفع الملف هنا", type=["jpg", "png", "pdf", "docx"])
    
    if uploaded_file is not None:
        if st.button("معالجة الملف 🚀"):
            with st.spinner("جاري قراءة الملف..."):
                try:
                    filename = uploaded_file.name
                    if filename.endswith(".docx"):
                        st.session_state.file_content = get_docx_text(uploaded_file)
                    elif filename.endswith(".pdf"):
                        st.session_state.file_content = get_pdf_text(uploaded_file)
                    else:
                        image = Image.open(uploaded_file)
                        response = model.generate_content(["استخرج كل النصوص", image])
                        st.session_state.file_content = response.text
                    
                    st.success("تم التجهيز! المدرس جاهز.")
                except Exception as e:
                    st.error(f"خطأ: {e}")

# --- 6. الوضع الأول: الشات ---
if mode == "💬 المذاكرة والشات":
    st.title("💬 دردش مع المذكرة")
    
    if not st.session_state.file_content:
        st.info("👈 من فضلك ارفع ملف من القائمة الجانبية الأول.")
    else:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("اكتب سؤالك..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            full_prompt = f"المحتوى التعليمي:\n{st.session_state.file_content}\n\nسؤال الطالب: {prompt}\nجاوب كأستاذ محترف."
            
            with st.chat_message("assistant"):
                with st.spinner("بيكتب..."):
                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})

# --- 7. الوضع الثاني: الامتحانات ---
elif mode == "📝 اختبار ومراجعة":
    st.title("📝 اختبر نفسك")
    
    if not st.session_state.file_content:
        st.warning("ارفع الملف الأول عشان أعرف أمتحنك فيه!")
    else:
        col1, col2 = st.columns(2)
        with col1:
            num_questions = st.slider("عدد الأسئلة", 3, 10, 5)
        with col2:
            difficulty = st.select_slider("مستوى الصعوبة", options=["سهل", "متوسط", "صعب"])

        if st.button("أنشئ الامتحان الآن 🎲"):
            with st.spinner("المدرس بيحط الأسئلة..."):
                quiz_prompt = f"""
                Create a quiz based on this text: "{st.session_state.file_content[:4000]}..."
                Create {num_questions} multiple choice questions. Difficulty: {difficulty}.
                The output MUST be a valid JSON array of objects. 
                Each object must have: "question", "options" (array of 4 strings), and "answer" (the correct string).
                Example format:
                [
                    {{"question": "What is...?", "options": ["A", "B", "C", "D"], "answer": "A"}}
                ]
                Response Language: Arabic.
                ONLY JSON. NO MARKDOWN.
                """
                try:
                    response = model.generate_content(quiz_prompt)
                    cleaned_json = clean_json_string(response.text)
                    st.session_state.current_quiz = json.loads(cleaned_json)
                    st.rerun()
                except Exception as e:
                    st.error("حصلت مشكلة في إنشاء الامتحان، حاول تاني.")
                    st.write(e)

        # عرض الامتحان لو موجود
        if st.session_state.current_quiz:
            with st.form("quiz_form"):
                user_answers = {}
                for i, q in enumerate(st.session_state.current_quiz):
                    st.subheader(f"س {i+1}: {q['question']}")
                    user_answers[i] = st.radio("الإجابة:", q['options'], key=f"q_{i}")
                    st.write("---")
                
                submitted = st.form_submit_button("تسليم الإجابة ✅")
                
                if submitted:
                    score = 0
                    total = len(st.session_state.current_quiz)
                    
                    st.write("### 📄 نتيجة الامتحان:")
                    for i, q in enumerate(st.session_state.current_quiz):
                        correct = q['answer']
                        user_choice = user_answers[i]
                        
                        if user_choice == correct:
                            score += 1
                            st.success(f"س {i+1}: إجابة صحيحة! ({user_choice})")
                        else:
                            st.error(f"س {i+1}: خطأ. إجابتك: {user_choice} | الصح: {correct}")
                    
                    final_score = (score / total) * 100
                    st.metric(label="الدرجة النهائية", value=f"{final_score}%")
                    
                    # حفظ النتيجة في التاريخ
                    st.session_state.exam_history.append({"Score": final_score, "Difficulty": difficulty, "Questions": total})
                    
                    if final_score >= 50:
                        st.balloons()
                    else:
                        st.warning("محتاج تذاكر أكتر! 📚")

# --- 8. الوضع الثالث: تقييم الأداء ---
elif mode == "📊 تقييم مستواك":
    st.title("📊 تقرير الأداء الشامل")
    
    if len(st.session_state.exam_history) == 0:
        st.info("لسه مفيش بيانات. ادخل وحل امتحانات الأول عشان أقيمك!")
    else:
        # تحويل البيانات لجدول عشان نعرضها
        df = pd.DataFrame(st.session_state.exam_history)
        
        # 1. ملخص سريع
        col1, col2, col3 = st.columns(3)
        col1.metric("عدد الامتحانات", len(df))
        col2.metric("متوسط الدرجات", f"{df['Score'].mean():.1f}%")
        col3.metric("أفضل درجة", f"{df['Score'].max()}%")
        
        st.divider()
        
        # 2. رسم بياني للتقدم
        st.subheader("📈 منحنى التقدم بتاعك")
        st.line_chart(df['Score'])
        
        # 3. نصيحة من المدرس
        avg = df['Score'].mean()
        st.subheader("👨‍🏫 تقييم المدرس:")
        if avg >= 85:
            st.success("مستواك ممتاز يا بطل! استمر على كده. 🌟")
        elif avg >= 70:
            st.info("مستوى جيد جداً، بس ركز شوية في التفاصيل. 👍")
        elif avg >= 50:
            st.warning("مستواك متوسط، محتاج تحل أسئلة أكتر وتراجع الأخطاء. ⚠️")
        else:
            st.error("المستوى ضعيف. أنصحك ترجع تقرأ المذكرة تاني وتستخدم الشات عشان تفهم اللي فاتك. 🛑")
        
        # عرض الجدول بالتفصيل
        with st.expander("سجل الامتحانات السابق"):
            st.dataframe(df)
