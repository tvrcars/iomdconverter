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
        
        try {
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            console.log('Server Response:', data); // Debug log
            
            if (response.ok) {
                document.querySelector('.preview-content').textContent = data.markdown;
                document.querySelector('.preview-container').style.display = 'block';
                updateScores(data);
            } else {
                alert(data.error || 'An error occurred');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while converting the file');
        }
    });

    // Handle download button
    document.querySelector('.download-btn').addEventListener('click', () => {
        const markdown = document.querySelector('.preview-content').textContent;
        downloadMarkdown(markdown);
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
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'converted.md';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}