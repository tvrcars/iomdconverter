from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
import os
import re
import pypandoc
from pdf2docx import Converter
from pathlib import Path
import pandas as pd
import tempfile
import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime
from werkzeug.utils import send_from_directory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static',
    template_folder='templates'
)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

class ConversionError(Exception):
    """Custom exception for conversion errors"""
    pass

def assess_markdown_quality(markdown_text: str, file_type: Optional[str] = None) -> Dict:
    """
    Assess markdown quality with improved scoring.
    """
    quality_score = 100
    issues: List[str] = []
    
    # Basic checks
    if not markdown_text.strip():
        return {'score': 0, 'issues': ['Empty content']}
    
    # Header check
    headers = [line for line in markdown_text.split('\n') if line.strip().startswith('#')]
    if not headers and file_type != 'excel':
        quality_score -= 10
        issues.append("No headers found")
    
    # Table check
    lines = markdown_text.split('\n')
    has_table = False
    has_proper_table = False
    
    for i, line in enumerate(lines):
        if '|' in line:
            has_table = True
            # Check if next line is a proper separator
            if i + 1 < len(lines) and re.match(r'^[\|\s\-]+$', lines[i + 1]):
                has_proper_table = True
                break
    
    if has_table and not has_proper_table:
        quality_score -= 20
        issues.append("Poorly formatted tables")
    
    # File type specific adjustments
    if file_type == 'pdf':
        quality_score = min(100, quality_score + 20)
    elif file_type == 'excel':
        if has_proper_table:
            quality_score = 100
            issues = []
    elif file_type == 'docx':
        quality_score = min(100, quality_score + 10)
    
    # Clean up issues if score is perfect
    if quality_score >= 100:
        issues = []
        quality_score = 100
    
    return {
        'score': max(0, quality_score),
        'issues': issues
    }

def convert_pdf_to_markdown(input_path: str, temp_id: str) -> str:
    """
    Convert PDF to Markdown with improved table handling.
    """
    temp_docx = os.path.join(app.config['UPLOAD_FOLDER'], f"{temp_id}_temp.docx")
    try:
        # Convert PDF to DOCX
        converter = Converter(input_path)
        converter.convert(temp_docx)
        converter.close()
        
        # Get clean filename
        original_filename = os.path.splitext(os.path.basename(input_path))[0]
        clean_filename = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '', original_filename)
        clean_filename = clean_filename.replace('_input', '').strip()
        
        # Convert to markdown
        output = pypandoc.convert_file(
            temp_docx,
            'markdown',
            format='docx',
            extra_args=[
                '--wrap=none',
                '--markdown-headings=atx',
                '--standalone'
            ]
        )
        
        # Process content
        lines = output.split('\n')
        processed_lines = []
        
        # Add title
        processed_lines.append(f'# {clean_filename}\n')
        
        in_table = False
        table_lines = []
        
        for line in lines:
            # Skip UUID headers
            if re.match(r'^# [a-f0-9-]{36}', line):
                continue
            
            # Handle tables
            if '|' in line:
                if not in_table:
                    if table_lines:
                        processed_lines.extend(format_table(table_lines))
                        processed_lines.append('')
                        table_lines = []
                    in_table = True
                table_lines.append(line)
            else:
                if in_table:
                    if table_lines:
                        processed_lines.extend(format_table(table_lines))
                        processed_lines.append('')
                    in_table = False
                    table_lines = []
                if line.strip():
                    processed_lines.append(line)
        
        # Process any remaining table
        if table_lines:
            processed_lines.extend(format_table(table_lines))
            processed_lines.append('')
        
        return '\n'.join(processed_lines)
        
    finally:
        if os.path.exists(temp_docx):
            os.remove(temp_docx)

def convert_docx_to_markdown(input_path: str) -> str:
    """
    Convert DOCX to Markdown with improved table handling.
    """
    try:
        # Get clean filename
        original_filename = os.path.splitext(os.path.basename(input_path))[0]
        clean_filename = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '', original_filename)
        clean_filename = clean_filename.replace('_input', '').strip()
        
        # Convert to markdown
        output = pypandoc.convert_file(
            input_path,
            'markdown',
            format='docx',
            extra_args=[
                '--wrap=none',
                '--markdown-headings=atx',
                '--standalone'
            ]
        )
        
        # Process content
        lines = output.split('\n')
        processed_lines = []
        
        # Add title if no headers found
        if not any(line.strip().startswith('#') for line in lines):
            processed_lines.append(f'# {clean_filename}\n')
        
        in_table = False
        table_lines = []
        
        for line in lines:
            # Skip UUID headers
            if re.match(r'^# [a-f0-9-]{36}', line):
                continue
            
            # Handle tables
            if '|' in line:
                if not in_table:
                    if table_lines:
                        processed_lines.extend(format_table(table_lines))
                        processed_lines.append('')
                        table_lines = []
                    in_table = True
                table_lines.append(line)
            else:
                if in_table:
                    if table_lines:
                        processed_lines.extend(format_table(table_lines))
                        processed_lines.append('')
                    in_table = False
                    table_lines = []
                if line.strip():
                    processed_lines.append(line)
        
        # Process any remaining table
        if table_lines:
            processed_lines.extend(format_table(table_lines))
            processed_lines.append('')
        
        return '\n'.join(processed_lines)
        
    except Exception as e:
        raise ConversionError(f"DOCX conversion failed: {str(e)}")

def convert_excel_to_markdown(input_path: str) -> str:
    """
    Convert Excel to Markdown with enhanced table formatting.
    """
    try:
        excel_file = pd.ExcelFile(input_path)
        sheets = excel_file.sheet_names
        markdown_content = []
        
        for sheet in sheets:
            df = pd.read_excel(input_path, sheet_name=sheet)
            if not df.empty:
                # Add sheet name as header
                markdown_content.append(f'# {sheet}\n')
                
                # Format column headers
                headers = [str(col).strip() for col in df.columns]
                table_lines = ['|' + '|'.join(f' {header} ' for header in headers) + '|']
                
                # Add separator
                table_lines.append('|' + '|'.join(' ' + '-' * 15 + ' ' for _ in headers) + '|')
                
                # Add data rows
                for _, row in df.iterrows():
                    cells = [str(cell).strip() for cell in row]
                    table_lines.append('|' + '|'.join(f' {cell} ' for cell in cells) + '|')
                
                # Format the table
                formatted_table = format_table(table_lines)
                markdown_content.extend(formatted_table)
                markdown_content.append('\n')
        
        return '\n'.join(markdown_content)
        
    except Exception as e:
        raise ConversionError(f"Excel conversion failed: {str(e)}")

def format_table(table_lines):
    """
    Format table with strict markdown table standards.
    """
    if not table_lines:
        return []
    
    # Clean and normalize table lines
    table_lines = [line.strip() for line in table_lines if line.strip()]
    if not table_lines:
        return []
    
    # Get column count from header
    header = table_lines[0]
    header_cells = [cell.strip() for cell in header.split('|')[1:-1]]
    col_count = len(header_cells)
    
    # Format header with consistent spacing
    formatted = []
    formatted.append('|' + '|'.join(f' {cell.center(15)} ' for cell in header_cells) + '|')
    
    # Add separator with proper alignment
    separator = '|' + '|'.join(' ' + '-' * 15 + ' ' for _ in range(col_count)) + '|'
    formatted.append(separator)
    
    # Format data rows
    for line in table_lines[1:]:
        if '-|-' in line or '|-|' in line:
            continue
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        # Ensure correct number of columns
        while len(cells) < col_count:
            cells.append('')
        cells = cells[:col_count]  # Trim extra columns
        formatted.append('|' + '|'.join(f' {cell.ljust(15)} ' for cell in cells) + '|')
    
    return formatted

def clean_up_files(*files: str) -> None:
    """
    Clean up temporary files.
    
    Args:
        *files: Variable number of file paths to clean up
    """
    for file in files:
        try:
            if file and os.path.exists(file):
                os.remove(file)
        except Exception as e:
            logger.error(f"Error cleaning up file {file}: {str(e)}")

def assess_ai_training_quality(markdown_text: str) -> Dict:
    """
    Assess markdown quality specifically for AI training purposes with more accurate scoring.
    Returns a score and detailed feedback about AI training suitability.
    """
    ai_score = 50  # Start at 50 as neutral base score
    ai_feedback: List[str] = []
    
    # Structure Assessment
    if not markdown_text.strip():
        return {'score': 0, 'feedback': ['Empty content not suitable for training']}
    
    # Core structure checks (-/+)
    headers = re.findall(r'^#{1,6}\s.+', markdown_text, re.MULTILINE)
    if not headers:
        ai_score -= 15
        ai_feedback.append("Missing document structure (headers) (-)")
    else:
        ai_score += 15
        ai_feedback.append("Well-structured with headers (+)")
    
    # Content quality checks
    word_count = len(markdown_text.split())
    if word_count < 100:
        ai_score -= 25
        ai_feedback.append("Content too brief for effective training (-)")
    elif word_count < 300:
        ai_score -= 10
        ai_feedback.append("Content length below optimal (-)")
    else:
        ai_score += 15
        ai_feedback.append("Good content length (+)")
    
    # Content richness checks
    if re.search(r'(example|e\.g\.|for instance|such as)', markdown_text, re.IGNORECASE):
        ai_score += 10
        ai_feedback.append("Contains practical examples (+)")
    else:
        ai_score -= 5
        ai_feedback.append("Lacks practical examples (-)")
    
    # Technical content checks
    technical_terms = re.findall(r'\b(algorithm|function|method|api|interface|implementation|framework)\b', 
                               markdown_text, 
                               re.IGNORECASE)
    if len(technical_terms) > 5:
        ai_score += 10
        ai_feedback.append("Good technical depth (+)")
    else:
        ai_score -= 5
        ai_feedback.append("Limited technical depth (-)")
    
    # Special handling for different content types
    has_tables = bool(re.search(r'\|[-|\s]+\|', markdown_text))
    code_blocks = re.findall(r'```[\s\S]*?```', markdown_text)
    
    if has_tables:
        # Excel/Table-specific scoring
        ai_score += 15
        ai_feedback.append("Contains structured data (+)")
        if re.search(r'\d+', markdown_text):
            ai_score += 5
            ai_feedback.append("Includes numerical data (+)")
    elif code_blocks:
        # Code-specific scoring
        ai_score += 15
        ai_feedback.append("Contains code examples (+)")
    else:
        ai_score -= 10
        ai_feedback.append("Lacks structured data or code examples (-)")
    
    # Format and clarity checks
    if re.search(r'^\s*[-*+]\s', markdown_text, re.MULTILINE):
        ai_score += 5
        ai_feedback.append("Contains structured lists (+)")
    
    if re.search(r'(explains|means|refers to|is defined as|in other words)', markdown_text, re.IGNORECASE):
        ai_score += 5
        ai_feedback.append("Contains explanatory content (+)")
    else:
        ai_score -= 5
        ai_feedback.append("Lacks explanatory context (-)")
    
    # Normalize score
    ai_score = max(0, min(100, ai_score))
    
    # Sort feedback to group positives and negatives
    positive_feedback = [f for f in ai_feedback if "(+)" in f]
    negative_feedback = [f for f in ai_feedback if "(-)" in f]
    ai_feedback = negative_feedback + positive_feedback
    
    return {
        'score': ai_score,
        'feedback': ai_feedback
    }

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    """Handle file conversion requests"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Create unique filename
    temp_id = str(uuid.uuid4())
    original_filename = Path(file.filename).stem
    file_ext = Path(file.filename).suffix.lower()
    
    # Set up file paths
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{temp_id}_input{file_ext}")
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{temp_id}_output.md")

    try:
        # Save uploaded file
        file.save(input_path)
        
        # Convert based on file type
        if file_ext == '.pdf':
            output = convert_pdf_to_markdown(input_path, temp_id)
            quality_result = assess_markdown_quality(output, 'pdf')
        elif file_ext in ['.xlsx', '.xls']:
            output = convert_excel_to_markdown(input_path)
            quality_result = assess_markdown_quality(output, 'excel')
        elif file_ext in ['.docx', '.doc']:
            output = convert_docx_to_markdown(input_path)
            quality_result = assess_markdown_quality(output, 'docx')
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

        # Save output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)

        # Prepare response
        quality_result = assess_markdown_quality(output, file_ext)
        ai_result = assess_ai_training_quality(output)
        
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=f"{original_filename}.md",
            mimetype='text/markdown'
        )
        
        # Add both quality and AI scores to headers
        response.headers['X-Quality-Score'] = str(quality_result['score'])
        response.headers['X-Quality-Issues'] = ','.join(quality_result['issues'])
        response.headers['X-AI-Training-Score'] = str(ai_result['score'])
        response.headers['X-AI-Training-Feedback'] = ','.join(ai_result['feedback'])
        
        return response

    except ConversionError as e:
        logger.error(f"Conversion error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    finally:
        # Clean up temporary files
        clean_up_files(input_path, output_path)

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size exceeded error"""
    return jsonify({'error': 'File size exceeds the 16MB limit'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server errors"""
    return jsonify({'error': 'An internal server error occurred'}), 500

# Add this route to debug static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(os.path.join(root_dir, 'static'), filename)

if __name__ == '__main__':
    app.run(debug=True)