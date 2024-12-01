document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.querySelector('.drop-zone');
    const fileInput = document.querySelector('.drop-zone__input');
    const form = document.getElementById('uploadForm');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when file is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    // Handle clicked files
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        updateThumbnail(fileInput.files[0]);
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        updateProgress(0, 'Starting conversion...');
        
        try {
            // Show progress before fetch
            updateProgress(30, 'Processing file...');
            
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });
            
            updateProgress(60, 'Converting format...');
            
            const data = await response.json();
            console.log('Server Response:', data); // Debug log
            
            updateProgress(90, 'Finalizing...');
            
            if (response.ok) {
                document.querySelector('.preview-content').textContent = data.markdown;
                document.querySelector('.preview-container').style.display = 'block';
                updateScores(data);
                updateProgress(100, 'Conversion complete!');
            } else {
                alert(data.error || 'An error occurred');
                updateProgress(100, 'Error occurred');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while converting the file');
            updateProgress(100, 'Error occurred');
        }
    });

    // Handle download button
    document.querySelector('.download-btn').addEventListener('click', async () => {
        const markdown = document.querySelector('.preview-content').textContent;
        await downloadMarkdown(markdown);
        
        // Reset UI after download
        document.querySelector('.preview-container').style.display = 'none';
        document.querySelector('.preview-content').textContent = '';
        document.querySelector('.quality-score').textContent = '';
        document.querySelector('.quality-issues').textContent = '';
        document.querySelector('.ai-training-score').textContent = '';
        document.querySelector('.ai-feedback').textContent = '';
        document.querySelector('.drop-zone__prompt').textContent = 'Drag and drop file or click to upload';
    });
});

function preventDefaults (e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    document.querySelector('.drop-zone').classList.add('drop-zone--over');
}

function unhighlight(e) {
    document.querySelector('.drop-zone').classList.remove('drop-zone--over');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    updateThumbnail(files[0]);
}

function updateThumbnail(file) {
    document.querySelector('.drop-zone__prompt').textContent = file.name;
}

function updateScores(data) {
    // Update quality score with fallback
    const qualityScore = data.quality_score || '0%';
    document.querySelector('.quality-score').textContent = 
        `Conversion Quality: ${qualityScore}`;
    
    // Update AI score with fallback
    const aiScore = data.ai_score || '0%';
    document.querySelector('.ai-training-score').textContent = 
        `AI Training Score: ${aiScore}`;
    
    // Update feedback messages with fallbacks
    document.querySelector('.quality-issues').textContent = 
        data.quality_issues || 'No quality issues found';
    document.querySelector('.ai-feedback').textContent = 
        data.ai_feedback || 'No AI training feedback available';
}

function downloadMarkdown(markdown) {
    // Create a temporary invisible element
    const a = document.createElement('a');
    const blob = new Blob([markdown], { type: 'text/markdown' });
    
    // Use showSaveFilePicker API if supported
    if (window.showSaveFilePicker) {
        (async () => {
            try {
                const handle = await window.showSaveFilePicker({
                    suggestedName: 'converted.md',
                    types: [{
                        description: 'Markdown file',
                        accept: {
                            'text/markdown': ['.md']
                        }
                    }]
                });
                
                const writable = await handle.createWritable();
                await writable.write(markdown);
                await writable.close();
            } catch (err) {
                if (err.name !== 'AbortError') {
                    console.error('Failed to save file:', err);
                    // Fallback to traditional download
                    fallbackDownload(a, blob);
                }
            }
        })();
    } else {
        // Fallback for browsers that don't support showSaveFilePicker
        fallbackDownload(a, blob);
    }
}

function fallbackDownload(a, blob) {
    const url = window.URL.createObjectURL(blob);
    a.href = url;
    a.download = 'converted.md';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

function updateProgress(percent, message = '') {
    const progressContainer = document.querySelector('.progress-bar-container');
    const progressBar = document.querySelector('.progress-bar__fill');
    const progressText = document.querySelector('.progress-bar__text');
    
    progressContainer.style.display = 'block';
    progressBar.style.width = `${percent}%`;
    progressText.textContent = message || `${percent}% complete`;
    
    if (percent >= 100) {
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
        }, 1000);
    }
}