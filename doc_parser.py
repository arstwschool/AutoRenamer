import os
import openpyxl
from docx import Document
import fitz

class DocParser:
    MAX_CHARS = 3000

    @staticmethod
    def extract_content(file_path):
        """
        根據副檔名分發處理邏輯。
        回傳: (str) 文件內容摘要，若失敗則回傳 None
        """
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.xlsx':
                return DocParser._read_xlsx(file_path)
            elif ext == '.docx':
                return DocParser._read_docx(file_path)
            elif ext == '.pdf':
                return DocParser._read_pdf(file_path)
            return None
        except Exception as e:
            print(f"解析文件失敗 {file_path}: {e}")
            return None

    @staticmethod
    def _read_xlsx(file_path):
        text_content = []
        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
            sheet = workbook.active
            for row in sheet.iter_rows(values_only=True):
                row_items = [str(cell).strip() for cell in row if cell is not None]
                row_text = " ".join(row_items)
                
                if row_text:
                    text_content.append(row_text)
                
                if sum(len(t) for t in text_content) > DocParser.MAX_CHARS:
                    break
            workbook.close()
        except Exception:
            pass
            
        return "\n".join(text_content)

    @staticmethod
    def _read_docx(file_path):
        text_content = []
        current_len = 0
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    text_content.append(text)
                    current_len += len(text)
                    if current_len > DocParser.MAX_CHARS:
                        break
        except Exception:
            pass
            
        return "\n".join(text_content)

    @staticmethod
    def _read_pdf(file_path):
        text_content = []
        current_len = 0
        
        try:
            with fitz.open(file_path) as doc:
                # max_pages = min(len(doc), 5)
                max_pages = len(doc)
                
                for i in range(max_pages):
                    page = doc[i]
                    text = page.get_text("text").strip()
                    
                    if text:
                        text_content.append(text)
                        current_len += len(text)
                        if current_len > DocParser.MAX_CHARS:
                            break
        except Exception as e:
            print(f"PDF 讀取錯誤: {e}")
            
        result = "\n".join(text_content)

        if not result.strip():
            return "[PDF is scanned image or encrypted, content unreadable]"
            
        return result