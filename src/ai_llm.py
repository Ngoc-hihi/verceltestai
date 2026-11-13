"""
Gemini LLM Integration for Minh An B2B Sales Agent
Utilizes Google GenAI SDK (gemini-3.1-flash-lite / gemini-3.5-flash-lite)
"""

import os
import json
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

class GeminiSalesAssistant:
    def __init__(self, api_key: str = None, model_name: str = "gemini-3.1-flash-lite"):
        if not api_key:
            # Load from env or config file
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                candidates = [
                    os.path.join(base_dir, "data", "config.json"),
                    os.path.join(os.getcwd(), "data", "config.json"),
                    os.path.join(os.path.dirname(os.getcwd()), "data", "config.json"),
                ]
                for p in candidates:
                    if os.path.exists(p):
                        try:
                            with open(p, "r", encoding="utf-8") as f:
                                cfg = json.load(f)
                                api_key = cfg.get("gemini_api_key")
                                if api_key:
                                    break
                        except Exception:
                            pass

        self.api_key = api_key
        self.model_name = model_name
        self.fallback_model = "gemini-3.5-flash-lite"
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def is_available(self) -> bool:
        return self.client is not None

    def _call_llm(self, prompt: str, system_instruction: str = None, response_schema: Any = None) -> Optional[str]:
        if not self.client:
            return None

        models_to_try = [self.model_name, self.fallback_model]
        for m in models_to_try:
            try:
                config = {}
                if system_instruction:
                    config["system_instruction"] = system_instruction
                if response_schema:
                    config["response_mime_type"] = "application/json"
                    config["response_schema"] = response_schema
                
                resp = self.client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=config if config else None
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                # Try next model
                continue
        return None

    def extract_with_llm(self, raw_text: str, catalog: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Sử dụng Gemini để bóc tách thông tin có cấu trúc từ email/form của khách hàng.
        """
        catalog_summary = "\n".join([
            f"- SKU: {p['sku']} | Tên: {p['name']} | Giá: {p['unit_price']:,} đ"
            for p in catalog
        ])

        system_instruction = (
            "Bạn là Chuyên viên Phân tích Yêu cầu Kinh doanh B2B (Sales Ops AI) của Công ty Công nghệ Minh An.\n"
            "Nhiệm vụ của bạn là đọc kỹ văn bản yêu cầu của khách hàng (Email hoặc Web Form) và trích xuất cấu trúc dữ liệu JSON chính xác.\n"
            "Hãy đối chiếu các sản phẩm khách hỏi với danh mục Catalog sản phẩm để tìm đúng mã SKU tương ứng.\n"
            "Nếu khách hàng không nêu rõ model sản phẩm hoặc không có số lượng, hãy đánh dấu vào missing_fields."
        )

        prompt = f"""Dưới đây là Danh mục Sản phẩm & Giá chuẩn của Công ty Minh An:
{catalog_summary}

--- VĂN BẢN YÊU CẦU CỦA KHÁCH HÀNG ---
{raw_text}

Hãy phân tích và trả về định dạng JSON với cấu trúc:
{{
  "sender_name": "Tên người liên hệ (hoặc rỗng nếu không có)",
  "company": "Tên công ty / đơn vị khách hàng",
  "sender_email": "Địa chỉ email (nếu có trong bài)",
  "phone": "Số điện thoại (nếu có)",
  "deadline_days": 10 (số ngày yêu cầu giao hàng/triển khai, nếu nói 'gấp' hoặc 'sáng mai' ghi 2, nếu không nhắc đến ghi null),
  "budget_vnd": 120000000 (ngân sách ước tính VNĐ, hoặc null nếu không có),
  "requested_discount_pct": 5.0 (tỷ lệ chiết khấu khách đề nghị %, hoặc 0.0 nếu không có),
  "items": [
    {{
      "matched_sku": "SKU-xxx khớp với catalog (nếu không xác định ghi null)",
      "requested_name": "Tên sản phẩm khách viết",
      "quantity": 2
    }}
  ],
  "missing_fields": ["Danh sách các thông tin cốt lõi bị thiếu để báo giá (ví dụ: 'chưa rõ mã sản phẩm', 'chưa rõ số lượng', 'thiếu thời hạn triển khai')"]
}}
Chỉ trả lời định dạng JSON hợp lệ, không bọc markdown thừa ngoài JSON."""

        raw_resp = self._call_llm(prompt, system_instruction=system_instruction)
        if not raw_resp:
            return None

        try:
            # Clean json fences if present
            cleaned = raw_resp
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            return json.loads(cleaned)
        except Exception:
            return None

    def draft_proposal_letter(self, deal_context: Dict[str, Any]) -> Optional[str]:
        """
        Sinh thư chào hàng & đề xuất giải pháp B2B mang tính thuyết phục cao.
        """
        prompt = f"""Hãy đóng vai NVKD chuyên nghiệp của Công ty Công nghệ Minh An, viết một bức thư Báo giá và Đề xuất giải pháp CNTT gửi khách hàng:
Thông tin cơ hội:
- Khách hàng: {deal_context.get('company')}
- Người nhận: {deal_context.get('customer_name')}
- Mã cơ hội: {deal_context.get('opp_id')}
- NVKD phụ trách: {deal_context.get('assigned_rep_name')} ({deal_context.get('assigned_rep_email')})
- Danh mục hạng mục: {json.dumps(deal_context.get('items', []), ensure_ascii=False)}
- Tổng giá trị niêm yết: {deal_context.get('subtotal', 0):,} VNĐ
- Chiết khấu ưu đãi: {deal_context.get('discount_pct', 0)}% (-{deal_context.get('discount_amount', 0):,} VNĐ)
- Tổng tiền sau chiết khấu (chưa VAT): {deal_context.get('total_after_discount', 0):,} VNĐ
- Thuế VAT 10%: {deal_context.get('vat_amount', 0):,} VNĐ
- Tổng thanh toán: {deal_context.get('grand_total', 0):,} VNĐ
- Thời gian bàn giao cam kết: {deal_context.get('fulfillment_days')} ngày làm việc.

Yêu cầu:
- Văn phong chuẩn mực B2B, trang trọng, lịch thiệp, tạo sự tin cậy cao.
- Nêu rõ cam kết chất lượng chính hãng và hỗ trợ kỹ thuật 24/7 từ Minh An.
- Nêu rõ điều khoản thanh toán (tạm ứng 30%, 70% sau nghiệm thu) và thời hạn báo giá 15 ngày."""

        return self._call_llm(prompt)

    def generate_manager_advice(self, deal_context: Dict[str, Any], reasons: List[str]) -> Optional[str]:
        """
        Sinh phân tích rủi ro & đề xuất phương án đàm phán cho Trưởng phòng Kinh doanh.
        """
        prompt = f"""Bạn là Cố vấn Chiến lược Bán hàng B2B cấp cao. Hãy viết bản tóm tắt phân tích và kiến nghị cho Trưởng phòng Kinh doanh Minh An về cơ hội bán hàng sau:
- Khách hàng: {deal_context.get('company')}
- Mã cơ hội: {deal_context.get('opp_id')}
- Tổng tiền: {deal_context.get('grand_total', 0):,} VNĐ
- Chiết khấu đề xuất: {deal_context.get('discount_pct', 0)}%
- Thời hạn khách muốn: {deal_context.get('requested_days')} ngày vs Khả thi: {deal_context.get('fulfillment_days')} ngày
- Các điểm vượt thẩm quyền: {json.dumps(reasons, ensure_ascii=False)}

Hãy đưa ra 3 phương án cụ thể:
1. Phương án Duyệt có điều kiện (ví dụ: chấp thuận chiết khấu nhưng tăng tỷ lệ tạm ứng lên 50%).
2. Phương án Thay thế kỹ thuật (nếu tiến độ giao hàng bị kẹt).
3. Đề xuất quyết định tối ưu nhất để vừa giữ chân khách hàng vừa bảo vệ lợi nhuận công ty."""

        return self._call_llm(prompt)

