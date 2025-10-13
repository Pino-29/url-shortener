document.addEventListener('DOMContentLoaded', function() {
    const urlForm = document.getElementById('url-form');
    const urlInput = document.getElementById('url-input');
    const resultContainer = document.getElementById('result-container');
    const shortUrlInput = document.getElementById('short-url');
    const copyBtn = document.getElementById('copy-btn');
    const messageDiv = document.getElementById('message');

    urlForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const url = urlInput.value.trim();
        if (!url) {
            showMessage('Please enter a valid URL', 'error');
            return;
        }

        try {
            const response = await fetch('/v1/urls/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url }),
            });

            const data = await response.json();

            if (response.ok) {
                // Success
                shortUrlInput.value = data.short_url;
                resultContainer.classList.add('show');
                showMessage('URL shortened successfully!', 'success');
            } else {
                // Error from API
                showMessage(data.error || 'Failed to shorten URL', 'error');
            }
        } catch (error) {
            // Network or other error
            showMessage('An error occurred. Please try again.', 'error');
            console.error('Error:', error);
        }
    });

    copyBtn.addEventListener('click', function() {
        shortUrlInput.select();
        document.execCommand('copy');
        showMessage('Copied to clipboard!', 'success');
    });

    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type} show`;
        
        // Hide message after 3 seconds
        setTimeout(() => {
            messageDiv.classList.remove('show');
        }, 3000);
    }
});