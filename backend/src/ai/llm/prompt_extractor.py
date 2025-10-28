"""Module để LLM tự động trích xuất PromptMetadata từ prompt người dùng.

Cung cấp các công cụ để phân tích prompt của người dùng và tự động xác định
loại prompt, các biến cần thiết, use case, v.v.

module này đã bị deprecated và được thay thế bởi `prompt_router.py` với
khả năng định tuyến prompt nâng cao hơn.
"""

import re
from typing import Any

from instruction import PromptMetadata, get_factory
from langchain_core.prompts import ChatPromptTemplate


class PromptExtractor:
    """Trích xuất thông tin metadata từ prompt người dùng."""

    # Pattern để phát hiện các biến trong prompt
    VARIABLE_PATTERN = r'\{(\w+)\}'

    def __init__(self):
        """Khởi tạo prompt extractor."""
        self.factory = get_factory()

    def extract_variables(self, text: str) -> list[str]:
        """Trích xuất tất cả các biến từ text.

        Args:
            text: Text cần trích xuất.

        Returns:
            List[str]: Danh sách các tên biến.
        """
        matches = re.findall(self.VARIABLE_PATTERN, text)
        return list(set(matches))  # Loại bỏ duplicates

    def calculate_similarity(self, user_variables: list[str], template_variables: list[str]) -> float:
        """Tính độ tương tự giữa hai danh sách biến.

        Args:
            user_variables: Biến từ prompt người dùng.
            template_variables: Biến từ template có sẵn.

        Returns:
            float: Độ tương tự (0-1).
        """
        if not template_variables:
            return 0.0

        matching = len(set(user_variables) & set(template_variables))
        return matching / len(template_variables)

    def find_best_matching_prompt(self, user_text: str) -> tuple[str | None, float]:
        """Tìm prompt template phù hợp nhất dựa trên text người dùng.

        Args:
            user_text: Text từ người dùng.

        Returns:
            Tuple[Optional[str], float]: (Tên prompt, Độ tương tự).
        """
        user_variables = self.extract_variables(user_text)

        best_match = None
        best_score = 0.0

        for prompt_name in self.factory.list_prompts():
            prompt = self.factory.get_prompt(prompt_name)
            template_vars = prompt.metadata.required_variables

            score = self.calculate_similarity(user_variables, template_vars)

            if score > best_score:
                best_score = score
                best_match = prompt_name

        return best_match, best_score


class PromptAnalyzer:
    """Phân tích prompt người dùng để tự động sinh PromptMetadata."""

    def __init__(self):
        """Khởi tạo prompt analyzer."""
        self.extractor = PromptExtractor()

    def analyze_user_prompt(self, user_prompt: str) -> dict[str, Any]:
        """Phân tích prompt người dùng và trích xuất thông tin.

        Args:
            user_prompt: Prompt từ người dùng.
Base
        Returns:
            Dict[str, Any]: Thông tin phân tích bao gồm:
                - detected_prompt_name: Tên prompt được phát hiện
                - confidence: Độ tin cậy (0-1)
                - extracted_variables: Biến được trích xuất
                - missing_variables: Biến còn thiếu
                - suggested_prompt_info: Thông tin prompt gợi ý
        """
        # Trích xuất biến từ user prompt
        extracted_vars = self.extractor.extract_variables(user_prompt)

        # Tìm prompt phù hợp nhất
        best_prompt_name, confidence = self.extractor.find_best_matching_prompt(user_prompt)

        result: dict[str, Any] = {
            "extracted_variables": extracted_vars,
            "detected_prompt_name": best_prompt_name,
            "confidence": confidence,
            "missing_variables": [],
            "suggested_prompt_info": None,
        }

        if best_prompt_name:
            prompt = self.extractor.factory.get_prompt(best_prompt_name)
            required = prompt.metadata.required_variables

            # Biến còn thiếu
            missing = [v for v in required if v not in extracted_vars]
            result["missing_variables"] = missing
            result["suggested_prompt_info"] = prompt.get_info()

        return result

    def extract_metadata_from_context(self, user_prompt: str, additional_context: str | None = None) -> PromptMetadata | None:
        """Trích xuất metadata từ prompt và ngữ cảnh.

        Args:
            user_prompt: Prompt từ người dùng.
            additional_context: Ngữ cảnh bổ sung (optional).

        Returns:
            Optional[PromptMetadata]: Metadata được trích xuất, hoặc None nếu không tìm thấy.
        """
        analysis = self.analyze_user_prompt(user_prompt)

        if analysis["detected_prompt_name"] and analysis["confidence"] > 0.5:
            prompt = self.extractor.factory.get_prompt(analysis["detected_prompt_name"])
            return prompt.metadata

        return None


class UserPromptAdapter:
    """Chuyển đổi prompt người dùng thành prompt template chuẩn."""

    def __init__(self):
        """Khởi tạo user prompt adapter."""
        self.analyzer = PromptAnalyzer()
        self.factory = get_factory()

    def adapt_user_prompt(self, user_prompt: str) -> ChatPromptTemplate | None:
        """Chuyển đổi user prompt thành template.

        Args:
            user_prompt: Prompt từ người dùng.

        Returns:
            Optional[ChatPromptTemplate]: Adapted template hoặc None.
        """
        metadata = self.analyzer.extract_metadata_from_context(user_prompt)

        if metadata:
            return self.factory.get_template(metadata.name)

        return None

    def get_adaptation_report(self, user_prompt: str) -> dict[str, Any]:
        """Lấy báo cáo chi tiết về quá trình chuyển đổi.

        Args:
            user_prompt: Prompt từ người dùng.

        Returns:
            Dict[str, Any]: Báo cáo chuyển đổi.
        """
        analysis = self.analyzer.analyze_user_prompt(user_prompt)

        return {
            "user_prompt": user_prompt,
            "analysis": analysis,
            "adapted_template": None if not analysis["detected_prompt_name"]
                              else self.factory.get_prompt(analysis["detected_prompt_name"]).get_info(),
            "recommendations": self._generate_recommendations(analysis)
        }

    def _generate_recommendations(self, analysis: dict[str, Any]) -> list[str]:
        """Tạo các khuyến nghị dựa trên phân tích.

        Args:
            analysis: Kết quả phân tích.

        Returns:
            List[str]: Danh sách khuyến nghị.
        """
        recommendations = []

        if analysis["confidence"] < 0.7:
            recommendations.append("Confidence thấp, hãy kiểm tra lại các biến")

        if analysis["missing_variables"]:
            recommendations.append(
                f"Thiếu các biến: {', '.join(analysis['missing_variables'])}. "
                f"Vui lòng cung cấp các biến này."
            )

        if not analysis["detected_prompt_name"]:
            recommendations.append("Không tìm thấy prompt phù hợp, hãy thử lại với prompt khác")

        return recommendations


class SmartPromptMatcher:
    """Matcher thông minh để tìm prompt phù hợp nhất dựa trên nhiều tiêu chí."""

    # Từ khóa liên quan đến từng loại prompt
    KEYWORD_MAPPING = {
        "embedding": ["embedding", "vector", "semantic", "biểu diễn"],
        "recipe_retrieval": ["tìm kiếm", "công thức", "recipe", "nấu ăn", "tìm", "recipe"],
        "recommendation": ["khuyến nghị", "recommend", "đề xuất", "gợi ý"],
        "content_generation": ["viết", "tạo", "generate", "mô tả", "nội dung"],
        "text_similarity": ["tương tự", "similarity", "giống", "so sánh"],
        "clustering": ["nhóm", "cluster", "phân cụm", "phân loại"],
        "query_enhancement": ["cải thiện", "enhance", "tăng cường", "truy vấn"],
        "nutritional_analysis": ["dinh dưỡng", "nutrition", "phân tích"],
    }

    def __init__(self):
        """Khởi tạo smart prompt matcher."""
        self.extractor = PromptExtractor()

    def find_by_keywords(self, text: str) -> dict[str, float]:
        """Tìm prompts dựa trên từ khóa.

        Args:
            text: Text cần tìm kiếm.

        Returns:
            Dict[str, float]: Mapping prompt_name -> score.
        """
        text_lower = text.lower()
        scores: dict[str, float] = {}

        for prompt_name, keywords in self.KEYWORD_MAPPING.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[prompt_name] = score

        return scores

    def find_best_match(self, text: str) -> tuple[str | None, float, str]:
        """Tìm prompt phù hợp nhất sử dụng nhiều phương pháp.

        Args:
            text: Text cần tìm kiếm.

        Returns:
            Tuple[Optional[str], float, str]: (Tên prompt, Điểm, Phương pháp).
        """
        # Phương pháp 1: So sánh biến
        var_match, var_score = self.extractor.find_best_matching_prompt(text)

        # Phương pháp 2: So sánh từ khóa
        keyword_scores = self.find_by_keywords(text)

        # Kết hợp kết quả
        if var_score >= 0.5:
            return var_match, var_score, "variable_matching"

        if keyword_scores:
            best_prompt = max(keyword_scores, key=keyword_scores.get)
            best_score = keyword_scores[best_prompt]
            normalized_score = min(best_score / 5.0, 1.0)  # Normalize to 0-1
            return best_prompt, normalized_score, "keyword_matching"

        return None, 0.0, "no_match"


def extract_prompt_metadata_from_user_text(text: str) -> dict[str, Any]:
    """Hàm tiện lợi để trích xuất metadata từ text người dùng.

    Args:
        text: Text từ người dùng.

    Returns:
        Dict[str, Any]: Thông tin metadata được trích xuất.
    """
    adapter = UserPromptAdapter()
    return adapter.get_adaptation_report(text)


def find_best_prompt_for_user_text(text: str) -> tuple[str | None, float, str]:
    """Hàm tiện lợi để tìm prompt tốt nhất cho text người dùng.

    Args:
        text: Text từ người dùng.

    Returns:
        Tuple[Optional[str], float, str]: (Tên prompt, Điểm, Phương pháp).
    """
    matcher = SmartPromptMatcher()
    return matcher.find_best_match(text)


def auto_detect_and_format(user_text: str, **kwargs) -> str | None:
    """Tự động phát hiện prompt type và format.

    Args:
        user_text: Text từ người dùng.
        **kwargs: Các biến để format.

    Returns:
        Optional[str]: Formatted prompt hoặc None nếu không tìm thấy.
    """
    prompt_name, _, _ = find_best_prompt_for_user_text(user_text)

    if not prompt_name:
        return None

    try:
        template = get_factory().get_template(prompt_name)
        return template.format(**kwargs)
    except Exception as e:
        print(f"Lỗi khi format prompt: {e}")
        return None

