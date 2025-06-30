import streamlit as st
import pandas as pd
from google.cloud import aiplatform
from google.cloud import translate_v2 as translate
import io
import html
import re
import emoji

# Initialize Google Cloud AI Platform
PROJECT_ID = 'ford-180395bd732cdd9af050c1f7'  # Your project ID
REGION = 'us-central1'  # Your region
aiplatform.init(project=PROJECT_ID, location=REGION)

# Initialize the Translator client
translate_client = translate.Client()

# List of common languages for user selection
LANGUAGES = {
    'Auto Detect': None,
    'Arabic': 'ar',
    'Bulgarian': 'bg',
    'Catalan': 'ca',
    'Chinese (Simplified)': 'zh-CN',
    'Chinese (Traditional)': 'zh-TW',
    'Croatian': 'hr',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'English': 'en',
    'Estonian': 'et',
    'Finnish': 'fi',
    'French': 'fr',
    'German': 'de',
    'Greek': 'el',
    'Hungarian': 'hu',
    'Indonesian': 'id',
    'Italian': 'it',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Latvian': 'lv',
    'Lithuanian': 'lt',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Romanian': 'ro',
    'Russian': 'ru',
    'Slovak': 'sk',
    'Slovenian': 'sl',
    'Spanish': 'es',
    'Swedish': 'sv',
    'Thai': 'th',
    'Turkish': 'tr',
    'Ukrainian': 'uk',
    'Vietnamese': 'vi'
}

def convert_emoticons(text):
    return emoji.demojize(text)

def remove_usernames(text):
    return re.sub(r'@\w+', '', text)

def remove_hyperlinks(text):
    return re.sub(r'http\S+|www\S+|https\S+', '', text)

def clean_extra_spaces(text):
    return re.sub(r'\s+', ' ', text).strip()

def standardize_quotes(text):
    return text.replace('“', '"').replace('”', '"')

# def remove_special_characters(text):
#     return re.sub(r'[^a-zA-Z0-9\s.,!?\'"()]+', '', text)

# Function to translate text to English with post-processing
def translate_text(text, source_language):
    try:
        result = translate_client.translate(text, target_language='en', source_language=source_language)
        translated_text = html.unescape(result['translatedText'])
        
        # Apply post-processing
        translated_text = convert_emoticons(translated_text)
        translated_text = remove_usernames(translated_text)
        translated_text = remove_hyperlinks(translated_text)
        translated_text = clean_extra_spaces(translated_text)
        translated_text = standardize_quotes(translated_text)
        # translated_text = remove_special_characters(translated_text)

        return translated_text
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit Application
st.title("CIA Language Translation App")
st.markdown("Description: This is an advanced AI-powered language translator that can Auto-detect and translate Multi-Sheet, Multi-Language MS Excel files")
st.write("Upload an Excel file with multiple sheets containing text for translation.")

# Language selection dropdown
source_language = st.selectbox("Select source language:", list(LANGUAGES.keys()))

# File uploader
uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx'])

if uploaded_file is not None:
    # Load the Excel file to get sheet names
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names

    # Select multiple sheets to translate
    selected_sheets = st.multiselect("Select sheets for translation:", sheet_names)

    # Submit button to trigger translation
    if st.button("Submit"):
        if selected_sheets:
            # Create a dictionary to hold all sheets
            all_sheets = {}

            # Load all sheets into the dictionary
            for sheet in sheet_names:
                df = pd.read_excel(uploaded_file, sheet_name=sheet)

                # If this sheet is selected, translate all columns
                if sheet in selected_sheets:
                    for column in df.columns:
                        df[column] = df[column].astype(str).apply(lambda x: translate_text(x, LANGUAGES[source_language]))
                    all_sheets[sheet] = df  # Save the translated DataFrame
                else:
                    all_sheets[sheet] = df  # Save the original DataFrame

            # Create a BytesIO buffer for the Excel file
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                for sheet_name, data in all_sheets.items():
                    data.to_excel(writer, index=False, sheet_name=sheet_name)

            # Set the buffer position to the beginning
            output_buffer.seek(0)

            # Download button for the translated output
            st.download_button(
                label="Download Translated File",
                data=output_buffer,
                file_name=f'translated_{uploaded_file.name}',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        else:
            st.warning("Please select at least one sheet to translate.")
