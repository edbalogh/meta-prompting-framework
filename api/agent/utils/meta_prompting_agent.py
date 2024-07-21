# Set up logging
import operator
import logging
from typing import Annotated, Literal, TypedDict, Sequence
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, FunctionMessage
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig
from langchain_core.language_models import LanguageModelLike
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langgraph.checkpoint import MemorySaver
from agent.utils.prompt_loader import load_markdown_prompt
from langgraph.prebuilt.tool_executor import ToolInvocation

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the state
class MetaPromptingState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    error_log: list[str]
    turn_count: int

# Load meta-prompter instructions
META_PROMPTER_INSTRUCTIONS = load_markdown_prompt("../prompts/meta-prompter.md")

MAX_TURNS = 15  # Increased maximum number of turns for more complex queries

def create_meta_prompting_agent(
    model: LanguageModelLike,
    tools: Sequence[BaseTool],
    checkpointer: MemorySaver = None,
):
    # Create ToolExecutor
    tool_executor = ToolExecutor(tools)

    # Create the meta-prompter node
    def meta_prompter(state: MetaPromptingState, config: RunnableConfig):
        messages = state['messages']
        turn_count = state.get('turn_count', 0) + 1
        
        if turn_count > MAX_TURNS:
            logger.info(f"Reached maximum turns ({MAX_TURNS}). Forcing end of conversation.")
            return {
                "messages": [AIMessage(content="I apologize, but I've been unable to provide a satisfactory answer within a reasonable number of steps. Here's my best attempt at a final answer based on what we've discussed: [Summary of the conversation]")],
                "turn_count": turn_count,
                "error_log": state.get("error_log", []) + ["Reached maximum turns"],
            }
        
        response = model.invoke(
            [
                HumanMessage(content=f"{META_PROMPTER_INSTRUCTIONS}\n\nRemember to use available tools for up-to-date information when necessary. When you have a final answer, start your response with 'FINAL ANSWER:' and be sure it's comprehensive."),
                *messages
            ],
            config
        )
        
        result = {
            "messages": [AIMessage(content=f"Meta-Prompter: {response.content}")],
            "turn_count": turn_count,
            "error_log": state.get("error_log", []),
        }
        
        return result

    # Create the expert node with ReAct-like behavior
    def expert_node(state: MetaPromptingState, config: RunnableConfig):
        messages = state['messages']
        tool_names = ", ".join([tool.name for tool in tools])
        
        expert_prompt = f"""You are an expert assistant with access to the following tools: {tool_names}. 
        Use them when necessary to provide accurate and up-to-date information. 
        To use a tool, respond with the tool name and input in the following format:
        Tool: <tool_name>
        Input: <tool_input>
        
        If you have a final answer, start your response with 'FINAL ANSWER:' and ensure it's comprehensive.
        
        Current conversation:
        {messages}
        
        What would you like to do next? Consider using a tool if you need current information or specific data."""
        
        response = model.invoke([HumanMessage(content=expert_prompt)], config)
        
        if "Tool:" in response.content and "Input:" in response.content:
            tool_name = response.content.split("Tool:")[1].split("\n")[0].strip()
            tool_input = response.content.split("Input:")[1].strip()
            
            logger.info(f"Using tool: {tool_name}")
            
            try:
                tool_invocation = ToolInvocation(tool=tool_name, tool_input=tool_input)
                tool_result = tool_executor.invoke(tool_invocation)
                
                result = {
                    "messages": [
                        AIMessage(content=response.content),
                        FunctionMessage(content=str(tool_result), name=tool_name)
                    ],
                    "error_log": state.get("error_log", [])
                }
            except Exception as e:
                error_message = f"Error executing {tool_name}: {str(e)}"
                logger.error(error_message)
                result = {
                    "messages": [AIMessage(content=f"I encountered an error while trying to use the {tool_name} tool. I'll try a different approach.")],
                    "error_log": state.get("error_log", []) + [error_message]
                }
        else:
            result = {
                "messages": [AIMessage(content=response.content)],
                "error_log": state.get("error_log", [])
            }
        
        result["turn_count"] = state.get("turn_count", 0)
        return result

    # Define the function to determine whether to continue or end
    def should_continue(state: MetaPromptingState) -> Literal["continue", "expert", "end"]:
        last_message = state['messages'][-1].content if state['messages'] else ""
        
        if "FINAL ANSWER:" in last_message:
            logger.info("FINAL ANSWER detected, ending conversation")
            return "end"
        elif state.get("turn_count", 0) >= MAX_TURNS:
            logger.info("Maximum turns reached, ending conversation")
            return "end"
        elif last_message.startswith("Meta-Prompter:"):
            return "expert"
        else:
            return "continue"

    # Create the graph
    workflow = StateGraph(MetaPromptingState)

    # Add nodes
    workflow.add_node("meta_prompter", meta_prompter)
    workflow.add_node("expert", expert_node)

    # Set entry point
    workflow.set_entry_point("meta_prompter")

    # Add edges
    workflow.add_conditional_edges(
        "meta_prompter",
        should_continue,
        {
            "continue": "meta_prompter",
            "expert": "expert",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "expert",
        should_continue,
        {
            "continue": "meta_prompter",
            "expert": "expert",
            "end": END
        }
    )

    # Compile the graph
    return workflow.compile(checkpointer=checkpointer)
