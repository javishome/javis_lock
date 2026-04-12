# Javis Lock Component (main_code/2024)

## Chức năng chính

- Tích hợp Home Assistant với hệ sinh thái TTLock qua cloud API.
- Điều khiển khóa từ HA: lock/unlock, đồng bộ trạng thái.
- Quản lý mật mã người dùng: tạo, đổi, xóa, dọn mã hết hạn.
- Theo dõi lịch sử mở khóa và thông tin user gần nhất.
- Hỗ trợ passage mode và auto-lock.
- Cập nhật nhanh trạng thái khóa qua webhook từ backend.
- Tương thích cơ chế chặn version từ backend theo format `vN`.
