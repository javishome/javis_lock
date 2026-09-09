# Javis Lock Component

## Chức năng chính
### Ngày 09/09/2026 (Version v20260909)
- **1 bản cài đặt duy nhất**: Tương thích mượt mà với mọi phiên bản Home Assistant (từ HA 2024 đến HA 2025+).
- **Bảo vệ mã nguồn an toàn**: Tự động mã hóa code bảo mật mà không làm ảnh hưởng đến tốc độ chạy.
- **Khởi chạy mượt mà**: Sửa lỗi luồng, đảm bảo không bị treo hay xung đột khi Home Assistant khởi động và gọi dịch vụ.

### Ngày 22/08/2026 (Version v20260822)
- Sửa lỗi trả về boolean an toàn khi cài đặt Passage Mode.
- Tự động biên dịch bảo mật khi commit.
- Tối ưu pipeline build nhanh và ổn định.
- Bổ sung bộ test kiểm tra toàn diện.

### Ngày 20/4/2026
- Tích hợp khóa TTLock vào Home Assistant qua Cloud API.
- Quản lý khóa: đóng/mở khóa từ xa và theo dõi trạng thái khóa.
- Quản lý mã PIN: tạo mới, đổi tên, xóa mã và tự động dọn dẹp mã hết hạn.
- Xem lịch sử mở khóa và thông tin người mở gần nhất.
- Hỗ trợ chế độ thông phòng (passage mode), tự động khóa (auto-lock), cảm biến pin và cảm biến cửa.
- Cập nhật trạng thái theo thời gian thực qua Webhook.
