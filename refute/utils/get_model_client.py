import os
import dotenv
import requests
import json
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages.utils import convert_to_openai_messages
from langchain_core.messages.ai import AIMessage
from refute.utils.logging_config import get_logger
import refute
from pathlib import Path

dotenv.load_dotenv(dotenv_path=Path(refute.__file__).parent / ".env")
logger = get_logger(__name__)

REASONING_MODELS = ["deepseek/deepseek-r1", "gemini-2.0-flash-thinking-exp-01-21", "openai/o3-mini"]


class R1API:
    """API client for interacting with DeepSeek R1 through OpenRouter."""

    def __init__(self, api_key: str, base_url: str, model_name: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    def invoke(self, messages: List[Any]) -> AIMessage:
        """Sends a request to the DeepSeek R1 model and returns the response."""
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = json.dumps({
            "model": self.model_name,
            "messages": convert_to_openai_messages(messages),
            "include_reasoning": True,
            "max_tokens": 50000,
            "provider": {
                "require_parameters": True,
                "order": ["DeepSeek", "Together", "Fireworks"],
                "allow_fallbacks": False
            }
        })

        resp = requests.post(url, headers=headers, data=data).json()
        message = resp["choices"][0]["message"]
        content = ""
        if "reasoning" in message and message["reasoning"] is not None:
            content = f"<thoughts>\n{message['reasoning']}\n</thoughts>"
        if "content" in message and message["content"] is not None:
            content += f"\n{message['content']}"

        return AIMessage(content)


class O3API:
    """API client for interacting with OpenAI models through OpenRouter."""

    def __init__(self, api_key: str, base_url: str, model_name: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    def invoke(self, messages: List[Any]) -> AIMessage:
        """Sends a request to the OpenAI O3 model and returns the response."""
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = json.dumps({
            "model": self.model_name,
            "messages": convert_to_openai_messages(messages),
            "max_tokens": 50000,
            "provider": {"require_parameters": True},
            "reasoning_effort": "high"
        })

        resp = requests.post(url, headers=headers, data=data).json()
        return AIMessage(resp["choices"][0]["message"]["content"])


def get_model_by_name(name: str) -> Any:
    if name == "gemini-2.0-flash-thinking-exp-01-21":
        logger.info(f"Using {name} (non-openrouter)")
        return ChatGoogleGenerativeAI(model=name)

    url = "https://openrouter.ai/api/v1"
    key = os.environ["OPENROUTER_KEY"]

    if name == "deepseek/deepseek-r1":
        logger.info("Using deepseek-r1 (custom params)")
        return R1API(api_key=key, base_url=url, model_name=name)

    if name == "openai/o3-mini":
        logger.info("Using o3-mini (custom params)")
        return O3API(api_key=key, base_url=url, model_name=name)

    logger.info(f"Using openrouter model: {name} (standard params)")
    return ChatOpenAI(
        api_key=key,
        base_url=url,
        model_name=name,
        temperature=0.2,
        top_p=0.95,
    )
