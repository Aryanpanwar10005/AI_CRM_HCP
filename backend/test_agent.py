import json
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from agent import graph
from langchain_core.messages import HumanMessage

async def test():
    try:
        res = await graph.ainvoke({
            'messages': [HumanMessage(content='hi')], 
            'current_form_state': {}, 
            'current_interaction_id': None, 
            'form_updates': {}, 
            'actions_taken': []
        })
        print("AGENT_SUCCESS")
        # print(json.dumps(res, default=str))
    except Exception as e:
        print(f"AGENT_ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
