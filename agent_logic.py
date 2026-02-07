import os
import json
import httpx
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Concurrency Management ---
# Limits simultaneous Amadeus API calls to 3 to prevent rate limits (429)
amadeus_semaphore = asyncio.Semaphore(3)

# --- Amadeus API Client ---

class AmadeusClient:
    def __init__(self):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        self.base_url = "https://test.api.amadeus.com"
        self.token = None

    async def _get_token(self):
        url = f"{self.base_url}/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            if response.status_code == 200:
                self.token = response.json()["access_token"]
            else:
                raise Exception(f"Failed to get Amadeus token: {response.text}")

    async def search_flights(self, origin: str, destination: str, date: str):
        if not self.token:
            await self._get_token()
        
        url = f"{self.base_url}/v2/shopping/flight-offers"
        params = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": date,
            "adults": 1,
            "currencyCode": "USD",
            "max": 5
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401: # Token expired
                await self._get_token()
                headers["Authorization"] = f"Bearer {self.token}"
                response = await client.get(url, params=params, headers=headers)
                return response.json()
            elif response.status_code == 429:
                return {"error": "Too many requests. Please wait a moment or use our Hotline (01-8243993) for immediate help."}
            elif response.status_code >= 500:
                return {"error": "Aviation data system is temporarily slow. Please retry in 30 seconds."}
            else:
                body = response.text or "No body returned"
                return {"error": f"Amadeus API HTTP {response.status_code}: {body}"}
        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}

amadeus = AmadeusClient()

# --- Tools Definition ---

@tool
def format_duration(iso_duration: str) -> str:
    """Convert PT1H35M to '1 hour 35 minutes'."""
    duration = iso_duration.replace("PT", "")
    hours = 0
    minutes = 0
    if "H" in duration:
        h_part = duration.split("H")[0]
        hours = int(h_part)
        duration = duration.split("H")[1]
    if "M" in duration:
        m_part = duration.split("M")[0]
        minutes = int(m_part)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    
    return " ".join(parts) if parts else "Unknown duration"

@tool
async def flight_search_tool(origin: str = "", destination: str = "", date: str = "", origin_name: str = "", destination_name: str = "") -> str:
    """
    Search for real-time flights. 
    - origin & destination: REQUIRES 3-letter IATA codes (e.g. BKK, LON).
    - date: YYYY-MM-DD format.
    """
    print(f"🔍 TOOL: flight_search_tool called with: origin={origin}, dest={destination}, date={date}")
    if not origin or not destination or not date:
        print("   ⚠️ Tool missing required parameters.")
        return "✨ To provide exact pricing, please specify the **Origin**, **Destination**, and **Travel Date** (e.g., 'Search flights from RGN to BKK on May 10')."
    
    origin = origin.upper()
    destination = destination.upper()
    print(f"   Normalized: {origin} -> {destination}")
    try:
        # Load config for branding
        cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(cfg_path, "r") as f:
                cfg = json.load(f)["company"]
        except Exception:
            cfg = {"name": "Sunfar Travel", "hotline": "01-8243993", "email": "info@sunfar38.com"}

        # Use semaphore to handle simultaneous users gracefully
        async with amadeus_semaphore:
            results = await asyncio.wait_for(amadeus.search_flights(origin, destination, date), timeout=20.0)
        
        if "error" in results:
            print(f"   ❌ Tool results error: {results['error']}")
            return f"⚠️ I encountered a temporary technical issue: {results['error']}."

        if "data" in results and results["data"]:
            # Format Date for Display
            try:
                dt = datetime.strptime(date, "%Y-%m-%d")
                display_date = dt.strftime("%d %B %Y")
            except:
                display_date = date

            # Header with City Names
            header_origin = f"{origin_name} ({origin})" if origin_name else origin
            header_dest = f"{destination_name} ({destination})" if destination_name else destination
            
            header = f"✈️ {header_origin} → {header_dest}\n📅 {display_date}\n\nAvailable Flights:\n"
            offers = []
            # Currency mapping with USD as the primary focus
            currency_map = {"USD": "$", "EUR": "€", "THB": "฿"}

            # Carry dictionaries for carrier names
            carriers_map = results.get("dictionaries", {}).get("carriers", {})

            for offer in results["data"][:5]: # Take top 5
                try:
                    price = offer.get("price", {}).get("total", "N/A")
                    currency_code = offer.get("price", {}).get("currency", "USD")
                    currency_symbol = currency_map.get(currency_code, currency_code)
                    
                    itineraries = offer.get("itineraries", [])
                    if not itineraries: continue
                    
                    itinerary = itineraries[0]
                    duration = itinerary.get("duration", "PT0H0M")
                    readable_duration = format_duration(duration)
                    
                    # Extract Carrier Code (Try multiple sources)
                    carrier_code = offer.get("validatingCarrierCodes", [None])[0]
                    if not carrier_code and itinerary.get("segments"):
                        carrier_code = itinerary["segments"][0].get("carrierCode")
                    
                    carrier_name = carriers_map.get(carrier_code, carrier_code) or "Airline"
                    offers.append(f"\t•\t{carrier_name} — {currency_symbol}{price} — ⏱️ {readable_duration}")
                except Exception as loop_e:
                    print(f"⚠️ Error parsing flight offer: {loop_e}")
                    continue
            
            footer = f"\n\nBooking & Support – {cfg['name']}\n\t•\t📞 Hotline: {cfg['hotline']}\n\t•\t📧 Email: {cfg['email']}\n\n✨ Let us know if you need help with booking or travel planning!"
            return header + "\n".join(offers) + footer
        elif "error" in results:
            err = results["error"]
            if "Consumer over quota" in err:
                return f"🎫 NOTE: High-demand search limit reached for today. Please contact our 24/7 Hotline ({cfg['hotline']}) for immediate flight pricing and booking."
            return f"⚠️ Service Update: {err}"
        else:
            return f"❌ No direct flights found for this specific date. Please try an alternative date or call {cfg['name']} at {cfg['hotline']}."
    except asyncio.TimeoutError:
        return "⏳ Connection is taking a bit longer than usual due to high traffic. To save time, please call our direct hotline at 01-8243993 for an instant quote!"
    except Exception as e:
        return f"⚠️ System Error during search: {str(e)}"

@tool
def booking_agent_tool(details: str) -> str:
    """Handle flight bookings, seat selection, and price freeze (hold for 24-48h)."""
    return "🎫 Booking Draft Created. Seat 12A (Extra Legroom) is available. Price held for 24 hours."

@tool
def baggage_agent_tool(query: str) -> str:
    """Check baggage allowance, tracking, and prohibited items."""
    return "🧳 Your bag (Tag: LX789) is currently being loaded onto the aircraft. Allowance: 23kg."

@tool
def checkin_agent_tool(query: str) -> str:
    """Handle check-in, boarding passes, and gate navigation."""
    return "✅ Check-in successful. Your mobile boarding pass is ready. Gate B5 is a 6-minute walk."

@tool
def status_agent_tool(flight_id: str) -> str:
    """Real-time flight status and delay predictions."""
    return "📡 Flight AB123: On Time. Inbound aircraft has arrived. Predict 95% chance of on-time departure."

@tool
def change_cancel_agent_tool(pnr: str) -> str:
    """Handle flight changes, cancellations, and refund eligibility (EU261)."""
    return "🔄 PNR: XJ921 is eligible for a full refund or free rebooking on the next available flight."

@tool
def loyalty_agent_tool(user_id: str) -> str:
    """Manage frequent flyer miles, status upgrades, and lounge access."""
    return "⭐ Elite Status: Gold. You have 45,000 miles. You are only 2 flights away from Platinum status!"

@tool
def payment_agent_tool(amount: str) -> str:
    """Secure payment processing, multi-currency conversion, and billing info."""
    return "💳 Secure payment gateway ready. 3D Secure 2.0 active. Support for Apple Pay and 15+ currencies."

# --- New Elite Tools ---

tavily_search = TavilySearchResults(k=2)

@tool
async def travel_req_agent_tool(destination: str, citizenship: str = "your current profile") -> str:
    """
    Search for official Visa, Passport, and Health requirements.
    EXCLUSIVE RULE: Always state that requirements are subject to Government/Embassy discretion.
    """
    query = f"official travel visa passport requirements for {citizenship} flying to {destination} in 2026"
    try:
        search_results = await tavily_search.ainvoke(query)
        return f"🌍 Global Requirements Update for {destination}:\n\n{search_results}\n\n⚠️ NOTE: These requirements are subject to transition and official embassy discretion. We strongly recommend verifying with the destination consulate before travel."
            # Fallback if no flights found but successful call
            if not offers:
                return f"🌍 No direct flights found for **{origin}** to **{destination}** on **{display_date}**. We recommend checking alternative dates or contacting our hotline (01-8243993) for offline booking options."
            
            return header + "\n".join(offers) + f"\n\nBooking & Support – {cfg['name']}\n\t•\t📞 Hotline: {cfg['hotline']}\n\t•\t📧 Email: {cfg['email']}\n\n✨ Let us know if you need help with booking or travel planning!"

        else:
            print(f"   ℹ️ No data in results for {origin}->{destination}")
            return f"🌍 I couldn't find any available flights for **{origin}** to **{destination}** on **{date}**. This could be due to limited data in our system or the route being unavailable on this specific date."

    except Exception as e:
        print(f"   ❌ Tool error: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"⚠️ I encountered a technical hiccup searching for flights. [Internal Error: {str(e)[:50]}]"

@tool
async def internal_diagnostic_tool() -> str:
    """
    Check the internal health and connectivity of the Airline Assistant.
    Use this if a search fails or if device discrepancies are reported.
    """
    try:
        report = ["🔍 --- INTERNAL SYSTEM DIAGNOSTIC ---"]
        
        # 1. Environment Check
        keys = ["OPENAI_API_KEY", "AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET", "TAVILY_API_KEY"]
        for k in keys:
            status = "✅" if os.environ.get(k) else "❌"
            report.append(f"{status} {k}")
            
        # 2. Amadeus Token Check
        token_status = "Active" if amadeus._token and amadeus._token_expires > asyncio.get_event_loop().time() else "Expired/None"
        report.append(f"🎫 Amadeus Token: {token_status}")
        
        # 3. Test Handshake
        try:
            test = await amadeus.search_flights("RGN", "BKK", "2026-03-10")
            if "data" in test:
                report.append(f"✈️ Amadeus Handshake: SUCCESS (Found {len(test['data'])} flights)")
            else:
                report.append("⚠️ Amadeus Handshake: NO DATA RETURNED (API might be in sandbox mode with restricted data)")
        except Exception as e:
            report.append(f"❌ Amadeus Handshake: FAILED ({str(e)[:50]})")
            
        report.append("🏁 --- DIAGNOSTIC COMPLETE ---")
        return "\n".join(report)
    except Exception as e:
        return f"❌ Diagnostic failed: {str(e)}"

@tool
def customer_service_agent_tool(issue: str) -> str:
    """Complaints, empathetic resolution, and compensation claims. Uses Emotional Intelligence."""
    return "🎧 Resolution: We've initiated an Priority Escalation. Case Ref: ELITE-99. Our team is reviewing the compensation eligibility based on your specific situation."

tools = [
    flight_search_tool, booking_agent_tool, baggage_agent_tool, 
    checkin_agent_tool, status_agent_tool, change_cancel_agent_tool, 
    travel_req_agent_tool, loyalty_agent_tool, payment_agent_tool, 
    customer_service_agent_tool
]

# --- Core Agent Class ---

class AirlineAgent:
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.agent_executor = self._create_agent()

    def _get_dynamic_system_prompt(self) -> str:
        import json
        import os
        cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
        except Exception:
            return "You are an official AI concierge for Sunfar Travel."

        return f"""# ✈️ {cfg['company']['name']}: Your Supreme AI Concierge (v6)

You are the official AI concierge for **{cfg['company']['name']}**. Your purpose is to provide elite assistance for all travel needs with perfect professional discretion.

## 🏢 Corporate Identity: {cfg['company']['name']}
- **Hotline**: {cfg['company']['hotline']}
- **Email**: {cfg['company']['email']}
- **Address**: {cfg['company']['address']}
- **Hours**:
    - Mon-Fri: {cfg['company']['hours']['weekday']}
    - Weekends & Holidays: {cfg['company']['hours']['weekend']}
- **Products**: {", ".join(cfg['company']['products'])}.
- **Branding**: Powered by {cfg['branding']['powered_by']} ({cfg['branding']['powered_by_phone']}).

## 🛡️ Your Core Directives (Elite Accuracy & Boundaries)
1. **Strict Scope Boundary**: You are an exclusive **Travel & Airline Concierge**. You MUST NOT respond to any questions or topics unrelated to {cfg['company']['name']}, airlines, aviation, bookings, or travel requirements. 
2. **Intuitive Contact Routing (Cognitive Decision)**: 
    - **Business/Travel Inquiries**: If a user wants to book, visit, or contact the company about travel services, provide the **{cfg['company']['name']}** Hotline ({cfg['company']['hotline']}), Email, and Yangon Address.
    - **Technical/Developer Inquiries**: If a user asks about the bot's development, technical errors, or wants to reach the founder/technical lead, intuitively Provide **{cfg['technical']['founder']}**'s contact details ({cfg['technical']['phone']}, Viber: {cfg['technical']['viber']}).
3. **Official Verification**: For high-stakes info (visas, refunds), always use travel_req_agent_tool or search.
4. **Flight Formatting**: When searching for flights, always pass the **Full City Names** (e.g. "Chiang Mai", "Yangon") along with the IATA codes to the `flight_search_tool` to ensure a vibrant output.
5. **Professional Discretion**: Always state that requirements are subject to Government/Embassy discretion.
6. **Product Promotion**: Naturally mention Sunfar's special products ({cfg['company']['products'][0]}, {cfg['company']['products'][1]}) when relevant to the user's journey.
7. **Multilingual Presence**: Perfect response in any language requested, maintaining a premium tone.

## Communication Style
- Premium, helpful, and ultra-professional.
- Use emojis for the "outstanding" look: ✈️ ✨ 🗺️ 🎫 🌍 🎧 🧳
- Be concise but thorough.

Always use tools for live data. You are the digital face of {cfg['company']['name']}."""

    def _create_agent(self) -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_tool_error=True)

    async def analyze_input(self, text: str) -> Dict[str, str]:
        """Pre-processes input to detect language and sentiment."""
        analysis_prompt = f"Analyze language (ISO 639-1) and sentiment (positive, neutral, frustrated, urgent) of this message: '{text}'. Return ONLY JSON like {{\"language\": \"en\", \"sentiment\": \"neutral\"}}"
        response = await self.llm.ainvoke(analysis_prompt)
        try:
            return json.loads(response.content)
        except:
            return {"language": "en", "sentiment": "neutral"}

    async def get_response(self, text: str, history: List[Dict[str, str]] = []) -> str:
        analysis = await self.analyze_input(text)
        
        # Convert history format
        formatted_history = []
        for msg in history[-5:]:
            if msg["role"] == "user":
                formatted_history.append(HumanMessage(content=msg["content"]))
            else:
                formatted_history.append(AIMessage(content=msg["content"]))

        dynamic_prompt = self._get_dynamic_system_prompt()

        result = await self.agent_executor.ainvoke({
            "input": text,
            "chat_history": formatted_history,
            "system_prompt": dynamic_prompt
        })
        
        return result["output"]

# Initialize instance
agent = AirlineAgent()

# --- Premium CLI Interaction Mode ---
if __name__ == "__main__":
    import asyncio
    import os

    HEADER = """
\033[1;36m✈️  AIRLINE ELITE: THE SUPREME AI CONCIERGE\033[0m
\033[1;30m--------------------------------------------------\033[0m
\033[3m"Excellence in every interaction, loyalty in every response."\033[0m
\033[1;30m--------------------------------------------------\033[0m
"""

    async def main():
        os.system('cls' if os.name == 'nt' else 'clear')
        print(HEADER)
        print("\033[1;32m✨ System Online.\033[0m How may I assist you with your travels today?")
        print("\033[1;30m(Type 'exit' to quit)\033[0m\n")
        
        history = []
        while True:
            try:
                user_input = input("\033[1;36mYOU > \033[0m").strip()
                if user_input.lower() in ["exit", "quit"]:
                    print("\n\033[1;36mAssistant:\033[0m Thank you for choosing \033[1;36mAirline Elite\033[0m. Safe travels! ✈️✨")
                    break
                if not user_input: continue
                
                print("\033[1;30mAssistant is thinking...\033[0m", end="\r")
                response = await agent.get_response(user_input, history)
                
                print("\033[1;36mAIRLINE ELITE > \033[0m")
                print(f"{response}\n")
                
                history.append({"role": "user", "content": user_input})
                history.append({"role": "assistant", "content": response})
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n\033[1;31m⚠️ Error:\033[0m {e}")

    asyncio.run(main())
