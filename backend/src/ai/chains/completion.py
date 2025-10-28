"""Completion chains sử dụng Gemini LLM từ Google Generative AI.

Module này cung cấp các classes để tạo completions tích hợp với instruction prompts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from langchain_core.output_parsers import BaseOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI


class ModelName(str, Enum):
    """Các models của Google Gemini."""
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"


@dataclass
class LLMConfig:
    """Cấu hình cho Gemini LLM.

    Attributes:
        model_name: Tên model
        temperature: Độ ngẫu nhiên (0-1)
        max_output_tokens: Số tokens tối đa
        top_p: Nucleus sampling
        top_k: Top-k sampling
        api_key: Google API key
    """
    model_name: ModelName = ModelName.GEMINI_2_0_FLASH
    temperature: float = 0.7
    max_output_tokens: int = 2048
    top_p: float = 0.95
    top_k: int = 40
    api_key: str | None = None


class CompletionChain(ABC):
    """Base class cho completion chains.

    Cung cấp interface để tạo completions với Gemini LLM.
    """

    def __init__(self, config: LLMConfig):
        """Khởi tạo chain.

        Args:
            config: Cấu hình LLM.
        """
        self.config = config
        self.llm = self._initialize_llm()
        self.chain: Runnable | None = None

    def _initialize_llm(self) -> ChatGoogleGenerativeAI:
        """Khởi tạo Gemini LLM.

        Returns:
            ChatGoogleGenerativeAI: Initialized LLM.
        """
        return ChatGoogleGenerativeAI(
            model=self.config.model_name.value,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            google_api_key=self.config.api_key,
        )

    @abstractmethod
    def _build_chain(self) -> Runnable:
        """Xây dựng chain - được implement bởi subclass.

        Returns:
            Runnable: Chain runnable.
        """
        pass

    def build(self) -> 'CompletionChain':
        """Xây dựng chain.

        Returns:
            CompletionChain: Self for chaining.
        """
        self.chain = self._build_chain()
        return self

    async def ainvoke(self, input_data: dict[str, Any]) -> str:
        """Gọi chain bất đồng bộ.

        Args:
            input_data: Input data.

        Returns:
            str: Output từ chain.
        """
        if not self.chain:
            self.build()

        result = await self.chain.ainvoke(input_data)
        return result if isinstance(result, str) else result.get("output", str(result))

    def invoke(self, input_data: dict[str, Any]) -> str:
        """Gọi chain đồng bộ.

        Args:
            input_data: Input data.

        Returns:
            str: Output từ chain.
        """
        if not self.chain:
            self.build()

        result = self.chain.invoke(input_data)
        return result if isinstance(result, str) else result.get("output", str(result))


class PromptBasedCompletionChain(CompletionChain):
    """Completion chain dựa trên instruction prompts.

    Tích hợp trực tiếp với instruction.py, sử dụng prompt templates từ PromptFactory.

    Ví dụ:
        from src.ai.llm.instruction import get_prompt

        chain = PromptBasedCompletionChain(config, get_prompt("recipe_retrieval"))
        result = chain.invoke({"query": "...", "ingredients": "...", ...})
    """

    def __init__(self, config: LLMConfig, prompt_template: ChatPromptTemplate):
        """Khởi tạo prompt-based completion chain.

        Args:
            config: Cấu hình LLM.
            prompt_template: ChatPromptTemplate từ instruction.py.
        """
        self.prompt_template = prompt_template
        super().__init__(config)

    def _build_chain(self) -> Runnable:
        """Xây dựng chain với prompt template.

        Returns:
            Runnable: Chain runnable.
        """
        return self.prompt_template | self.llm | StrOutputParser()


class CustomPromptCompletionChain(CompletionChain):
    """Completion chain với custom prompt string.

    Ví dụ:
        chain = CustomPromptCompletionChain(
            config,
            system_prompt="Bạn là một trợ lý nấu ăn",
            prompt_template="Hãy giúp tôi: {request}"
        )
        result = chain.invoke({"request": "nấu cơm tấm"})
    """

    def __init__(
        self,
        config: LLMConfig,
        prompt_template: str,
        system_prompt: str | None = None
    ):
        """Khởi tạo custom prompt completion chain.

        Args:
            config: Cấu hình LLM.
            prompt_template: Template string với {variables}.
            system_prompt: System prompt (optional).
        """
        self.prompt_str = prompt_template
        self.system_prompt = system_prompt
        super().__init__(config)

    def _build_chain(self) -> Runnable:
        """Xây dựng chain từ custom prompt.

        Returns:
            Runnable: Chain runnable.
        """
        from langchain_core.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate

        if self.system_prompt:
            system = SystemMessagePromptTemplate.from_template(self.system_prompt)
            human = HumanMessagePromptTemplate.from_template(self.prompt_str)
            prompt = ChatPromptTemplate.from_messages([system, human])
        else:
            prompt = ChatPromptTemplate.from_template(self.prompt_str)

        return prompt | self.llm | StrOutputParser()


class CustomParserCompletionChain(CompletionChain):
    """Completion chain với custom output parser.

    Ví dụ:
        class JSONParser(BaseOutputParser):
            def parse(self, text: str):
                return json.loads(text)

        chain = CustomParserCompletionChain(
            config,
            prompt_template=get_prompt("recipe_retrieval"),
            parser=JSONParser()
        )
    """

    def __init__(
        self,
        config: LLMConfig,
        prompt_template: ChatPromptTemplate,
        parser: BaseOutputParser
    ):
        """Khởi tạo custom parser completion chain.

        Args:
            config: Cấu hình LLM.
            prompt_template: ChatPromptTemplate.
            parser: Custom output parser.
        """
        self.prompt_template = prompt_template
        self.parser = parser
        super().__init__(config)

    def _build_chain(self) -> Runnable:
        """Xây dựng chain với custom parser.

        Returns:
            Runnable: Chain runnable.
        """
        return self.prompt_template | self.llm | self.parser


class ChainBuilder:
    """Builder class để tạo completion chains một cách dễ dàng.

    Ví dụ:
        from src.ai.llm.instruction import get_prompt

        # Sử dụng instruction prompt
        chain = (ChainBuilder(config)
                 .with_prompt(get_prompt("recipe_retrieval"))
                 .build())

        result = chain.invoke({...})

        # Hoặc sử dụng custom prompt
        chain = (ChainBuilder(config)
                 .with_custom_prompt("Hãy giúp tôi: {request}", "Bạn là trợ lý")
                 .build())

        result = chain.invoke({"request": "..."})
    """

    def __init__(self, config: LLMConfig | None = None):
        """Khởi tạo builder.

        Args:
            config: Cấu hình LLM (hoặc dùng mặc định).
        """
        self.config = config or LLMConfig()
        self.chain: CompletionChain | None = None

    def with_prompt(self, prompt_template: ChatPromptTemplate) -> 'ChainBuilder':
        """Tạo chain từ instruction prompt.

        Args:
            prompt_template: ChatPromptTemplate từ instruction.py.

        Returns:
            ChainBuilder: Self for chaining.
        """
        self.chain = PromptBasedCompletionChain(self.config, prompt_template)
        return self

    def with_custom_prompt(
        self,
        template: str,
        system_prompt: str | None = None
    ) -> 'ChainBuilder':
        """Tạo chain từ custom prompt string.

        Args:
            template: Template string với {variables}.
            system_prompt: System prompt (optional).

        Returns:
            ChainBuilder: Self for chaining.
        """
        self.chain = CustomPromptCompletionChain(self.config, template, system_prompt)
        return self

    def with_custom_parser(
        self,
        prompt_template: ChatPromptTemplate,
        parser: BaseOutputParser
    ) -> 'ChainBuilder':
        """Tạo chain với custom output parser.

        Args:
            prompt_template: ChatPromptTemplate.
            parser: Custom output parser.

        Returns:
            ChainBuilder: Self for chaining.
        """
        self.chain = CustomParserCompletionChain(self.config, prompt_template, parser)
        return self

    def build(self) -> CompletionChain:
        """Xây dựng và trả về chain.

        Returns:
            CompletionChain: Xây dựng chain.

        Raises:
            ValueError: Nếu chưa chọn loại chain.
        """
        if not self.chain:
            raise ValueError(
                "Chưa chọn loại chain. "
                "Hãy gọi .with_prompt(), .with_custom_prompt() hoặc .with_custom_parser()"
            )

        return self.chain.build()


# Convenience functions
def create_completion_with_prompt(
    prompt_template: ChatPromptTemplate,
    input_data: dict[str, Any],
    config: LLMConfig | None = None
) -> str:
    """Tạo completion nhanh chóng từ instruction prompt.

    Args:
        prompt_template: ChatPromptTemplate từ instruction.py.
        input_data: Input data.
        config: LLM config (optional).

    Returns:
        str: Completion result.
    """
    cfg = config or LLMConfig()
    chain = PromptBasedCompletionChain(cfg, prompt_template).build()
    return chain.invoke(input_data)


async def create_completion_with_prompt_async(
    prompt_template: ChatPromptTemplate,
    input_data: dict[str, Any],
    config: LLMConfig | None = None
) -> str:
    """Tạo completion nhanh chóng từ instruction prompt (async).

    Args:
        prompt_template: ChatPromptTemplate từ instruction.py.
        input_data: Input data.
        config: LLM config (optional).

    Returns:
        str: Completion result.
    """
    cfg = config or LLMConfig()
    chain = PromptBasedCompletionChain(cfg, prompt_template).build()
    return await chain.ainvoke(input_data)


def create_completion_with_custom_prompt(
    template: str,
    input_data: dict[str, Any],
    system_prompt: str | None = None,
    config: LLMConfig | None = None
) -> str:
    """Tạo completion nhanh chóng từ custom prompt.

    Args:
        template: Template string.
        input_data: Input data.
        system_prompt: System prompt (optional).
        config: LLM config (optional).

    Returns:
        str: Completion result.
    """
    cfg = config or LLMConfig()
    chain = CustomPromptCompletionChain(cfg, template, system_prompt).build()
    return chain.invoke(input_data)


async def create_completion_with_custom_prompt_async(
    template: str,
    input_data: dict[str, Any],
    system_prompt: str | None = None,
    config: LLMConfig | None = None
) -> str:
    """Tạo completion nhanh chóng từ custom prompt (async).

    Args:
        template: Template string.
        input_data: Input data.
        system_prompt: System prompt (optional).
        config: LLM config (optional).

    Returns:
        str: Completion result.
    """
    cfg = config or LLMConfig()
    chain = CustomPromptCompletionChain(cfg, template, system_prompt).build()
    return await chain.ainvoke(input_data)

