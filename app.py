from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import PyPDF2
import pytesseract
from PIL import Image
import pdf2image
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
from heapq import nlargest
import uuid
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create necessary directories if they don't exist
UPLOAD_FOLDER = 'uploads'
SUMMARY_FOLDER = 'summaries'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

# Download NLTK resources
try:
    nltk.download('punkt')
    nltk.download('stopwords')
except Exception as e:
    logger.error(f"Failed to download NLTK resources: {e}")

@app.route('/')
def index():
    return "MediWhiz API is running"

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
        
        if file and file.filename.endswith('.pdf'):
            # Generate unique filename
            unique_filename = str(uuid.uuid4()) + '.pdf'
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            # Process PDF
            text = extract_text_from_pdf(file_path)
            
            # Generate summary
            summary = generate_summary(text)
            
            # Save summary to file
            summary_filename = str(uuid.uuid4()) + '.txt'
            summary_path = os.path.join(SUMMARY_FOLDER, summary_filename)
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            return jsonify({
                'success': True, 
                'message': 'PDF uploaded and processed successfully!',
                'original_filename': file.filename,
                'pdf_id': unique_filename.split('.')[0],
                'summary_id': summary_filename.split('.')[0]
            }), 200
        else:
            return jsonify({'success': False, 'message': 'File must be a PDF'}), 400
    
    except Exception as e:
        logger.error(f"Error processing PDF upload: {e}")
        return jsonify({'success': False, 'message': f'Error processing PDF: {str(e)}'}), 500

@app.route('/get_summary/<summary_id>', methods=['GET'])
def get_summary(summary_id):
    try:
        summary_path = os.path.join(SUMMARY_FOLDER, f"{summary_id}.txt")
        if not os.path.exists(summary_path):
            return jsonify({'success': False, 'message': 'Summary not found'}), 404
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary = f.read()
        
        return jsonify({'success': True, 'summary': summary}), 200
    
    except Exception as e:
        logger.error(f"Error retrieving summary: {e}")
        return jsonify({'success': False, 'message': f'Error retrieving summary: {str(e)}'}), 500

@app.route('/view_pdf/<pdf_id>', methods=['GET'])
def view_pdf(pdf_id):
    try:
        pdf_path = os.path.join(UPLOAD_FOLDER, f"{pdf_id}.pdf")
        if not os.path.exists(pdf_path):
            return jsonify({'success': False, 'message': 'PDF not found'}), 404
        
        return send_from_directory(UPLOAD_FOLDER, f"{pdf_id}.pdf")
    
    except Exception as e:
        logger.error(f"Error retrieving PDF: {e}")
        return jsonify({'success': False, 'message': f'Error retrieving PDF: {str(e)}'}), 500

def extract_text_from_pdf(pdf_path):
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                extracted_text = pdf_reader.pages[page_num].extract_text()
                if extracted_text:
                    text += extracted_text
                else:
                    print(f"Page {page_num + 1} has no text, using OCR.")

        # If no text found, use OCR
        if len(text.strip()) < 100:
            images = pdf2image.convert_from_path(pdf_path)
            for i, image in enumerate(images):
                ocr_text = pytesseract.image_to_string(image)
                print(f"OCR extracted from page {i + 1}:", ocr_text[:200])  # Print first 200 chars
                text += ocr_text

        return text
    except Exception as e:
        print("Error extracting text from PDF:", e)
        return ""

def generate_summary(text, max_sentences=5):
    """Generate a summary using frequency-based extractive summarization"""
    try:
        # Tokenize text
        sentences = sent_tokenize(text)
        
        # Skip summarization if there are few sentences
        if len(sentences) <= max_sentences:
            return text
        
        # Tokenize words and remove stopwords
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in stop_words]
        
        # Compute word frequencies
        freq = FreqDist(words)
        
        # Score sentences based on word frequencies
        scores = {}
        for i, sentence in enumerate(sentences):
            words_in_sentence = word_tokenize(sentence.lower())
            words_in_sentence = [word for word in words_in_sentence if word.isalnum()]
            score = sum(freq[word] for word in words_in_sentence if word in freq)
            scores[i] = score
        
        # Select top sentences
        selected_indices = nlargest(max_sentences, scores, key=scores.get)
        selected_indices.sort()  # Sort to maintain original order
        
        # Combine selected sentences
        summary = ' '.join(sentences[i] for i in selected_indices)
        
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise

if __name__ == '__main__':
    app.run(debug=True)

    import nltk
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')
except Exception as e:
    print(f"NLTK download error: {e}")
