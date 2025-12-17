import re
import os
import uuid

class RenameManager:
    def __init__(self):
        self.files = []
        self.history = []
        self.redo_stack = []

    def set_files(self, file_paths):
        self.files = []
        for f in file_paths:
            if os.path.exists(f):
                self.files.append({
                    'id': str(uuid.uuid4()),
                    'path': f,
                    'is_dir': os.path.isdir(f),
                    'override_name': None
                })
        self.files.sort(key=lambda x: x['path'])

    def add_files(self, file_paths):
        existing_paths = {f['path'] for f in self.files}
        for f in file_paths:
            if os.path.exists(f) and f not in existing_paths:
                self.files.append({
                    'id': str(uuid.uuid4()),
                    'path': f,
                    'is_dir': os.path.isdir(f),
                    'override_name': None
                })
        self.files.sort(key=lambda x: x['path'])

    def set_file_override(self, uid, new_name):
        """設定特定檔案的強制命名 (用於 AI 重命名)"""
        for f in self.files:
            if f['id'] == uid:
                f['override_name'] = new_name
                break

    def remove_file_by_id(self, target_id):
        self.files = [f for f in self.files if f['id'] != target_id]
        def filter_batch(batch):
            return [op for op in batch if op['id'] != target_id]
        self.history = [filter_batch(batch) for batch in self.history]
        self.history = [b for b in self.history if b]
        self.redo_stack = [filter_batch(batch) for batch in self.redo_stack]
        self.redo_stack = [b for b in self.redo_stack if b]

    def validate_files(self):
        missing_ids = [x['id'] for x in self.files if not os.path.exists(x['path'])]
        if missing_ids:
            for mid in missing_ids:
                self.remove_file_by_id(mid)
            return len(self.files), len(missing_ids)
        return len(self.files), 0

    def _convert_repl_format(self, repl_str):
        if not repl_str: return ""
        temp_marker = "___ESCAPED_DOLLAR___"
        s = repl_str.replace(r'\$', temp_marker)
        s = re.sub(r'\$(\d+)', r'\\\1', s)
        s = s.replace(temp_marker, '$')
        return s

    def get_preview(self, pattern, repl):
        self.validate_files()
        previews = []
        has_conflict = False
        
        regex = None
        clean_repl = ""
        regex_error = None
        
        if pattern:
            clean_repl = self._convert_repl_format(repl)
            try:
                regex = re.compile(pattern)
            except re.error as e:
                regex_error = f"RegEx 錯誤: {e}"

        seen_full_paths = set()

        for item in self.files:
            file_path = item['path']
            dir_name = os.path.dirname(file_path)
            old_name = os.path.basename(file_path)
            
            new_name = old_name # 預設不變

            # 邏輯判斷：優先權 Override > RegEx
            if item['override_name']:
                new_name = item['override_name']
            elif regex:
                try:
                    new_name = regex.sub(clean_repl, old_name)
                except re.error:
                    pass
            
            # 如果有 RegEx 錯誤且沒有 Override，回報錯誤
            if regex_error and not item['override_name']:
                return [], regex_error, False

            new_full_path = os.path.join(dir_name, new_name)
            status = "ok"
            
            if os.path.exists(new_full_path) and new_name != old_name:
                 status = "conflict"
                 has_conflict = True
            
            if new_full_path in seen_full_paths:
                status = "duplicate"
                has_conflict = True
            
            seen_full_paths.add(new_full_path)
            
            previews.append({
                'id': item['id'],
                'original': old_name, 
                'new': new_name, 
                'full_old': file_path,
                'full_new': new_full_path,
                'status': status,
                'is_dir': item['is_dir'],
                'is_overridden': bool(item['override_name']) # 讓 UI 知道這是 AI 命名的
            })

        return previews, None, has_conflict

    def execute_rename(self, previews):
        batch_history = []
        try:
            for item in previews:
                if item['original'] != item['new'] and item['status'] == 'ok':
                    os.rename(item['full_old'], item['full_new'])
                    
                    batch_history.append({
                        'id': item['id'],
                        'new_path': item['full_new'],
                        'old_path': item['full_old']
                    })
                    
                    for f in self.files:
                        if f['id'] == item['id']:
                            f['path'] = item['full_new']
                            f['override_name'] = None 
                            break
            
            if batch_history:
                self.history.append(batch_history)
                self.redo_stack.clear()
                self.files.sort(key=lambda x: x['path'])
                
            return True, f"成功重命名 {len(batch_history)} 個檔案"
        except Exception as e:
            self.validate_files()
            return False, f"執行失敗: {e}"

    def undo(self):
        if not self.history: return False, "無可復原的操作"
        last_batch = self.history.pop()
        redo_batch = []
        try:
            for op in last_batch:
                if os.path.exists(op['new_path']):
                    os.rename(op['new_path'], op['old_path'])
                    redo_batch.append({
                        'id': op['id'],
                        'new_path': op['old_path'],
                        'old_path': op['new_path']
                    })
                    for f in self.files:
                        if f['id'] == op['id']:
                            f['path'] = op['old_path']
                            break
            if redo_batch:
                self.redo_stack.append(redo_batch)
                self.files.sort(key=lambda x: x['path'])
                return True, "已復原"
            else:
                return False, "部分檔案已遺失"
        except Exception as e:
            self.validate_files()
            return False, f"復原失敗: {e}"

    def redo(self):
        if not self.redo_stack: return False, "無可重做的操作"
        last_redo_batch = self.redo_stack.pop()
        history_batch = []
        try:
            for op in last_redo_batch:
                src = op['new_path']
                dst = op['old_path']
                if os.path.exists(src):
                    os.rename(src, dst)
                    history_batch.append({
                        'id': op['id'],
                        'new_path': dst,
                        'old_path': src
                    })
                    for f in self.files:
                        if f['id'] == op['id']:
                            f['path'] = dst
                            break
            if history_batch:
                self.history.append(history_batch)
                self.files.sort(key=lambda x: x['path'])
                return True, "已重做"
            else:
                return False, "無法重做"
        except Exception as e:
            self.validate_files()
            return False, f"重做失敗: {e}"