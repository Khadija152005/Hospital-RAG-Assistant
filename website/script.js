document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const questionInput = document.getElementById('question');
    const assetIdInput = document.getElementById('asset-id');
    const chatHistory = document.getElementById('chat-history');
    const sendBtn = document.getElementById('send-btn');

    // Safe markdown options
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) return;

        const assetId = assetIdInput.value.trim();

        // 1. Add user message
        appendUserMessage(question);
        questionInput.value = '';
        
        // 2. Show loading
        const loadingId = appendLoadingIndicator();
        sendBtn.disabled = true;

        try {
            // 3. API request to the central backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    asset_id: assetId ? assetId : null
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server returned ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            
            removeElement(loadingId);
            appendAssistantMessage(data.answer, data.sources);

        } catch (error) {
            removeElement(loadingId);
            appendAssistantMessage(`**Error:** ${error.message}\nCheck if the backend is running properly.`, []);
        } finally {
            sendBtn.disabled = false;
            questionInput.focus();
        }
    });

    function appendUserMessage(text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message user-message';
        
        msgDiv.innerHTML = `
            <div class="message-avatar">
                <img src="https://ui-avatars.com/api/?name=Biomedical+Engineer&background=cbd5e1&color=475569" alt="User Profile" style="width:100%; border-radius:50%;">
            </div>
            <div class="message-content">
                <p>${escapeHTML(text)}</p>
            </div>
        `;
        
        chatHistory.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendAssistantMessage(markdownText, sources) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant-message';
        
        let sourcesHTML = '';
        if (sources && sources.length > 0) {
            sourcesHTML = `<div class="sources-container">
                <h4>Sources Cited</h4>`;
            
            sources.forEach(src => {
                sourcesHTML += `
                <div class="source-card">
                    <div class="source-card-header">
                        <span class="source-manual"><i class="fa-solid fa-file-pdf"></i> ${escapeHTML(src.manual)}</span>
                        <span class="source-page">Pg ${escapeHTML(String(src.page))}</span>
                    </div>
                    <div class="source-preview">"${escapeHTML(src.preview)}"</div>
                </div>`;
            });
            sourcesHTML += `</div>`;
        }

        const parsedContent = marked.parse(markdownText);

        msgDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="message-content">
                ${parsedContent}
                ${sourcesHTML}
            </div>
        `;
        
        chatHistory.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendLoadingIndicator() {
        const id = 'loading-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant-message';
        msgDiv.id = id;
        
        msgDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="message-content" style="padding: 0.8rem 1.25rem;">
                <div class="typing-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        `;
        
        chatHistory.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, tag => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
        }[tag] || tag));
    }

    // --- Settings & Dark Mode Logic ---
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettings = document.getElementById('close-settings');
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const llmApiKey = document.getElementById('llm-api-key');
    const saveSettingsBtn = document.getElementById('save-settings-btn');

    // Load saved preferences
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-theme');
        darkModeToggle.checked = true;
    }

    settingsBtn.addEventListener('click', (e) => {
        e.preventDefault();
        settingsModal.classList.remove('hidden');
    });

    closeSettings.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
    });

    darkModeToggle.addEventListener('change', (e) => {
        if (e.target.checked) {
            document.body.classList.add('dark-theme');
            localStorage.setItem('darkMode', 'true');
        } else {
            document.body.classList.remove('dark-theme');
            localStorage.setItem('darkMode', 'false');
        }
    });

    saveSettingsBtn.addEventListener('click', async () => {
        const apiKey = llmApiKey.value.trim();
        if (!apiKey) {
            settingsModal.classList.add('hidden');
            return;
        }

        const originalText = saveSettingsBtn.textContent;
        saveSettingsBtn.textContent = 'Saving...';
        saveSettingsBtn.disabled = true;

        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ groq_api_key: apiKey })
            });

            if (!response.ok) throw new Error('Failed to update settings');
            
            // clear input for security and close
            llmApiKey.value = '';
            settingsModal.classList.add('hidden');
            alert("API Key updated successfully!");
        } catch (error) {
            alert(error.message);
        } finally {
            saveSettingsBtn.textContent = originalText;
            saveSettingsBtn.disabled = false;
        }
    });
});
