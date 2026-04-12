# Javis Lock Component

## Chức năng chính

- Tích hợp TTLock vào Home Assistant qua SmartLock Cloud API.
- Quản lý lock entity: khóa/mở khóa và trạng thái khóa.
- Quản lý passcode: tạo, đổi, xóa, dọn passcode hết hạn.
- Lấy lịch sử mở khóa và thông tin người thao tác gần nhất.
- Hỗ trợ passage mode, auto-lock, sensor và binary sensor.
- Nhận webhook từ backend để cập nhật state theo thời gian thực.
- Hỗ trợ policy version chuẩn `vN` khi backend yêu cầu version tối thiểu.
