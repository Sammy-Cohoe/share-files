import asyncio
from pathlib import Path
from typing import Dict, List
from unstructured.partition.auto import partition
import pdfplumber

from .base import BaseExtractor, ExtractedContent

class UnstructuredExtractor(BaseExtractor):
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.txt', '.doc'}
    
    async def extract(self, file_path: str) -> ExtractedContent:
        loop = asyncio.get_event_loop()

        pdf_tables = await loop.run_in_executor(
            None,
            self._extract_tables_with_pdfplumber,
            file_path
        )

        elements = await loop.run_in_executor(
            None, 
            partition,
            file_path
        )

        organized = self._organize_elements(elements, pdf_tables)

        return ExtractedContent(
            sections=organized['sections'],
            tables=organized['tables'],
            metadata=organized['metadata'],
            full_text=organized['full_text'],
            has_tables=len(organized['tables']) > 0
        )
        
        
    def supports_file_type(self, file_path: str) -> bool:
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS

    def _extract_tables_with_pdfplumber(self, file_path: str) -> List[Dict]:
        tables = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()

                    for table_num, table in enumerate(page_tables, 1):
                        if table:
                            # Convert table to text representation
                            table_text = self._table_to_text(table)

                            tables.append({
                                'text': table_text,
                                'data': table,  # Raw table data as list of lists
                                'metadata': {
                                    'page_number': page_num,
                                    'table_number': table_num,
                                    'rows': len(table),
                                    'columns': len(table[0]) if table else 0
                                }
                            })
        except Exception as e:
            print(f"Warning: pdfplumber table extraction failed: {e}")

        return tables

    def _table_to_text(self, table: List[List]) -> str:
        """Convert a table (list of lists) to formatted text"""
        if not table:
            return ""

        # Filter out None values and convert to strings
        cleaned_table = []
        for row in table:
            cleaned_row = [str(cell) if cell is not None else "" for cell in row]
            cleaned_table.append(cleaned_row)

        # Calculate column widths
        if not cleaned_table:
            return ""

        col_widths = [0] * len(cleaned_table[0])
        for row in cleaned_table:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        # Format table as text
        lines = []
        for row in cleaned_table:
            formatted_row = " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
            lines.append(formatted_row)

        return "\n".join(lines)
    
    def _organize_elements(self, elements, pdf_tables: List[Dict]) -> Dict:
        sections = {}
        all_text = []
        current_section = 'introduction'
        sections[current_section] = []

        # Colect table cells to filter them out 
        table_cells = set()
        for table in pdf_tables:
            for row in table.get('data', []):
                for cell in row:
                    if cell:
                        table_cells.add(str(cell).strip().lower())

        for element in elements:
            element_type = type(element).__name__
            element_text = element.text.strip()

            if element_text.lower() in table_cells:
                continue

            if element_type == 'Title':
                slash_count = element_text.count('/')
                word_count = len(element_text.split())

                # Skip if it looks like concatenated table cells
                if slash_count >= 1 and word_count <= 3:
                    continue

                # Only create section if title is substantial
                if len(element_text) > 3:
                    section_name = element_text.lower().replace(' ', '_')
                    current_section = section_name
                    sections[current_section] = []
                    all_text.append(element_text)

            elif element_type == 'NarrativeText':
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(element_text)
                all_text.append(element_text)

            elif element_type == 'ListItem':
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(element_text)
                all_text.append(element_text)

        for table in pdf_tables:
            all_text.append(table['text'])

        return {
            'sections': sections,
            'tables': pdf_tables,
            'metadata': {
                'total_sections': len(sections),
                'total_tables': len(pdf_tables)
            },
            'full_text': '\n\n'.join(all_text)
        }
        
    def _extract_element_metadata(self, element):
        if hasattr(element, 'metadata') and element.metadata:
            if hasattr(element.metadata, 'to_dict'):
                return element.metadata.to_dict()
            return dict(element.metadata)
        return {}
            
