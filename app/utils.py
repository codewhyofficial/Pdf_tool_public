import os
import re
import PyPDF2
from fpdf import FPDF
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the uploads directory exists
UPLOAD_FOLDER = 'app/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure Google Generative AI with the API key from the environment variable
API_KEY = os.getenv('API_KEY')
genai.configure(api_key=API_KEY)

def preprocess_text(text):
    # Replace newlines and carriage returns with spaces
    text = text.replace("\n", " ").replace("\r", "")
    
    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)

    #keep only printable ascii characters 
    text = re.sub(r'[^\x20-\x7E]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Replace single asterisks with bullet points
    text = re.sub(r'(?<!\*)\*([^*]+)(?<!\*)\*', r'\1', text)  # Change *text* to • text

    # Replace double asterisks with bold tags
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)  # Change **text** to <b>text</b>

    return text.strip()

def extract_text_from_pdf(pdf_path):
    full_text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            full_text += preprocess_text(text) + " "
    return full_text.strip()

def get_questions_from_gemini(full_text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Extract only genuine questions exactly as they appear in the following text without adding any explanations or instructions: {full_text}"
    response = model.generate_content(prompt)
    
    questions = [
        q.strip() for q in response.text.split('\n')
        if q.strip() 
        and not re.search(r"(?i)(genuine|standalone|provide me|the questions are|context|referring to|need the text|identify)", q)
        and len(q.strip()) > 10
    ]
    
    return questions

def get_answers_from_gemini(questions):
    answers = []
    for question in questions:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(question)
        answers.append(response.text.strip())
    return answers

def remove_unsupported_characters(text):
    # Remove characters that are not printable ASCII
    return re.sub(r'[^\x20-\x7E]', '', text)  # Keep only printable ASCII characters


def create_enhanced_output_pdf(qa_pairs, output_path):
    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    for question, answer in qa_pairs:
        question = remove_unsupported_characters(question)
        answer = remove_unsupported_characters(answer)
        # Add question
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Q: {question}", ln=True, align='L', border=0)

        # Clean the answer text
        answer = answer.replace('*', '')  # Remove asterisks
        answer = re.sub(r'\n\s*\n+', '\n\n', answer)  # Reduce multiple blank lines to one

        # Split the answer into lines to handle bullet points
        lines = answer.split('\n')
        for line in lines:
            line = line.strip()  # Remove leading/trailing whitespace
            if not line:  # Skip empty lines
                continue

            # Check for bullet points
            if line.startswith('-'):
                pdf.cell(0, 10, line, ln=True, align='L', border=0)
            else:
                # Replace bold markers with a marker for FPDF
                parts = re.split(r'(\*\*.*?\*\*)', line)  # Split on bold markers
                for part in parts:
                    part = part.strip()  # Clean part
                    if part.startswith('**') and part.endswith('**'):
                        bold_text = part[2:-2]  # Remove the bold markers
                        pdf.set_font("Arial", 'B', 12)  # Set bold font
                        pdf.multi_cell(0, 10, bold_text)  # Use multi_cell for wrapping
                    elif part:  # Ensure part is not empty
                        pdf.set_font("Arial", '', 12)  # Reset to regular font
                        pdf.multi_cell(0, 10, part)  # Use multi_cell for wrapping
        pdf.ln(5)  # Add space between Q&A pairs

    try:
        pdf.output(output_path)  # Finalize the PDF creation
    except Exception as e:
        print(f"Error creating PDF: {e}")  # Log the error for debugging
