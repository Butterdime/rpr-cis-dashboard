// Basic JavaScript for RPR CIS Dashboard

document.addEventListener('DOMContentLoaded', function() {
    // File upload validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            const maxSize = 16 * 1024 * 1024; // 16MB
            
            for (let file of files) {
                if (file.size > maxSize) {
                    alert(`File ${file.name} is too large. Maximum size is 16MB.`);
                    e.target.value = '';
                    return;
                }
            }
            
            // Show selected files
            if (files.length > 0) {
                const fileList = files.map(f => f.name).join(', ');
                console.log('Selected files:', fileList);
            }
        });
    });
    
    // Form validation
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            
            for (let field of requiredFields) {
                if (!field.value.trim()) {
                    alert('Please fill in all required fields.');
                    e.preventDefault();
                    field.focus();
                    return;
                }
            }
        });
    });
    
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });
});