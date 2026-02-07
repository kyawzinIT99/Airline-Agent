import asyncio
import os
import sys
from agent_logic import agent

# Clear screen for premium experience
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Premium Header
HEADER = """
\033[1;36m✈️  AIRLINE ELITE: THE SUPREME AI CONCIERGE\033[0m
\033[1;30m--------------------------------------------------\033[0m
\033[3m"Excellence in every interaction, loyalty in every response."\033[0m
\033[1;30m--------------------------------------------------\033[0m
"""

async def run_cli_bot():
    clear_screen()
    print(HEADER)
    print("\033[1;32m✨ System Online.\033[0m How may I assist you with your travels today?")
    print("\033[1;30m(Type 'quit' or 'exit' to terminate the session)\033[0m\n")
    
    history = []
    
    while True:
        try:
            # Styled Input
            user_input = input("\033[1;36mYOU > \033[0m").strip()
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n\033[1;36mAssistant:\033[0m Thank you for choosing \033[1;36mAirline Elite\033[0m. Safe travels! ✈️✨")
                break
            
            if not user_input:
                continue

            # Loading indicator
            print("\033[1;30mAssistant is thinking...\033[0m", end="\r")
            
            # Get response from the core agent
            response = await agent.get_response(user_input, history)
            
            # Styled Output
            print("\033[1;36mAIRLINE ELITE > \033[0m")
            print(f"{response}\n")
            
            # Update history
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            print("\n\033[1;31mSession terminated by user.\033[0m")
            break
        except Exception as e:
            print(f"\n\033[1;31m⚠️  A technical anomaly occurred:\033[0m {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_cli_bot())
    except KeyboardInterrupt:
        pass
