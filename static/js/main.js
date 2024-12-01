document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.querySelector('.drop-zone');
    const fileInput = document.querySelector('.drop-zone__input');
    const form = document.getElementById('uploadForm');
    let convertedBlob = null;
    const previewContainer = document.querySelector('.preview-container');
    const previewContent = document.querySelector('.preview-content');
    const downloadBtn = document.querySelector('.download-btn');
    const progressBarContainer = document.querySelector('.progress-bar-container');
    const progressBarFill = document.querySelector('.progress-bar__fill');
    const progressBarText = document.querySelector('.progress-bar__text');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    // Handle clicked files
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleChange);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropZone.classList.add('drop-zone--over');
    }

    function unhighlight(e) {
        dropZone.classList.remove('drop-zone--over');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        handleFiles(files);
    }

    function handleChange(e) {
        const files = e.target.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length) {
            const file = files[0];
            updateDropZoneText(file);
        }
    }

    function updateDropZoneText(file) {
        const prompt = dropZone.querySelector('.drop-zone__prompt');
        prompt.textContent = file.name;
    }

    function showProgress() {
        progressBarContainer.style.display = 'block';
        let width = 0;
        return setInterval(() => {
            if (width >= 90) return;
            width += 5;
            progressBarFill.style.width = width + '%';
            progressBarText.textContent = 'Converting...';
        }, 500);
    }

    function hideProgress() {
        progressBarContainer.style.display = 'none';
        progressBarFill.style.width = '0%';
        progressBarText.textContent = '';
    }

    function resetUI() {
        // Reset file input and drop zone text
        fileInput.value = '';
        const prompt = dropZone.querySelector('.drop-zone__prompt');
        prompt.textContent = 'Drop file here or click to upload';
        
        // Hide preview container
        previewContainer.style.display = 'none';
        previewContent.textContent = '';
        
        // Reset quality info to default state
        document.querySelector('.quality-score').textContent = 'Conversion Quality: --';
        document.querySelector('.quality-issues').textContent = '';
        
        // Reset AI training info to default state
        document.querySelector('.ai-training-score').textContent = 'AI Training Score: --';
        document.querySelector('.ai-feedback').textContent = '';
        
        // Reset blob
        convertedBlob = null;
        progressBarContainer.style.display = 'none';
        progressBarFill.style.width = '0%';
    }

    async function handleSubmit(e) {
        e.preventDefault();
        
        if (!fileInput.files.length) {
            alert('Please select a file first');
            return;
        }

        const formData = new FormData(form);
        const progressInterval = showProgress();
        
        try {
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                // Check if the error response is JSON
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Conversion failed');
                }
                throw new Error('Conversion failed');
            }

            // Get both quality and AI training scores
            const qualityScore = response.headers.get('X-Quality-Score');
            const qualityIssues = response.headers.get('X-Quality-Issues');
            const aiScore = response.headers.get('X-AI-Training-Score');
            const aiFeedback = response.headers.get('X-AI-Training-Feedback');

            // Update quality information display
            document.querySelector('.quality-score').textContent = 
                `Conversion Quality: ${qualityScore}%`;
            
            // Update AI training score display
            document.querySelector('.ai-training-score').textContent = 
                `AI Training Score: ${aiScore}%`;
            
            const issuesElement = document.querySelector('.quality-issues');
            const aiFeedbackElement = document.querySelector('.ai-feedback');
            
            if (qualityIssues && qualityIssues !== '') {
                issuesElement.textContent = `Quality Issues: ${qualityIssues.split(',').join(', ')}`;
            } else {
                issuesElement.textContent = 'No quality issues found';
            }
            
            if (aiFeedback && aiFeedback !== '') {
                aiFeedbackElement.textContent = `AI Training Feedback: ${aiFeedback.split(',').join(', ')}`;
            } else {
                aiFeedbackElement.textContent = 'No AI training feedback available';
            }

            // Store the blob and show preview
            convertedBlob = await response.blob();
            const text = await convertedBlob.text();
            previewContent.textContent = text;
            previewContainer.style.display = 'block';

        } catch (error) {
            alert(error.message);
        } finally {
            clearInterval(progressInterval);
            hideProgress();
        }
    }

    downloadBtn.addEventListener('click', async () => {
        if (convertedBlob) {
            try {
                // Create a download link
                const url = window.URL.createObjectURL(convertedBlob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                
                // Get the original filename from the input
                const originalFilename = fileInput.files[0].name;
                const markdownFilename = originalFilename.split('.')[0] + '.md';
                a.download = markdownFilename;
                
                // Trigger download
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                
                // Reset UI after successful save
                resetUI();
            } catch (err) {
                if (err.name !== 'AbortError') {
                    console.error('Failed to save file:', err);
                    alert('Failed to save file: ' + err.message);
                }
            }
        }
    });

    // Add form submit handler
    form.addEventListener('submit', handleSubmit);

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
});