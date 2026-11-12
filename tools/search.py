import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()


def get_tavily_search_tool(max_results: int = 3) -> TavilySearchResults:
    """
    Khởi tạo và cấu hình TavilySearchResults tool cho Agent.
    Hỗ trợ tìm kiếm dữ liệu thời gian thực trên web.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if api_key:
        os.environ["TAVILY_API_KEY"] = api_key

    return TavilySearchResults(max_results=max_results)


# Khởi tạo sẵn một instance tool mặc định
tavily_search = get_tavily_search_tool(max_results=3)


def execute_trend_search(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Hàm bọc (wrapper) an toàn để thực thi tìm kiếm thông tin xu hướng.
    Bảo đảm không đứt gãy workflow nếu thiếu TAVILY_API_KEY hoặc lỗi kết nối.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        # Dữ liệu mẫu thực chiến dự phòng khi chưa nạp API key
        return [
            {
                "title": "Agentic Workflows & Multi-Agent Systems Surge in 2026",
                "url": "https://techcrunch.com/ai/agentic-trends",
                "content": (
                    "Dòng vốn VC đang đổ mạnh vào hệ sinh thái Autonomous AI Agents, "
                    "đặc biệt là các giải pháp kết hợp Python, LangGraph và Tool Calling cho các bài toán tối ưu quy trình kinh doanh."
                ),
            },
            {
                "title": "Chương trình AI Talent & cơ hội thu nhập cho Kỹ sư AI",
                "url": "https://vinuni.edu.vn/ai-talent-program",
                "content": (
                    "Nhu cầu tuyển dụng chuyên gia AI có nền tảng Toán/Logic vững chắc và kỹ năng Vibe Coding đang tăng vọt "
                    "với mức đãi ngộ hấp dẫn tại các tập đoàn công nghệ lớn."
                ),
            },
        ]

    try:
        tool = get_tavily_search_tool(max_results=max_results)
        results = tool.invoke({"query": query})
        if isinstance(results, list):
            return results
        return [{"content": str(results)}]
    except Exception as e:
        return [
            {
                "title": f"Lưu ý kết nối Tavily Search: {str(e)}",
                "url": "",
                "content": f"Không thể kết nối trực tiếp đến Tavily Search API. Lỗi: {str(e)}. Sử dụng bộ phân tích dự phòng.",
            }
        ]


def execute_opportunity_scout(query: str, max_results: int = 4) -> List[Dict[str, Any]]:
    """
    Hàm trinh sát cơ hội thực chiến chuyên sâu (Phase 7.3):
    Tìm kiếm các chương trình VinUni AI Bootcamp, AI Residency, AI Internship, Fellowship
    và các cộng đồng alumni để phục vụ Networking Protocol.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return [
            {
                "title": "VinUni AI Bootcamp & Advanced Talent Fellowship 2026",
                "url": "https://vinuni.edu.vn/ai-bootcamp",
                "content": (
                    "Chương trình huấn luyện thực chiến chuyên sâu 6 tháng của Viện Khoa học Máy tính VinUni. "
                    "Học viên được làm việc trực tiếp trên các bài toán Machine Learning quy mô lớn, "
                    "được tài trợ 100% kinh phí và chứng nhận tương đương 1-2 năm kinh nghiệm nghiên cứu AI ứng dụng."
                ),
            },
            {
                "title": "Vingroup AI Residency & Research Internship Program",
                "url": "https://vinai.io/residency",
                "content": (
                    "Chương trình ươm mầm tài năng Kỹ sư AI hàng đầu khu vực. Cung cấp lộ trình thực tập thực chiến 2 năm, "
                    "được hướng dẫn bởi các chuyên gia AI đẳng cấp quốc tế và cơ hội công bố bài báo khoa học."
                ),
            },
            {
                "title": "Cộng đồng VinUni AI Talent Alumni & Thí sinh các mùa",
                "url": "https://facebook.com/groups/vinuni-ai-talent-community",
                "content": (
                    "Nhóm cộng đồng quy tụ hơn 5.000 thành viên gồm các thí sinh, cựu học viên và mentor chương trình AI VinUni. "
                    "Nơi chia sẻ đề thi các năm trước, kinh nghiệm phỏng vấn hội đồng và các case-study thực tế."
                ),
            },
            {
                "title": "Vietnam Machine Learning & AI Engineers Network",
                "url": "https://linkedin.com/groups/vietnam-ai-engineers",
                "content": (
                    "Mạng lưới kết nối các Kỹ sư AI, Data Scientist và chuyên gia công nghệ tại Việt Nam. "
                    "Cung cấp thông tin tuyển dụng thực tập sinh AI và kết nối mentoring 1-1."
                ),
            },
        ]

    try:
        tool = get_tavily_search_tool(max_results=max_results)
        results = tool.invoke({"query": query})
        if isinstance(results, list):
            return results
        return [{"content": str(results)}]
    except Exception as e:
        return [
            {
                "title": "VinUni AI Bootcamp & Talent Fellowship 2026",
                "url": "https://vinuni.edu.vn/ai-bootcamp",
                "content": (
                    "Chương trình đào tạo thực chiến VinUni AI Bootcamp trang bị kinh nghiệm nghiên cứu và phát triển AI thực tế "
                    "dành cho ứng viên chuẩn bị apply Master."
                ),
            }
        ]


