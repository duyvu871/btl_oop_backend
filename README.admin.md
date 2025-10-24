# Admin User Management System

Hệ thống quản lý user với phân quyền admin đã được xây dựng hoàn chỉnh cho cả Backend (FastAPI) và Frontend (React).

## Tính năng

### Backend API
- ✅ **Phân quyền API**: Tất cả endpoints admin yêu cầu quyền admin
- ✅ **CRUD Operations**: Quản lý user (tạo, đọc, cập nhật, xóa)
- ✅ **Filtering & Search**: Tìm kiếm và lọc user theo nhiều tiêu chí
- ✅ **Pagination**: Phân trang danh sách user
- ✅ **Statistics**: Thống kê tổng quan về users
- ✅ **Security**: Ngăn admin tự xóa hoặc hạ cấp tài khoản của chính mình

### Frontend Admin Dashboard
- ✅ **Dashboard Overview**: Hiển thị thống kê tổng quan (tổng số user, verified, unverified, admin)
- ✅ **User Management Table**: Bảng danh sách user với đầy đủ thông tin
- ✅ **Search & Filter**: Tìm kiếm theo email/username, lọc theo role và trạng thái verified
- ✅ **Edit User**: Modal chỉnh sửa thông tin user (username, email, role, verified status)
- ✅ **Delete User**: Xác nhận xóa user
- ✅ **Access Control**: Chỉ admin mới có thể truy cập trang admin
- ✅ **Admin Badge**: Hiển thị badge admin trong dashboard

## API Endpoints

### Admin Endpoints (Yêu cầu quyền admin)

#### 1. Lấy danh sách users
```http
GET /api/v1/admin/users
Query Parameters:
  - page: int (default: 1)
  - page_size: int (default: 10, max: 100)
  - search: string (tìm kiếm theo email hoặc username)
  - role: string ("user" | "admin")
  - verified: boolean

Response: UserListResponse
{
  "total": 100,
  "page": 1,
  "page_size": 10,
  "users": [...]
}
```

#### 2. Lấy thông tin user cụ thể
```http
GET /api/v1/admin/users/{user_id}
Response: UserAdminRead
```

#### 3. Cập nhật user
```http
PATCH /api/v1/admin/users/{user_id}
Body: UserUpdate
{
  "user_name": "string",
  "email": "user@example.com",
  "verified": true,
  "role": "admin",
  "preferences": []
}
```

#### 4. Xóa user
```http
DELETE /api/v1/admin/users/{user_id}
Response: 204 No Content
```

#### 5. Lấy thống kê
```http
GET /api/v1/admin/stats
Response:
{
  "total_users": 100,
  "verified_users": 80,
  "unverified_users": 20,
  "admin_users": 5,
  "recent_users": 10
}
```

## Cài đặt và Chạy

### Backend

1. Tạo admin user đầu tiên:
```bash
cd backend
python scripts/create_admin.py
```

2. Chạy server:
```bash
make dev  # hoặc uvicorn src.main:app --reload
```

### Frontend

1. Cài đặt dependencies (đã hoàn tất):
```bash
cd frontend
npm install
```

2. Chạy development server:
```bash
npm run dev
```

## Sử dụng

### Tạo Admin User
```bash
cd backend
python scripts/create_admin.py
```
Script sẽ hỏi:
- Email (mặc định: admin@example.com)
- Password (mặc định: admin123)
- Username (mặc định: admin)

### Đăng nhập với Admin
1. Mở browser tại `http://localhost:5173`
2. Đăng nhập với email và password admin
3. Trong Dashboard, click nút "Admin Panel" để vào trang quản lý

### Quản lý Users
1. **Xem danh sách**: Tất cả users hiển thị trong bảng với thông tin đầy đủ
2. **Tìm kiếm**: Nhập email hoặc username vào ô search
3. **Lọc**: Chọn role (User/Admin) hoặc trạng thái (Verified/Unverified)
4. **Chỉnh sửa**: Click icon edit để mở modal chỉnh sửa
5. **Xóa**: Click icon delete để xóa user (có xác nhận)

## Cấu trúc Code

### Backend
```
backend/src/
├── api/v1/
│   ├── admin.py          # Admin endpoints
│   ├── auth.py           # Authentication endpoints
│   └── main.py           # Router registration
├── core/
│   └── security.py       # Security functions & dependencies
├── schemas/
│   └── user.py           # User schemas (UserAdminRead, UserUpdate, etc.)
└── scripts/
    └── create_admin.py   # Script tạo admin user
```

### Frontend
```
frontend/src/
├── api/
│   └── admin.ts          # Admin API client
├── hooks/
│   ├── useAuth.ts        # Auth hook
│   └── useAdmin.ts       # Admin hook
├── pages/
│   ├── AdminDashboardPage.tsx  # Admin dashboard
│   └── DashboardPage.tsx       # User dashboard
├── store/
│   └── auth.ts           # Auth state management
└── App.tsx               # Routes with AdminRoute guard
```

## Bảo mật

### Backend
- ✅ JWT token authentication
- ✅ Role-based access control (RBAC)
- ✅ Dependency injection cho phân quyền
- ✅ Ngăn admin tự xóa hoặc hạ cấp chính mình
- ✅ Validation đầy đủ cho input

### Frontend
- ✅ Route guards (ProtectedRoute, AdminRoute)
- ✅ Role-based UI rendering
- ✅ Token storage trong localStorage
- ✅ Auto-redirect khi không có quyền

## Testing

### Test Backend
```bash
cd backend
# Test tạo admin
python scripts/create_admin.py

# Test API (cần token admin)
curl -X GET http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Test Frontend
1. Đăng nhập với user thường -> Không thấy nút "Admin Panel"
2. Đăng nhập với admin -> Thấy nút "Admin Panel" và có thể truy cập
3. Truy cập trực tiếp `/admin` với user thường -> Redirect về dashboard

## Troubleshooting

### Lỗi "Admin privileges required"
- Đảm bảo user có role "admin" trong database
- Kiểm tra token còn hiệu lực
- Logout và login lại

### Không thấy Admin Panel button
- Kiểm tra user.role === 'admin' trong console
- Refresh page sau khi thay đổi role

### 403 Forbidden khi truy cập /admin
- User hiện tại không có quyền admin
- Cần đăng nhập với tài khoản admin

## Mở rộng

### Thêm quyền mới
1. Thêm enum trong `backend/src/core/database/models/user.py`
2. Tạo dependency mới trong `backend/src/core/security.py`
3. Áp dụng dependency cho endpoints cần bảo vệ

### Thêm fields cho User
1. Update model trong `backend/src/core/database/models/user.py`
2. Tạo migration: `alembic revision --autogenerate -m "add_new_field"`
3. Apply migration: `alembic upgrade head`
4. Update schemas trong `backend/src/schemas/user.py`
5. Update frontend types trong `frontend/src/api/admin.ts`

## Liên hệ
Nếu có vấn đề hoặc câu hỏi, vui lòng tạo issue hoặc liên hệ team phát triển.

