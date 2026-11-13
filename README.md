# HỆ THỐNG AI AGENT XỬ LÝ CƠ HỘI BÁN HÀNG B2B - CÔNG TY MINH AN

Hệ thống AI Agent giải quyết bài toán tiếp nhận ~180 yêu cầu/tuần cho 6 Nhân viên Kinh doanh, tự động hóa toàn bộ quy trình từ yêu cầu ban đầu (Email/Web Form) đến Hồ sơ Cơ hội, Thẩm định tồn kho & giá, Lập báo giá và Phân luồng phê duyệt theo sơ đồ chuẩn.

---

## 1. CẤU TRÚC DỰ ÁN

```text
Agent QTKD1/
├── data/
│   ├── products_catalog.json    # Danh mục sản phẩm & Bảng giá niêm yết hiện hành
│   ├── inventory_status.json    # Tồn kho khả dụng & Lead time nhập hàng từ Vận hành
│   ├── approval_policy.json     # Ma trận phân quyền phê duyệt & Chính sách chiết khấu
│   ├── sales_team.json          # Danh sách 6 NVKD & Trưởng phòng kinh doanh
│   └── sample_requests.json     # 5 kịch bản kiểm thử thực tế đa dạng
├── src/
│   ├── __init__.py
│   └── engine.py                # Lõi AI Agent Workflow thực thi 7 bước theo sơ đồ
├── app.py                       # Giao diện Web tương tác trực quan (Streamlit)
├── run_test.py                  # Script kiểm thử tự động 5 kịch bản qua dòng lệnh
└── README.md                    # Hướng dẫn sử dụng & Tài liệu kiến trúc
```

---

## 2. CÁCH KHẮC PHỤC 4 NỖI ĐAU (PAIN POINTS) CỦA CÔNG TY MINH AN

| Nỗi đau hiện tại | Nguyên nhân | Giải pháp của AI Agent |
| :--- | :--- | :--- |
| **Bỏ sót hạng mục** | NVKD đọc thủ công email dài, nhiều dòng sản phẩm | AI Agent phân tích ngữ cảnh, bóc tách toàn bộ mã hàng, số lượng và quy cách kỹ thuật |
| **Dùng giá cũ** | NVKD dùng file Excel giá cá nhân, không cập nhật | AI Agent bắt buộc tra cứu trực tiếp từ CSDL Master (`products_catalog.json`) |
| **Hứa sai tiến độ** | Hỏi miệng hoặc đoán chừng ngày bàn giao | AI Agent đối soát tồn kho khả dụng (`inventory_status.json`); cảnh báo đỏ nếu hạn khách yêu cầu < Lead time nhập hàng |
| **Cơ hội bị trôi, thiếu người theo dõi** | Thiếu ngân sách hoặc không rõ người duyệt | Tự động cấp mã `OPP-YYYYMMDD-XXXX` và gán NVKD theo tải công việc (Round-robin) ngay từ đầu; nếu thiếu thông tin tự động sinh email hỏi khách |

---

## 3. HƯỚNG DẪN CHẠY HỆ THỐNG

### Cách 1: Chạy Kiểm thử Tự động qua Dòng lệnh
```powershell
python run_test.py
```
Lệnh này sẽ tự động chạy 5 kịch bản:
- Kịch bản 1: Yêu cầu chuẩn, đủ thông tin -> Tự động sinh báo giá và duyệt.
- Kịch bản 2: Yêu cầu thiếu thông tin -> Tự động kích hoạt nhánh sinh email yêu cầu khách làm rõ.
- Kịch bản 3: Yêu cầu chiết khấu 10% (> 5%) & giá trị lớn -> Tự động lập Tờ trình chuyển Trưởng phòng duyệt.
- Kịch bản 4: Hết tồn kho khả dụng và thời hạn gấp -> Cảnh báo rủi ro tiến độ nghiêm trọng.
- Kịch bản 5: Yêu cầu thiết bị bảo mật & dịch vụ -> Tự động gán cho NVKD chuyên môn tương ứng.

### Cách 2: Khởi chạy Giao diện Trực quan (Web App)
```powershell
streamlit run app.py
```
Trình duyệt sẽ tự động mở tại `http://localhost:8501`, cung cấp:
1. **Live Demo Xử lý Yêu cầu**: Cho phép chọn kịch bản hoặc dán nội dung email thực tế, xem Agent thực thi từng bước.
2. **Bảng điều khiển Cơ hội (CRM Pipeline)**: Thống kê số lượng deal, doanh số pipeline và phân bổ tải công việc của 6 NVKD.
3. **CSDL Master & Phân quyền**: Tra cứu giá, tồn kho và hạn mức tự quyết.
4. **Tài liệu & Sơ đồ**: Đối chiếu 1:1 với sơ đồ quy trình của Ban Giám đốc.

