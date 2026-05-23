import json
import logging
import asyncio
from datetime import date
from sqlalchemy.orm import Session

from app.models.schemas import AppSetting
from app.services.llm_tools import TOOL_FUNCTIONS, LLM_TOOLS_SCHEMA
from app.utils.api_key_manager import get_active_key, mark_key_exhausted
import httpx

logger = logging.getLogger(__name__)

DEFAULT_OPENROUTER_MODEL = "poolside/laguna-m.1:free"
OPENROUTER_MODEL_SETTING_KEY = "openrouter_model"

def get_configured_openrouter_model(db: Session) -> str:
    db_setting = db.query(AppSetting).filter(
        AppSetting.setting_key == OPENROUTER_MODEL_SETTING_KEY
    ).first()
    if db_setting and db_setting.setting_value.strip():
        return db_setting.setting_value.strip()
    return DEFAULT_OPENROUTER_MODEL

async def _call_openrouter_with_tools(db: Session, messages: list) -> dict:
    url = "https://openrouter.ai/api/v1/chat/completions"
    max_retries = 3
    retry_count = 0
    model_name = get_configured_openrouter_model(db)
    
    while retry_count < max_retries:
        api_key = get_active_key(db, "openrouter")
        if not api_key:
            raise ValueError("No active OpenRouter API key is available.")
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # We also pass the tools to OpenRouter
        payload = {
            "model": model_name,
            "messages": messages,
            "tools": LLM_TOOLS_SCHEMA,
            "tool_choice": "auto",
            "temperature": 0.2,
            "max_tokens": 3000
        }
        logger.info(f"Calling OpenRouter model: {model_name}")
        
        try:
            async with httpx.AsyncClient() as client:
                # 2-minute timeout for LLM
                response = await client.post(url, headers=headers, json=payload, timeout=120.0)
                
                if response.status_code in (429, 403, 402):
                    logger.warning(f"OpenRouter API key exhausted: {response.status_code}")
                    mark_key_exhausted(db, "openrouter", api_key)
                    retry_count += 1
                    await asyncio.sleep(1)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                # Extract the message object directly (could have tool_calls or content)
                return data["choices"][0]["message"]
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 403, 402):
                logger.warning(f"OpenRouter API key exhausted: {e}")
                mark_key_exhausted(db, "openrouter", api_key)
                retry_count += 1
                await asyncio.sleep(1)
            else:
                logger.error(f"OpenRouter API error: {e.response.text}")
                raise e
        except Exception as e:
            logger.error(f"Error calling OpenRouter: {e}")
            raise e
            
    raise ValueError("All OpenRouter API keys are exhausted or failed.")

async def run_agentic_loop(db: Session, system_prompt: str, briefing_text: str, max_tool_calls: int = 15) -> str:
    """
    Executes a ReAct-style loop. The LLM receives the briefing, can call tools,
    and must eventually respond with the final JSON.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"INITIAL BRIEFING:\n{briefing_text}\n\nYou may use your tools to investigate further. Once you have enough information, output your final prediction in the requested JSON format (and ONLY the JSON)."}
    ]
    
    tool_call_count = 0
    
    while tool_call_count <= max_tool_calls:
        logger.info(f"Agent Loop Iteration {tool_call_count+1}")
        message = await _call_openrouter_with_tools(db, messages)
        
        # Append the assistant's message to the conversation
        messages.append(message)
        
        # Did it call a tool?
        if "tool_calls" in message and message["tool_calls"]:
            for tool_call in message["tool_calls"]:
                tool_call_count += 1
                function_name = tool_call["function"]["name"]
                args_str = tool_call["function"]["arguments"]
                
                logger.info(f"LLM called tool: {function_name} with args: {args_str}")
                
                try:
                    args = json.loads(args_str)
                    if function_name in TOOL_FUNCTIONS:
                        result = TOOL_FUNCTIONS[function_name](db, **args)
                    else:
                        result = f"Error: Tool {function_name} not found."
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    result = f"Error executing tool: {str(e)}"
                    
                # Append tool result
                messages.append({
                    "role": "tool",
                    "name": function_name,
                    "tool_call_id": tool_call["id"],
                    "content": str(result)
                })
                
            if tool_call_count >= max_tool_calls:
                # Force an answer
                messages.append({
                    "role": "user",
                    "content": "You have exhausted your tool call budget. Please output your final JSON prediction now based on what you have learned."
                })
        else:
            # No tool calls made, so this must be the final text answer
            return message.get("content", "")
            
    # Fallback if loop ends weirdly
    return messages[-1].get("content", "")
