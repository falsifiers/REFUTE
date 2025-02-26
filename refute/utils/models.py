from pathlib import Path
from typing import Optional, List
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate

from refute.utils.dataset_parser import desc_problem
from refute.utils.logging_config import get_logger
from refute.utils.get_model_client import get_model_by_name, REASONING_MODELS
import refute

logger = get_logger(__name__)
root_dir = Path(refute.__file__).parent
prompt_dir = root_dir / "prompt_templates"


class BaseLLM:
    """Base class for interacting with LLMs using predefined system and human prompts."""

    def __init__(self, model_name: str, method: str, max_retries: int = 5) -> None:
        self.model = get_model_by_name(model_name)
        self.max_retries = max_retries
        self.method = method
        self.raw_name = model_name

        sys_prompt_file = f"{method}_system.txt"
        human_prompt_file = f"{method}_human.txt"

        if model_name in REASONING_MODELS:
            logger.info("Using reasoning model")
            reasoning_sys_prompt = prompt_dir / f"reasoning_{sys_prompt_file}"
            if reasoning_sys_prompt.exists():
                sys_prompt_file = "reasoning_" + sys_prompt_file
            else:
                logger.warning("Reasoning prompt not found, using default")

        with open(prompt_dir / sys_prompt_file, "r") as f:
            self.sys_prompt = f.read()
        with open(prompt_dir / human_prompt_file, "r") as f:
            self.human_prompt_pref = f.read()

        logger.info(f"Using model {self.raw_name} with {self.method}")

    def _get_response(self, messages: List[BaseMessage]) -> str:
        """Sends messages to the model and retries on failure."""
        for _ in range(self.max_retries):
            try:
                return self.model.invoke(messages).content
            except Exception as e:
                if _ == self.max_retries - 1:
                    logger.error("Max retries reached, raising exception", exc_info=True)
                    raise e
                logger.warning("Error, retrying...", exc_info=True)

    def _ask_with_system_prompt(self, human: str) -> str:
        """Sends a human message with the pre-configured system prompt."""
        messages = [SystemMessage(content=self.sys_prompt), HumanMessage(content=human)]
        # print(ChatPromptTemplate(messages).format())
        return self._get_response(messages)


class VanillaLLM(BaseLLM):
    """Makes standard and randsearch queries."""

    def __init__(self, model_name: str, method: str, max_retries: int = 5) -> None:
        assert method in ["few_shot", "zero_shot", "randsearch"]
        super().__init__(model_name, method, max_retries)

    def ask(self, problem: dict[str, str], code: Optional[str]) -> str:
        """Sends a problem and optional incorrect code to the model."""
        if self.method == "randsearch_no_code":
            assert code is None
        else:
            assert code is not None

        human_prompt = f"""{self.human_prompt_pref}\n\n{desc_problem(problem)}"""
        if code:
            human_prompt += f"""
## Code
```
{code}
```"""
        return self._ask_with_system_prompt(human_prompt)


class VanillaOracleLLM(BaseLLM):
    """Makes standard queries with correct code revealed."""

    def __init__(self, model_name: str, method: str, max_retries: int = 5) -> None:
        assert method == "zero_shot_oracle"
        super().__init__(model_name, method, max_retries)

    def ask(self, problem: dict[str, str], buggy_code: str, correct_code: str) -> str:
        """Sends a problem with buggy and correct code to the model."""
        human_prompt = f"""{self.human_prompt_pref}\n\n{desc_problem(problem)}

## Buggy Code
```
{buggy_code}
```

## Correct Code
```
{correct_code}
```"""
        return self._ask_with_system_prompt(human_prompt)


class RandSearchOracleLLM(BaseLLM):
    """Makes randsearch with oracle comparisons."""

    def __init__(self, model_name: str, method: str, max_retries: int = 5) -> None:
        assert method == "randsearch_oracle"
        super().__init__(model_name, method, max_retries)

    def ask(self, problem: dict[str, str], buggy_code: Optional[str], correct_code: Optional[str]) -> str:
        """Sends a problem with optional buggy and correct code to the model."""
        human_prompt = f"{self.human_prompt_pref}\n\n{desc_problem(problem)}"
        return self._ask_with_system_prompt(human_prompt)
