"""
Core AI Agent Engine for B2B Sales Opportunity Processing
Minh An Company - B2B Technology & Equipment Services
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from src.ai_llm import GeminiSalesAssistant

class SalesOpportunityAgent:
    def __init__(self, data_dir: str = None, use_ai: bool = True):
        if not data_dir or not os.path.exists(data_dir):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidates = [
                os.path.join(base_dir, "data"),
                os.path.join(os.getcwd(), "data"),
                os.path.join(os.path.dirname(os.getcwd()), "data")
            ]
            for c in candidates:
                if os.path.exists(os.path.join(c, "products_catalog.json")):
                    data_dir = c
                    break
            if not data_dir:
                data_dir = os.path.join(base_dir, "data")
        self.data_dir = data_dir
        self.use_ai = use_ai
        
        self.catalog = self._load_json("products_catalog.json")
        self.inventory = self._load_json("inventory_status.json")
        self.policy = self._load_json("approval_policy.json")
        self.team = self._load_json("sales_team.json")
        self.reps = self.team.get("reps", [])
        self.manager = self.team.get("manager", {})
        
        # Initialize Gemini AI Assistant
        self.ai_assistant = GeminiSalesAssistant()
        
        # In-memory database of processed opportunities for tracking
        self.opportunities_db = []
        self._opportunity_counter = 100

    def _load_json(self, filename: str) -> Any:
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    # -------------------------------------------------------------
    # BƯỚC 1 & 2: PHÂN LOẠI & KIỂM TRA THÔNG TIN (Intake & Validate)
    # -------------------------------------------------------------
    def parse_and_validate_request(self, raw_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trích xuất thông tin từ văn bản thô (email / web form) và
        kiểm tra tính đầy đủ theo tiêu chuẩn tiếp nhận cơ hội B2B.
        """
        content = raw_request.get("raw_content", "")
        sender_name = raw_request.get("sender_name", "")
        sender_email = raw_request.get("sender_email", "")
        company = raw_request.get("company", "")
        phone = raw_request.get("phone", "")

        # 1. Trích xuất thông tin khách hàng nếu chưa có sẵn
        if not sender_name:
            name_match = re.search(r"(?:kính gửi|chào|tôi là|người gửi:?)\s*([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,3})", content, re.IGNORECASE)
            sender_name = name_match.group(1) if name_match else "Quý khách hàng"

        extraction_engine = "Quy tắc Tự Động (Heuristics)"

        # Thử sử dụng Gemini AI LLM nếu được kích hoạt
        if self.use_ai and self.ai_assistant.is_available():
            try:
                llm_res = self.ai_assistant.extract_with_llm(content, self.catalog)
                if llm_res and isinstance(llm_res, dict):
                    extraction_engine = f"Google Gemini AI ({self.ai_assistant.model_name})"
                    s_name = llm_res.get("sender_name") or sender_name
                    c_name = llm_res.get("company") or company
                    s_mail = llm_res.get("sender_email") or sender_email
                    s_phone = llm_res.get("phone") or phone
                    d_days = llm_res.get("deadline_days")
                    b_vnd = llm_res.get("budget_vnd")
                    r_disc = float(llm_res.get("requested_discount_pct", 0.0) or 0.0)

                    ai_items = []
                    for it in llm_res.get("items", []):
                        m_sku = it.get("matched_sku")
                        cat_p = next((p for p in self.catalog if p["sku"] == m_sku), None)
                        if cat_p and not any(x["sku"] == cat_p["sku"] for x in ai_items):
                            ai_items.append({
                                "sku": cat_p["sku"],
                                "name": cat_p["name"],
                                "requested_qty": it.get("quantity", 1),
                                "unit_price": cat_p["unit_price"],
                                "category": cat_p["category"]
                            })

                    missing_f = list(llm_res.get("missing_fields", []))
                    if not ai_items:
                        missing_f.append("Danh sách sản phẩm / dịch vụ cụ thể (chưa rõ model, quy cách)")
                    if d_days is None:
                        missing_f.append("Thời hạn mong muốn hoàn tất bàn giao / triển khai")

                    is_suff = (len(missing_f) == 0) and (len(ai_items) > 0)

                    return {
                        "is_sufficient": is_suff,
                        "missing_fields": list(dict.fromkeys(missing_f)),
                        "sender_name": s_name,
                        "sender_email": s_mail,
                        "company": c_name or "Quý Doanh Nghiệp",
                        "phone": s_phone,
                        "channel": raw_request.get("channel", "Email"),
                        "extracted_items": ai_items,
                        "budget_vnd": b_vnd,
                        "deadline_days": d_days,
                        "requested_discount_pct": r_disc,
                        "raw_content": content,
                        "extraction_engine": extraction_engine
                    }
            except Exception:
                pass # Chuyển sang fallback heuristics nếu có lỗi

        # 2. Nhận diện các sản phẩm được đề cập bằng Fuzzy/Keyword Matching với Catalog
        extracted_items = []
        for prod in self.catalog:
            keywords = []
            if "R750" in prod["sku"]:
                keywords = ["r750", "dell r750", "poweredge r750"]
            elif "DL380" in prod["sku"]:
                keywords = ["dl380", "hpe dl380", "proliant dl380"]
            elif "C9200L-24P" in prod["sku"]:
                keywords = ["c9200l 24", "9200l 24", "cisco catalyst 9200l 24", "cisco 24 cổng", "24 cổng poe"]
            elif "C9200L-48P" in prod["sku"]:
                keywords = ["c9200l 48", "9200l 48", "cisco catalyst 9200l 48", "cisco 48 cổng", "48 cổng poe"]
            elif "FORTI-60F" in prod["sku"]:
                keywords = ["fortinet", "fortigate 60f", "tường lửa fortinet"]
            elif "ARUBA-AP505" in prod["sku"]:
                keywords = ["aruba", "ap-505", "ap505", "wifi aruba"]
            elif "UPS-APC" in prod["sku"]:
                keywords = ["ups", "apc", "3000va", "srt3000xli", "lưu điện apc"]
            elif "WINSRV" in prod["sku"]:
                keywords = ["windows server 2022", "win srv", "bản quyền microsoft"]
            elif "DEPLOY-BASIC" in prod["sku"]:
                keywords = ["lắp đặt, cấu hình", "dịch vụ lắp đặt", "triển khai mạng & server cơ bản"]
            elif "MIGRATION-ADV" in prod["sku"]:
                keywords = ["chuyển đổi dữ liệu", "ảo hóa vmware", "triển khai ảo hóa"]

            for kw in keywords:
                if kw in content.lower():
                    qty = 1
                    # Tìm dòng chứa keyword
                    lines = content.split("\n")
                    for line in lines:
                        if kw in line.lower():
                            # Bỏ số thứ tự đầu dòng như "1. ", "2. ", "- "
                            clean_line = re.sub(r"^\s*(?:\d+[\.\)]|[-*•])\s*", "", line)
                            qty_m = re.search(r"(\d+)\s*(?:bộ|chiếc|cái|gói|license|hộp|con)", clean_line, re.IGNORECASE)
                            if qty_m:
                                try:
                                    qty = int(qty_m.group(1))
                                except:
                                    qty = 1
                            else:
                                # Thử tìm số đơn giản đầu dòng đã làm sạch
                                start_num_m = re.match(r"^(\d+)\b", clean_line.strip())
                                if start_num_m:
                                    try:
                                        qty = int(start_num_m.group(1))
                                    except:
                                        qty = 1
                            break

                    # Tránh thêm trùng SKU
                    if not any(item["sku"] == prod["sku"] for item in extracted_items):
                        extracted_items.append({
                            "sku": prod["sku"],
                            "name": prod["name"],
                            "requested_qty": qty,
                            "unit_price": prod["unit_price"],
                            "category": prod["category"]
                        })
                    break

        # 3. Trích xuất ngân sách nếu có
        budget_vnd = None
        budget_match = re.search(r"(?:ngân sách|kinh phí|tổng tiền dự kiến|ngân sách nội bộ)[^\d]{0,40}(\d{1,3}(?:\.\d{3})+|\d+)\s*(?:vnđ|đồng|triệu)?", content, re.IGNORECASE)
        if budget_match:
            raw_num = budget_match.group(1).replace(".", "")
            try:
                num = float(raw_num)
                if num < 1000 and "triệu" in content.lower():
                    num = num * 1_000_000
                budget_vnd = num
            except:
                budget_vnd = None

        # 4. Trích xuất thời hạn triển khai (Lead time / Deadline yêu cầu)
        deadline_days = None
        deadline_match = re.search(r"(?:trong vòng|hạn chót|thời hạn|hoàn tất trong|thời hạn triển khai:?|thời hạn nhận hàng bắt buộc:?)\s*(?:khoảng)?\s*(\d+)\s*ngày", content, re.IGNORECASE)
        if deadline_match:
            deadline_days = int(deadline_match.group(1))
        elif "gấp" in content.lower() or "sáng mai" in content.lower():
            deadline_days = 2
        elif "tuần tới" in content.lower():
            deadline_days = 7

        # 5. Trích xuất chiết khấu yêu cầu (Chỉ lấy khi người dùng ghi rõ %)
        requested_discount_pct = 0.0
        discount_match = re.search(r"(?:chiết khấu|giảm giá)\s*(\d+(?:\.\d+)?)\s*%", content, re.IGNORECASE)
        if discount_match:
            requested_discount_pct = float(discount_match.group(1))

        # 6. KIỂM TRA ĐẦY ĐỦ THÔNG TIN (Validation Rules)
        missing_fields = []
        if not extracted_items:
            missing_fields.append("Danh sách sản phẩm / dịch vụ cụ thể (chưa rõ model, quy cách)")
        else:
            # Kiểm tra xem có sản phẩm nào số lượng không hợp lý không
            for itm in extracted_items:
                if itm["requested_qty"] <= 0:
                    missing_fields.append(f"Số lượng cho sản phẩm {itm['name']}")

        if deadline_days is None:
            missing_fields.append("Thời hạn mong muốn hoàn tất bàn giao / triển khai")

        if not company and not sender_name:
            missing_fields.append("Thông tin đơn vị hoặc người liên hệ đại diện")

        is_sufficient = len(missing_fields) == 0

        return {
            "is_sufficient": is_sufficient,
            "missing_fields": missing_fields,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "company": company or "Quý Doanh Nghiệp",
            "phone": phone,
            "channel": raw_request.get("channel", "Email"),
            "extracted_items": extracted_items,
            "budget_vnd": budget_vnd,
            "deadline_days": deadline_days,
            "requested_discount_pct": requested_discount_pct,
            "raw_content": content,
            "extraction_engine": extraction_engine
        }

    # -------------------------------------------------------------
    # NHÁNH: KHÔNG ĐỦ THÔNG TIN -> YÊU CẦU KH LÀM RÕ / BỔ SUNG
    # -------------------------------------------------------------
    def generate_clarification_draft(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sinh bản nháp email phản hồi lịch sự, cụ thể các hạng mục cần bổ sung.
        Khắc phục tình trạng chuyển qua lại vô định mà không ai hỏi lại khách.
        """
        missing_list_str = "\n".join([f"- {item}" for item in parsed_data["missing_fields"]])
        
        email_body = f"""Kính gửi Anh/Chị {parsed_data['sender_name']},
Đại diện: {parsed_data['company']}

Lời đầu tiên, Công ty TNHH Công nghệ Minh An xin trân trọng cảm ơn Anh/Chị đã quan tâm và gửi yêu cầu hợp tác đến chúng tôi.

Để có thể gửi đến Quý công ty bảng báo giá chính xác, áp dụng các chính sách chiết khấu tốt nhất cũng như cam kết tiến độ khả thi, Minh An xin phép được trao đổi thêm để làm rõ một số thông tin còn thiếu sau:

{missing_list_str}

Quý Anh/Chị vui lòng phản hồi trực tiếp qua email này hoặc liên hệ hotline kỹ thuật 024.3999.8888 để được đội ngũ chuyên viên của Minh An hỗ trợ tư vấn cấu hình tối ưu nhất.

Ngay khi nhận được thông tin bổ sung, Minh An cam kết sẽ gửi hồ sơ báo giá chính thức trong vòng tối đa 02 giờ làm việc.

Kính chúc Quý công ty luôn phát triển và thành công!

Trân trọng,
Phòng Kinh doanh Doanh nghiệp - Công ty Công nghệ Minh An
Hotline: 024.3999.8888 | Email: sales@minhan.com.vn
Website: https://minhan.com.vn"""

        return {
            "status": "AWAITING_CLARIFICATION",
            "clarification_email_subject": f"[Minh An Tech] Phản hồi yêu cầu báo giá thiết bị & giải pháp CNTT - {parsed_data['company']}",
            "clarification_email_body": email_body,
            "missing_fields": parsed_data["missing_fields"]
        }

    # -------------------------------------------------------------
    # BƯỚC 3: TẠO HỒ SƠ CƠ HỘI & GẮN NGƯỜI PHỤ TRÁCH (Opportunity Management)
    # -------------------------------------------------------------
    def create_opportunity(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo mã định danh cơ hội và tự động gán NVKD theo chuyên môn & tải công việc.
        Giải quyết triệt để tình trạng 'cơ hội mồ côi không có người theo dõi'.
        """
        self._opportunity_counter += 1
        date_str = datetime.now().strftime("%Y%m%d")
        opp_id = f"OPP-{date_str}-{self._opportunity_counter:04d}"

        # Thuật toán phân công (Sales Assignment):
        # 1. Tìm NVKD có chuyên môn khớp với sản phẩm chủ đạo
        # 2. Nếu có nhiều NVKD, chọn người có active_deals_count thấp nhất (Least Busy)
        dominant_category = ""
        if parsed_data["extracted_items"]:
            dominant_category = parsed_data["extracted_items"][0].get("category", "")

        assigned_rep = None
        # Ghép chuyên môn
        matching_reps = [
            r for r in self.reps 
            if any(k.lower() in r["specialty"].lower() for k in dominant_category.split())
        ]
        
        if matching_reps:
            # Chọn người ít việc nhất trong nhóm chuyên môn
            assigned_rep = min(matching_reps, key=lambda x: x["active_deals_count"])
        else:
            # Chọn người ít việc nhất toàn bộ đội
            assigned_rep = min(self.reps, key=lambda x: x["active_deals_count"])

        # Tăng tải công việc tạm thời
        assigned_rep["active_deals_count"] += 1

        opportunity_record = {
            "opp_id": opp_id,
            "created_at": datetime.now().isoformat(),
            "customer_name": parsed_data["sender_name"],
            "company": parsed_data["company"],
            "email": parsed_data["sender_email"],
            "phone": parsed_data["phone"],
            "assigned_rep": {
                "id": assigned_rep["id"],
                "name": assigned_rep["name"],
                "email": assigned_rep["email"],
                "specialty": assigned_rep["specialty"]
            },
            "status": "OPPORTUNITY_CREATED",
            "audit_trail": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "Tạo Hồ sơ Cơ hội thành công",
                    "actor": "System AI Agent",
                    "note": f"Đã gán phụ trách cho NVKD {assigned_rep['name']} ({assigned_rep['specialty']})."
                }
            ]
        }

        return opportunity_record

    # -------------------------------------------------------------
    # BƯỚC 4: THẨM ĐỊNH TỒN KHO & GIÁ (Inventory & Price Verification)
    # -------------------------------------------------------------
    def verify_inventory_and_pricing(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tra cứu trực tiếp CSDL Catalog và CSDL Tồn kho thời gian thực.
        Khắc phục triệt để lỗi:
        - Bỏ sót hạng mục
        - Dùng giá cũ
        - Hứa thời hạn sai thực tế tồn kho & vận hành
        """
        verified_items = []
        earliest_fulfillment_days = 2 # Mặc định 2 ngày test & đóng gói
        has_stock_shortage = False
        shortage_details = []

        for item in parsed_data["extracted_items"]:
            sku = item["sku"]
            qty = item["requested_qty"]

            # Lấy thông tin tồn kho
            inv = self.inventory.get(sku, {
                "available_qty": 0,
                "lead_time_days_if_out_of_stock": 14,
                "location": "Không xác định"
            })

            available_qty = inv.get("available_qty", 0)
            lead_time = inv.get("lead_time_days_if_out_of_stock", 7)
            location = inv.get("location", "Kho trung tâm")

            is_available = available_qty >= qty
            item_fulfillment_days = 2 if is_available else lead_time

            if not is_available:
                has_stock_shortage = True
                shortage_details.append({
                    "sku": sku,
                    "name": item["name"],
                    "requested": qty,
                    "available": available_qty,
                    "shortage": qty - available_qty,
                    "lead_time_days": lead_time,
                    "note": f"Thiếu {qty - available_qty} chiếc trong kho. Cần {lead_time} ngày nhập hàng."
                })

            if item_fulfillment_days > earliest_fulfillment_days:
                earliest_fulfillment_days = item_fulfillment_days

            verified_items.append({
                "sku": sku,
                "name": item["name"],
                "category": item["category"],
                "unit_price": item["unit_price"],
                "quantity": qty,
                "line_total": item["unit_price"] * qty,
                "available_in_stock": available_qty,
                "is_in_stock": is_available,
                "fulfillment_days": item_fulfillment_days,
                "warehouse_location": location
            })

        # So sánh với thời hạn khách yêu cầu
        requested_deadline = parsed_data.get("deadline_days", 15)
        timeline_conflict = False
        timeline_warning_message = ""

        if requested_deadline and requested_deadline < earliest_fulfillment_days:
            timeline_conflict = True
            timeline_warning_message = (
                f"RỦI RO TIẾN ĐỘ: Khách hàng yêu cầu giao trong {requested_deadline} ngày, "
                f"tuy nhiên thời gian sẵn sàng sớm nhất của kho vận hành là {earliest_fulfillment_days} ngày. "
                f"Cần Trưởng phòng hoặc Vận hành can thiệp xử lý phương án vận chuyển hỏa tốc hoặc giao từng phần."
            )

        return {
            "verified_items": verified_items,
            "earliest_fulfillment_days": earliest_fulfillment_days,
            "has_stock_shortage": has_stock_shortage,
            "shortage_details": shortage_details,
            "timeline_conflict": timeline_conflict,
            "timeline_warning_message": timeline_warning_message,
            "requested_deadline_days": requested_deadline
        }

    # -------------------------------------------------------------
    # BƯỚC 5: LẬP BÁO GIÁ & DỰ THẢO ĐỀ XUẤT (Quotation & Proposal)
    # -------------------------------------------------------------
    def generate_quotation_and_proposal(
        self,
        parsed_data: Dict[str, Any],
        opportunity: Dict[str, Any],
        verification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Tính toán tổng tiền, áp mức chiết khấu hợp lý, thuế VAT 10%
        và soạn thảo bức thư chào hàng & bảng báo giá hoàn chỉnh.
        """
        subtotal = sum(item["line_total"] for item in verification["verified_items"])
        
        # Áp dụng chiết khấu đúng theo yêu cầu của người dùng (Không tự bịa % chiết khấu)
        discount_pct = float(parsed_data.get("requested_discount_pct", 0.0) or 0.0)
            
        discount_amount = int(subtotal * (discount_pct / 100.0))
        total_after_discount = subtotal - discount_amount
        vat_amount = int(total_after_discount * self.policy.get("vat_rate", 0.1))
        grand_total = total_after_discount + vat_amount

        # So sánh với ngân sách của khách
        budget_vnd = parsed_data.get("budget_vnd")
        budget_status = "N/A"
        budget_diff = 0
        if budget_vnd:
            budget_diff = budget_vnd - grand_total
            if budget_diff >= 0:
                budget_status = f"Nằm trong ngân sách (Dư {budget_diff:,.0f} đ)"
            else:
                budget_status = f"Vượt quá ngân sách {abs(budget_diff):,.0f} đ (-{abs(budget_diff)/budget_vnd*100:.1f}%)"

        # Soạn bảng chi tiết hạng mục dạng text
        table_lines = []
        for idx, itm in enumerate(verification["verified_items"], 1):
            stock_status = "Có sẵn" if itm["is_in_stock"] else f"Cần {itm['fulfillment_days']} ngày"
            table_lines.append(
                f"{idx}. {itm['name']}\n"
                f"   - Số lượng: {itm['quantity']} | Đơn giá niêm yết: {itm['unit_price']:,.0f} đ\n"
                f"   - Thành tiền: {itm['line_total']:,.0f} đ | Kho: {itm['warehouse_location']} ({stock_status})"
            )
        items_detail_str = "\n".join(table_lines)

        rep_name = opportunity["assigned_rep"]["name"]
        rep_email = opportunity["assigned_rep"]["email"]

        # Soạn thảo thư báo giá gửi khách hàng
        proposal_email_body = f"""Kính gửi Anh/Chị {parsed_data['sender_name']},
Đơn vị: {parsed_data['company']}

Công ty TNHH Công nghệ Minh An xin trân trọng gửi tới Quý khách Báo giá và Đề xuất giải pháp kỹ thuật theo yêu cầu:

MÃ CƠ HỘI / BÁO GIÁ: {opportunity['opp_id']}
Ngày lập: {datetime.now().strftime('%d/%m/%Y')}
Chuyên viên phụ trách: {rep_name} ({rep_email})

--- DANH MỤC THIẾT BỊ & DỊCH VỤ ĐỀ XUẤT ---
{items_detail_str}

--- TỔNG KẾT TÀI CHÍNH ---
+ Tổng giá trị niêm yết: {subtotal:,.0f} VNĐ
+ Mức chiết khấu ưu đãi ({discount_pct}%): -{discount_amount:,.0f} VNĐ
+ Tổng tiền trước thuế: {total_after_discount:,.0f} VNĐ
+ Thuế GTGT (VAT 10%): {vat_amount:,.0f} VNĐ
=========================================
TỔNG THANH TOÁN (ĐÃ GỒM VAT): {grand_total:,.0f} VNĐ
(Bằng chữ: {self._number_to_vietnamese_text(grand_total)})

--- ĐIỀU KHOẢN GIAO HÀNG & BẢO HÀNH ---
- Thời gian bàn giao cam kết: {verification['earliest_fulfillment_days']} ngày làm việc kể từ ngày hoàn tất ký kết Hợp đồng.
- Địa điểm bàn giao: Tận nơi theo yêu cầu của Quý công ty.
- Bảo hành: Theo đúng tiêu chuẩn chính hãng (Hỗ trợ kỹ thuật 24/7 từ Minh An).
- Điều khoản thanh toán: {self.policy.get('standard_payment_terms')}
- Hiệu lực báo giá: {self.policy.get('quote_validity_days')} ngày kể từ ngày phát hành.

Rất mong sớm nhận được phản hồi và có cơ hội đồng hành cùng Quý công ty.

Trân trọng,
{rep_name} - Đại diện Kinh doanh
Công ty TNHH Công nghệ Minh An
Hotline: 024.3999.8888 | Website: https://minhan.com.vn"""

        return {
            "subtotal": subtotal,
            "discount_pct": discount_pct,
            "discount_amount": discount_amount,
            "total_after_discount": total_after_discount,
            "vat_amount": vat_amount,
            "grand_total": grand_total,
            "budget_vnd": budget_vnd,
            "budget_status": budget_status,
            "proposal_email_subject": f"[Minh An Tech - Báo giá {opportunity['opp_id']}] Cung cấp thiết bị & giải pháp CNTT - {parsed_data['company']}",
            "proposal_email_body": proposal_email_body
        }

    # -------------------------------------------------------------
    # BƯỚC 6: KIỂM TRA THẨM QUYỀN & CHUYỂN DUYỆT (Approval Routing)
    # -------------------------------------------------------------
    def check_and_route_approval(
        self,
        opportunity: Dict[str, Any],
        verification: Dict[str, Any],
        quotation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Đối soát với Ma trận Phân quyền phê duyệt:
        - Chiết khấu > 5%?
        - Giá trị đơn hàng > 150 triệu?
        - Rủi ro thời hạn (lead time conflict)?
        """
        rep_limits = self.policy.get("sales_rep_limits", {})
        max_rep_discount = rep_limits.get("max_discount_pct", 5.0)
        max_rep_deal_value = rep_limits.get("max_deal_value_vnd", 150_000_000)

        escalation_reasons = []

        if quotation["discount_pct"] > max_rep_discount:
            escalation_reasons.append(
                f"Mức chiết khấu {quotation['discount_pct']}% vượt thẩm quyền tự quyết của NVKD (Tối đa {max_rep_discount}%)."
            )

        if quotation["total_after_discount"] > max_rep_deal_value:
            escalation_reasons.append(
                f"Giá trị cơ hội ({quotation['total_after_discount']:,.0f} đ) vượt hạn mức chuẩn {max_rep_deal_value:,.0f} đ."
            )

        if verification["timeline_conflict"]:
            escalation_reasons.append(verification["timeline_warning_message"])

        requires_manager_approval = len(escalation_reasons) > 0

        approval_result = {
            "requires_manager_approval": requires_manager_approval,
            "escalation_reasons": escalation_reasons,
            "approver": self.manager if requires_manager_approval else opportunity["assigned_rep"],
            "status": "PENDING_MANAGER_APPROVAL" if requires_manager_approval else "APPROVED_AUTO",
            "manager_brief": None
        }

        # Nếu cần Trưởng phòng duyệt, tạo Tờ trình phê duyệt tóm tắt (Executive Summary)
        if requires_manager_approval:
            reasons_str = "\n".join([f"  (!) {r}" for r in escalation_reasons])
            
            ai_advice_text = ""
            if self.use_ai and self.ai_assistant.is_available():
                try:
                    deal_ctx = {
                        "company": opportunity["company"],
                        "opp_id": opportunity["opp_id"],
                        "grand_total": quotation["grand_total"],
                        "discount_pct": quotation["discount_pct"],
                        "requested_days": verification["requested_deadline_days"],
                        "fulfillment_days": verification["earliest_fulfillment_days"]
                    }
                    advice = self.ai_assistant.generate_manager_advice(deal_ctx, escalation_reasons)
                    if advice:
                        ai_advice_text = f"\n\n--- CỐ VẤN CHIẾN LƯỢC TỪ AI AGENT (GEMINI) ---\n{advice}\n"
                except Exception:
                    pass

            approval_result["manager_brief"] = f"""=====================================================
PHIẾU TRÌNH PHÊ DUYỆT CƠ HỘI BÁN HÀNG VƯỢT THẨM QUYỀN
=====================================================
Kính gửi: {self.manager['title']} - {self.manager['name']}
Người trình: NVKD {opportunity['assigned_rep']['name']}
Mã Cơ hội: {opportunity['opp_id']} | Khách hàng: {opportunity['company']}

LÝ DO CẦN PHÊ DUYỆT:
{reasons_str}

THÔNG SỐ ĐỀ XUẤT:
- Tổng giá trị niêm yết: {quotation['subtotal']:,.0f} VNĐ
- Chiết khấu xin duyệt: {quotation['discount_pct']}% ({quotation['discount_amount']:,.0f} VNĐ)
- Tổng tiền sau chiết khấu (chưa VAT): {quotation['total_after_discount']:,.0f} VNĐ
- Tình trạng kho: {'Có thiếu hàng cần nhập' if verification['has_stock_shortage'] else 'Đủ hàng sẵn'}
- Thời gian hoàn tất tối thiểu: {verification['earliest_fulfillment_days']} ngày (Khách yêu cầu: {verification['requested_deadline_days']} ngày)
{ai_advice_text}
ĐỀ XUẤT HÀNH ĐỘNG DÀNH CHO TRƯỞNG PHÒNG:
[ ] 1. DUYỆT ĐỒNG Ý: Chấp thuận chiết khấu và ủy quyền ký hợp đồng.
[ ] 2. ĐIỀU CHỈNH: Giảm chiết khấu về tối đa 6% hoặc yêu cầu khách ứng 50%.
[ ] 3. TỪ CHỐI: Không khả thi về tiến độ hoặc biên độ lợi nhuận quá thấp.
====================================================="""

        return approval_result

    # -------------------------------------------------------------
    # BƯỚC 7: KẾT THÚC: CẬP NHẬT & THEO DÕI (Tracking & Orchestration)
    # -------------------------------------------------------------
    def process_complete_workflow(self, raw_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bộ điều phối trung tâm (Workflow Orchestrator) thực thi toàn bộ
        7 bước trong quy trình của Công ty Minh An.
        """
        step_logs = []
        
        # Bước 1 & 2: Tiếp nhận, Phân loại & Kiểm tra thông tin
        step_logs.append({"step": 1, "title": "Tiếp nhận & Bóc tách yêu cầu", "status": "COMPLETED"})
        parsed = self.parse_and_validate_request(raw_request)
        
        # Bước 3: Rẽ nhánh Đủ / Thiếu thông tin
        if not parsed["is_sufficient"]:
            step_logs.append({
                "step": 2,
                "title": "Kiểm tra thông tin",
                "status": "INCOMPLETE_INFO",
                "detail": f"Thiếu: {', '.join(parsed['missing_fields'])}"
            })
            clarification = self.generate_clarification_draft(parsed)
            step_logs.append({
                "step": 3,
                "title": "Yêu cầu KH làm rõ / bổ sung",
                "status": "SENT_CLARIFICATION_EMAIL"
            })
            
            result = {
                "workflow_outcome": "AWAITING_CUSTOMER_CLARIFICATION",
                "step_logs": step_logs,
                "parsed_data": parsed,
                "clarification": clarification,
                "opportunity": None,
                "verification": None,
                "quotation": None,
                "approval": None
            }
            return result

        step_logs.append({"step": 2, "title": "Kiểm tra thông tin", "status": "FULL_INFO_PASSED"})

        # Bước 3 (Nhánh Đủ): Tạo Hồ sơ Cơ hội & Gắn người phụ trách
        opportunity = self.create_opportunity(parsed)
        step_logs.append({
            "step": 3,
            "title": "Tạo Hồ sơ Cơ hội & Phân công NVKD",
            "status": "SUCCESS",
            "opp_id": opportunity["opp_id"],
            "assigned_rep": opportunity["assigned_rep"]["name"]
        })

        # Bước 4: Thẩm định tồn kho & giá
        verification = self.verify_inventory_and_pricing(parsed)
        step_logs.append({
            "step": 4,
            "title": "Thẩm định tồn kho & bảng giá niêm yết",
            "status": "VERIFIED",
            "has_shortage": verification["has_stock_shortage"],
            "timeline_conflict": verification["timeline_conflict"]
        })

        # Bước 5: Lập Báo giá & Dự thảo đề xuất
        quotation = self.generate_quotation_and_proposal(parsed, opportunity, verification)
        step_logs.append({
            "step": 5,
            "title": "Lập Báo giá & Dự thảo đề xuất",
            "status": "GENERATED",
            "grand_total": quotation["grand_total"]
        })

        # Bước 6: Kiểm tra ma trận vượt thẩm quyền
        approval = self.check_and_route_approval(opportunity, verification, quotation)
        step_logs.append({
            "step": 6,
            "title": "Phân luồng & Kiểm tra thẩm quyền phê duyệt",
            "status": approval["status"],
            "requires_manager": approval["requires_manager_approval"]
        })

        # Bước 7: Kết thúc: Cập nhật & Theo dõi
        final_status = "PENDING_MANAGER_APPROVAL" if approval["requires_manager_approval"] else "READY_FOR_CUSTOMER_DISPATCH"
        opportunity["status"] = final_status
        opportunity["audit_trail"].append({
            "timestamp": datetime.now().isoformat(),
            "action": "Cập nhật hồ sơ hoàn tất",
            "status": final_status,
            "actor": "System AI Agent"
        })

        step_logs.append({
            "step": 7,
            "title": "Kết thúc: Cập nhật hồ sơ & Đưa vào danh sách theo dõi",
            "status": final_status
        })

        # Lưu vào danh sách theo dõi chung
        full_record = {
            "workflow_outcome": final_status,
            "step_logs": step_logs,
            "parsed_data": parsed,
            "opportunity": opportunity,
            "verification": verification,
            "quotation": quotation,
            "approval": approval
        }
        self.opportunities_db.append(full_record)

        return full_record

    def _number_to_vietnamese_text(self, amount: float) -> str:
        """Chuyển đổi số tiền thành văn bản tiếng Việt đơn giản cho hợp đồng."""
        # Triệu và nghìn
        tr = int(amount // 1_000_000)
        ngh = int((amount % 1_000_000) // 1_000)
        res = []
        if tr > 0:
            res.append(f"{tr} triệu")
        if ngh > 0:
            res.append(f"{ngh} nghìn")
        res.append("đồng")
        return " ".join(res)
