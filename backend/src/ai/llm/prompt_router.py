from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.ai.llm.instruction import get_factory


class RoutingOutput(BaseModel):
    target_prompt: str = Field(..., description="Tên prompt được chọn")
    confidence: float = Field(..., ge=0, le=1, description="Độ tin cậy 0..1")
    variables: dict[str, Any] = Field(default_factory=dict, description="Map của các biến đã trích xuất")
    missing_required: list[str] = Field(default_factory=list, description="Danh sách biến bắt buộc còn thiếu")
    notes: str | None = Field(default=None, description="Ghi chú ngắn gọn về cách map/giả định")

class PromptRouter:
    """
    Lớp PromptRouter để định tuyến prompt dựa trên phân tích đầu vào.
    """

    def __init__(self, llm_model):
        """
        Khởi tạo PromptRouter với mô hình ngôn ngữ lớn (LLM).

        Args:
            llm_model: Mô hình ngôn ngữ lớn để sử dụng cho phân tích và định tuyến.
        """
        self.llm = llm_model
        self.factory = get_factory()

    def build_router_prompt(self, prompts_info: dict[str, dict]) -> ChatPromptTemplate:
        """
        Xây dựng prompt định tuyến dựa trên thông tin các prompt có sẵn.
        Args:
            prompts_info: Thông tin về các prompt có sẵn.
        Returns:
            ChatPromptTemplate để sử dụng trong chuỗi định tuyến.
        """
        # Tạo “catalog” text cho LLM
        lines = []
        for name, info in prompts_info.items():
            lines.append(
                f"- name: {name}\n  use_case: {info['use_case']}\n"
                f"  description: {info['description']}\n"
                f"  required_variables: {', '.join(info['required_variables']) if info['required_variables'] else '(none)'}"
            )
        catalog = "\n".join(lines)

        system = (
            "Bạn là bộ định tuyến tác vụ cho nền tảng AI nấu ăn. "
            "Nhiệm vụ: xác định PROMPT phù hợp nhất cho đầu vào người dùng và trích xuất biến theo schema. "
            "Bạn chỉ trả về JSON hợp lệ theo schema yêu cầu (không bình luận, không giải thích)."
        )
        instructions = (
            "CATALOG PROMPTS:\n"
            f"{catalog}\n\n"
            "YÊU CẦU:\n"
            "1) Chọn `target_prompt` phù hợp nhất với ý định user.\n"
            "2) `variables`: chỉ điền các khóa có trong `required_variables` của prompt được chọn. "
            "   Giá trị không chắc chắn thì để null/chuỗi rỗng; tuyệt đối không bịa.\n"
            "3) `missing_required`: liệt kê các biến bắt buộc chưa suy ra được.\n"
            "4) `confidence`: 0..1, dựa trên độ khớp ý định và độ đầy đủ dữ kiện.\n"
            "5) `notes`: ghi chú ngắn gọn (tối đa 1–2 câu, không suy luận dài dòng).\n"
            "6) Nếu user chỉ muốn tạo vector/embedding → chọn `embedding` và để `variables` rỗng.\n"
            "7) Nếu câu hỏi so sánh 2 văn bản → `text_similarity`.\n"
            "8) Nếu muốn truy xuất/tìm công thức theo tiêu chí → `recipe_retrieval`.\n"
            "9) Nếu muốn gợi ý theo hồ sơ người dùng → `recommendation`.\n"
            "10) Nếu yêu cầu tạo nội dung/bài viết → `content_generation`.\n"
            "11) Nếu muốn tăng cường/chuẩn hóa truy vấn → `query_enhancement`.\n"
            "12) Nếu phân tích dinh dưỡng → `nutritional_analysis`.\n"
            "13) Nếu gom nhóm/dàn mục → `clustering`.\n"
        )

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system),
            ("system", instructions),
            ("human", "User input:\n{user_query}"),
        ])
        return prompt

    def build_router_chain(
            self,
            base_url: str | None = None,
            api_key: str | None = None,
            model: str = "gpt-4o-mini",  # hoặc model OpenAI-compatible
            temperature: float = 0.0,
    ):
        """
        Xây dựng chuỗi định tuyến prompt.
        Args:
            base_url: URL cơ sở của API LLM (nếu có).
            api_key: Khóa API để xác thực với dịch vụ LLM (nếu có).
            model: Tên mô hình LLM để sử dụng.
            temperature: Nhiệt độ sinh văn bản (điều khiển độ sáng tạo).
        Returns:
            Chuỗi định tuyến prompt.
        """
        prompts_info = self.factory.get_all_prompts_info()
        prompt = self.build_router_prompt(prompts_info)

        # LLM client (OpenAI-compatible)
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
        )

        parser = JsonOutputParser(pydantic_object=RoutingOutput)

        chain = (
            prompt
            | llm
            | parser
        )

        # Hậu xử lý: đảm bảo chỉ trả về biến thuộc required_variables, tính missing_required
        def postprocess(result: RoutingOutput) -> RoutingOutput:
            name = result.target_prompt
            info = prompts_info.get(name)
            if not info:
                # fallback: chọn embedding nếu không khớp
                info = prompts_info["embedding"]
                name = "embedding"

            allowed = set(info["required_variables"])
            # giữ đúng keys và order
            cleaned_vars = {k: result.variables.get(k) for k in info["required_variables"]}
            missing = [k for k in info["required_variables"] if not cleaned_vars.get(k)]

            return RoutingOutput(
                target_prompt=name,
                confidence=result.confidence,
                variables=cleaned_vars,
                missing_required=missing,
                notes=result.notes,
            )

        return chain | RunnableLambda(postprocess)
