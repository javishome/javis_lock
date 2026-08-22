# Javis Lock Component

## Chức năng chính
### Ngày 22/08/2026 (Version v20260822)
- **Sửa lỗi Passage Mode API**: Xử lý phản hồi `set_passage_mode()` an toàn, trả về boolean (`True`/`False`) dựa trên `errcode` thay vì `await res.json()`.
- **Tương thích Pydantic V2**: Hỗ trợ chuẩn xác định kiểu cho `EpochMs` và các schema cấu hình.
- **Tự động Compile Bytecode (.pyc)**: Tích hợp `auto_encode.py` vào Pre-commit Hook, tự động biên dịch và bảo mật mã nguồn trước khi push.
- **Tối ưu CI/CD Pipeline**: Chuyển sang base image `alpine:latest`, giảm thời gian pipeline từ 90s xuống ~5s.
- **Kiểm thử & Linter**: Hoàn thiện 100% test case cho tất cả các Service/API và áp dụng Ruff linter.

### Ngày 20/4/2026
- Tích hợp TTLock vào Home Assistant qua SmartLock Cloud API.
- Quản lý lock entity: khóa/mở khóa và trạng thái khóa.
- Quản lý passcode: tạo, đổi, xóa, dọn passcode hết hạn.
- Lấy lịch sử mở khóa và thông tin người thao tác gần nhất.
- Hỗ trợ passage mode, auto-lock, sensor và binary sensor.
- Nhận webhook từ backend để cập nhật state theo thời gian thực.
- Hỗ trợ policy version chuẩn `vN` khi backend yêu cầu version tối thiểu.
