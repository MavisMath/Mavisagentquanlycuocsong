# BẢN ĐẶC TẢ KỸ THUẬT VÀ YÊU CẦU SẢN PHẨM (PRD)

## DỰ ÁN: MAVIS AI EXECUTIVE LIFE COACH AGENT

**Phiên bản:** 1.0 | **Ngày khởi tạo:** 06/11/2026 | **Người phê duyệt:** Mavis

## 1. TỔNG QUAN DỰ ÁN (EXECUTIVE SUMMARY)

Xây dựng một Autonomous AI Agent (Tác nhân AI Tự trị) đóng vai trò là "Elite Executive & Life Coach" độc bản cho người dùng (Mavis). Hệ thống vượt ra khỏi khái niệm To-do list truyền thống bằng cách áp dụng **Agentic Workflow**, tự động hóa toàn bộ quy trình: Phân rã mục tiêu, Lập lịch dựa trên nhịp sinh học (Energy-based Scheduling), Huấn luyện tâm lý (Socratic Coaching), và Trinh sát xu hướng công nghệ (Trend Scouting) để đón đầu dòng tiền.

## 2. NGỮ CẢNH HỆ THỐNG & CHÂN DUNG NGƯỜI DÙNG (CONTEXT & PERSONA)

Hệ thống cần được thiết lập chặt chẽ dựa trên profile của End-User (Mavis) thông qua cơ chế RAG (Retrieval-Augmented Generation):

* **Background:** Cựu sinh viên Ngoại thương, cựu nhân viên Purchasing, tư duy logic (Toán/Tin học). Từng là CEO/HR dẫn dắt team vào Top 20 toàn quốc cuộc thi SIL. Đã có kinh nghiệm Vibe Coding (App SleepSync, Web Toán 9).

* **Mục tiêu ngắn hạn (Immediate Goals):** Đạt IELTS 7.0 trong 2 tháng (sử dụng Study4); Thi đỗ chương trình tài năng AI của VinUni/Vingroup.

* **Nhịp sinh học (Biorhythm):** Não bộ hoạt động đỉnh cao vào 08:00 - 10:00 sáng. Sau 14:00 thường giảm năng lượng.

## 3. KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)

Hệ thống sử dụng kiến trúc Multi-Node Agent, bao gồm 4 Module lõi:

1. **Brain Module (Logic Engine):** LLM (khuyến nghị Gemini 1.5 Pro) xử lý NLP, Sentiment Analysis (phân tích cảm xúc) và Decision Making (đưa ra quyết định).

2. **Memory Module (Contextual RAG):** Vector Database lưu trữ 3 nhóm dữ liệu: Mục tiêu dài hạn, Nhịp sinh học, và Sổ tay Thành tựu (Achievement Ledger).

3. **Execution Module (Tool Calling):** Tích hợp Google Calendar API (Read/Write) để tìm free-slot và Time-blocking.

4. **External Data Module (Trend Scraper):** Tích hợp Web Search API (Tavily/Exa.ai) để quét tin tức công nghệ, tài chính theo thời gian thực.

## 4. CÁC LUỒNG TÍNH NĂNG CỐT LÕI (CORE WORKFLOWS)

### Feature 1: Dynamic Task Breakdown & Energy-Aware Scheduling

* **Input:** "Tôi muốn ôn IELTS Listening hôm nay."

* **Process:** Agent truy vấn RAG để biết nhịp sinh học. Phân rã task (VD: 30 phút TED Talk, 45 phút Study4). Gọi Google Calendar API quét lịch.

* **Logic:** Ép các task "High Cognitive Load" (Học AI, Code, Giải đề) vào khung giờ vàng (08:00 - 10:00). Đẩy task nhẹ xuống buổi chiều.

### Feature 2: Executive Decision Framework (Bộ lọc Chi phí cơ hội)

* **Process:** Áp dụng Chain-of-Thought. Khi User phân vân một quyết định, Agent không trả lời Yes/No mà đối chiếu với "Long-term Goals" (IELTS, VinUni) để tính toán *Opportunity Cost* và phản biện bằng phương pháp Socratic.

### Feature 3: Contextual Motivation & Pride-Activation (Giao thức Tự hào)

* **Trigger:** Cảm biến Sentiment nhận diện cảm xúc tiêu cực (chán nản, mệt mỏi, bug code).

* **Process:** Bỏ qua các lời khuyên sáo rỗng. Trích xuất `Achievement Ledger` để nhắc lại các chiến thắng quá khứ (Top 20 SIL, Tự code SleepSync) nhằm kích hoạt Dopamine. Đề xuất quy trình giảm tải (Pomodoro 15 phút).

### Feature 4: Socratic Evening Reflection (Phản tư Cuối ngày)

* **Trigger:** Cron-job lúc 22:00.

* **Process:** Đặt 2-3 câu hỏi mở đánh giá hiệu suất năng lượng trong ngày (VD: "Khung 8h sáng nay làm việc có trơn tru không?"). Phân tích câu trả lời của User để tự động cập nhật lại cơ sở dữ liệu nhịp sinh học cho những ngày tiếp theo.

### Feature 5: Autonomous Trend Scouting (Trinh sát Tiền tệ & Cơ hội)

* **Trigger:** Cron-job cuối tuần.

* **Process:** Kích hoạt Web Search API. Quét xu hướng AI, khởi nghiệp. Lọc các thông tin match với skill-set của Mavis (Python, System logic).

* **Output:** Trả về "Weekly Alpha Brief" - Phân tích dòng tiền chảy đi đâu và User cần học thêm kỹ năng gì (kèm tự động xếp lịch học skill mới đó vào Calendar).

## 5. TECH STACK (CÔNG NGHỆ LÕI) & MÔI TRƯỜNG THI CÔNG

Áp dụng phương pháp luận **"Vibe Coding"** qua các công cụ sau:

* **Workspace (Xưởng chế tác):** Sử dụng **Antigravity**. User ra lệnh bằng Tiếng Việt để AI tự động gen code.

* **Agentic Framework:** Sử dụng **LangGraph** (tối ưu cho luồng điều hướng toán học/logic game) hoặc **CrewAI**.

* **Core LLM:** Google Gemini 1.5 Pro (hoặc tương đương) có hỗ trợ Function Calling.

* **Cloud Deployment:**

  * **Backend / Agent Logic:** Đẩy lên **Render** (để chạy các tác vụ ngầm định kỳ, duy trì trạng thái).

  * **Frontend (UI/UX):** Code bằng Next.js/React hoặc Streamlit, đẩy lên **Vercel** để lấy URL public.

## 6. LỘ TRÌNH TRIỂN KHAI (IMPLEMENTATION PIPELINE)

* **Phase 1: Workspace Initialization (Tại Antigravity)**

  * Prompt: Khởi tạo project Python trống. Cài đặt `langgraph`, `google-api-python-client`, `tavily-python`. Thiết lập cấu trúc thư mục `/agents`, `/tools`, `/ui`.

* **Phase 2: Framework Assembly (Lắp ráp Đồ thị LangGraph)**

  * Prompt: Build luồng Graph với 3 Nodes: (1) Nhận lệnh & Phân tích tâm lý, (2) Lập lịch Google Calendar, (3) Tìm kiếm Web. Thiết lập Conditional Edges (Cạnh điều kiện): Nếu User mệt -> Chuyển sang Node Khích lệ tâm lý; Nếu User hỏi xu hướng -> Chuyển sang Node Search Web.

* **Phase 3: Instantiation & Deployment (Nhập thể lên Mây)**

  * Prompt: Wrap bộ core logic vào một ứng dụng web. Liên kết Git Repo với Render (Host backend) và Vercel (Host giao diện).

  * Result: Cấp phát 1 URL duy nhất để Mavis sử dụng trên Tablet.

## 7. SYSTEM INSTRUCTIONS (PROMPT LÕI CHO AGENT)

*(Sử dụng đoạn prompt này nạp vào System Role của LangGraph node)*

> "Bạn là Elite Executive & Life Coach độc quyền của Mavis. Bạn không phải trợ lý nhắc việc, bạn là một Chiến lược gia.
> Nhiệm vụ: Xây dựng lịch trình tối ưu nhịp sinh học, tập trung vào mục tiêu IELTS 7.0 và đỗ VinUni AI.
> Nguyên tắc:
>
> 1. Nếu Mavis quá tải, ép giảm tải.
>
> 2. Lịch học nặng phải rơi vào 8h-10h sáng.
>
> 3. Nếu Mavis nản, nhắc lại thành tựu từng làm CEO Top 20 SIL, tự build web Toán 9, app SleepSync để kích hoạt sự tự hào.
>
> 4. Cuối ngày, hỏi câu hỏi mở (Socratic) để Mavis tự ngẫm lại hiệu suất.
>
> 5. Cập nhật xu hướng AI để định hướng kỹ năng sinh lời cho Mavis."