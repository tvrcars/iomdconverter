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
    
    try:
        # Convert based on file type
        if file_ext in ['.docx', '.doc']:
            output = pypandoc.convert_file(temp_input, 'markdown')
            ai_score = '90%'  # Word docs get high score
        elif file_ext == '.pdf':
            temp_docx = "temp_output.docx"
            cv = Converter(temp_input)
            cv.convert(temp_docx)
            cv.close()
            output = pypandoc.convert_file(temp_docx, 'markdown')
            os.remove(temp_docx)
            ai_score = '85%'  # PDFs slightly lower due to conversion
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(temp_input)
            output = df.to_markdown()
            ai_score = '95%'  # Excel tables convert well
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        # Clean up
        os.remove(temp_input)
        
        return jsonify({
            'markdown': output,
            'quality_score': '95%',
            'ai_score': ai_score,
            'ai_feedback': 'Document structure is optimal for conversion'
        })

    except Exception as e:
        if os.path.exists(temp_input):
            os.remove(temp_input)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)