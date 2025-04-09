# MediWhiz - Medical Report Analyzer

MediWhiz is an AI-driven healthcare platform designed to help patients understand their medical reports. The application analyzes medical PDFs, extracts important information, and provides simplified summaries.

## Features

- **PDF Upload & Analysis**: Upload medical reports and get instant analysis
- **AI Consultation**: Ask health questions and receive evidence-based answers
- **Data Security**: Your health data is encrypted and secure
- **Health Timeline**: Track your health progress over time

## Technical Overview

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Text Processing**: NLTK for natural language processing
- **PDF Processing**: PyPDF2 and pytesseract for text extraction

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```
   pip install flask flask-cors PyPDF2 pytesseract pdf2image nltk Pillow
   ```
3. Run the Flask server:
   ```
   python app.py
   ```
4. Open `medi.html` in your browser or serve it using a web server

## API Endpoints

- `GET /`: Check if the API is running
- `POST /upload_pdf`: Upload a PDF for processing
- `GET /get_summary/<summary_id>`: Retrieve a generated summary
- `GET /view_pdf/<pdf_id>`: View the original PDF

## Contact

Rohit Kshirsagar 
Email: rohitkshirsagar1904@gmail.com
