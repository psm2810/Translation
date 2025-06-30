import streamlit as st
import pandas as pd
from google.cloud import aiplatform
from google.cloud import translate_v2 as translate
import io
import html
import re
import emoji
import os

# Initialize Google Cloud AI Platform
PROJECT_ID = 'ford-180395bd732cdd9af050c1f7'  # Your project ID
REGION = 'us-central1'  # Your region
aiplatform.init(project=PROJECT_ID, location=REGION)

# Initialize the Translator client
translate_client = translate.Client()

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
def translate_to_english(verbatim):
    try:
        result = translate_client.translate(verbatim, target_language='en')
        translated_text = html.unescape(result['translatedText'])
        
        # Apply post-processing
        translated_text = convert_emoticons(translated_text)
        translated_text = remove_usernames(translated_text)
        translated_text = remove_hyperlinks(translated_text)
        translated_text = clean_extra_spaces(translated_text)
        translated_text = standardize_quotes(translated_text)
        #translated_text = remove_special_characters(translated_text)

        return translated_text
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit Application
st.title("CIA Language Translation App")
st.markdown("Description: This is a Multi-Sheet, Multi-Language Auto-detect capabled Translation App")
st.write("Upload an Excel file with multiple sheets containing a 'Verbatim' column for translation.")

# File uploader
uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx'])

if uploaded_file is not None:
    # Extract the original file name without the extension
    original_file_name = os.path.splitext(uploaded_file.name)[0]
    
    # Load the Excel file to get sheet names
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names

    # Select a sheet to translate
    selected_sheet = st.selectbox("Select a sheet for translation:", sheet_names)

    if selected_sheet:
        # Load the selected sheet
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # Check if 'Verbatim' column exists
        if 'Verbatim' in df.columns:
            # Translate the 'Verbatim' column
            df['Translation'] = df['Verbatim'].apply(translate_to_english)

            # Display the DataFrame with translations
            st.write(f"Translations completed for sheet: {selected_sheet}")
            st.dataframe(df)

            # Create a BytesIO buffer for the Excel file
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Translations')

            # Set the buffer position to the beginning
            output_buffer.seek(0)

            # Download button for the translated output
            st.download_button(
                label="Download Translated File",
                data=output_buffer,
                file_name=f'{original_file_name}_translated_{selected_sheet}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            st.error("The selected sheet does not contain a 'Verbatim' column.")
