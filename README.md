# Javis Lock Component

## Chức năng chính
### Ngày 09/09/2026 (Version v20260909)
- Bản build Universal duy nhất tương thích mọi phiên bản Home Assistant Core (2024.x, 2025.x, 2026.x+).
- Tự động mã hóa bảo vệ mã nguồn qua Universal Dynamic Encrypted Loader (nạp động trên RAM).
- Khởi tạo bất đồng bộ `async_setup` tuân thủ chuẩn Event Loop Thread-Safety của HA.
- Tích hợp ma trận kiểm thử 2 tầng tự động trên 5 mốc HA Core khi chạy `auto_encode.py`.
- Chuẩn hóa cấu trúc: mã nguồn gốc tại `main_code/`, bản build xuất thẳng vào `build/`.
- Chuẩn hóa Release Tag dạng `vYYYYMMDD` đồng bộ liên thông HACS và Server Version Policy.

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
