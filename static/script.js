document.addEventListener('DOMContentLoaded', function() {
    // Add visual feedback when pasting Spotify URL
    const playlistUrlInput = document.getElementById('playlist_url');
    if (playlistUrlInput) {
        // Check if input has value when page loads (e.g. after error)
        if (playlistUrlInput.value.trim() !== '') {
            playlistUrlInput.classList.add('has-value');
        }
          // Add validation for Spotify URLs
        playlistUrlInput.addEventListener('input', function() {
            const value = this.value.trim();
            if (value !== '') {
                this.classList.add('has-value');
                // Validation for Spotify playlist or album URL format
                if (value.includes('open.spotify.com/playlist/') || value.includes('open.spotify.com/album/')) {
                    this.classList.remove('invalid');
                    this.classList.add('valid');
                } else {
                    this.classList.remove('valid');
                    this.classList.add('invalid');
                }
            } else {
                this.classList.remove('has-value');
                this.classList.remove('valid');
                this.classList.remove('invalid');
            }
        });
    }
    
    // Add loading state to form submission
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('.submit-btn');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = 'Generating... <span class="spinner"></span>';
                submitButton.classList.add('loading');
            }
              // Create a loading overlay
            const loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <p>Analyzing music and generating cover art...</p>
                    <p class="loading-subtext">This may take a minute or two</p>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
            
            // Allow form submission to continue
            return true;
        });
    }
    
    // On result page, add animation for cover reveal
    const albumCover = document.querySelector('.album-cover');
    if (albumCover) {
        // Add fade-in animation when image loads
        albumCover.style.opacity = '0';
        albumCover.addEventListener('load', function() {
            setTimeout(() => {
                albumCover.style.transition = 'opacity 1s ease-in-out';
                albumCover.style.opacity = '1';
            }, 300);
        });
    }
    
    // Handle LoRA tabs
    const tabButtons = document.querySelectorAll('.lora-tab-btn');
    const tabContents = document.querySelectorAll('.lora-tab-content');
    
    if (tabButtons.length && tabContents.length) {
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons and contents
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Show corresponding content
                const tabName = this.getAttribute('data-tab');
                document.getElementById(`lora-${tabName}-tab`).classList.add('active');
            });
        });
    }
    
    // LoRA file upload handling
    const loraUploadForm = document.getElementById('lora-upload-form');
    if (loraUploadForm) {
        loraUploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const uploadStatus = document.getElementById('upload-status');
            
            // Validate file
            const fileInput = document.getElementById('lora_file');
            if (!fileInput.files.length) {
                uploadStatus.textContent = 'Please select a file to upload';
                uploadStatus.className = 'error';
                return;
            }
            
            const file = fileInput.files[0];
            const validExtensions = ['.safetensors', '.ckpt', '.pt'];
            const fileExt = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
            
            if (!validExtensions.includes(fileExt)) {
                uploadStatus.textContent = 'Invalid file type. Please upload a .safetensors, .ckpt, or .pt file';
                uploadStatus.className = 'error';
                return;
            }
            
            // Create loading state
            uploadStatus.textContent = 'Uploading...';
            uploadStatus.className = '';
            
            // Submit via AJAX
            fetch('/api/upload_lora', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uploadStatus.textContent = data.message;
                    uploadStatus.className = 'success';
                    
                    // Refresh page after a delay to show updated LoRA list
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    uploadStatus.textContent = data.error || 'Upload failed';
                    uploadStatus.className = 'error';
                }
            })
            .catch(error => {
                uploadStatus.textContent = 'Error: ' + error.message;
                uploadStatus.className = 'error';
            });
        });
    }
    
    // LoRA link form
    const loraLinkForm = document.getElementById('lora-link-form');
    if (loraLinkForm) {
        // Strength slider update
        const strengthSlider = document.getElementById('link_strength');
        const strengthOutput = document.getElementById('strength-output');
        
        if (strengthSlider && strengthOutput) {
            strengthSlider.addEventListener('input', function() {
                strengthOutput.textContent = this.value;
            });
        }
        
        // Form submission
        loraLinkForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const uploadStatus = document.getElementById('upload-status');
            const nameInput = document.getElementById('link_name');
            const urlInput = document.getElementById('link_url');
            const strengthInput = document.getElementById('link_strength');
            
            // Validate URL
            if (!urlInput.value.trim()) {
                uploadStatus.textContent = 'Please enter a LoRA URL';
                uploadStatus.className = 'error';
                return;
            }
            
            const url = urlInput.value.trim();
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                uploadStatus.textContent = 'Please enter a valid URL starting with http:// or https://';
                uploadStatus.className = 'error';
                return;
            }
            
            // Create loading state
            uploadStatus.textContent = 'Adding LoRA link...';
            uploadStatus.className = '';
            
            // Prepare data
            const data = {
                name: nameInput.value.trim(),
                url: url,
                strength: parseFloat(strengthInput.value)
            };
            
            // Submit via AJAX
            fetch('/api/add_lora_link', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uploadStatus.textContent = data.message;
                    uploadStatus.className = 'success';
                    
                    // Refresh page after a delay to show updated LoRA list
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    uploadStatus.textContent = data.error || 'Failed to add LoRA link';
                    uploadStatus.className = 'error';
                }
            })
            .catch(error => {
                uploadStatus.textContent = 'Error: ' + error.message;
                uploadStatus.className = 'error';
            });
        });
    }
    
    // Mutual exclusivity between dropdown and URL input
    const loraSelector = document.getElementById('lora_name');
    const loraUrlInput = document.getElementById('lora_url');
    const loraPreviewContainer = document.getElementById('lora-preview-container');
    
    if (loraSelector && loraUrlInput) {
        loraSelector.addEventListener('change', function() {
            if (this.value !== 'none') {
                // When a saved LoRA is selected, clear URL input
                loraUrlInput.value = '';
                
                // Display preview or info about selected LoRA
                if (loraPreviewContainer) {
                    const selectedOption = this.options[this.selectedIndex];
                    const loraName = selectedOption.textContent;
                    loraPreviewContainer.innerHTML = `
                        <p>Selected style: <strong>${loraName}</strong></p>
                        <p class="help-text">This LoRA will influence the visual style of your generated cover</p>
                    `;
                }
            } else if (loraPreviewContainer) {
                loraPreviewContainer.innerHTML = `<p class="no-lora">No LoRA selected</p>`;
            }
        });
        
        loraUrlInput.addEventListener('input', function() {
            if (this.value.trim() !== '') {
                // When URL is entered, reset dropdown to 'none'
                loraSelector.value = 'none';
                
                // Show preview info about URL
                if (loraPreviewContainer) {
                    // Check if URL is from Civitai
                    const url = this.value.trim();
                    if (url.includes('civitai.com/models/')) {
                        loraPreviewContainer.innerHTML = `
                            <p>Using LoRA from Civitai</p>
                            <p class="help-text">This will use the LoRA from the provided Civitai link</p>
                        `;
                    } else if (url.endsWith('.safetensors') || url.endsWith('.ckpt') || url.endsWith('.pt')) {
                        loraPreviewContainer.innerHTML = `
                            <p>Using direct LoRA file URL</p>
                            <p class="help-text">This URL will be used once for this generation</p>
                        `;
                    } else {
                        loraPreviewContainer.innerHTML = `
                            <p>Using custom LoRA URL</p>
                            <p class="help-text">Make sure this URL points to a valid LoRA resource</p>
                        `;
                    }
                }
            }
        });
    }
    
    // Add CSS styles for the newly added elements
    const style = document.createElement('style');
    style.textContent = `
        input.valid {
            border-left: 4px solid #1DB954 !important;
        }
        
        input.invalid {
            border-left: 4px solid #ff5252 !important;
        }
        
        .submit-btn.loading {
            background-color: #168f40;
            pointer-events: none;
        }
        
        .spinner {
            display: inline-block;
            width: 15px;
            height: 15px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
            margin-left: 8px;
            vertical-align: middle;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .loading-content {
            text-align: center;
            padding: 30px;
            background: #1e1e1e;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }
        
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 5px solid rgba(29, 185, 84, 0.3);
            border-radius: 50%;
            border-top-color: #1DB954;
            margin: 0 auto 20px;
            animation: spin 1s ease infinite;
        }
        
        .loading-subtext {
            color: #a0a0a0;
            font-size: 0.9rem;
        }
    `;
    document.head.appendChild(style);
    
    // ----- PRESET BUTTONS FUNCTIONALITY ----- //
    const presetButtons = document.querySelectorAll('.preset-btn');
    const moodInput = document.getElementById('mood');
    
    if (presetButtons.length > 0 && moodInput) {
        presetButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                presetButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Set the mood input value based on preset
                const preset = this.getAttribute('data-preset');
                switch(preset) {
                    case 'minimalist':
                        moodInput.value = 'clean minimalist design with subtle colors';
                        break;
                    case 'high-contrast':
                        moodInput.value = 'bold high contrast design with striking visuals';
                        break;
                    case 'retro':
                        moodInput.value = 'vintage retro aesthetic with analog texture';
                        break;
                    case 'bold-colors':
                        moodInput.value = 'vibrant colorful design with bold typography';
                        break;
                }
            });
        });
    }
    
    // ----- RESULT PAGE FUNCTIONALITIES ----- //
    
    // Copy title button
    const copyTitleButton = document.getElementById('copy-title');
    if (copyTitleButton) {
        copyTitleButton.addEventListener('click', function() {
            const title = document.querySelector('.album-title').textContent.trim();
            
            navigator.clipboard.writeText(title)
                .then(() => {
                    // Show success message
                    this.textContent = 'Title Copied!';
                    
                    // Reset button text after a delay
                    setTimeout(() => {
                        this.textContent = 'Copy Title';
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy title: ', err);
                });
        });
    }
    
    // Copy/Download cover button
    const copyCoverButton = document.getElementById('copy-cover');
    if (copyCoverButton) {
        copyCoverButton.addEventListener('click', function() {
            const imagePath = this.getAttribute('data-image-path');
            const imageUrl = `/generated_covers/${imagePath}`;
            
            // Create a temporary link to download the image
            const a = document.createElement('a');
            a.href = imageUrl;
            a.download = imagePath;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // Show success message
            this.textContent = 'Cover Downloaded!';
            
            // Reset button text after a delay
            setTimeout(() => {
                this.textContent = 'Download Cover';
            }, 2000);
        });
    }
    
    // Regenerate cover button
    const regenerateButton = document.getElementById('regenerate-cover');
    if (regenerateButton) {
        regenerateButton.addEventListener('click', function() {
            const playlistUrl = this.getAttribute('data-playlist-url');
            const mood = this.getAttribute('data-mood') || '';
            const loraName = this.getAttribute('data-lora-name') || '';
            const loraUrl = this.getAttribute('data-lora-url') || '';
            
            // Create a loading overlay
            const loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <p>Regenerating cover with same playlist...</p>
                    <p class="loading-subtext">This may take a minute</p>
                </div>
            `;
            document.body.appendChild(loadingOverlay);
            
            // Make AJAX request to regenerate endpoint
            fetch('/api/regenerate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    playlist_url: playlistUrl,
                    mood: mood,
                    lora_name: loraName,
                    lora_url: loraUrl
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Refresh the page to show new results
                    window.location.reload();
                } else {
                    // Remove loading overlay
                    document.body.removeChild(loadingOverlay);
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                // Remove loading overlay
                document.body.removeChild(loadingOverlay);
                console.error('Error regenerating cover:', error);
                alert('Failed to regenerate cover. Please try again.');
            });
        });
    }
});