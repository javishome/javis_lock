# Javis Lock Component

## Chức năng chính
### Ngày 22/08/2026 (Version v20260822)
- Sửa lỗi trả về boolean an toàn khi cài đặt Passage Mode.
- Tự động biên dịch file `.pyc` bảo mật khi commit.
- Tối ưu pipeline CI/CD build siêu tốc (~5 giây).
- Bổ sung bộ test và linter kiểm tra toàn diện.

### Ngày 20/4/2026
- Tích hợp TTLock vào Home Assistant qua SmartLock Cloud API.
- Quản lý lock entity: khóa/mở khóa và trạng thái khóa.
- Quản lý passcode: tạo, đổi, xóa, dọn passcode hết hạn.
- Lấy lịch sử mở khóa và thông tin người thao tác gần nhất.
- Hỗ trợ passage mode, auto-lock, sensor và binary sensor.
- Nhận webhook từ backend để cập nhật state theo thời gian thực.
- Hỗ trợ policy version chuẩn `vN` khi backend yêu cầu version tối thiểu.
