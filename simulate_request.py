import httpx
import asyncio

async def simulate_user():
    url = "http://localhost:8000/chat"
    payload = {
        "message": "flight schedule on 13/03/2026 by Yangon to Chaing Mai",
        "history": []
    }
    print(f"🚀 Sending request to {url}...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_user())
