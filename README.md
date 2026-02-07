<<<<<<< HEAD
# Airline-Agent
=======
# ✈️ Sunfar Travels & Tours - Elite AI Concierge

The most advanced, professional, and responsive AI travel assistant. Designed for **Sunfar Travels & Tours**, this agent combines elite knowledge accuracy with a world-class, ChatGPT-inspired user experience.

---

## 🌟 The Elite Experience
This is not just a chatbot; it is a **Premium Travel Concierge** built to handle high-stakes travel requirements with perfect discretion and real-time accuracy.

### 🍱 The Specialized Agent Suite:
1.  **️ Knowledge Guard**: Real-time search verification to prevent hallucinations on visa/passport rules.
2.  **🔍 Smart Flight Search**: Live Amadeus API integration for real pricing and availability.
3.  **🎫 VIP Assistance**: Native support for Sunfar's Airport VIP & Tour services.
4.  **🌍 Multilingual Mastery**: Automatic detection and professional response in 15+ languages.
5.  **📱 Perfect Frame**: Fully responsive design optimized for both **iPhone** and **Laptop**.
6.  **🛡️ Professional Guardrails**: Strict scope control to prevent off-topic conversations.
7.  **🧠 Cognitive Contact Routing**: Intuitively routes business inquiries to Sunfar and technical/developer inquiries to the founder.

---

## ⚙️ Workflow Architecture
Our system uses a **multi-stage agentic workflow** to ensure reliability:

1.  **Intent Orchestration**: The brain (GPT-4o) analyzes user sentiment and language.
2.  **Tool Augmentation**: If the query requires live data (Flights, Visas), the agent invokes specialized tools:
    -   `flight_search_tool`: Live Amadeus integration.
    -   `travel_req_agent_tool`: Real-time Tavily search for high-accuracy travel requirements.
3.  **Professional Filter**: Responses are polished to match Sunfar’s premium tone, including mandatory legal caveats for travel rules.

---

## 🎨 Design Philosophy
The UI is inspired by **ChatGPT's minimalist excellence**:
- **Light Mode Evolution**: A clean, pristine white background (`#ffffff`) for professional clarity.
- **Left-Frame Sidebar**: Fixed navigation frame containing official Sunfar contact details and hotlines.
- **Centralized Focus**: An 800px wide chat stream to keep interaction productive and distraction-free.
- **Responsive Fluidity**: Using advanced CSS Grid and Media Queries to provide a "Native App" feel on mobile devices.

---

## � User Manual

### 1. Prerequisites
- Python 3.9+
- OpenAI API Key
- (Optional) Amadeus & Tavily API Keys for live search.

### 2. Quick Installation
```bash
# Clone the repository and enter the directory
cd airline-agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup your environment variables in .env
# (Use .env.example as a template)
```

### 3. Running the Agent
There are two ways to interact with the concierge:

#### **Choice A: Premium Web Interface (Recommended)**
Perfect for a full-screen, branded experience on laptop or mobile.
```bash
python server.py
```
Visit: `http://localhost:8000`

#### **Choice B: High-Performance CLI**
Ideal for testing or quick text-only interactions.
```bash
python cli_bot.py
```

### 4. Usage Tips
- **Voice Input**: Click the 🎤 icon in the web UI to talk to the agent.
- **Document Upload**: Use the 📎 icon to simulate passport/ticket processing.
- **Mobile Access**: Resize your browser or open on your phone to see the sliding **Hamburger Menu**.

---

## � Corporate Contact
- **Hotline**: 01-8243993
- **Email**: info@sunfar38.com
- **Yangon Office**: No. 29/31, 38th Street, Kyauktada Township, Yangon, Myanmar.

---
## 👨‍💻 Technical Support & Inquiries
For technical support, custom AI integrations, or project inquiries, please contact the developer:

- **Founder**: **MR. KYAW ZIN TUN**
- **Phone/WhatsApp**: [+95949567820](tel:0949567820)
- **Viber**: [+9595043252](viber://chat?number=9595043252)
- **Line**: [0949567820](https://line.me/ti/p/~0949567820)

**Powered by [itsolutions.mm](tel:0949567820)**
*Pushing the boundaries of Agentic AI Excellence.* ✈️✨🛡️
>>>>>>> 7926c42 (Initial production commit: Sunfar Elite AI Concierge v6)
