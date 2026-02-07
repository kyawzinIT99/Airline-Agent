// --- Core Chat Logic ---
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const voiceBtn = document.getElementById('voice-btn');
const uploadBtn = document.getElementById('upload-btn');
const insightsContent = document.getElementById('insights-content');

let chatHistory = [];

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    appendMessage('user', text);
    userInput.value = '';
    const typingId = showTyping();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: chatHistory })
        });
        const data = await response.json();
        removeTyping(typingId);

        if (data.status === 'success') {
            await appendMessage('system', data.response);
            chatHistory.push({ role: 'user', content: text });
            chatHistory.push({ role: 'assistant', content: data.response });
            updateInsights(data.response);
        } else {
            await appendMessage('system', '⚠️ Pardon me, I encountered a technical difficulty.');
        }
    } catch (error) {
        removeTyping(typingId);
        await appendMessage('system', '⚠️ Connection lost. Ensure the backend is running.');
    }
}

async function appendMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    if (role === 'system') msgDiv.classList.add('typing');

    const avatar = role === 'user' ? '👤' : '✨';
    msgDiv.innerHTML = `
        <div class="message-wrapper">
            <div class="avatar">${avatar}</div>
            <div class="bubble"></div>
        </div>
    `;

    const bubble = msgDiv.querySelector('.bubble');
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if (role === 'system') {
        await typeWriter(bubble, content);
        msgDiv.classList.remove('typing');
    } else {
        bubble.textContent = content;
    }
}

async function typeWriter(element, text) {
    const speed = 15; // ms per character
    let i = 0;

    // We iterate through the string, but handle emojis correctly (which can be surrogate pairs)
    const chars = Array.from(text);

    for (const char of chars) {
        element.textContent += char;
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Dynamic speed: slower for punctuation
        let currentSpeed = speed;
        if (['.', '!', '?', '\n'].includes(char)) currentSpeed = speed * 4;

        await new Promise(r => setTimeout(r, currentSpeed));
    }
}

function showTyping() {
    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message system typing';
    typingDiv.id = id;
    typingDiv.innerHTML = `
        <div class="message-wrapper">
            <div class="avatar">✨</div>
            <div class="bubble">Thinking...</div>
        </div>
    `;
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return id;
}

const chatbot = {
    name: "Airline Elite",
    status: "Active",
    welcomeMessage: "✨ Welcome to Airline Elite. I am your premium AI concierge. How may I elevate your travel experience today?",
    userGreeting: "✨ **Elite Concierge Active**. Welcome back, John."
};

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function updateInsights(response) {
    const insightsContent = document.getElementById('insights-content');
    if (!insightsContent) return; // Exit if element doesn't exist

    if (response.includes('flight') || response.includes('✈️') || response.includes('AB123')) {
        insightsContent.innerHTML = `<div class="insight-item">✨ Flight detected. Updating live tracker...</div>`;
        updateMap('AB123');
        updateDashboard('AB123', 'Gate B5');
    }
}

function updateMap(flightId) {
    const plane = document.querySelector('.plane-icon');
    const route = document.querySelector('.route-line');

    if (plane) {
        plane.style.left = '70%';
        plane.style.top = '30%';
    }
    if (route) {
        route.style.width = '60%';
    }
}

function updateDashboard(flight, gate) {
    const flightEl = document.getElementById('next-flight-val');
    const gateEl = document.getElementById('gate-val');
    if (flightEl) flightEl.innerText = flight;
    if (gateEl) {
        gateEl.innerText = gate;
        gateEl.style.color = 'var(--accent)';
    }
}

// --- Advanced Interactions (Voice) ---
const recognition = window.SpeechRecognition || window.webkitSpeechRecognition ? new (window.SpeechRecognition || window.webkitSpeechRecognition)() : null;

if (recognition) {
    recognition.onstart = () => {
        voiceBtn.classList.add('active');
        userInput.placeholder = "Listening...";
    };
    recognition.onresult = (e) => {
        userInput.value = e.results[0][0].transcript;
        sendMessage();
    };
    recognition.onend = () => {
        voiceBtn.classList.remove('active');
        userInput.placeholder = "Search flights, check baggage...";
    };
    voiceBtn.addEventListener('click', () => recognition.start());
}

// --- Advanced Interactions (File Upload) ---
const fileInput = document.createElement('input');
fileInput.type = 'file';
fileInput.accept = 'image/*';
fileInput.style.display = 'none';
document.body.appendChild(fileInput);

uploadBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    appendMessage('user', `Uploaded document: ${file.name}`);
    const typingId = showTyping();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const data = await response.json();
        removeTyping(typingId);

        if (data.status === 'success') {
            await appendMessage('system', `✨ **${data.message}**\n\n- Name: ${data.extracted_data.name}\n- Passport: ${data.extracted_data.passport_number}`);
        }
    } catch (error) {
        removeTyping(typingId);
        await appendMessage('system', '⚠️ Failed to process document.');
    }
});

// --- Proactive Notifications (WebSocket) ---
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const socket = new WebSocket(`${wsProtocol}//${window.location.host}/notifications`);

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'alert') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `message system alert ${data.severity || 'info'}`;
        alertDiv.innerHTML = `<div class="bubble">🔔 **Notice**: ${data.message}</div>`;
        chatContainer.appendChild(alertDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Update dashboard if gate info present
        if (data.message.includes('Gate')) {
            const gateMatch = data.message.match(/Gate ([A-Z][0-9]+)/);
            if (gateMatch) updateDashboard('AB123', gateMatch[1]);
        }
    }
};

socket.onclose = () => console.log("Notification stream closed.");

// --- Initialization ---
window.onload = async () => {
    userInput.focus();
    loadConfig();
    // Messages are pre-rendered in index.html for "delightful" instant feedback
};

// --- Dynamic Config Loader ---
async function loadConfig() {
    try {
        const response = await fetch('config.json');
        const cfg = await response.json();

        // Update Sidebar via IDs
        document.getElementById('cfg-hotline').textContent = cfg.company.hotline;
        document.getElementById('cfg-email').textContent = cfg.company.email;
        document.getElementById('cfg-address').textContent = cfg.company.address;

        const hoursContainer = document.getElementById('cfg-hours');
        hoursContainer.innerHTML = `
            <p>MON - FRI: ${cfg.company.hours.weekday}</p>
            <p>WEEKENDS: ${cfg.company.hours.weekend}</p>
        `;

        const productsList = document.getElementById('cfg-products');
        productsList.innerHTML = cfg.company.products.map(p => `<li>${p}</li>`).join('');

        const poweredBy = document.querySelector('.powered-by');
        poweredBy.innerHTML = `
            <p>Powered by <a href="tel:${cfg.branding.powered_by_phone}">${cfg.branding.powered_by}</a></p>
            <span>(${cfg.branding.powered_by_phone})</span>
        `;
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Mobile Menu Toggle
const menuToggle = document.getElementById('menu-toggle');
const sidePanel = document.querySelector('.side-panel');

if (menuToggle) {
    menuToggle.addEventListener('click', () => {
        sidePanel.classList.toggle('active');
    });
}

// Close sidebar when clicking on chat area (mobile)
chatContainer.addEventListener('click', () => {
    if (window.innerWidth <= 768) {
        sidePanel.classList.remove('active');
    }
});

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
