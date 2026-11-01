"""Ambiente real com cliente e API em origens HTTP diferentes."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
import os

import pytest
from werkzeug.serving import make_server

from server.app import create_app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def servidores():
    class ClienteHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/config.js':
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript')
                self.end_headers()
                self.wfile.write(f'window.LIVRARIA_CONFIG = {{API_BASE_URL: "{self.server.api_url}"}};'.encode())
            else:
                super().do_GET()

        def log_message(self, *args):
            pass

    cliente = ThreadingHTTPServer(('127.0.0.1', 0), partial(ClienteHandler, directory=str(ROOT / 'client')))
    origem = f'http://127.0.0.1:{cliente.server_port}'
    app = create_app(config={'ALLOWED_ORIGINS': (origem,), 'SECRET_KEY': 'ambiente-de-interface-chave-estavel'})
    api = make_server('127.0.0.1', 0, app, threaded=True)
    api_url = f'http://127.0.0.1:{api.server_port}'
    cliente.api_url = api_url
    threads = [Thread(target=servidor.serve_forever, daemon=True) for servidor in (cliente, api)]
    for thread in threads:
        thread.start()
    try:
        yield SimpleNamespace(app=app, api=api, api_url=api_url, cliente_url=origem)
    finally:
        for servidor in (cliente, api):
            servidor.shutdown()
            servidor.server_close()
        for thread in threads:
            thread.join(timeout=5)


@pytest.fixture
def browser():
    playwright = pytest.importorskip('playwright.sync_api')
    executavel = os.environ.get('PLAYWRIGHT_BROWSER_EXECUTABLE') or next((p for p in (
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
        'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ) if Path(p).is_file()), None)
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executavel, headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={'width': 1366, 'height': 900}, locale='pt-BR')
    page = context.new_page()
    page.set_default_timeout(6000)
    yield page
    context.close()
