"""
Quotation Document Exporter for Minh An B2B Sales
Generates professional Excel (.xlsx) quotations with formatting, styling and formulas.
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def generate_excel_quotation(opportunity_data: Dict[str, Any], output_path: str = None) -> str:
    """
    Xuất bảng Báo giá chính thức định dạng Excel chuẩn doanh nghiệp B2B.
    Tương thích hoàn toàn với môi trường Serverless (Vercel/AWS Lambda) sử dụng /tmp.
    """
    opp = opportunity_data["opportunity"]
    ver = opportunity_data["verification"]
    quo = opportunity_data["quotation"]
    
    if output_path is None:
        # Sử dụng thư mục tạm hệ thống (tương thích Vercel /tmp và Windows Temp)
        quotes_dir = os.path.join(tempfile.gettempdir(), "minhan_exports")
        os.makedirs(quotes_dir, exist_ok=True)
        filename = f"Bao_Gia_{opp['opp_id']}_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
        output_path = os.path.join(quotes_dir, filename)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Báo Giá B2B"
    ws.views.sheetView[0].showGridLines = True

    # Định nghĩa Styles
    font_company = Font(name="Calibri", size=15, bold=True, color="1B365D")
    font_sub = Font(name="Calibri", size=10, italic=True, color="555555")
    font_title = Font(name="Calibri", size=16, bold=True, color="0D47A1")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=11, bold=True)
    font_regular = Font(name="Calibri", size=11)
    
    fill_header = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    fill_summary = PatternFill(start_color="F2F4F7", end_color="F2F4F7", fill_type="solid")
    fill_highlight = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

    thin_border_side = Side(border_style="thin", color="CCCCCC")
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_bottom = Border(bottom=Side(border_style="double", color="1F4E79"))

    # 1. Header Công ty
    ws.merge_cells("A1:G1")
    ws["A1"] = "CÔNG TY TNHH CÔNG NGHỆ MINH AN"
    ws["A1"].font = font_company

    ws.merge_cells("A2:G2")
    ws["A2"] = "Địa chỉ: Tầng 8, Tòa nhà Công nghệ, Cầu Giấy, Hà Nội | Hotline: 024.3999.8888 | Email: sales@minhan.com.vn"
    ws["A2"].font = font_sub

    # 2. Tiêu đề Báo giá
    ws.merge_cells("A4:G4")
    ws["A4"] = "BẢNG BÁO GIÁ VÀ ĐỀ XUẤT THIẾT BỊ - GIẢI PHÁP CNTT"
    ws["A4"].font = font_title
    ws["A4"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A5:G5")
    ws["A5"] = f"Mã số báo giá: {opp['opp_id']}  |  Ngày lập: {datetime.now().strftime('%d/%m/%Y')}  |  Hiệu lực: 15 ngày"
    ws["A5"].font = font_sub
    ws["A5"].alignment = Alignment(horizontal="center")

    # 3. Thông tin Khách hàng & Nhân viên phụ trách
    ws["A7"] = "Đơn vị nhận báo giá:"
    ws["A7"].font = font_bold
    ws["B7"] = opp["company"]
    ws["B7"].font = font_bold

    ws["A8"] = "Người liên hệ:"
    ws["A8"].font = font_bold
    ws["B8"] = f"{opp['customer_name']} (Email: {opp['email']} - SĐT: {opp['phone'] or 'N/A'})"
    ws["B8"].font = font_regular

    ws["E7"] = "Đại diện kinh doanh:"
    ws["E7"].font = font_bold
    ws["F7"] = opp["assigned_rep"]["name"]
    ws["F7"].font = font_bold

    ws["E8"] = "Email phụ trách:"
    ws["E8"].font = font_bold
    ws["F8"] = opp["assigned_rep"]["email"]
    ws["F8"].font = font_regular

    # 4. Bảng danh mục sản phẩm (Table Header)
    row = 10
    headers = ["STT", "Mã SKU", "Tên Hàng Hóa / Dịch Vụ", "Số Lượng", "Đơn Giá (VNĐ)", "Thành Tiền (VNĐ)", "Tình Trạng Kho"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_cell
    ws.row_dimensions[row].height = 25

    # 5. Dòng dữ liệu
    row_start = row + 1
    for idx, item in enumerate(ver["verified_items"], 1):
        row += 1
        stock_text = "Sẵn sàng (2 ngày)" if item["is_in_stock"] else f"Nhập hàng ({item['fulfillment_days']} ngày)"
        
        ws.cell(row=row, column=1, value=idx).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=2, value=item["sku"]).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=3, value=item["name"]).alignment = Alignment(horizontal="left")
        ws.cell(row=row, column=4, value=item["quantity"]).alignment = Alignment(horizontal="center")
        
        c_price = ws.cell(row=row, column=5, value=item["unit_price"])
        c_price.number_format = "#,##0"
        c_price.alignment = Alignment(horizontal="right")

        c_total = ws.cell(row=row, column=6, value=f"=D{row}*E{row}")
        c_total.number_format = "#,##0"
        c_total.alignment = Alignment(horizontal="right")

        c_stock = ws.cell(row=row, column=7, value=stock_text)
        c_stock.alignment = Alignment(horizontal="center")

        for c in range(1, 8):
            ws.cell(row=row, column=c).font = font_regular
            ws.cell(row=row, column=c).border = border_cell
        ws.row_dimensions[row].height = 22

    row_end = row

    # 6. Tổng kết tài chính
    row += 1
    ws.merge_cells(f"A{row}:E{row}")
    ws.cell(row=row, column=1, value="Tổng giá trị niêm yết (chưa chiết khấu):").alignment = Alignment(horizontal="right")
    ws.cell(row=row, column=1).font = font_bold
    ws.cell(row=row, column=6, value=f"=SUM(F{row_start}:F{row_end})").number_format = "#,##0"
    ws.cell(row=row, column=6).font = font_bold
    ws.row_dimensions[row].height = 20

    row += 1
    ws.merge_cells(f"A{row}:E{row}")
    ws.cell(row=row, column=1, value=f"Chiết khấu thương mại ({quo['discount_pct']}%):").alignment = Alignment(horizontal="right")
    ws.cell(row=row, column=1).font = font_bold
    ws.cell(row=row, column=6, value=f"=F{row-1}*{quo['discount_pct']}/100").number_format = "#,##0"
    ws.cell(row=row, column=6).font = font_bold
    ws.row_dimensions[row].height = 20

    row += 1
    ws.merge_cells(f"A{row}:E{row}")
    ws.cell(row=row, column=1, value="Tổng tiền trước thuế GTGT (VAT):").alignment = Alignment(horizontal="right")
    ws.cell(row=row, column=1).font = font_bold
    ws.cell(row=row, column=6, value=f"=F{row-2}-F{row-1}").number_format = "#,##0"
    ws.cell(row=row, column=6).font = font_bold
    ws.row_dimensions[row].height = 20

    row += 1
    ws.merge_cells(f"A{row}:E{row}")
    ws.cell(row=row, column=1, value="Thuế GTGT (VAT 10%):").alignment = Alignment(horizontal="right")
    ws.cell(row=row, column=1).font = font_bold
    ws.cell(row=row, column=6, value=f"=F{row-1}*0.1").number_format = "#,##0"
    ws.cell(row=row, column=6).font = font_bold
    ws.row_dimensions[row].height = 20

    row += 1
    ws.merge_cells(f"A{row}:E{row}")
    cell_tot_lbl = ws.cell(row=row, column=1, value="TỔNG CỘNG THANH TOÁN (ĐÃ GỒM VAT):")
    cell_tot_lbl.alignment = Alignment(horizontal="right")
    cell_tot_lbl.font = Font(name="Calibri", size=12, bold=True, color="1F4E79")
    cell_tot_val = ws.cell(row=row, column=6, value=f"=F{row-2}+F{row-1}")
    cell_tot_val.number_format = "#,##0"
    cell_tot_val.font = Font(name="Calibri", size=12, bold=True, color="1F4E79")
    cell_tot_val.fill = fill_highlight
    ws.row_dimensions[row].height = 25

    # 7. Điều khoản & Chữ ký
    row += 2
    ws.cell(row=row, column=1, value="ĐIỀU KHOẢN THƯƠNG MẠI & BẢO HÀNH:").font = font_bold
    
    terms = [
        f"1. Tiến độ giao hàng: Trong vòng {ver['earliest_fulfillment_days']} ngày làm việc kể từ ngày ký Hợp đồng.",
        "2. Địa điểm giao hàng: Tận nơi theo yêu cầu của Quý công ty tại Việt Nam.",
        "3. Thanh toán: Tạm ứng 30% khi ký Hợp đồng, 70% còn lại trong vòng 07 ngày sau khi nghiệm thu.",
        "4. Bảo hành: Bảo hành chính hãng 100% kèm dịch vụ hỗ trợ kỹ thuật 24/7 từ Minh An."
    ]
    for t in terms:
        row += 1
        ws.cell(row=row, column=1, value=t).font = font_regular

    row += 2
    ws.cell(row=row, column=2, value="ĐẠI DIỆN KHÁCH HÀNG").font = font_bold
    ws.cell(row=row, column=2).alignment = Alignment(horizontal="center")
    ws.cell(row=row, column=6, value="ĐẠI DIỆN CÔNG TY MINH AN").font = font_bold
    ws.cell(row=row, column=6).alignment = Alignment(horizontal="center")

    row += 1
    ws.cell(row=row, column=2, value="(Ký, ghi rõ họ tên)").font = font_sub
    ws.cell(row=row, column=2).alignment = Alignment(horizontal="center")
    ws.cell(row=row, column=6, value=f"{opp['assigned_rep']['name']}").font = font_sub
    ws.cell(row=row, column=6).alignment = Alignment(horizontal="center")

    # Điều chỉnh độ rộng cột tự động
    col_widths = {1: 8, 2: 18, 3: 45, 4: 12, 5: 18, 6: 22, 7: 22}
    for col_idx, width in col_widths.items():
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = width

    wb.save(output_path)
    return output_path
