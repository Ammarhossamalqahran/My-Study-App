import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import docx  # دي المكتبة الجديدة للورد

# --- 1. إعداد مفتاح جوجل ---
# هنجيب المفتاح من مخزن الأسرار في السيرفر
api_key = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)
genai.configure(api_key=api_key)

# --- 2. إعداد الموديل (النسخة السريعة) ---
model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. دوال قراءة الملفات ---

# قراءة PDF
def get_pdf_text(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# قراءة Word (جديد)
def get_docx_text(uploaded_file):
    doc = docx.Document(uploaded_file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# --- 4. واجهة التطبيق ---
st.set_page_config(page_title="المدرس الشامل", page_icon="📚", layout="wide")

st.title("📚 المدرس الشامل (Word, PDF, صور)")
st.write("ارفع مذكراتك (Word أو PDF) أو صور المسائل، وسأقوم بشرحها.")

# تم إضافة docx للقائمة المسموحة
uploaded_file = st.file_uploader("اختر ملفاً...", type=["jpg", "png", "pdf", "docx"])

if uploaded_file is not None:
    # زرار الشرح
    if st.button("🚀 ابدأ الشرح والتحليل"):
        with st.spinner('جاري قراءة الملف وتحليله...'):
            try:
                filename = uploaded_file.name
                prompt_text = ""
                
                # 1. لو كان ملف Word
                if filename.endswith(".docx"):
                    text_content = get_docx_text(uploaded_file)
                    st.info("تم قراءة ملف الورد بنجاح ✅")
                    prompt_text = text_content
                    
                    # إرسال النص للموديل
                    response = model.generate_content(f"قم بتلخيص وشرح هذا المحتوى الدراسي بأسلوب مبسط:\n\n{prompt_text}")
                    st.markdown("### 📝 الشرح:")
                    st.write(response.text)

                # 2. لو كان ملف PDF
                elif filename.endswith(".pdf"):
                    text_content = get_pdf_text(uploaded_file)
                    st.info("تم قراءة ملف PDF بنجاح ✅")
                    prompt_text = text_content
                    
                    # إرسال النص للموديل
                    response = model.generate_content(f"قم بتلخيص وشرح هذا المحتوى الدراسي بأسلوب مبسط:\n\n{prompt_text}")
                    st.markdown("### 📝 الشرح:")
                    st.write(response.text)

                # 3. لو كان صورة
                else:
                    image = Image.open(uploaded_file)
                    st.image(image, caption='الصورة المرفوعة', use_column_width=True)
                    response = model.generate_content(["اشرح لي محتوى هذه الصورة التعليمية بالتفصيل.", image])
                    st.markdown("### 💡 شرح الصورة:")
                    st.write(response.text)

            except Exception as e:
                st.error(f"حدث خطأ: {e}")