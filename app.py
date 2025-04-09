from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
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
from datetime import datetime
import shutil

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create necessary directories if they don't exist
UPLOAD_FOLDER = 'uploads'
SUMMARY_FOLDER = 'summaries'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

# Download NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    logger.error(f"Failed to download NLTK resources: {e}")

@app.route('/')
def index():
    # Serve the HTML template instead of JSON for the root route
    return render_template('medi.html')

@app.route('/api/status')
def api_status():
    # Move the JSON status to a separate endpoint
    return jsonify({
        "status": "success",
        "message": "MediWhiz API is running",
        "version": "1.0.0",
        "endpoints": {
            "upload_pdf": "/upload_pdf (POST)",
            "get_summary": "/get_summary/<summary_id> (GET)",
            "view_pdf": "/view_pdf/<pdf_id> (GET)"
        }
    })

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
        
        if file and file.filename.lower().endswith('.pdf'):
            unique_filename = str(uuid.uuid4()) + '.pdf'
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            logger.info(f"PDF uploaded: {file.filename} -> {unique_filename}")
            
            try:
                logger.info(f"Processing PDF: {unique_filename}")
                text = extract_text_from_pdf(file_path)
                
                if not text or len(text.strip()) < 50:
                    logger.warning(f"Extracted text is too short or empty for {unique_filename}")
                    return jsonify({
                        'success': False, 
                        'message': 'Could not extract sufficient text from the PDF. Please try another file.'
                    }), 400
                
                logger.info(f"Generating summary for {unique_filename}")
                summary = generate_summary(text)
                
                summary_filename = str(uuid.uuid4()) + '.txt'
                summary_path = os.path.join(SUMMARY_FOLDER, summary_filename)
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                
                logger.info(f"Summary saved: {summary_filename}")
                
                return jsonify({
                    'success': True, 
                    'message': 'PDF uploaded and processed successfully!',
                    'original_filename': file.filename,
                    'pdf_id': unique_filename.split('.')[0],
                    'summary_id': summary_filename.split('.')[0]
                }), 200
            except Exception as e:
                logger.error(f"Error processing {unique_filename}: {e}")
                return jsonify({
                    'success': False, 
                    'message': f'Error processing the PDF: {str(e)}'
                }), 500
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
            logger.warning(f"Summary not found: {summary_id}.txt")
            return jsonify({'success': False, 'message': 'Summary not found'}), 404
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary = f.read()
        
        logger.info(f"Summary retrieved: {summary_id}.txt")
        return jsonify({'success': True, 'summary': summary}), 200
    
    except Exception as e:
        logger.error(f"Error retrieving summary {summary_id}: {e}")
        return jsonify({'success': False, 'message': f'Error retrieving summary: {str(e)}'}), 500

@app.route('/view_pdf/<pdf_id>', methods=['GET'])
def view_pdf(pdf_id):
    try:
        pdf_path = os.path.join(UPLOAD_FOLDER, f"{pdf_id}.pdf")
        if not os.path.exists(pdf_path):
            logger.warning(f"PDF not found: {pdf_id}.pdf")
            return jsonify({'success': False, 'message': 'PDF not found'}), 404
        
        logger.info(f"PDF viewed: {pdf_id}.pdf")
        return send_from_directory(directory=UPLOAD_FOLDER, path=f"{pdf_id}.pdf")
    
    except Exception as e:
        logger.error(f"Error retrieving PDF {pdf_id}: {e}")
        return jsonify({'success': False, 'message': f'Error retrieving PDF: {str(e)}'}), 500

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyPDF2 and fallback to OCR if needed"""
    try:
        text = ""
        logger.info(f"Extracting text from {pdf_path}")
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                extracted_text = pdf_reader.pages[page_num].extract_text()
                if extracted_text:
                    text += extracted_text
                else:
                    logger.info(f"Page {page_num + 1} has no extractable text, will use OCR.")

        if len(text.strip()) < 100:
            logger.info(f"Insufficient text extracted, falling back to OCR for {pdf_path}")
            try:
                images = pdf2image.convert_from_path(pdf_path)
                ocr_text = ""
                for i, image in enumerate(images):
                    page_text = pytesseract.image_to_string(image)
                    ocr_text += page_text
                    logger.info(f"OCR extracted {len(page_text)} characters from page {i + 1}")
                
                if len(ocr_text) > len(text):
                    text = ocr_text
                    logger.info(f"Using OCR result: {len(text)} characters extracted")
            except Exception as e:
                logger.error(f"OCR processing failed: {e}")
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise

def generate_summary(text, max_sentences=5):
    """Generate a summary using frequency-based extractive summarization"""
    try:
        sentences = sent_tokenize(text)
        
        if len(sentences) <= max_sentences:
            logger.info(f"Text has only {len(sentences)} sentences, returning full text")
            return text
        
        stop_words = set(stopwords.words('english'))
        medical_terms = {'doctor', 'patient', 'blood', 'test', 'diagnosis', 'treatment', 
                         'symptoms', 'medication', 'disease', 'condition', 'hospital',
                         'clinic', 'report', 'results', 'abnormal', 'normal'}
        
        words = word_tokenize(text.lower())
        freq = FreqDist(words)
        
        for term in medical_terms:
            if freq[term] > len(sentences) * 0.5:
                stop_words.add(term)
        
        words = [word for word in words if word.isalnum() and word not in stop_words]
        freq = FreqDist(words)
        
        scores = {}
        for i, sentence in enumerate(sentences):
            words_in_sentence = word_tokenize(sentence.lower())
            words_in_sentence = [word for word in words_in_sentence if word.isalnum()]
            score = sum(freq[word] for word in words_in_sentence if word in freq) / len(words_in_sentence) if len(words_in_sentence) > 0 else 0
            scores[i] = score
        
        selected_indices = nlargest(max_sentences, scores, key=scores.get)
        selected_indices.sort()
        
        summary = ' '.join(sentences[i] for i in selected_indices)
        
        logger.info(f"Summary generated: {len(sentences)} sentences -> {len(selected_indices)} sentences")
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)