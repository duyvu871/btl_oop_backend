"""Demo sử dụng PromptExtractor để LLM tự động trích xuất PromptMetadata.

Ví dụ về cách sử dụng các công cụ tự động phát hiện và trích xuất prompt.
"""

from src.ai.llm.prompt_extractor import (
    PromptAnalyzer,
    PromptExtractor,
    SmartPromptMatcher,
    UserPromptAdapter,
    auto_detect_and_format,
    extract_prompt_metadata_from_user_text,
    find_best_prompt_for_user_text,
)


def demo_basic_extraction():
    """Demo trích xuất cơ bản."""
    print("=" * 80)
    print("DEMO 1: Trích xuất cơ bản từ user prompt")
    print("=" * 80)

    # Ví dụ 1: Tìm kiếm công thức
    user_prompt_1 = """
    Hãy tìm công thức nấu ăn với:
    - query: cơm tấm
    - ingredients: thịt nướng
    - excluded_ingredients: tôm
    - cuisine_type: Việt Nam
    - difficulty_level: dễ
    - max_time: 30 phút
    - dietary_preferences: không hạn chế
    """

    report = extract_prompt_metadata_from_user_text(user_prompt_1)
    print(f"\nPrompt người dùng:\n{user_prompt_1}")
    print("\nKết quả phân tích:")
    print(f"  - Prompt được phát hiện: {report['analysis']['detected_prompt_name']}")
    print(f"  - Độ tin cậy: {report['analysis']['confidence']:.2%}")
    print(f"  - Biến được trích xuất: {report['analysis']['extracted_variables']}")
    print(f"  - Biến còn thiếu: {report['analysis']['missing_variables']}")

    # Ví dụ 2: Khuyến nghị
    user_prompt_2 = """
    Tạo 10 khuyến nghị công thức nấu ăn cho:
    - user_id: 123
    - favorite_ingredients: cà chua, tỏi
    - cuisine_preferences: Á Đông
    - skill_level: trung bình
    """

    report_2 = extract_prompt_metadata_from_user_text(user_prompt_2)
    print(f"\n\nPrompt người dùng:\n{user_prompt_2}")
    print("\nKết quả phân tích:")
    print(f"  - Prompt được phát hiện: {report_2['analysis']['detected_prompt_name']}")
    print(f"  - Độ tin cậy: {report_2['analysis']['confidence']:.2%}")
    print(f"  - Biến được trích xuất: {report_2['analysis']['extracted_variables']}")
    print(f"  - Khuyến nghị: {report_2['recommendations']}")


def demo_smart_matching():
    """Demo smart matching dựa trên từ khóa."""
    print("\n\n" + "=" * 80)
    print("DEMO 2: Smart matching dựa trên từ khóa")
    print("=" * 80)

    test_prompts = [
        "Tìm kiếm công thức nấu ăn cơm tấm",
        "Viết mô tả hấp dẫn cho món ăn",
        "Phân tích tương tự giữa hai công thức",
        "Khuyến nghị các món ăn cho người dùng",
        "Tính toán giá trị dinh dưỡng",
        "Nhóm các công thức nấu ăn tương tự",
    ]

    matcher = SmartPromptMatcher()

    for prompt in test_prompts:
        best_prompt, score, method = find_best_prompt_for_user_text(prompt)
        print(f"\nPrompt: {prompt}")
        print(f"  → Prompt được phát hiện: {best_prompt} (Phương pháp: {method})")
        print(f"  → Điểm: {score:.2%}")


def demo_analyzer():
    """Demo PromptAnalyzer chi tiết."""
    print("\n\n" + "=" * 80)
    print("DEMO 3: Phân tích chi tiết từ PromptAnalyzer")
    print("=" * 80)

    analyzer = PromptAnalyzer()

    user_prompt = """
    Hãy phân tích dinh dưỡng cho:
    - recipe_name: Bánh mì nướng thịt
    - ingredients_list: bánh mì, thịt nướng, rau
    - serving_size: 1 chiếc
    - num_servings: 1
    - target_diet: bình thường
    - allergies: không có
    - goals: khỏe mạnh
    """

    result = analyzer.analyze_user_prompt(user_prompt)

    print(f"\nPrompt: {user_prompt}")
    print("\nKết quả phân tích chi tiết:")
    print("  - Biến được trích xuất:")
    for var in result["extracted_variables"]:
        print(f"    • {var}")
    print(f"  - Prompt được phát hiện: {result['detected_prompt_name']}")
    print(f"  - Độ tin cậy: {result['confidence']:.2%}")
    if result["missing_variables"]:
        print("  - Biến còn thiếu:")
        for var in result["missing_variables"]:
            print(f"    • {var}")
    if result["suggested_prompt_info"]:
        print("  - Thông tin prompt gợi ý:")
        info = result["suggested_prompt_info"]
        print(f"    • Tên: {info['name']}")
        print(f"    • Mô tả: {info['description']}")
        print(f"    • Use case: {info['use_case']}")


def demo_extractor():
    """Demo PromptExtractor trích xuất biến."""
    print("\n\n" + "=" * 80)
    print("DEMO 4: Trích xuất biến từ text")
    print("=" * 80)

    extractor = PromptExtractor()

    test_texts = [
        "Tìm công thức với {query} và {ingredients}",
        "Phân tích {text1} so với {text2}",
        "Tạo nội dung {content_type} cho {recipe_name}",
    ]

    for text in test_texts:
        variables = extractor.extract_variables(text)
        print(f"\nText: {text}")
        print(f"Biến được trích xuất: {variables}")


def demo_auto_format():
    """Demo auto detect và format."""
    print("\n\n" + "=" * 80)
    print("DEMO 5: Auto detect và format")
    print("=" * 80)

    user_text = "Tìm kiếm {query} với {ingredients}"

    best_prompt, confidence, method = find_best_prompt_for_user_text(user_text)
    print(f"\nUser text: {user_text}")
    print(f"Prompt detected: {best_prompt}")
    print(f"Confidence: {confidence:.2%}")
    print(f"Method: {method}")

    # Format với biến
    if best_prompt == "recipe_retrieval":
        formatted = auto_detect_and_format(
            user_text,
            query="cơm tấm",
            ingredients="thịt nướng",
            excluded_ingredients="tôm",
            cuisine_type="Việt Nam",
            difficulty_level="dễ",
            max_time="30 phút",
            dietary_preferences="không hạn chế"
        )
        print(f"\nFormatted prompt (first 200 chars):\n{formatted[:200]}...")


def demo_adapter():
    """Demo UserPromptAdapter."""
    print("\n\n" + "=" * 80)
    print("DEMO 6: UserPromptAdapter - Chuyển đổi user prompt")
    print("=" * 80)

    adapter = UserPromptAdapter()

    user_prompt = """
    Hãy viết nội dung về công thức nấu ăn:
    - content_type: mô tả
    - recipe_name: Phở Hà Nội
    - ingredients: gà, hành
    - cuisine_type: Việt Nam
    - difficulty: dễ
    - cooking_time: 1 giờ
    - servings: 4 người
    - length: 500 từ
    - include_sections: hướng dẫn, mẹo
    - target_audience: gia đình
    - tone: thân thiện
    - recipe_details: nước dùng từ gà
    """

    report = adapter.get_adaptation_report(user_prompt)

    print(f"\nUser prompt: {user_prompt[:100]}...")
    print("\nBáo cáo chuyển đổi:")
    print(f"  - Detected prompt: {report['analysis']['detected_prompt_name']}")
    print(f"  - Confidence: {report['analysis']['confidence']:.2%}")
    print("  - Recommendations:")
    for rec in report['recommendations']:
        print(f"    • {rec}")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "DEMO: LLM Auto Extract PromptMetadata" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")

    demo_basic_extraction()
    demo_smart_matching()
    demo_analyzer()
    demo_extractor()
    demo_auto_format()
    demo_adapter()

    print("\n\n" + "=" * 80)
    print("Tất cả demos đã hoàn tất!")
    print("=" * 80)

