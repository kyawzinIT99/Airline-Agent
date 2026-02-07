import asyncio
import os
from agent_logic import flight_search_tool, agent

async def debug_scenario():
    print("🔍 --- FLIGHT SEARCH DEBUG SCENARIO ---\n")
    
    # User's query: "flight schedule on 03/12/2026 from Yangon to Chiang Mai"
    # Testing both interpretation: March 12 and Dec 3
    
    dates = ["2026-03-12", "2026-03-13"]
    
    for d in dates:
        print(f"🧪 Testing Date: {d} (Yangon [RGN] to Chiang Mai [CNX])")
        res = await flight_search_tool.ainvoke({"origin": "RGN", "destination": "CNX", "date": d})
        print(f"Tool Output: {res}\n")

    print("🧠 Testing Agent Thinking for the same query...")
    query = "flight schedule on 03/12/2026 from Yangon to Chiang Mai"
    agent_res = await agent.get_response(query)
    print(f"Agent Final Response: {agent_res}")

if __name__ == "__main__":
    asyncio.run(debug_scenario())
