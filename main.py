import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

from src.tools import (
    list_files,
    list_directories,
    get_file_metadata,
    read_file,
    read_files_iterative,
    search_in_files,
    tools_configuration
)
from src.utils import SAFE_BASE_DIR
from src.prompts import system_prompt
from config import agent_model, max_iterations

client = OpenAI()

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text: str, color: str = Colors.ENDC):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.ENDC}")

def print_tool_call(tool_name: str, arguments: Dict[str, Any]):
    """Print tool call information"""
    print_colored(f"\n🔧 Calling tool: {tool_name}", Colors.CYAN)
    print_colored(f"   Arguments: {json.dumps(arguments, indent=2)}", Colors.BLUE)

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool based on its name and return the result"""
    print_tool_call(tool_name, arguments)
    
    try:
        if tool_name == "list_files":
            result = list_files(**arguments)
        elif tool_name == "list_directories":
            result = list_directories(**arguments)
        elif tool_name == "get_file_metadata":
            result = get_file_metadata(**arguments)
        elif tool_name == "read_file":
            result = read_file(**arguments)
        elif tool_name == "read_files_iterative":
            result = read_files_iterative(**arguments)
        elif tool_name == "search_in_files":
            result = search_in_files(**arguments)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        print_colored(f"   ✓ Tool completed", Colors.GREEN)
        return result
    except Exception as e:
        error_result = {"error": str(e)}
        print_colored(f"   ✗ Tool error: {str(e)}", Colors.RED)
        return error_result

def process_conversation(messages: List[Dict[str, Any]]) -> str:
    """Process the conversation with OpenAI and handle tool calls"""
    max_iterations = max_iterations  
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.chat.completions.create(
            model=agent_model,
            messages=messages,
            tools=tools_configuration,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        message_dict = {
            "role": "assistant",
            "content": assistant_message.content
        }
        
        if assistant_message.tool_calls:
            message_dict["tool_calls"] = assistant_message.tool_calls
        
        messages.append(message_dict)
        
        # If there are tool calls, execute them all
        if assistant_message.tool_calls:
            print_colored(f"\n🔄 Executing {len(assistant_message.tool_calls)} tool call(s)...", Colors.YELLOW)
            
            # Execute all tool calls and collect results
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                tool_result = execute_tool(function_name, function_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })
            
            # Continue the loop to allow the model to process all tool results
            # and potentially make more tool calls or provide a final answer
            continue
        else:
            # No tool calls, we have a final response
            return assistant_message.content
    
    print_colored(f"\n⚠️  Reached maximum iterations ({max_iterations}). Returning last response.", Colors.YELLOW)
    return assistant_message.content if assistant_message.content else "I apologize, but I couldn't complete the task within the iteration limit."

def main():
    """Main interactive loop"""
    print_colored("\n" + "="*60, Colors.BOLD)
    print_colored("File Management Agent with OpenAI", Colors.HEADER + Colors.BOLD)
    print_colored("="*60, Colors.BOLD)
    
    print_colored(f"\n📁 Current working directory (SAFE_BASE_DIR):", Colors.GREEN)
    print_colored(f"   {SAFE_BASE_DIR}", Colors.CYAN)
    
    if not os.path.exists(SAFE_BASE_DIR):
        print_colored(f"\n⚠️  Warning: SAFE_BASE_DIR does not exist. Creating it...", Colors.YELLOW)
        os.makedirs(SAFE_BASE_DIR, exist_ok=True)
    
    print_colored("\n💡 You can ask me to:", Colors.YELLOW)
    print("   - List files in directories")
    print("   - Read and analyze file contents")
    print("   - Search for text across multiple files")
    print("   - Get file metadata")
    print("   - Summarize multiple files")
    
    print_colored("\nType 'exit' or 'quit' to end the conversation.\n", Colors.YELLOW)
    
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]
    
    while True:
        try:
            user_input = input(f"\n{Colors.GREEN}You: {Colors.ENDC}")
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print_colored("\n👋 Goodbye! Thanks for using the File Management Agent.", Colors.CYAN)
                break
            
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            print_colored("\n🤔 Thinking...", Colors.YELLOW)
            response = process_conversation(messages)
            
            print_colored(f"\n{Colors.BLUE}Assistant: {Colors.ENDC}{response}")
            
        except KeyboardInterrupt:
            print_colored("\n\n⚠️  Interrupted by user. Exiting...", Colors.YELLOW)
            break
        except Exception as e:
            print_colored(f"\n❌ Error: {str(e)}", Colors.RED)
            print_colored("Please try again or type 'exit' to quit.", Colors.YELLOW)
            if messages and messages[-1]["role"] == "user":
                messages.pop()

if __name__ == "__main__":
    main()
