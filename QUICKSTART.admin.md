# Hướng dẫn nhanh - Admin User Management

## 🚀 Quick Start

### 1. Tạo Admin User đầu tiên
```bash
cd backend
python scripts/create_admin.py
```
Nhập thông tin:
- Email: admin@example.com (hoặc email tùy chỉnh)
- Password: admin123 (hoặc mật khẩu tùy chỉnh)
- Username: admin (hoặc username tùy chỉnh)

### 2. Chạy Backend
```bash
cd backend
make dev
# hoặc: uvicorn src.main:app --reload
```

### 3. Chạy Frontend
```bash
cd frontend
npm run dev
```

### 4. Truy cập Admin Panel
1. Mở browser: http://localhost:5173
2. Đăng nhập với tài khoản admin vừa tạo
3. Trong Dashboard, click nút **"Admin Panel"**
4. Bạn sẽ thấy trang quản lý user với đầy đủ tính năng

## 📋 Chức năng đã hoàn thành

### Backend ✅
- [x] API endpoints cho admin (GET, PATCH, DELETE users)
- [x] Phân quyền API với dependency `get_admin_user`
- [x] Filtering & Search (theo email, username, role, verified)
- [x] Pagination (trang, kích thước trang)
- [x] Statistics endpoint (thống kê users)
- [x] Bảo mật: Ngăn admin tự xóa/hạ cấp chính mình
- [x] Schemas đầy đủ (UserAdminRead, UserUpdate, UserListResponse)

### Frontend ✅
- [x] Admin Dashboard với thống kê tổng quan
- [x] Bảng danh sách users với pagination
- [x] Tìm kiếm theo email/username
- [x] Lọc theo role (User/Admin)
- [x] Lọc theo trạng thái verified
- [x] Modal chỉnh sửa user (username, email, role, verified)
- [x] Xác nhận xóa user
- [x] Admin Route Guard (phân quyền frontend)
- [x] Badge hiển thị role admin
- [x] Notification system

## 🎯 Test nhanh

### Test phân quyền Backend
```bash
# Lấy token admin (sau khi login)
TOKEN="your_admin_token_here"

# Test lấy danh sách users
curl -X GET "http://localhost:8000/api/v1/admin/users?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# Test thống kê
curl -X GET "http://localhost:8000/api/v1/admin/stats" \
  -H "Authorization: Bearer $TOKEN"
```

### Test phân quyền Frontend
1. **User thường**: Đăng nhập → Không thấy nút "Admin Panel" → Không thể truy cập /admin
2. **Admin**: Đăng nhập → Thấy badge "Admin" → Click "Admin Panel" → Quản lý users

## 📦 Files đã tạo/sửa

### Backend
```
backend/src/
├── api/v1/
│   ├── admin.py              # ✨ MỚI: Admin endpoints
│   └── main.py               # ✏️ CẬP NHẬT: Register admin router
├── core/
│   └── security.py           # ✏️ CẬP NHẬT: Thêm get_admin_user
├── schemas/
│   └── user.py               # ✏️ CẬP NHẬT: Thêm admin schemas
└── scripts/
    └── create_admin.py       # ✨ MỚI: Script tạo admin
```

### Frontend
```
frontend/src/
├── api/
│   └── admin.ts              # ✨ MỚI: Admin API client
├── hooks/
│   └── useAdmin.ts           # ✨ MỚI: Admin hook
├── pages/
│   ├── AdminDashboardPage.tsx # ✨ MỚI: Admin dashboard
│   └── DashboardPage.tsx     # ✏️ CẬP NHẬT: Thêm Admin Panel button
├── providers/
│   └── AppProviders.tsx      # ✏️ CẬP NHẬT: Thêm Notifications
├── store/
│   └── auth.ts               # ✏️ CẬP NHẬT: Thêm role vào User
└── App.tsx                   # ✏️ CẬP NHẬT: Thêm AdminRoute
```

### Documentation
```
README.admin.md              # ✨ MỚI: Tài liệu đầy đủ
QUICKSTART.admin.md          # ✨ MỚI: Hướng dẫn nhanh (file này)
```

## 🔒 Bảo mật

### Backend
- ✅ JWT authentication required
- ✅ Role-based access control (chỉ admin)
- ✅ Input validation
- ✅ Ngăn admin tự phá hoại tài khoản

### Frontend
- ✅ Route guards (AdminRoute)
- ✅ Conditional rendering based on role
- ✅ Auto-redirect khi không có quyền

## 💡 Tips

### Promote user thành admin
```python
# Trong Python shell hoặc script
from src.core.database.models.user import User, Role

# Update user role
user.role = Role.ADMIN
user.verified = True
await db.commit()
```

### Xem API documentation
Mở browser: http://localhost:8000/scalar

## 🐛 Troubleshooting

**Q: Không thấy nút Admin Panel?**
- A: Kiểm tra user.role === 'admin', logout và login lại

**Q: Lỗi 403 Forbidden khi truy cập /admin?**
- A: User hiện tại không có quyền admin

**Q: Build frontend lỗi?**
- A: Đảm bảo đã cài đặt `@mantine/notifications`: `npm install @mantine/notifications`

## 📞 Support
Xem chi tiết trong `README.admin.md`

