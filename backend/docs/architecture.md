# Kiến trúc hệ thống

Tài liệu này mô tả kiến trúc tổng thể của hệ thống, bao gồm các thành phần chính và cách chúng tương tác với nhau. Hệ thống được thiết kế theo kiến trúc microservices, được quản lý và điều phối bằng Docker Compose.

## Sơ đồ kiến trúc

```mermaid
graph TD
    subgraph "Client"
        User[<i class="fa fa-user"></i> Người dùng]
    end

    subgraph "Hệ thống"
        Frontend[Frontend (React/Vite) <br> Port: 5000]
        FastAPI[Backend API (FastAPI) <br> Port: 8000]
        Worker[Worker (ARQ)]
        Postgres[PostgreSQL <br> Port: 5441]
        Redis[Redis <br> Port: 6579]
        Qdrant[Qdrant (Vector DB) <br> Port: 6333]
    end

    User --> Frontend
    Frontend --> FastAPI
    FastAPI --> Postgres
    FastAPI --> Redis
    FastAPI --> Qdrant
    FastAPI --> Worker
    Worker --> Redis
    Worker --> Postgres
```

## Các thành phần chính

Hệ thống bao gồm các service sau, được định nghĩa trong `docker-compose.prod.yml`:

### 1. Frontend (`frontend`)

- **Công nghệ:** React (sử dụng Vite) và Nginx để phục vụ các file tĩnh.
- **Vai trò:** Cung cấp giao diện người dùng (UI) cho ứng dụng. Người dùng tương tác trực tiếp với service này qua trình duyệt.
- **Tương tác:**
  - Giao tiếp với **Backend API (`fastapi`)** để lấy dữ liệu, xác thực và thực hiện các nghiệp vụ.
  - Được build thành các file tĩnh và phục vụ bởi Nginx.

### 2. Backend API (`fastapi`)

- **Công nghệ:** FastAPI (Python).
- **Vai trò:** Là service trung tâm, xử lý toàn bộ logic nghiệp vụ, quản lý dữ liệu và xác thực người dùng.
- **Tương tác:**
  - Nhận request từ **Frontend**.
  - Lưu trữ và truy xuất dữ liệu chính từ **PostgreSQL**.
  - Sử dụng **Redis** cho việc caching và làm message queue cho **Worker**.
  - Tương tác với **Qdrant** để thực hiện các chức năng tìm kiếm ngữ nghĩa hoặc các tác vụ AI khác.
  - Đẩy các tác vụ tốn thời gian (như gửi email) vào hàng đợi (queue) để **Worker** xử lý.

### 3. Worker (`worker_send_mail`)

- **Công nghệ:** ARQ (Python), chạy trên cùng một image với `fastapi`.
- **Vai trò:** Xử lý các tác vụ nền (background tasks) một cách bất đồng bộ để không làm block API chính. Ví dụ điển hình là gửi email xác thực, thông báo, hoặc xử lý dữ liệu lớn.
- **Tương tác:**
  - Lắng nghe các job mới từ hàng đợi trên **Redis**.
  - Có thể truy cập **PostgreSQL** để đọc hoặc ghi dữ liệu liên quan đến tác vụ đang xử lý.
  - Giao tiếp với các dịch vụ bên ngoài (ví dụ: SMTP server để gửi email).

### 4. PostgreSQL (`postgres`)

- **Công nghệ:** PostgreSQL.
- **Vai trò:** Là cơ sở dữ liệu quan hệ chính của hệ thống. Lưu trữ dữ liệu có cấu trúc như thông tin người dùng, sản phẩm, v.v.
- **Tương tác:**
  - Được truy cập chủ yếu bởi **Backend API** và **Worker**.

### 5. Redis (`redis`)

- **Công nghệ:** Redis.
- **Vai trò:**
  1. **Message Broker:** Hoạt động như một hàng đợi (queue) cho ARQ, giúp kết nối giữa **Backend API** và **Worker**.
  2. **Caching:** Lưu trữ các dữ liệu thường xuyên truy cập để giảm tải cho **PostgreSQL** và tăng tốc độ phản hồi của API.
  3. **Rate Limiting:** Dùng để theo dõi và giới hạn số lượng request từ người dùng trong một khoảng thời gian nhất định.
- **Tương tác:**
  - Được sử dụng bởi **Backend API** và **Worker**.

### 6. Qdrant (`qdrant`)

- **Công nghệ:** Qdrant.
- **Vai trò:** Là một cơ sở dữ liệu vector, chuyên dụng cho việc lưu trữ và tìm kiếm các vector embedding. Được sử dụng cho các tính năng liên quan đến AI như tìm kiếm ngữ nghĩa, gợi ý sản phẩm, v.v.
- **Tương tác:**
  - **Backend API** sẽ tạo và lưu các vector vào Qdrant, cũng như gửi các truy vấn tìm kiếm vector đến service này.

## Luồng hoạt động (Ví dụ: Đăng ký tài khoản)

1. **Người dùng** điền thông tin đăng ký trên **Frontend**.
2. **Frontend** gửi một API request đến endpoint `/register` của **Backend API**.
3. **Backend API**:
   - Validate dữ liệu đầu vào.
   - Kiểm tra xem email đã tồn tại trong **PostgreSQL** chưa.
   - Nếu chưa, tạo một record người dùng mới trong **PostgreSQL**.
   - Đẩy một job "gửi email xác thực" vào hàng đợi trên **Redis**.
   - Trả về response thành công cho **Frontend**.
4. **Worker**:
   - Lấy job gửi email từ **Redis**.
   - Tạo nội dung email từ template.
   - Gửi email đến người dùng thông qua một SMTP server.
   - Cập nhật trạng thái của job.

