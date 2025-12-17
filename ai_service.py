import os
import base64
from openai import OpenAI, BadRequestError
from doc_parser import DocParser

MAX_SIZE_MB = 2

ALLOWED_EXTENSIONS = {
    '.jpg', '.png', '.jpeg', 
    '.txt', '.csv', '.xlsx', '.docx', '.pdf', 
    '.md', '.py', '.json', '.js', '.html', '.css', '.xml', '.yml', '.yaml', 
    '.jsonl', '.tsv', '.log', '.mdx', '.ts', '.tsx', '.jsx'
}

IMAGE_EXTENSIONS = {'.jpg', '.png', '.jpeg'}

TEXT_EXTENSIONS = {
    '.txt', '.csv', '.md', '.py', '.json', '.js', '.html', '.css', '.xml', 
    '.yml', '.yaml', '.jsonl', '.tsv', '.log', '.mdx', '.ts', '.tsx', '.jsx'
}

DOC_EXTENSIONS = {'.xlsx', '.docx', '.pdf'}

class AIService:
    _client = None
    _api_key = None
    _base_url = "https://api.openai.com/v1"
    
    # 模型名稱
    MODEL_NAME = "gpt-5-nano"

    @staticmethod
    def is_configured():
        return AIService._client is not None

    @staticmethod
    def configure(api_key, base_url):
        AIService._api_key = api_key
        AIService._base_url = base_url
        AIService._client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    @staticmethod
    def validate_file(file_path):
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"不支援的格式: {ext}"

        try:
            if not os.path.exists(file_path):
                 return False, "檔案不存在"
        except OSError as e:
            return False, f"無法讀取檔案: {e}"

        return True, ""

    @staticmethod
    def _encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    @staticmethod
    def _read_text_head(file_path, chars=3000):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(chars)
        except Exception:
            return None

    @staticmethod
    def analyze_and_rename(file_path):
        if not AIService._client:
            return None, "尚未設定 API Key"

        valid, msg = AIService.validate_file(file_path)
        if not valid:
            return None, msg

        base_name = os.path.basename(file_path)
        _, ext = os.path.splitext(base_name)
        ext = ext.lower()

        try:
            messages = []
            user_content = []
            
            system_prompt = (
                "You are a file renaming assistant. "
                "Analyze the user's file content and suggest a short, descriptive, English filename (snake_case). "
                f"You must KEEP the original extension '{ext}'. "
                "Output ONLY the filename. No markdown, no explanation."
            )

            if ext in IMAGE_EXTENSIONS:
                base64_image = AIService._encode_image(file_path)
                user_content.append({"type": "text", "text": "What is in this image? Rename it."})
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
            
            elif ext in TEXT_EXTENSIONS:
                content = AIService._read_text_head(file_path)
                if content:
                    user_content.append({"type": "text", "text": f"File content:\n{content}\n\nSuggest a filename."})
                else:
                    user_content.append({"type": "text", "text": f"Original filename: '{base_name}'. Content is empty or unreadable. Suggest a clean filename."})

            elif ext in DOC_EXTENSIONS:
                content = DocParser.extract_content(file_path)
                if content:
                     user_content.append({"type": "text", "text": f"Document content excerpt:\n{content}\n\nSuggest a filename based on this content."})
                else:
                     user_content.append({"type": "text", "text": f"Original filename: '{base_name}'. Could not parse document text. Suggest a clean filename."})

            else:
                user_content.append({"type": "text", "text": f"Original filename: '{base_name}'. Clean up and standardize this filename."})

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            is_official_api = "api.openai.com" in AIService._base_url
            
            SAFE_TOKEN_LIMIT = 1000 

            request_kwargs = {
                "model": AIService.MODEL_NAME,
                "messages": messages,
            }

            request_kwargs["reasoning_effort"] = "low"

            if is_official_api:
                request_kwargs["max_completion_tokens"] = SAFE_TOKEN_LIMIT
            else:
                request_kwargs["max_tokens"] = SAFE_TOKEN_LIMIT

            # --- 發送請求與自動修復邏輯 ---
            def send_request(kwargs):
                print("[Debug] 發送請求:", kwargs)
                return AIService._client.chat.completions.create(**kwargs)

            try:
                response = send_request(request_kwargs)

            except BadRequestError as e:
                error_msg = str(e).lower()
                retry_needed = False
                
                if "reasoning_effort" in error_msg or (e.body and "reasoning_effort" in str(e.body)):
                    print("API 不支援 reasoning_effort，移除後重試...")
                    if "reasoning_effort" in request_kwargs:
                        del request_kwargs["reasoning_effort"]
                        retry_needed = True

                if "max_tokens" in error_msg or "max_completion_tokens" in error_msg:
                    print("API Token 參數不相容，切換參數名稱後重試...")

                    if "max_tokens" in request_kwargs:
                        del request_kwargs["max_tokens"]
                        request_kwargs["max_completion_tokens"] = SAFE_TOKEN_LIMIT
                    elif "max_completion_tokens" in request_kwargs:
                        del request_kwargs["max_completion_tokens"]
                        request_kwargs["max_tokens"] = SAFE_TOKEN_LIMIT
                    retry_needed = True
                
                if retry_needed:
                    try:
                        response = send_request(request_kwargs)
                    except Exception as e2:
                        raise e2
                else:
                    raise e

            # --- 處理回應 ---
            suggested_name = response.choices[0].message.content.strip()
            suggested_name = suggested_name.replace("`", "").strip()
            
            if not suggested_name.lower().endswith(ext):
                suggested_name += ext

            return suggested_name, "AI 分析完成"

        except Exception as e:
            return None, f"API 請求錯誤: {str(e)}"