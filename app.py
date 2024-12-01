from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import pypandoc
from pdf2docx import Converter
import pandas as pd

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
    
    # Convert based on file type
    try:
        if file_ext in ['.docx', '.doc']:
            output = pypandoc.convert_file(temp_input, 'markdown')
        elif file_ext == '.pdf':
            # Convert PDF to DOCX first
            temp_docx = "temp_output.docx"
            cv = Converter(temp_input)
            cv.convert(temp_docx)
            cv.close()
            # Then convert DOCX to Markdown
            output = pypandoc.convert_file(temp_docx, 'markdown')
            os.remove(temp_docx)
        elif file_ext in ['.xlsx', '.xls']:
            # Read Excel file
            df = pd.read_excel(temp_input)
            # Convert to markdown table
            output = df.to_markdown()
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        # Clean up
        os.remove(temp_input)
        
        return jsonify({
            'markdown': output,
            'quality_score': '95%',  # Placeholder
            'ai_score': '90%'        # Placeholder
        })

    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_input):
            os.remove(temp_input)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)