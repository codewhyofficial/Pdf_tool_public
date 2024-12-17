from flask import Blueprint, render_template, request, send_file, send_from_directory, current_app
import os
from .utils import extract_text_from_pdf, get_questions_from_gemini, get_answers_from_gemini, create_enhanced_output_pdf

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    pdf_link = None  # Initialize pdf_link

    if request.method == 'POST':
        # Path to the output PDF
        output_pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'output.pdf')

        # Attempt to remove the previous output PDF if it exists
        try:
            if os.path.exists(output_pdf_path):
                os.remove(output_pdf_path)
                print(f"Successfully removed existing output.pdf: {output_pdf_path}")  # Debug statement
            else:
                print(f"No existing output.pdf to remove at: {output_pdf_path}")  # Debug statement
        except Exception as e:
            print(f"Error removing output.pdf: {e}")  # Log error

        file = request.files['pdf_file']
        if file:
            # Ensure the uploads directory exists
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            filepath = os.path.join(upload_folder, file.filename)
            file.save(filepath)
            print(f"Uploaded file saved at: {filepath}")  # Debug statement

            # Extract full text from PDF
            full_text = extract_text_from_pdf(filepath)
            print(f"Extracted text: {full_text[:100]}...")  # Print first 100 chars for debug

            # Identify original questions using Gemini
            questions = get_questions_from_gemini(full_text)
            print(f"Identified questions: {questions}")  # Debug statement

            # Get answers for the identified questions
            answers = get_answers_from_gemini(questions)
            print(f"Obtained answers: {answers}")  # Debug statement

            # Combine questions and answers
            qa_pairs = list(zip(questions, answers))
            
            # Create the new output PDF
            try:
                create_enhanced_output_pdf(qa_pairs, output_pdf_path)
                print(f"Output PDF created at: {output_pdf_path}")  # Debug statement
            except Exception as e:
                print(f"Error creating PDF: {e}")  # Log error

            # Check if the PDF was created successfully
            if os.path.exists(output_pdf_path):
                pdf_link = f'/uploads/output.pdf'  # Set link to download the PDF
            else:
                print("Failed to create output.pdf")  # Debug statement

    return render_template('index.html', pdf_link=pdf_link)

@main.route('/uploads/<path:filename>', methods=['GET'])
def upload_file(filename):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.isfile(file_path):
        return "File not found", 404
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

