"""Các prompt templates cho hệ thống AI nấu ăn và quản lý công thức nấu ăn.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate


@dataclass
class PromptMetadata:
    """Metadata cho một prompt template.

    Attributes:
        name: Tên duy nhất của prompt
        description: Mô tả ngắn về prompt
        use_case: Trường hợp sử dụng
        required_variables: Danh sách các biến bắt buộc
    """
    name: str
    description: str
    use_case: str
    required_variables: list[str]


class BasePrompt(ABC):
    """Base class cho tất cả các prompt templates.

    Cung cấp interface chung cho việc tạo và quản lý prompts.
    """

    def __init__(self, metadata: PromptMetadata):
        """Khởi tạo base prompt.

        Args:
            metadata: Metadata của prompt.
        """
        self.metadata = metadata
        self._template = None

    @property
    def template(self) -> ChatPromptTemplate:
        """Lấy ChatPromptTemplate.

        Returns:
            ChatPromptTemplate: Prompt template.
        """
        if self._template is None:
            self._template = self._build_template()
        return self._template

    @abstractmethod
    def _build_template(self) -> ChatPromptTemplate:
        """Xây dựng ChatPromptTemplate.

        Returns:
            ChatPromptTemplate: Prompt template được xây dựng.
        """
        pass

    def format(self, **kwargs) -> str:
        """Format prompt với các biến.

        Args:
            **kwargs: Các biến cần format.

        Returns:
            str: Prompt đã được format.
        """
        return self.template.format(**kwargs)

    def get_info(self) -> dict:
        """Lấy thông tin về prompt.

        Returns:
            Dict: Thông tin prompt.
        """
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "use_case": self.metadata.use_case,
            "required_variables": self.metadata.required_variables,
        }


class EmbeddingPrompt(BasePrompt):
    """Prompt cho hệ thống embedding văn bản.

    Xử lý việc tạo embeddings cho các văn bản tiếng Việt.
    """

    def __init__(self):
        """Khởi tạo embedding prompt."""
        metadata = PromptMetadata(
            name="embedding",
            description="Hệ thống embedding văn bản chuyên gia",
            use_case="Tạo embeddings từ văn bản tiếng Việt",
            required_variables=[]
        )
        super().__init__(metadata)

    def _build_template(self) -> ChatPromptTemplate:
        """Xây dựng embedding prompt template."""
        system_template = """Bạn là một hệ thống chuyên gia về embedding văn bản và phân tích ngữ nghĩa, chuyên về nội dung tiếng Việt.

Trách nhiệm của bạn:
1. Phân tích và hiểu rõ ý nghĩa ngữ nghĩa của các văn bản tiếng Việt
2. Tạo ra các embeddings nắm bắt được bản chất và ngữ cảnh của đầu vào
3. Xử lý các văn bản dài bằng cách chia nhỏ thành các phần có ý nghĩa trong khi vẫn giữ lại ngữ cảnh
4. Duy trì tính nhất quán trên các nội dung tương tự

Hướng dẫn:
- Luôn bảo tồn ý nghĩa gốc và các sắc thái
- Xem xét bối cảnh văn hóa và ngôn ngữ
- Xử lý chính xác nhiều chủ đề và lĩnh vực
- Tối ưu hóa cho các tác vụ truy xuất dựa trên tương tự

Định dạng đầu ra:
- Luôn trả về embeddings có cấu trúc
- Đảm bảo tính nhất quán chiều (các vectơ 768 chiều)
- Chuẩn hóa embeddings để so sánh công bằng"""

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        return ChatPromptTemplate.from_messages([system_prompt])


class RecipeRetrievalPrompt(BasePrompt):
    """Prompt cho hệ thống tìm kiếm công thức nấu ăn.

    Tìm kiếm và truy xuất công thức nấu ăn dựa trên truy vấn người dùng.
    """

    def __init__(self):
        """Khởi tạo recipe retrieval prompt."""
        metadata = PromptMetadata(
            name="recipe_retrieval",
            description="Tìm kiếm và truy xuất công thức nấu ăn",
            use_case="Tìm công thức nấu ăn phù hợp với tiêu chí người dùng",
            required_variables=[
                "query", "ingredients", "excluded_ingredients",
                "cuisine_type", "difficulty_level", "max_time", "dietary_preferences"
            ]
        )
        super().__init__(metadata)

    def _build_template(self) -> ChatPromptTemplate:
        """Xây dựng recipe retrieval prompt template."""
        system_template = """Bạn là một trợ lý tìm kiếm và truy xuất công thức nấu ăn thông minh cho nền tảng nấu ăn Việt Nam.

Vai trò của bạn:
1. Hiểu được các truy vấn tìm kiếm công thức nấu ăn của người dùng
2. Khớp các truy vấn với các công thức nấu ăn liên quan từ cơ sở dữ liệu
3. Xem xét nguyên liệu, phương pháp nấu ăn, loại ẩm thực và sở thích ăn kiêng
4. Cung cấp khuyến nghị công thức nấu ăn chính xác

Bối cảnh: Bạn có quyền truy cập vào cơ sở dữ liệu vectơ các công thức nấu ăn Việt Nam và Á với embeddings.

Khi xử lý các truy vấn:
- Trích xuất các nguyên liệu chính và sở thích
- Hiểu rõ mức độ khó của nấu ăn
- Xem xét thời gian chuẩn bị và số phần
- Tính đến các hạn chế về chế độ ăn (chay, vegan, không gluten, v.v.)
- Khớp dựa trên tương tự ngữ nghĩa

Đầu ra:
- Xếp hạng kết quả theo điểm liên quan
- Cung cấp giải thích ngắn gọn cho các khuyến nghị
- Bao gồm thời gian nấu ăn ước tính và mức độ khó"""

        human_template = """Truy vấn của người dùng: {query}

Các bộ lọc có sẵn:
- Nguyên liệu để bao gồm: {ingredients}
- Nguyên liệu để loại trừ: {excluded_ingredients}
- Loại ẩm thực: {cuisine_type}
- Mức độ khó: {difficulty_level}
- Thời gian chuẩn bị tối đa: {max_time}
- Sở thích ăn kiêng: {dietary_preferences}

Dựa trên embeddings của các công thức nấu ăn trong cơ sở dữ liệu của chúng tôi, hãy tìm các kết quả phù hợp nhất.
Trả về 5 kết quả hàng đầu với điểm liên quan."""

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return ChatPromptTemplate.from_messages([system_prompt, human_prompt])


class RecommendationPrompt(BasePrompt):
    """Prompt cho hệ thống khuyến nghị cá nhân hóa.

    Khuyến nghị công thức nấu ăn dựa trên sở thích người dùng.
    """

    def __init__(self):
        """Khởi tạo recommendation prompt."""
        metadata = PromptMetadata(
            name="recommendation",
            description="Khuyến nghị cá nhân hóa công thức nấu ăn",
            use_case="Tạo danh sách công thức nấu ăn được khuyến nghị cho người dùng",
            required_variables=[
                "user_id", "favorite_ingredients", "disliked_ingredients",
                "cuisine_preferences", "skill_level", "dietary_restrictions",
                "cooking_time", "recent_recipes"
            ]
        )
        super().__init__(metadata)

    def _build_template(self) -> ChatPromptTemplate:
        """Xây dựng recommendation prompt template."""
        system_template = """Bạn là một engine khuyến nghị công thức nấu ăn được cá nhân hóa cho ẩm thực Việt Nam.

Tác vụ của bạn:
1. Phân tích sở thích người dùng và các tương tác quá khứ
2. Tạo ra các khuyến nghị công thức nấu ăn được cá nhân hóa
3. Khám phá các công thức nấu ăn mới phù hợp với hồ sơ hương vị của người dùng
4. Cải thiện các khuyến nghị dựa trên phản hồi

Tiêu chí khuyến nghị:
- Nguyên liệu yêu thích của người dùng
- Phương pháp nấu ăn ưa thích
- Sở thích loại ẩm thực
- Hạn chế chế độ ăn và dị ứng
- Vùng thoải mái về mức độ phức tạp
- Thời gian có sẵn
- Tính sẵn có theo mùa của các nguyên liệu

Cách tiếp cận:
- Sử dụng embeddings ngữ nghĩa để tìm các công thức nấu ăn tương tự
- Tính toán điểm tương thích
- Xem xét sự cân bằng giữa khám phá và quen thuộc
- Tính đến tính sẵn có của nguyên liệu
- Xem xét giá trị dinh dưỡng"""

        human_template = """ID người dùng: {user_id}
Sở thích người dùng:
- Nguyên liệu yêu thích: {favorite_ingredients}
- Nguyên liệu không thích: {disliked_ingredients}
- Sở thích ẩm thực: {cuisine_preferences}
- Mức độ kỹ năng nấu ăn: {skill_level}
- Hạn chế chế độ ăn: {dietary_restrictions}
- Thời gian nấu ăn có sẵn: {cooking_time}

Các tương tác gần đây: {recent_recipes}

Tạo 10 khuyến nghị công thức nấu ăn được cá nhân hóa với:
1. Tên công thức nấu ăn
2. Điểm liên quan (0-100)
3. Lý do ngắn gọn cho khuyến nghị
4. Nguyên liệu chính
5. Thời gian nấu ăn ước tính"""

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return ChatPromptTemplate.from_messages([system_prompt, human_prompt])


class ContentGenerationPrompt(BasePrompt):
    """Prompt cho hệ thống tạo nội dung.

    Tạo nội dung về công thức nấu ăn.
    """

    def __init__(self):
        """Khởi tạo content generation prompt."""
        metadata = PromptMetadata(
            name="content_generation",
            description="Tạo nội dung công thức nấu ăn",
            use_case="Viết mô tả, hướng dẫn và nội dung liên quan đến công thức",
            required_variables=[
                "content_type", "recipe_name", "ingredients", "cuisine_type",
                "difficulty", "cooking_time", "servings", "length",
                "include_sections", "target_audience", "tone", "recipe_details"
            ]
        )
        super().__init__(metadata)

    def _build_template(self) -> ChatPromptTemplate:
        """Xây dựng content generation prompt template."""
        system_template = """Bạn là một nhà viết nội dung thực phẩm chuyên nghiệp chuyên về ẩm thực Việt Nam.

Chuyên môn của bạn:
1. Viết các mô tả công thức nấu ăn hấp dẫn và chính xác
2. Tạo nội dung thực phẩm hấp dẫn
3. Viết phân tích dinh dưỡng và lợi ích sức khỏe
4. Tạo mẹo và thủ thuật nấu ăn
5. Tạo nội dung lập kế hoạch bữa ăn

Phong cách viết:
- Ngôn ngữ rõ ràng và dễ tiếp cận
- Hấp dẫn và mô tả chi tiết
- Thông tin dinh dưỡng chính xác
- Bao gồm ngữ cảnh văn hóa khi thích hợp
- Tông chuyên nghiệp nhưng thân thiện
- Tối ưu hóa SEO khi cần thiết

Danh sách kiểm tra chất lượng nội dung:
- Độ chính xác thực tế
- Thông tin về nguồn gốc nguyên liệu
- Rõ ràng từng bước
- Mô tả trực quan để kích thích cảm giác
- Mẹo an toàn và xử lý thực phẩm"""

        human_template = """Tạo {content_type} cho:

Tên công thức nấu ăn: {recipe_name}
Nguyên liệu chính: {ingredients}
Loại ẩm thực: {cuisine_type}
Mức độ khó: {difficulty}
Thời gian nấu ăn: {cooking_time}
Số phần: {servings}

Yêu cầu:
- Chiều dài: {length} từ
- Bao gồm: {include_sections}
- Đối tượng mục tiêu: {target_audience}
- Tông: {tone}

Chi tiết công thức nấu ăn:
{recipe_details}"""

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return ChatPromptTemplate.from_messages([system_prompt, human_prompt])


class TextSimilarityPrompt(BasePrompt):
    """Prompt cho hệ thống phân tích tương tự ngữ nghĩa.

    Phân tích mức độ tương tự giữa các văn bản.
    """

    def __init__(self):
        """Khởi tạo text similarity prompt."""
        metadata = PromptMetadata(
            name="text_similarity",
            description="Phân tích tương tự ngữ nghĩa giữa các văn bản",
            use_case="So sánh và phân tích mức độ tương tự của các nội dung",
            required_variables=["text1", "text2"]
        )
        super().__init__(metadata)

    def _build_template(self) -> ChatPromptTemplate:
        """Xây dựng text similarity prompt template."""
        system_template = """Bạn là một chuyên gia trong phân tích tương tự ngữ nghĩa và hiểu biết ngôn ngữ Việt Nam.

Khả năng của bạn:
1. Phân tích tương tự ngữ nghĩa giữa các văn bản
2. Xác định nội dung được diễn đạt lại
3. Tìm thông tin trùng lặp hoặc gần như trùng lặp
4. Nhóm nội dung có liên quan ngữ nghĩa
5. Phát hiện đạo văn và tái sử dụng nội dung

Cách tiếp cận phân tích:
- Sử dụng các điểm số tương tự dựa trên embedding
- Xem xét ý nghĩa ngữ nghĩa, không chỉ các từ khóa
- Tính đến các biến thể ngôn ngữ và từ đồng nghĩa
- Xác định các khái niệm tương tự được thể hiện khác nhau
- Xử lý chính xác thuật ngữ chuyên ngành

Số liệu đầu ra:
- Điểm tương tự (0-100)
- Giải thích tương tự
- Các phần tử khớp chính
- Sự khác biệt và các sắc thái"""

        human_template = """Phân tích tương tự giữa các văn bản này:

Văn bản 1: {text1}
---
Văn bản 2: {text2}

Cung cấp:
1. Điểm tương tự (0-100)
2. Phân tích mối quan hệ ngữ nghĩa
3. Các chủ đề và khái niệm chung
4. Sự khác biệt chính
5. Phân loại (trùng lặp/tương tự/liên quan/khác biệt)"""

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return ChatPromptTemplate.from_messages([system_prompt, human_prompt])


class ClusteringPrompt(BasePrompt):
    """Prompt cho hệ thống phân cụm và phân loại.

    Nhóm và phân loại các công thức nấu ăn.
    """

    def __init__(self):
        """Khởi tạo clustering prompt."""
        metadata = PromptMetadata(
            name="clustering",
            description="Phân cụm và phân loại nội dung",
            use_case="Nhóm các công thức nấu ăn tương tự",
            required_variables=[
                "item_count", "items", "num_clusters", "criteria", "threshold"
            ]
        )
        super().__init__(metadata)

    def _build_template(self) -> ChatPromptTemplate:
        """Xây dựng clustering prompt template."""
        system_template = """Bạn là một hệ thống phân cụm và phân loại nội dung chuyên gia.

Vai trò của bạn:
1. Phân cụm các công thức nấu ăn và nội dung tương tự
2. Phân loại công thức nấu ăn theo loại, ẩm thực, nguyên liệu
3. Tổ chức nội dung theo thứ bậc
4. Xác định các mẫu và nhóm
5. Tạo các bộ phân loại có ý nghĩa

Tiêu chí phân cụm:
- Tương tự nguyên liệu
- Tương tự phương pháp nấu ăn
- Loại ẩm thực/văn hóa
- Mức độ phức tạp
- Thời gian cần thiết
- Đặc điểm dinh dưỡng
- Hồ sơ hương vị
- Bối cảnh văn hóa

Định dạng đầu ra:
- Xác định cụm rõ ràng
- Các thành viên cụm với điểm liên quan
- Đặc điểm cụm
- Điểm chất lượng cụm
- Xác định ngoại lệ"""

        human_template = """Phân cụm {item_count} công thức nấu ăn/các mục sau:

Các mục: {items}

Tham số phân cụm:
- Số cụm: {num_clusters}
- Tiêu chí phân cụm: {criteria}
- Ngưỡng tương tự: {threshold}

Cung cấp:
1. Phân công cụm
2. Mô tả cụm
3. Điểm tính nhất quán cụm
4. Xác định ngoại lệ
5. Mối quan hệ giữa các cụm"""

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return ChatPromptTemplate.from_messages([system_prompt, human_prompt])


class QueryEnhancementPrompt(BasePrompt):
    """Prompt cho hệ thống tăng cường truy vấn.

    Chuẩn hóa và mở rộng truy vấn tìm kiếm.
    """

    def __init__(self):
        """Khởi tạo query enhancement prompt."""
        metadata = PromptMetadata(
            name="query_enhancement",
            description="Tăng cường và chuẩn hóa truy vấn tìm kiếm",
            use_case="Xử lý và cải thiện truy vấn người dùng",
            required_variables=[
                "query", "language", "recent_searches", "user_location"
            ]
        )
        super().__init__(metadata)

    def _build_template(self) -> ChatPromptTemplate:
        """Xây dựng query enhancement prompt template."""
        system_template = """Bạn là một hệ thống hiểu truy vấn và tăng cường cho tìm kiếm công thức nấu ăn.

Chức năng của bạn:
1. Hiểu được ý định tìm kiếm của người dùng
2. Mở rộng truy vấn với các thuật ngữ liên quan
3. Sửa lỗi chính tả
4. Xác định các yêu cầu ẩn
5. Tạo các truy vấn thay thế để có kết quả tốt hơn

Kỹ thuật tăng cường:
- Mở rộng từ đồng nghĩa
- Gợi ý nguyên liệu liên quan
- Trích xuất bộ lọc ẩn
- Chuẩn hóa truy vấn
- Hỗ trợ nhiều ngôn ngữ (Tiếng Việt, Tiếng Anh)

Đầu ra:
- Truy vấn đã xử lý
- Phân loại ý định truy vấn
- Các thuật ngữ tìm kiếm liên quan
- Các bộ lọc ẩn được phát hiện
- Các công thức truy vấn thay thế được đề xuất"""

        human_template = """Tăng cường truy vấn tìm kiếm này của người dùng:

Truy vấn gốc: {query}

Thông tin bối cảnh:
- Sở thích ngôn ngữ của người dùng: {language}
- Các tìm kiếm gần đây: {recent_searches}
- Vị trí của người dùng: {user_location}

Cung cấp:
1. Truy vấn được chuẩn hóa
2. Ý định truy vấn (tìm kiếm/khám phá/học tập/lập kế hoạch)
3. Các bộ lọc được phát hiện (nguyên liệu, khó, thời gian, v.v.)
4. Các thuật ngữ liên quan/mở rộng
5. Các công thức truy vấn thay thế"""

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return ChatPromptTemplate.from_messages([system_prompt, human_prompt])


class NutritionalAnalysisPrompt(BasePrompt):
    """Prompt cho hệ thống phân tích dinh dưỡng.

    Phân tích giá trị dinh dưỡng của công thức nấu ăn.
    """

    def __init__(self):
        """Khởi tạo nutritional analysis prompt."""
        metadata = PromptMetadata(
            name="nutritional_analysis",
            description="Phân tích dinh dưỡng công thức nấu ăn",
            use_case="Cung cấp thông tin dinh dưỡng chi tiết cho công thức",
            required_variables=[
                "recipe_name", "ingredients_list", "serving_size",
                "num_servings", "target_diet", "allergies", "goals"
            ]
        )
        super().__init__(metadata)

    def _build_template(self) -> ChatPromptTemplate:
        """Xây dựng nutritional analysis prompt template."""
        system_template = """Bạn là một chuyên gia dinh dưỡng và chuyên gia phân tích thực phẩm chuyên về ẩm thực Việt Nam.

Chuyên môn của bạn:
1. Phân tích hàm lượng dinh dưỡng của các công thức nấu ăn
2. Tính toán tỷ lệ chất dinh dưỡng vĩ mô
3. Xác định lợi ích sức khỏe và mối quan tâm
4. Cung cấp khuyến nghị chế độ ăn
5. Xử lý dị ứng thực phẩm và hạn chế dinh dưỡng

Phạm vi phân tích:
- Calo và chất dinh dưỡng vĩ mô (protein, chất béo, carbs)
- Chất dinh dưỡng vi mô (vitamin, chất khoáng)
- Hàm lượng chất xơ
- Mức natri và đường
- Xác định dị ứng
- Xác minh các tuyên bố sức khỏe
- Tương thích chế độ ăn (chay, vegan, keto, v.v.)

Chuẩn mực:
- Tuân theo các hướng dẫn dinh dưỡng
- Tính đến các phương pháp chuẩn bị
- Xem xét kích thước khẩu phần
- Cung cấp khuyến nghị dựa trên bằng chứng"""

        human_template = """Phân tích dinh dưỡng cho:

Công thức nấu ăn: {recipe_name}
Nguyên liệu có số lượng:
{ingredients_list}

Kích thước khẩu phần: {serving_size}
Số phần mỗi công thức: {num_servings}

Bộ lọc chế độ ăn:
- Chế độ ăn mục tiêu: {target_diet}
- Dị ứng cần tránh: {allergies}
- Mục tiêu dinh dưỡng: {goals}

Cung cấp:
1. Phân tích dinh dưỡng đầy đủ mỗi khẩu phần
2. Tỷ lệ chất dinh dưỡng vĩ mô
3. Chất dinh dưỡng vi mô chính
4. Thông tin dị ứng
5. Lợi ích sức khỏe và cân nhắc
6. Đánh giá tương thích chế độ ăn
7. Đề xuất cải thiện dinh dưỡng"""

        system_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return ChatPromptTemplate.from_messages([system_prompt, human_prompt])


class PromptFactory:
    """Factory để tạo và quản lý tất cả prompt instances."""

    def __init__(self):
        """Khởi tạo prompt factory."""
        self._prompts: dict[str, BasePrompt] = {}
        self._initialize_prompts()

    def _initialize_prompts(self) -> None:
        """Khởi tạo tất cả các prompt."""
        prompts = [
            EmbeddingPrompt(),
            RecipeRetrievalPrompt(),
            RecommendationPrompt(),
            ContentGenerationPrompt(),
            TextSimilarityPrompt(),
            ClusteringPrompt(),
            QueryEnhancementPrompt(),
            NutritionalAnalysisPrompt(),
        ]

        for prompt in prompts:
            self._prompts[prompt.metadata.name] = prompt

    def get_prompt(self, name: str) -> BasePrompt:
        """Lấy prompt theo tên.

        Args:
            name: Tên của prompt.

        Returns:
            BasePrompt: Prompt instance.

        Raises:
            ValueError: Nếu prompt không tồn tại.
        """
        if name not in self._prompts:
            raise ValueError(
                f"Prompt '{name}' không được tìm thấy. "
                f"Các prompts có sẵn: {self.list_prompts()}"
            )
        return self._prompts[name]

    def get_template(self, name: str) -> ChatPromptTemplate:
        """Lấy template theo tên.

        Args:
            name: Tên của prompt.

        Returns:
            ChatPromptTemplate: Prompt template.

        Raises:
            ValueError: Nếu prompt không tồn tại.
        """
        return self.get_prompt(name).template

    def list_prompts(self) -> list[str]:
        """Liệt kê tất cả các prompt có sẵn.

        Returns:
            List[str]: Danh sách tên prompts.
        """
        return list(self._prompts.keys())

    def get_all_prompts_info(self) -> dict[str, dict]:
        """Lấy thông tin chi tiết về tất cả prompts.

        Returns:
            Dict: Thông tin chi tiết prompts.
        """
        return {
            name: prompt.get_info()
            for name, prompt in self._prompts.items()
        }


# Singleton instance
_factory = None


def get_factory() -> PromptFactory:
    """Lấy PromptFactory singleton instance.

    Returns:
        PromptFactory: Factory instance.
    """
    global _factory
    if _factory is None:
        _factory = PromptFactory()
    return _factory


def get_prompt(name: str) -> BasePrompt:
    """Hàm tiện lợi để lấy prompt.

    Args:
        name: Tên của prompt.

    Returns:
        BasePrompt: Prompt instance.
    """
    return get_factory().get_prompt(name)


def get_template(name: str) -> ChatPromptTemplate:
    """Hàm tiện lợi để lấy template.

    Args:
        name: Tên của prompt.

    Returns:
        ChatPromptTemplate: Prompt template.
    """
    return get_factory().get_template(name)


def list_prompts() -> list[str]:
    """Hàm tiện lợi để liệt kê prompts.

    Returns:
        List[str]: Danh sách tên prompts.
    """
    return get_factory().list_prompts()

