"""
Test Suite and Demonstration Runner for Minh An B2B Sales AI Agent
"""

import os
import json
from src.engine import SalesOpportunityAgent

def print_separator(char="=", length=80):
    print(char * length)

def run_all_scenarios():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    
    agent = SalesOpportunityAgent(data_dir=data_dir)
    sample_requests_path = os.path.join(data_dir, "sample_requests.json")
    
    with open(sample_requests_path, "r", encoding="utf-8") as f:
        requests = json.load(f)
        
    print_separator("=")
    print("   HỆ THỐNG AI AGENT XỬ LÝ CƠ HỘI BÁN HÀNG B2B - MINH AN COMPANY")
    print("   Kiểm thử 5 Kịch bản Thực tế theo Quy trình Chuẩn")
    print_separator("=")

    for idx, req in enumerate(requests, 1):
        print(f"\n[KỊCH BẢN {idx}/{len(requests)}]: {req['id']} - {req['company']} ({req['channel']})")
        print(f"Người gửi: {req['sender_name']} <{req['sender_email']}> | SĐT: {req['phone']}")
        print(f"Kỳ vọng nghiệp vụ: {req['test_expected_outcome']}")
        print_separator("-", 60)
        
        result = agent.process_complete_workflow(req)
        
        # In các bước thực thi
        print(">> LUỒNG THỰC THI (WORKFLOW EXECUTION LOG):")
        for s in result["step_logs"]:
            print(f"   [Bước {s['step']}] {s['title']} -> {s['status']}")
            
        print_separator(".", 40)
        
        if result["workflow_outcome"] == "AWAITING_CUSTOMER_CLARIFICATION":
            clarification = result["clarification"]
            print("[KẾT QUẢ]: THIẾU THÔNG TIN -> KÍCH HOẠT NHÁNH YÊU CẦU LÀM RÕ")
            print(f"Các trường thông tin còn thiếu:")
            for m in clarification["missing_fields"]:
                print(f"  * {m}")
            print("\n[BẢN NHÁP EMAIL TỰ ĐỘNG GỬI KHÁCH HÀNG]:")
            print(clarification["clarification_email_subject"])
            print(clarification["clarification_email_body"])
            
        else:
            opp = result["opportunity"]
            ver = result["verification"]
            quo = result["quotation"]
            app = result["approval"]
            
            print(f"[KẾT QUẢ]: ĐỦ THÔNG TIN -> ĐÃ TẠO HỒ SƠ CƠ HỘI")
            print(f"  - Mã cơ hội: {opp['opp_id']}")
            print(f"  - NVKD phụ trách: {opp['assigned_rep']['name']} ({opp['assigned_rep']['specialty']})")
            print(f"  - Thẩm định kho & lead time: Thời gian khả thi = {ver['earliest_fulfillment_days']} ngày | Khách yêu cầu = {ver['requested_deadline_days']} ngày")
            if ver["has_stock_shortage"]:
                print(f"    (!) TỒN KHO THIẾU: {len(ver['shortage_details'])} hạng mục cần nhập bổ sung.")
            if ver["timeline_conflict"]:
                print(f"    (!) CẢNH BÁO TIẾN ĐỘ: {ver['timeline_warning_message']}")
                
            print(f"  - Tổng niêm yết: {quo['subtotal']:,.0f} đ | Chiết khấu: {quo['discount_pct']}% ({quo['discount_amount']:,.0f} đ)")
            print(f"  - Tổng thanh toán (VAT): {quo['grand_total']:,.0f} VNĐ")
            print(f"  - Đánh giá ngân sách khách: {quo['budget_status']}")
            
            print_separator(".", 40)
            if app["requires_manager_approval"]:
                print("[PHÊ DUYỆT]: VƯỢT THẨM QUYỀN -> CHUYỂN TRƯỞNG PHÒNG DUYỆT")
                for r in app["escalation_reasons"]:
                    print(f"  (!) Lý do: {r}")
                print("\n[TỜ TRÌNH TRƯỞNG PHÒNG TỰ ĐỘNG]:")
                print(app["manager_brief"])
            else:
                print(f"[PHÊ DUYỆT]: HỢP LỆ TRONG THẨM QUYỀN -> SẴN SÀNG GỬI BÁO GIÁ CHO KHÁCH")
                print(f"\n[BẢN NHÁP BÁO GIÁ & ĐỀ XUẤT (PROPOSAL DRAFT)]:")
                print(quo["proposal_email_subject"])
                print(quo["proposal_email_body"])
                
        print_separator("=", 80)

if __name__ == "__main__":
    run_all_scenarios()

