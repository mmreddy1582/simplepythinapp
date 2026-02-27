import streamlit as st
import requests
import os
from dotenv import load_dotenv
import base64
import zipfile
import io

# Page config
st.set_page_config(page_title="Document Translator", page_icon=":globe_with_meridians:", layout="centered")

# Load environment variables
load_dotenv()
url = "https://esiautomationai.openai.azure.com/translator/document:translate"
#url = "https://EISCustomTranslator2.cognitiveservices.azure.com/translator/document:translate"
#AZURE_API_KEY="1SvAQpdYc3liDmIevZLMosUFdJ0h1GtpFtVtqMnov9D1FhBUyaNWJQQJ99BHACULyCpXJ3w3AAAbACOGyN8s"
AZURE_KEY = os.getenv("AZURE_API_KEY")
headers = {
    "Ocp-Apim-Subscription-Key": AZURE_KEY
}

# Custom CSS
st.markdown("""
<style>
    /* Enable scrolling based on content */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
        min-height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    [data-testid="stAppViewBlockContainer"] {
        overflow-y: visible !important;
        height: auto !important;
        padding-bottom: 2rem;
    }
    
    /* Header */
    .header {
        display: flex;
        align-items: center;
        padding: 10px 20px;
        border-bottom: 3px solid #E53935;
        background-color: #fff;
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    .header img {
        height: 40px;
    }

    /* Upload box */
    .upload-box {
        border: 2px dashed #ddd;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        color: #666;
        background-color: #fafafa;
        margin-bottom: 20px;
    }

    /* Translate button */
    div.stButton > button:first-child {
        background-color: #E53935;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 20px;
    }
    div.stButton > button:first-child:hover {
        background-color: #c62828;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# Function to encode image as base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        b64_img = base64.b64encode(img_file.read()).decode()
    return b64_img

# Use relative path for logo
logo_path = os.path.join(os.path.dirname(__file__), "es.gif")
logo_base64 = get_base64_image(logo_path)

# Header with logo (base64) and title
st.markdown(
    f"""
<div class="header">
    <img src="data:image/gif;base64,{logo_base64}">
    <h2 style="margin-left:56px; color:#E53935; font-weight:700;">ESI Document Translator</h2>
</div>
    """,
    unsafe_allow_html=True
)

# Upload file box (add xlsx, xls, csv) - marked as mandatory, single file only
uploaded_file = st.file_uploader("Upload Document *", type=["doc", "docx", "pdf", "txt", "ppt", "pptx", "xlsx", "xls", "csv"], accept_multiple_files=False)

# Language selectors with empty option for validation
source_lang = st.selectbox(
    "Source Language: *",
    ["", "Afrikaans", "Chinese (Literary)", "Chinese Simplified", "Chinese Traditional", "Dutch", "English", "Filipino", "French", "German", "Greek", "Hindi", "Indonesian", "Italian", "Japanese", "Korean", "Malay (Latin)", "Russian", "Thai", "Vietnamese"],
    index=6  # "English" is now at index 6 (after empty option)
)
target_lang = st.selectbox(
    "Target Language: *",
    ["", "Afrikaans", "Chinese (Literary)", "Chinese Simplified", "Chinese Traditional", "Dutch", "English", "Filipino", "French", "German", "Greek", "Hindi", "Indonesian", "Italian", "Japanese", "Korean", "Malay (Latin)", "Russian", "Thai", "Vietnamese"]
)

# Map UI languages to Azure codes (add more as needed)
language_options = {
    "Afrikaans": "af",
    "Chinese (Literary)": "lzh",
    "Chinese Simplified": "zh-Hans",
    "Chinese Traditional": "zh-Hant",
    "Dutch": "nl",
    "English": "en",
    "Filipino": "fil",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Hindi": "hi",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Malay (Latin)": "ms",
    "Russian": "ru",
    "Thai": "th",
    "Vietnamese": "vi"
}

# Translate button and logic
if st.button("🔄 Translate"):
    # Validate all mandatory fields
    errors = []
    
    if not uploaded_file:
        errors.append("❌ Please upload a document. This field is mandatory.")
    
    # Check if multiple files were somehow uploaded (extra safety check)
    if isinstance(uploaded_file, list):
        errors.append("❌ Multiple file uploads are not supported. Please upload only one document at a time.")
    
    if not source_lang or source_lang == "":
        errors.append("❌ Please select a Source Language. This field is mandatory.")
    
    if not target_lang or target_lang == "":
        errors.append("❌ Please select a Target Language. This field is mandatory.")
    
    # Check if source and target languages are the same
    if source_lang and target_lang and source_lang == target_lang:
        errors.append("❌ Source Language and Target Language must be different.")
    
    # Check if API key is configured
    if not AZURE_KEY:
        errors.append("❌ Azure API key not configured. Please contact admin.")
    
    # Display all validation errors
    if errors:
        for error in errors:
            st.error(error)
    else:
        # Get file extension
        ext = uploaded_file.name.split('.')[-1].lower()
        
        # Check if file is empty
        if uploaded_file.size == 0:
            st.error("❌ The uploaded file is empty. Please upload a valid document.")
        else:
            # Define supported file formats
            supported_formats = ["doc", "docx", "pdf", "txt", "ppt", "pptx", "xlsx", "xls", "csv"]
            
            # Check if file format is supported
            if ext not in supported_formats:
                st.error(f"❌ Unsupported file format: '.{ext}'. Please upload a file with one of these formats: {', '.join(supported_formats)}")
            else:
                # Check file size before translation
                max_bytes = 50 * 1024 * 1024 if ext != 'txt' else 1 * 1024 * 1024  # 50MB or 1MB
                if uploaded_file.size > max_bytes:
                    st.error(f"❌ The uploaded file exceeds the maximum allowed size ({max_bytes // (1024*1024)} MB). Please upload a smaller file.")
                else:
                    # All validations passed, proceed with translation
                    params = {
                        "sourceLanguage": language_options.get(source_lang, "en"),
                        "targetLanguage": language_options.get(target_lang, "te"),
                        "api-version": "2024-05-01"
                    }
                    mime_types = {
                        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "doc": "application/msword",
                        "pdf": "application/pdf",
                        "txt": "text/plain",
                        "ppt": "application/vnd.ms-powerpoint",
                        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "xls": "application/vnd.ms-excel",
                        "csv": "text/csv"
                    }
                    mime_type = mime_types.get(ext, "application/octet-stream")
                    files = {
                        "document": (uploaded_file.name, uploaded_file, mime_type)
                    }
                    try:
                        # Show progress bar during upload and translation
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("Uploading document...")
                        progress_bar.progress(25)
                        
                        with st.spinner("Translating..."):
                            response = requests.post(url, headers=headers, params=params, files=files, timeout=300)
                            progress_bar.progress(75)
                            status_text.text("Processing translation...")
                        
                        progress_bar.progress(100)
                        status_text.text("Translation complete!")
                        
                        if response.status_code == 200:
                            st.success("Translation successful!")
                            st.download_button(
                                label=f"Download Translated {ext.upper()}",
                                data=response.content,
                                file_name=f"Translated_{target_lang}.{ext}",
                                mime=mime_type
                            )
                            st.info("**Disclaimer:** The Document Translator achieves about 99% accuracy for supported formats. Please review all translated documents before publishing or sharing.")
                        elif response.status_code == 401:
                            st.error("❌ Authentication failed—invalid Azure API key.")
                        elif response.status_code == 403:
                            st.error("❌ Access Denied. Check Azure permissions and quotas.")
                            # Check for specific quota errors in response
                            try:
                                error_data = response.json()
                                if "error" in error_data:
                                    error_code = error_data.get("error", {}).get("code", "")
                                    inner_error = error_data.get("error", {}).get("innerError", {})
                                    inner_code = inner_error.get("code", "")
                                    if "QuotaExceeded" in error_code or "QuotaExceeded" in inner_code:
                                        st.error("❌ Translation quota has been exceeded. Please contact your administrator or try again later.")
                                    elif "MaxDocumentSizeExceeded" in error_code or "MaxDocumentSizeExceeded" in inner_code:
                                        st.error("❌ The document size exceeds the maximum allowed limit.")
                            except:
                                pass
                        elif response.status_code == 429:
                            st.error("❌ Rate limit exceeded. Please try again later.")
                        elif response.status_code == 500:
                            st.error("❌ Translation service is unavailable. Please try again later.")
                        else:
                            st.error(f"❌ Translation failed with status code: {response.status_code}")
                            # Try to parse and display specific error messages from API
                            try:
                                error_data = response.json()
                                if "error" in error_data:
                                    error_message = error_data.get("error", {}).get("message", "")
                                    error_code = error_data.get("error", {}).get("code", "")
                                    inner_error = error_data.get("error", {}).get("innerError", {})
                                    inner_code = inner_error.get("code", "")
                                    inner_message = inner_error.get("message", "")
                                    
                                    if error_message:
                                        st.error(f"Error: {error_message}")
                                    if error_code:
                                        st.error(f"Error Code: {error_code}")
                                    if inner_code:
                                        st.error(f"Details: {inner_code} - {inner_message}")
                                    
                                    # Check for specific quota/limit errors
                                    if "QuotaExceeded" in error_code or "QuotaExceeded" in inner_code:
                                        st.error("❌ Translation quota has been exceeded. Please contact your administrator.")
                                    elif "MaxDocumentSizeExceeded" in error_code or "MaxDocumentSizeExceeded" in inner_code:
                                        st.error("❌ The document size exceeds the maximum allowed limit.")
                                else:
                                    st.error(response.text)
                            except:
                                st.error(response.text)
                    except requests.exceptions.Timeout:
                        st.error("❌ Request timed out. The translation service is taking too long to respond. Please try again later.")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Connection error. Unable to reach the translation service. Please check your internet connection and try again.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Network error: {str(e)}. Please check your connection and try again.")
