import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel

logger = logging.getLogger("docnest.tables")


class ExtractedTable(BaseModel):
    table_index: int
    page_number: int
    row_count: int
    column_count: int
    headers: List[str]
    markdown_table: str
    raw_lines: List[str]


class TableExtractor:
    """
    Structure-preserving table extraction service converting ASCII tables,
    whitespace-aligned columns, and delimited tabular structures into clean Markdown.
    """

    MIN_TABLE_ROWS = 2
    MIN_TABLE_COLS = 2

    def extract_tables_from_text(self, text: str, page_number: int = 1) -> Tuple[str, List[ExtractedTable]]:
        """
        Scan text for tabular regions, replace them with formatted Markdown tables,
        and return extracted table metadata.
        """
        lines = text.splitlines()
        extracted_tables: List[ExtractedTable] = []
        output_lines: List[str] = []

        table_buffer: List[str] = []
        table_idx = 1

        for line in lines:
            if self._is_table_row(line):
                table_buffer.append(line)
            else:
                if len(table_buffer) >= self.MIN_TABLE_ROWS:
                    md_table, meta = self.format_table_block(table_buffer, table_idx, page_number)
                    if meta:
                        extracted_tables.append(meta)
                        output_lines.append(md_table)
                        table_idx += 1
                    else:
                        output_lines.extend(table_buffer)
                elif table_buffer:
                    output_lines.extend(table_buffer)

                table_buffer = []
                output_lines.append(line)

        # Flush remaining buffer
        if len(table_buffer) >= self.MIN_TABLE_ROWS:
            md_table, meta = self.format_table_block(table_buffer, table_idx, page_number)
            if meta:
                extracted_tables.append(meta)
                output_lines.append(md_table)
            else:
                output_lines.extend(table_buffer)
        elif table_buffer:
            output_lines.extend(table_buffer)

        return "\n".join(output_lines), extracted_tables

    def _is_table_row(self, line: str) -> bool:
        """Heuristic check whether a line resembles a tabular row."""
        s = line.strip()
        if not s:
            return False
        # Pipe delimited
        if s.startswith("|") and s.endswith("|"):
            return True
        # Tab delimited with 1+ tabs
        if s.count("\t") >= 1:
            return True
        # Multiple columns separated by 2+ consecutive spaces
        chunks = [c.strip() for c in re.split(r"\s{2,}", s) if c.strip()]
        if len(chunks) >= self.MIN_TABLE_COLS:
            return True
        return False

    def format_table_block(
        self,
        lines: List[str],
        table_index: int = 1,
        page_number: int = 1,
    ) -> Tuple[str, Optional[ExtractedTable]]:
        """Parse raw lines into a standardized GitHub Flavored Markdown table."""
        rows: List[List[str]] = []

        for line in lines:
            s = line.strip()
            # Skip existing divider rows |---|---|
            if re.match(r"^\|?(\s*:?-+:?\s*\|)+\s*$", s):
                continue

            if "|" in s:
                cells = [c.strip() for c in s.split("|")]
                if cells and not cells[0]:
                    cells.pop(0)
                if cells and not cells[-1]:
                    cells.pop()
            elif "\t" in s:
                cells = [c.strip() for c in s.split("\t") if c.strip()]
            else:
                cells = [c.strip() for c in re.split(r"\s{2,}", s) if c.strip()]

            if cells:
                rows.append(cells)

        if len(rows) < self.MIN_TABLE_ROWS:
            return "\n".join(lines), None

        max_cols = max(len(r) for r in rows)
        if max_cols < self.MIN_TABLE_COLS:
            return "\n".join(lines), None

        # Build clean Markdown table
        headers = rows[0] + [""] * (max_cols - len(rows[0]))
        clean_headers = [h.replace("|", "/") for h in headers]

        md_lines = [
            "| " + " | ".join(clean_headers) + " |",
            "| " + " | ".join(["---"] * max_cols) + " |",
        ]

        for r in rows[1:]:
            padded_row = r + [""] * (max_cols - len(r))
            clean_cells = [c.replace("|", "/") for c in padded_row]
            md_lines.append("| " + " | ".join(clean_cells) + " |")

        formatted_md = "\n".join(md_lines)
        meta = ExtractedTable(
            table_index=table_index,
            page_number=page_number,
            row_count=len(rows),
            column_count=max_cols,
            headers=clean_headers,
            markdown_table=formatted_md,
            raw_lines=lines,
        )

        return formatted_md, meta


_table_extractor: Optional[TableExtractor] = None


def get_table_extractor() -> TableExtractor:
    global _table_extractor
    if _table_extractor is None:
        _table_extractor = TableExtractor()
    return _table_extractor
