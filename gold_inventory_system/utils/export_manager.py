import os
from datetime import datetime
from typing import List, Dict
from database.db_manager import EXPORTS_DIR
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font

GREEN = '90EE90'
RED = 'FFB6C1'


class ExportManager:
    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime('%Y%m%d_%H%M%S')

    @staticmethod
    def export_comparison_to_html(rows: List[Dict[str, object]], meta: Dict[str, str]) -> str:
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        filename = f"comparison_{meta.get('year','')}-{meta.get('month','')}_{ExportManager._timestamp()}.html"
        path = os.path.join(EXPORTS_DIR, filename)
        css = f"""
        body {{ font-family: Arial, sans-serif; direction: rtl; }}
        h1, h2, h3 {{ text-align: right; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
        th {{ background: #f2f2f2; }}
        .pos {{ background-color: #{GREEN}; }}
        .neg {{ background-color: #{RED}; }}
        """
        header = f"""
        <h1>{meta.get('factory_name','')}</h1>
        <h2>{meta.get('report_title','')}</h2>
        <p>التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p>السنة: {meta.get('year','')} الشهر: {meta.get('month','')}</p>
        """
        rows_html = []
        rows_html.append('<table>')
        rows_html.append('<tr><th>اسم الصنف</th><th>الوحدة</th><th>الشهر الحالي</th><th>الشهر السابق</th><th>الفرق</th></tr>')
        for r in rows:
            diff = float(r['diff'])
            sign = '+' if diff > 0 else ('-' if diff < 0 else '')
            cls = 'pos' if diff > 0 else ('neg' if diff < 0 else '')
            diff_text = f"{sign}{abs(diff):.3f}"
            rows_html.append(
                f"<tr><td>{r['name']}</td><td>{r['unit']}</td>"
                f"<td>{float(r['qty_curr']):.3f}</td><td>{float(r['qty_prev']):.3f}</td>"
                f"<td class='{cls}'>{diff_text}</td></tr>"
            )
        rows_html.append('</table>')
        html = f"""
        <html>
        <head><meta charset='utf-8'><style>{css}</style><title>تقرير</title></head>
        <body>{header}{''.join(rows_html)}</body>
        </html>
        """
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        return path

    @staticmethod
    def export_comparison_to_excel(rows: List[Dict[str, object]], meta: Dict[str, str]) -> str:
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        filename = f"comparison_{meta.get('year','')}-{meta.get('month','')}_{ExportManager._timestamp()}.xlsx"
        path = os.path.join(EXPORTS_DIR, filename)
        wb = Workbook()
        ws = wb.active
        ws.title = 'تقرير'

        header_font = Font(bold=True)
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        align = Alignment(horizontal='right')

        headers = ['اسم الصنف', 'الوحدة', 'الشهر الحالي', 'الشهر السابق', 'الفرق']
        ws.append(headers)
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = header_font
            cell.border = border
            cell.alignment = align

        for r in rows:
            diff = float(r['diff'])
            sign = '+' if diff > 0 else ('-' if diff < 0 else '')
            diff_text = f"{sign}{abs(diff):.3f}"
            row_values = [
                r['name'], r['unit'], float(r['qty_curr']), float(r['qty_prev']), diff_text
            ]
            ws.append(row_values)
            last_row = ws.max_row
            for col in range(1, 6):
                cell = ws.cell(row=last_row, column=col)
                cell.border = border
                cell.alignment = align
            diff_cell = ws.cell(row=last_row, column=5)
            if diff > 0:
                diff_cell.fill = PatternFill(start_color=GREEN, end_color=GREEN, fill_type='solid')
            elif diff < 0:
                diff_cell.fill = PatternFill(start_color=RED, end_color=RED, fill_type='solid')

        for col in range(1, 6):
            ws.column_dimensions[chr(64 + col)].width = 20

        wb.save(path)
        return path