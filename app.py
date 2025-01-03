from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import os
import pypandoc
import pandas as pd
import fitz  # PyMuPDF
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static',
    template_folder='templates'
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(os.path.join(root_dir, 'static'), filename)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Get file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # Save uploaded file temporarily
    temp_input = f"temp_input{file_ext}"
    file.save(temp_input)
    
    try:
        ai_feedback = ""
        quality_issues = []

        if file_ext in ['.docx', '.doc']:
            try:
                logger.debug(f"Starting DOCX conversion for file: {file.filename}")
                logger.debug("Checking pypandoc installation...")
                pypandoc_version = pypandoc.get_pandoc_version()
                logger.debug(f"Pandoc version: {pypandoc_version}")
                
                output = pypandoc.convert_file(temp_input, 'markdown')
                logger.debug("DOCX conversion completed successfully")
                
                # Analyze content for AI training suitability
                word_count = len(output.split())
                if word_count < 100:
                    ai_score = "40%"
                    ai_feedback = "Limited content for AI training. This document needs more comprehensive information to be useful for training."
                    quality_issues.append("Document is too short for effective training")
                elif word_count < 500:
                    ai_score = "70%"
                    ai_feedback = "Moderate content volume. Adding more examples and detailed explanations would improve training quality."
                    quality_issues.append("Consider adding more detailed examples")
                else:
                    ai_score = "85%"
                    ai_feedback = "Good content volume for AI training. Consider adding structured sections and technical details if applicable."
                    
            except OSError as e:
                logger.error(f"Pandoc system error: {str(e)}")
                return jsonify({
                    'error': 'System configuration error. Please try again later.',
                    'details': str(e)
                }), 500
                
            except Exception as e:
                logger.error(f"DOCX conversion error: {str(e)}")
                return jsonify({
                    'error': 'Failed to convert DOCX file',
                    'details': str(e)
                }), 500
                
        elif file_ext == '.pdf':
            # Open the PDF file
            doc = fitz.open(temp_input)
            text = ""
            
            # Extract text from each page
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # Add some basic markdown formatting
            output = f"# {os.path.splitext(file.filename)[0]}\n\n{text}"
            
            # PDF-specific analysis
            content_length = len(output)
            if content_length < 500:
                ai_score = "60%"
                ai_feedback = "PDF conversion successful but limited content."
                quality_issues.append("Short PDF content may not provide enough context")
            else:
                ai_score = "75%"
                ai_feedback = "Good content volume from PDF conversion."
            
        elif file_ext in ['.xlsx', '.xls']:
            # Read Excel file
            df = pd.read_excel(temp_input)
            output = df.to_markdown()
            
            # Analyze spreadsheet structure
            rows, cols = df.shape
            if rows < 10:
                ai_score = "50%"
                ai_feedback = "Limited dataset. More rows would improve training quality. Consider adding more examples."
                quality_issues.append("Dataset too small for effective training")
            elif cols < 3:
                ai_score = "65%"
                ai_feedback = "Good number of examples but limited features. Consider adding more descriptive columns."
                quality_issues.append("Limited number of features/columns")
            else:
                ai_score = "85%"
                ai_feedback = "Good structured data for training. Consider adding column descriptions and data type information."
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        # Clean up
        os.remove(temp_input)
        
        # Calculate quality score based on content and issues
        quality_score = f"{min(95, 100 - (len(quality_issues) * 10))}%"
        
        # Save the markdown output to a file
        with open('output.md', 'w', encoding='utf-8') as f:
            f.write(output)
            
        # Store the original filename in the response
        original_name = os.path.splitext(file.filename)[0]
        
        return jsonify({
            'markdown': output,
            'quality_score': quality_score,
            'quality_issues': '. '.join(quality_issues) if quality_issues else "No significant quality issues found",
            'ai_score': ai_score,
            'ai_feedback': ai_feedback,
            'filename': original_name
        })

    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        return str(e), 500

@app.route('/download', methods=['GET'])
def download_file():
    file_path = 'output.md'
    if not os.path.exists(file_path):
        return "File not found", 404
    
    # Read the content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create response
    response = app.response_class(
        response=content,
        status=200,
        mimetype='text/markdown'
    )
    
    # Set headers for download
    response.headers['Content-Disposition'] = 'attachment; filename="{}.md"'.format(
        request.args.get('filename', 'output')
    )
    
    return response

if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=5000)