"""O deploy estático recebe assets públicos e a URL real da API."""

import json
import pytest


def cliente(raiz):
    arquivos = {
        'client/index.html': '<script src="config.js"></script>',
        'client/config.js': 'window.LIVRARIA_CONFIG = {API_BASE_URL: "http://127.0.0.1:5000"};',
        'client/css/app.css': 'body { color: green; }',
        'client/js/api.js': 'window.transport = true;',
        'client/js/app.js': 'window.app = true;',
        'client/.env': 'SECRET_KEY=privado',
        'client/AGENTS.md': 'instrucoes locais',
        'client/agents.md': 'instrucoes locais',
        'client/superpowers/plano.md': 'local',
        'client/.superpowers/plano.md': 'local',
        'client/js/debug.json': '{"token":"privado"}',
        'server/app.py': 'privado',
    }
    for nome, conteudo in arquivos.items():
        path = raiz / nome
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(conteudo, encoding='utf-8')


def test_pacote_publica_apenas_assets_com_configuracao_https_sem_alterar_fonte(tmp_path):
    from scripts.package_frontend import criar_pacote

    cliente(tmp_path)
    fonte = (tmp_path / 'client/config.js').read_bytes()
    destino = tmp_path / 'dist/client'
    criar_pacote(tmp_path, destino, 'https://livraria.azurewebsites.net/')
    assert {p.relative_to(destino).as_posix() for p in destino.rglob('*') if p.is_file()} == {
        'index.html', 'config.js', 'css/app.css', 'js/api.js', 'js/app.js',
    }
    config = (destino / 'config.js').read_text(encoding='utf-8')
    valores = json.loads(config.removeprefix('window.LIVRARIA_CONFIG = ').strip().removesuffix(';'))
    assert valores == {'API_BASE_URL': 'https://livraria.azurewebsites.net', 'TIMEOUT_MS': 10000}
    assert (tmp_path / 'client/config.js').read_bytes() == fonte
    assert (destino / 'css/app.css').read_text() == 'body { color: green; }'


@pytest.mark.parametrize('url', [
    '', 'http://api.azurewebsites.net', 'https://api.azurewebsites.net/api',
    'https://usuario:senha@api.azurewebsites.net', 'https://api.azurewebsites.net?token=privado',
    'https://api.azurewebsites.net#fragmento', 'https://localhost',
    'https://127.0.0.1', 'https://[::1]', 'https://api.azurewebsites.net:invalida',
    'https://api azurewebsites.net',
])
def test_url_invalida_nao_modifica_artefato_existente(tmp_path, url):
    from scripts.package_frontend import criar_pacote

    cliente(tmp_path)
    destino = tmp_path / 'dist/client'
    destino.mkdir(parents=True)
    (destino / 'index.html').write_text('versao anterior')
    with pytest.raises(ValueError):
        criar_pacote(tmp_path, destino, url)
    assert (destino / 'index.html').read_text() == 'versao anterior'


def test_nao_sobrescreve_cliente_fonte(tmp_path):
    from scripts.package_frontend import criar_pacote

    cliente(tmp_path)
    fonte = (tmp_path / 'client/config.js').read_bytes()
    with pytest.raises(ValueError):
        criar_pacote(tmp_path, tmp_path / 'client', 'https://api.azurewebsites.net')
    assert (tmp_path / 'client/config.js').read_bytes() == fonte
