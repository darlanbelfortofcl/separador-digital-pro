class JobStore:
    def __init__(self, path: Path):
        import json
        self.Path = Path
        self.json = json
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists(): self.path.write_text("{}", encoding='utf-8')
    def _read(self): return self.json.loads(self.path.read_text(encoding='utf-8'))
    def _write(self, obj): self.path.write_text(self.json.dumps(obj, ensure_ascii=False), encoding='utf-8')
    def put(self, task_id: str, payload: dict):
        data=self._read(); data[task_id]=payload; self._write(data)
    def get(self, task_id: str):
        return self._read().get(task_id)
