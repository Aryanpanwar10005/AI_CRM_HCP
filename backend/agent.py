import json
import os
from typing import TypedDict, Optional, Annotated, List, Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from tools import log_interaction, edit_interaction, get_hcp_profile, compliance_check, next_best_action

# Simple reducer for form_updates to ensure we don't lose updates
def merge_updates(current: dict, new: dict) -> dict:
    if not new: return current
    return {**current, **new}

# Define the state for the agent
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_form_state: dict
    current_interaction_id: Optional[int]
    form_updates: Annotated[dict, merge_updates]
    actions_taken: List[str]

# Initialize models from env
primary_model = os.getenv("GROQ_MODEL_PRIMARY", "llama-3.1-8b-instant")
groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    temperature=0,
    groq_api_key=groq_api_key,
    model_name=primary_model
)

# Bind tools to the LLM
tools_list = [log_interaction, edit_interaction, get_hcp_profile, compliance_check, next_best_action]
llm_with_tools = llm.bind_tools(tools_list)

# --- Nodes ---

def call_model(state: AgentState):
    """
    The agent decision node. 
    It looks at the conversation and decides which tool to call.
    """
    system_prompt = SystemMessage(content=f"""
You are an expert AI Assistant for a Pharmaceutical CRM. 
You help medical representatives log interactions with HCPs (Doctors).

TOOLS & TRIGGERS:
1. log_interaction: Use when the user describes a visit, call, email, or video meeting.
2. edit_interaction: Use when the user wants to change or correct a specific field (e.g., "change date", "update sentiment").
3. get_hcp_profile: Use when the user asks about a doctor's history, specialty, or details.
4. compliance_check: Use when the user asks if they can visit a doctor again or asks about monthly limits.
5. next_best_action: Use when the user asks for a recommendation or "what should I do next" with a doctor.

STATE CONTEXT:
- Current Interaction ID: {state.get("current_interaction_id")}
- Current Form Values: {json.dumps(state.get("current_form_state", {}))}

RULES:
- If the user provides info for multiple fields, call log_interaction.
- If the user wants to update a field, call edit_interaction.
- If the user asks about visit eligibility, monthly limits, or whether they can visit an HCP again, call compliance_check when an HCP name is present.
- If the user asks for history or profile details and gives an HCP name, call get_hcp_profile.
- If the user asks what to do next and gives an HCP name, call next_best_action.
- ALWAYS call a tool if possible.
- IMPORTANT: After a tool is called, provide a clean, professional summary in plain text.
- NEVER mention internal tool names, ask the user to use a tool, include JSON blocks, code snippets, or technical field names (like 'hcp_id') in your final reply to the user.
- If details are missing, ask for them in plain business language.
- Be professional, concise, and helpful.
""")
    
    messages = [system_prompt] + state["messages"]
    
    # WORKAROUND: If the last message is a ToolMessage, we force tool_choice="none"
    # to avoid Groq/LangChain loop or validation errors (e.g. phantom brave_search).
    from langchain_core.messages import ToolMessage
    if state["messages"] and isinstance(state["messages"][-1], ToolMessage):
        response = llm_with_tools.invoke(messages, tool_choice="none")
    else:
        response = llm_with_tools.invoke(messages)
        
    return {"messages": [response], "form_updates": {}}

def custom_tools_node(state: AgentState):
    """
    Executes the tool calls and parses the JSON results into the graph state.
    This fixes the 'State Black Hole' by explicitly updating form_updates.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_outputs = []
    new_form_updates = {}
    new_actions = []
    interaction_id = state.get("current_interaction_id")
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Inject current_interaction_id for edit_interaction if missing
        if tool_name == "edit_interaction" and "interaction_id" not in tool_args:
            tool_args["interaction_id"] = interaction_id
            
        # Find and execute tool
        target_tool = next(t for t in tools_list if t.name == tool_name)
        result_str = target_tool.invoke(tool_args)
        
        # Parse tool result (which we made JSON in tools.py)
        try:
            result_json = json.loads(result_str)
            display_message = result_json.get("message", result_str)
            
            # Extract form updates if present
            if "form_updates" in result_json:
                new_form_updates.update(result_json["form_updates"])
                
            # Update current interaction ID if it was a log action
            if "interaction_id" in result_json.get("form_updates", {}):
                interaction_id = result_json["form_updates"]["interaction_id"]
                
            new_actions.append(result_json.get("action", tool_name))
        except:
            display_message = result_str
            new_actions.append(tool_name)
            
        tool_outputs.append(ToolMessage(
            tool_call_id=tool_call["id"],
            content=display_message
        ))
        
    return {
        "messages": tool_outputs,
        "form_updates": new_form_updates,
        "actions_taken": new_actions,
        "current_interaction_id": interaction_id
    }

# --- Build Graph ---

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", custom_tools_node)

workflow.set_entry_point("agent")

def route_after_agent(state: AgentState):
    last_msg = state["messages"][-1]
    if last_msg.tool_calls:
        return "tools"
    return END

workflow.add_conditional_edges(
    "agent",
    route_after_agent,
    {"tools": "tools", END: END}
)

workflow.add_edge("tools", "agent")

graph = workflow.compile()
