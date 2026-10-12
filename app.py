"""Local browser demo. Run python3 app.py, then open http://127.0.0.1:8765."""
import json, os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from engine import answer

def load_env():
    p = Path(__file__).with_name('.env')
    if p.exists():
        for line in p.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"\''))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/': self.send_error(404); return
        body=Path(__file__).with_name('index.html').read_bytes()
        self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        if self.path != '/api/answer': self.send_error(404); return
        try:
            data=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))))
            query=data.get('query','').strip()
            if not query or len(query)>2000: raise ValueError('Enter a question of 1–2000 characters.')
            result=answer(query); code=200
        except Exception as e:
            result={'error': 'Unable to answer. Check server configuration or API availability.'}; code=500
        self.send_response(code); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps(result).encode())
    def log_message(self,*args): pass
if __name__=='__main__':
    load_env(); print('Live Search Router: http://127.0.0.1:8765',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
