import asyncio
import json
import os
from agent_logic import flight_search_tool

async def verify_format():
    print("🧪 Verifying New Flight Output Format...")
    
    # Mocking successful results to test formatting only
    # Note: To fully test, we'd need to mock AmadeusClient.search_flights
    # But we can also just run it with real data if credentials are valid.
    
    try:
        # Example from user: Chiang Mai (CNX) -> Yangon (RGN)
        res = await flight_search_tool.ainvoke({
            "origin": "CNX", 
            "destination": "RGN", 
            "date": "2026-03-17", 
            "origin_name": "Chiang Mai", 
            "destination_name": "Yangon"
        })
        print("\n--- OUTPUT START ---")
        print(res)
        print("--- OUTPUT END ---\n")
        
        if "✈️ Chiang Mai (CNX) → Yangon (RGN)" in res and "📅 17 March 2026" in res:
            print("✅ Format matches user request!")
        else:
            print("❌ Format mismatch. Check header and date.")
            
        if "⏱️" in res and "•" in res:
            print("✅ Emojis and bullet points present!")
        else:
            print("❌ Missing emojis or bullet points.")

    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_format())
