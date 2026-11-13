"""
Interactive Web Application for Minh An B2B Sales AI Agent
Built with Streamlit
"""

import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime
from src.engine import SalesOpportunityAgent
from src.exporter import generate_excel_quotation

st.set_page_config(
    page_title="AI Agent B2B Sales - Minh An Company",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo Agent và Session State
@st.cache_resource
def get_agent():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    return SalesOpportunityAgent(data_dir=data_dir)

agent = get_agent()

if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/fluency/96/networking-manager.png", width=70)
st.sidebar.title("MINH AN TECH")
st.sidebar.markdown("**AI Agent Vận Hành Bán Hàng B2B**")
st.sidebar.caption("Giải pháp tự động hóa quy trình cơ hội & báo giá")

# Trạng thái Kết nối Trí tuệ Nhân tạo Gemini
if agent.ai_assistant.is_available():
    st.sidebar.success(f"🟢 **Gemini AI Đang Hoạt Động**\n\nModel: `{agent.ai_assistant.model_name}`")
else:
    st.sidebar.warning("⚡ **Chế độ Heuristic Rules**")

use_ai_opt = st.sidebar.toggle("🧠 Kích hoạt Gemini LLM Nâng Cao", value=True)
agent.use_ai = use_ai_opt

menu = st.sidebar.radio(
    "Điều hướng chức năng:",
    ["🤖 Xử lý Yêu cầu Bán hàng (Live Demo)", "📊 Bảng điều khiển Cơ hội (CRM Pipeline)", "🗄️ CSDL Master & Ma trận Phân quyền", "📖 Tài liệu & Sơ đồ Quy trình"]
)

st.sidebar.divider()
st.sidebar.info(
    "💡 **Mục tiêu hệ thống**:\n"
    "- Giải quyết 180 yêu cầu/tuần cho 6 NVKD\n"
    "- 0% sai sót giá / báo giá cũ\n"
    "- 0% hứa sai tiến độ giao hàng\n"
    "- 100% cơ hội có mã theo dõi & người phụ trách"
)

# -------------------------------------------------------------------------------------
# TRANG 1: LIVE DEMO XỬ LÝ YÊU CẦU
# -------------------------------------------------------------------------------------
if menu == "🤖 Xử lý Yêu cầu Bán hàng (Live Demo)":
    st.title("🤖 Trợ Lý AI Điều Phối Cơ Hội Bán Hàng B2B")
    st.markdown("Quy trình tự động hóa: *Tiếp nhận -> Phân loại -> Thẩm định kho & giá -> Lập đề xuất -> Phân luồng duyệt*")

    # Tải danh sách kịch bản mẫu
    sample_requests_path = os.path.join(agent.data_dir, "sample_requests.json")
    with open(sample_requests_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    sample_options = {
        f"Kịch bản {idx+1}: {s['company']} ({s['id']} - {s['test_expected_outcome'][:45]}...)": s 
        for idx, s in enumerate(samples)
    }
    sample_options["[Tự nhập văn bản yêu cầu mới]"] = None

    selected_option = st.selectbox("🎯 Chọn tình huống thực tế hoặc nhập tự do:", list(sample_options.keys()))

    col_input, col_meta = st.columns([2, 1])

    if sample_options[selected_option] is not None:
        current_data = sample_options[selected_option]
        default_company = current_data["company"]
        default_sender = current_data["sender_name"]
        default_email = current_data["sender_email"]
        default_phone = current_data["phone"]
        default_channel = current_data["channel"]
        default_content = current_data["raw_content"]
        expected_note = current_data["test_expected_outcome"]
    else:
        default_company = ""
        default_sender = ""
        default_email = ""
        default_phone = ""
        default_channel = "Email"
        default_content = ""
        expected_note = "Nhập văn bản tự do của khách hàng để thử nghiệm phản ứng của AI Agent."

    with col_input:
        st.subheader("📥 Nội dung văn bản yêu cầu (Email / Biểu mẫu)")
        raw_text = st.text_area("Nội dung gốc từ khách hàng:", value=default_content, height=220)
        
    with col_meta:
        st.subheader("ℹ️ Metadata tiếp nhận")
        company_input = st.text_input("Tên Doanh nghiệp:", value=default_company)
        sender_input = st.text_input("Người liên hệ:", value=default_sender)
        email_input = st.text_input("Email:", value=default_email)
        channel_input = st.selectbox("Kênh gửi:", ["Email", "Web Form", "Zalo OA", "Điện thoại"], index=0 if default_channel == "Email" else 1)
        st.caption(f"📌 **Kỳ vọng:** {expected_note}")

    if st.button("🚀 KÍCH HOẠT AI AGENT XỬ LÝ QUY TRÌNH", type="primary", use_container_width=True):
        if not raw_text.strip():
            st.warning("Vui lòng nhập nội dung yêu cầu của khách hàng.")
        else:
            req_payload = {
                "id": "LIVE-REQ",
                "channel": channel_input,
                "sender_name": sender_input,
                "sender_email": email_input,
                "company": company_input,
                "phone": default_phone,
                "raw_content": raw_text
            }

            with st.spinner("Đang điều phối quy trình qua các Agent và Tools..."):
                result = agent.process_complete_workflow(req_payload)

            st.success("✅ Đã xử lý xong quy trình nghiệp vụ!")
            
            # Hiển thị thanh tiến trình trực quan
            st.subheader("🛣️ Luồng thực thi theo Sơ đồ Quy trình (Workflow Trail)")
            step_cols = st.columns(len(result["step_logs"]))
            for idx, (col, step) in enumerate(zip(step_cols, result["step_logs"])):
                with col:
                    status_color = "🟢" if "FAIL" not in step["status"] and "INCOMPLETE" not in step["status"] and "RISK" not in step["status"] else "🟡"
                    st.markdown(f"**{status_color} Bước {step['step']}**")
                    st.caption(f"**{step['title']}**\n\n`{step['status']}`")

            st.divider()

            # RẼ NHÁNH HIỂN THỊ KẾT QUẢ
            if result["workflow_outcome"] == "AWAITING_CUSTOMER_CLARIFICATION":
                st.warning("⚠️ **QUYẾT ĐỊNH: YÊU CẦU KHÁCH HÀNG LÀM RÕ / BỔ SUNG THÔNG TIN**")
                st.markdown("Hệ thống phát hiện yêu cầu chưa đủ thông tin tối thiểu để định giá chính xác và cam kết tiến độ:")
                for mf in result["clarification"]["missing_fields"]:
                    st.markdown(f"- 🔴 **{mf}**")

                st.subheader("✉️ Bản nháp Email Tự Động Gửi Khách Hàng (Tạo bởi Agent)")
                st.text_input("Tiêu đề email:", value=result["clarification"]["clarification_email_subject"], disabled=True)
                st.text_area("Nội dung email nháp (NVKD có thể gửi ngay chỉ với 1 click):", value=result["clarification"]["clarification_email_body"], height=280)
                st.info("📌 Trạng thái hồ sơ được lưu: `AWAITING_CUSTOMER_CLARIFICATION`. Khi nhận email phản hồi, quy trình sẽ tự động kích hoạt tiếp từ Bước 1.")

            else:
                opp = result["opportunity"]
                ver = result["verification"]
                quo = result["quotation"]
                app = result["approval"]

                # Header hồ sơ
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("MÃ CƠ HỘI", opp["opp_id"])
                c2.metric("NVKD PHỤ TRÁCH", opp["assigned_rep"]["name"])
                c3.metric("TỔNG GIÁ TRỊ (VAT)", f"{quo['grand_total']:,.0f} đ")
                c4.metric("TRẠNG THÁI", "🔴 CẦN DUYỆT" if app["requires_manager_approval"] else "🟢 SẴN SÀNG GỬI")

                tab_quote, tab_inventory, tab_approval = st.tabs(["📄 Báo Giá & Đề Xuất", "📦 Thẩm Định Tồn Kho & Lead time", "🛡️ Phê Duyệt Thẩm Quyền"])

                with tab_quote:
                    st.markdown(f"**Doanh nghiệp:** {opp['company']} | **Người đại diện:** {opp['customer_name']} ({opp['email']})")
                    st.markdown(f"**Đánh giá ngân sách khách hàng:** `{quo['budget_status']}`")
                    
                    # Bảng chi tiết sản phẩm
                    items_df = pd.DataFrame([
                        {
                            "Mã SKU": it["sku"],
                            "Tên Sản Phẩm / Dịch Vụ": it["name"],
                            "Số Lượng": it["quantity"],
                            "Đơn Giá Chuẩn (VNĐ)": f"{it['unit_price']:,.0f}",
                            "Thành Tiền (VNĐ)": f"{it['line_total']:,.0f}",
                            "Trạng Thái Kho": "✅ Đủ hàng" if it["is_in_stock"] else f"⏳ Thiếu ({it['fulfillment_days']} ngày)",
                            "Vị Trí": it["warehouse_location"]
                        } for it in ver["verified_items"]
                    ])
                    st.dataframe(items_df, use_container_width=True)

                    c_fin1, c_fin2, c_fin3, c_fin4 = st.columns(4)
                    c_fin1.markdown(f"**Tổng giá niêm yết:**\n### {quo['subtotal']:,.0f} đ")
                    c_fin2.markdown(f"**Chiết khấu ({quo['discount_pct']}%):**\n### -{quo['discount_amount']:,.0f} đ")
                    c_fin3.markdown(f"**Tiền trước VAT:**\n### {quo['total_after_discount']:,.0f} đ")
                    c_fin4.markdown(f"**Tổng thanh toán (VAT):**\n### :green[{quo['grand_total']:,.0f} đ]")

                    st.caption(f"🤖 Động cơ phân tích: **{result['parsed_data'].get('extraction_engine', 'AI Agent')}**")

                    st.divider()
                    
                    # Nút xuất bảng Báo giá Excel (.xlsx) chuẩn doanh nghiệp
                    excel_path = generate_excel_quotation(result)
                    with open(excel_path, "rb") as f_excel:
                        st.download_button(
                            label="📥 TẢI BẢNG BÁO GIÁ EXCEL CHÍNH THỨC (.XLSX)",
                            data=f_excel.read(),
                            file_name=os.path.basename(excel_path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                            use_container_width=True
                        )

                    st.subheader("📧 Bản Nháp Email Báo Giá Hoàn Chỉnh Gửi Khách Hàng")
                    st.text_input("Tiêu đề thư chào hàng:", value=quo["proposal_email_subject"], disabled=True)
                    st.text_area("Thư đề xuất giải pháp & Điều khoản thương mại:", value=quo["proposal_email_body"], height=320)

                with tab_inventory:
                    st.subheader("Đối soát Tồn kho khả dụng & Thời gian triển khai (Lead time)")
                    if ver["has_stock_shortage"]:
                        st.error(f"⚠️ Phát hiện {len(ver['shortage_details'])} hạng mục không đủ tồn kho sẵn có!")
                        for sh in ver["shortage_details"]:
                            st.warning(f"**{sh['name']}** (Mã: {sh['sku']}): Yêu cầu {sh['requested']} chiếc, hiện có {sh['available']} chiếc. {sh['note']}")
                    else:
                        st.success("✅ Toàn bộ hạng mục đều có sẵn trong kho khả dụng!")

                    if ver["timeline_conflict"]:
                        st.error(f"🚨 **{ver['timeline_warning_message']}**")
                    else:
                        st.info(f"⏱️ Thời gian giao hàng khả thi: **{ver['earliest_fulfillment_days']} ngày** (Khách yêu cầu: **{ver['requested_deadline_days']} ngày** -> Đáp ứng tốt)")

                with tab_approval:
                    st.subheader("Rà soát Ma trận Phân quyền & Phê duyệt")
                    if app["requires_manager_approval"]:
                        st.error("🚨 **YÊU CẦU VƯỢT THẨM QUYỀN - CẦN TRƯỞNG PHÒNG KINH DOANH PHÊ DUYỆT!**")
                        st.markdown("**Các nguyên nhân kích hoạt chuyển duyệt:**")
                        for r in app["escalation_reasons"]:
                            st.markdown(f"- 🔴 {r}")
                        
                        st.markdown("#### 📝 Tờ Trình Phê Duyệt Tự Động Cho Trưởng Phòng")
                        st.code(app["manager_brief"], language="text")

                        col_act1, col_act2, col_act3 = st.columns(3)
                        with col_act1:
                            if st.button("✅ DUYỆT ĐỒNG Ý (Trưởng phòng)", use_container_width=True):
                                st.balloons()
                                st.success("Trưởng phòng đã phê duyệt đặc cách cơ hội này!")
                        with col_act2:
                            if st.button("✏️ YÊU CẦU ĐIỀU CHỈNH", use_container_width=True):
                                st.info("Đã gửi phản hồi yêu cầu NVKD điều chỉnh mức chiết khấu.")
                        with col_act3:
                            if st.button("❌ TỪ CHỐI DUYỆT", use_container_width=True):
                                st.error("Đã từ chối duyệt đề xuất này.")
                    else:
                        st.success("✅ **NẰM TRONG THẨM QUYỀN TỰ QUYẾT CỦA NHÂN VIÊN KINH DOANH**")
                        st.markdown(f"- Mức chiết khấu ({quo['discount_pct']}%) <= 5.0%")
                        st.markdown(f"- Giá trị cơ hội ({quo['total_after_discount']:,.0f} đ) <= 150.000.000 đ")
                        st.markdown(f"- Tiến độ giao hàng ({ver['earliest_fulfillment_days']} ngày) đáp ứng thời hạn của khách.")
                        st.info("NVKD được quyền ký nháy và gửi báo giá trực tiếp tới khách hàng.")

# -------------------------------------------------------------------------------------
# TRANG 2: DASHBOARD QUẢN TRỊ CƠ HỘI (CRM PIPELINE)
# -------------------------------------------------------------------------------------
elif menu == "📊 Bảng điều khiển Cơ hội (CRM Pipeline)":
    st.title("📊 Bảng Điều Khiển Quản Trị Cơ Hội Bán Hàng")
    st.markdown("Theo dõi tình trạng tiếp nhận ~180 cơ hội/tuần của 6 Nhân viên Kinh doanh")

    # Tạo dữ liệu giả lập pipeline nếu rỗng
    if not agent.opportunities_db:
        # Load và chạy sẵn các sample để có dữ liệu
        sample_path = os.path.join(agent.data_dir, "sample_requests.json")
        with open(sample_path, "r", encoding="utf-8") as f:
            for s in json.load(f):
                agent.process_complete_workflow(s)

    opps = [o for o in agent.opportunities_db if o.get("opportunity")]
    
    col1, col2, col3, col4 = st.columns(4)
    total_deals = len(opps)
    total_pipeline_val = sum(o["quotation"]["grand_total"] for o in opps)
    pending_appr = sum(1 for o in opps if o["approval"]["requires_manager_approval"])
    ready_send = total_deals - pending_appr

    col1.metric("Tổng Số Cơ Hội", f"{total_deals} deals")
    col2.metric("Tổng Giá Trị Pipeline", f"{total_pipeline_val:,.0f} đ")
    col3.metric("Cần Trưởng Phòng Duyệt", f"{pending_appr} deals", delta=f"{pending_appr} vượt quyền", delta_color="inverse")
    col4.metric("Sẵn Sàng Gửi Khách", f"{ready_send} deals", delta=f"{ready_send} đúng hạn")

    st.subheader("📋 Danh Sách Cơ Hội Bán Hàng Đang Xử Lý")
    pipeline_rows = []
    for o in opps:
        opp_info = o["opportunity"]
        quo = o["quotation"]
        app = o["approval"]
        pipeline_rows.append({
            "Mã Cơ Hội": opp_info["opp_id"],
            "Doanh Nghiệp": opp_info["company"],
            "Người Phụ Trách": opp_info["assigned_rep"]["name"],
            "Tổng Tiền (VNĐ)": f"{quo['grand_total']:,.0f}",
            "Chiết Khấu": f"{quo['discount_pct']}%",
            "Tình Trạng Duyệt": "🔴 Chờ Trưởng phòng duyệt" if app["requires_manager_approval"] else "🟢 Đã duyệt tự động",
            "Trạng Thái CRM": opp_info["status"]
        })
    st.dataframe(pd.DataFrame(pipeline_rows), use_container_width=True)

    st.subheader("👥 Phân Bổ Tải Công Việc Của 6 Nhân Viên Kinh Doanh")
    rep_df = pd.DataFrame(agent.reps)
    rep_df.columns = ["Mã NV", "Họ và Tên", "Email", "Số Deal Đang Xử Lý", "Lĩnh Vực Chuyên Môn"]
    st.dataframe(rep_df, use_container_width=True)

# -------------------------------------------------------------------------------------
# TRANG 3: CSDL MASTER & MA TRẬN PHÂN QUYỀN
# -------------------------------------------------------------------------------------
elif menu == "🗄️ CSDL Master & Ma trận Phân quyền":
    st.title("🗄️ Cơ Sở Dữ Liệu Tập Trung (Chống Dùng Giá Cũ & Hứa Sai Hạn)")
    
    tab_cat, tab_inv, tab_pol = st.tabs(["🏷️ Bảng Giá Master (Catalog)", "📦 Tồn Kho & Lead Time", "⚖️ Ma Trận Phân Quyền"])

    with tab_cat:
        st.subheader("Bảng Giá Niêm Yết Chuẩn Hiện Hành")
        st.caption("AI Agent luôn bắt buộc tra cứu bảng giá này, loại bỏ hoàn toàn việc NVKD dùng file Excel giá cũ cá nhân.")
        cat_df = pd.DataFrame(agent.catalog)
        cat_df["unit_price"] = cat_df["unit_price"].apply(lambda x: f"{x:,.0f} VNĐ")
        cat_df.columns = ["Mã SKU", "Tên Sản Phẩm / Dịch Vụ", "Nhóm Hàng", "Đơn Vị", "Đơn Giá Niêm Yết", "Mô Tả Kỹ Thuật"]
        st.dataframe(cat_df, use_container_width=True)

    with tab_inv:
        st.subheader("Tồn Kho Khả Dụng & Thời Gian Nhập Hàng (Bộ Phận Vận Hành)")
        st.caption("Được đồng bộ liên tục với kho vận để kiểm soát cam kết tiến độ với khách hàng.")
        inv_rows = []
        for sku, info in agent.inventory.items():
            inv_rows.append({
                "Mã SKU": sku,
                "Tồn Khả Dụng": info["available_qty"],
                "Lead Time Nhập Hàng (Ngày)": info["lead_time_days_if_out_of_stock"],
                "Vị Trí Kho": info["location"],
                "Cập Nhật Lúc": info["updated_at"]
            })
        st.dataframe(pd.DataFrame(inv_rows), use_container_width=True)

    with tab_pol:
        st.subheader("Ma Trận Phân Quyền & Hạn Mức Tự Quyết")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 👤 Hạn Mức Tự Quyết Của NVKD")
            st.markdown("- **Mức chiết khấu tối đa:** `5.0%`")
            st.markdown("- **Hạn mức giá trị hợp đồng:** `<= 150.000.000 VNĐ`")
            st.markdown("- **Tiến độ cam kết:** Bắt buộc `>= Lead time khả thi của kho`")
        with col_p2:
            st.markdown("#### 👔 Thẩm Quyền Phê Duyệt Của Trưởng Phòng")
            st.markdown("- **Phê duyệt chiết khấu đặc biệt:** `5.1% - 15.0%`")
            st.markdown("- **Phê duyệt hợp đồng lớn:** `> 150.000.000 VNĐ`")
            st.markdown("- **Phê duyệt giao hàng gấp / hỏa tốc khi thiếu tồn kho**")

# -------------------------------------------------------------------------------------
# TRANG 4: TÀI LIỆU & SƠ ĐỒ QUY TRÌNH
# -------------------------------------------------------------------------------------
elif menu == "📖 Tài liệu & Sơ đồ Quy trình":
    st.title("📖 Sơ Đồ Vận Hành & Thiết Kế Kiến Trúc")
    st.markdown("Được ánh xạ 1:1 theo sơ đồ nghiệp vụ chuẩn của Công ty Minh An:")
    
    st.code("""
    [Bắt đầu: Tiếp nhận yêu cầu]
              │
              ▼
    [Phân loại & Kiểm tra thông tin]
              │
      Có đủ thông tin? ──────(Không)─────► [Yêu cầu KH làm rõ / bổ sung]
              │ (Có)                                       ▲
              ▼                                            │
    [Tạo Hồ sơ Cơ hội & Gắn người phụ trách] ──────────────┘ (Khi có thông tin)
              │
              ▼
    [Thẩm định tồn kho & giá] (Tra cứu Catalog & Kho Vận hành)
              │
              ▼
    [Lập Báo giá & Dự thảo đề xuất]
              │
      Có vượt thẩm quyền / Cần chiết khấu đặc biệt?
              │ (Không)                          │ (Có)
              ▼                                  ▼
    [Kết thúc: Cập nhật & Theo dõi] ◄── [Trưởng phòng duyệt]
    """, language="text")

    st.markdown("""
    ### Tóm tắt giá trị giải pháp:
    1. **Tốc độ phản hồi vượt bậc**: Giảm thời gian xử lý một yêu cầu từ **4-8 giờ** xuống còn **dưới 1 phút**.
    2. **Độ chính xác 100%**: Giá và tồn kho tra cứu trực tiếp từ hệ thống master, không có sai lệch con người.
    3. **Không còn cơ hội bị bỏ rơi**: Tự động cấp mã `OPP-ID` và gán NVKD theo tải công việc ngay từ giây đầu tiên.
    4. **Kiểm soát rủi ro chặt chẽ**: Tự động phát hiện chiết khấu vượt trần và xung đột thời hạn giao hàng để báo cáo Trưởng phòng.
    """)

