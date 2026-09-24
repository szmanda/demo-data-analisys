"""
Generic Excel exporter parametrized by table schema and dataset.
Creates:
1. A consolidated multi-sheet workbook containing all tables.
2. Individual .xlsx workbooks per table for pipeline compatibility.
"""
from pathlib import Path
from typing import Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from src.schema import DatabaseSchema


class ExcelExporter:
    def __init__(self, output_dir: Path | str):
        self.output_dir = Path(output_dir)

    def _style_header(self, ws):
        header_fill = PatternFill(start_color="2F4F4F", end_color="2F4F4F", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

    def export(
        self,
        schema: DatabaseSchema,
        dataset: dict[str, list[dict[str, Any]]],
        export_individual: bool = True
    ) -> list[Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        created_files: list[Path] = []

        # 1. Consolidated multi-sheet workbook
        consolidated_path = self.output_dir / "olejki_calosc.xlsx"
        master_wb = openpyxl.Workbook()
        # Remove default active sheet later
        first_sheet = True

        for table_name, rows in dataset.items():
            table_schema = schema.get_table(table_name)
            if not table_schema:
                continue

            columns = table_schema.column_names
            # Excel worksheet name limit is 31 chars
            sheet_title = table_name[:31]

            if first_sheet:
                ws = master_wb.active
                ws.title = sheet_title
                first_sheet = False
            else:
                ws = master_wb.create_sheet(title=sheet_title)

            # Write header
            ws.append(columns)
            # Write rows
            for row in rows:
                ws.append([row.get(col) for col in columns])

            self._style_header(ws)
            ws.freeze_panes = "A2"

            # 2. Individual table workbook
            if export_individual:
                single_wb = openpyxl.Workbook()
                single_ws = single_wb.active
                single_ws.title = sheet_title
                single_ws.append(columns)
                for row in rows:
                    single_ws.append([row.get(col) for col in columns])
                self._style_header(single_ws)
                single_ws.freeze_panes = "A2"
                single_path = self.output_dir / f"{table_name}.xlsx"
                single_wb.save(single_path)
                created_files.append(single_path)

        master_wb.save(consolidated_path)
        created_files.append(consolidated_path)

        return created_files
