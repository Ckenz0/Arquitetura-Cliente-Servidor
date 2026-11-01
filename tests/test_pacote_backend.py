"""O artefato publicado contém somente os componentes de execução da API."""

from zipfile import ZipFile


def test_pacote_exclui_documentacao_segredos_frontend_e_caches(tmp_path):
    from scripts.package_backend import criar_pacote

    raiz = tmp_path / 'projeto'
    arquivos = {
        'requirements.txt': '-r server/requirements.txt\n',
        'startup.sh': 'exec python -m waitress --call server.app:create_app\n',
        'server/app.py': 'def create_app(): pass\n',
        'server/requirements.txt': 'Flask>=3.1,<4\n',
        'server/domain/regras.py': 'REGRA = True\n',
        'server/openapi.yaml': 'openapi: 3.1.0\n',
        'docs/specs/local.md': 'documentação local',
        'AGENTS.md': 'instruções locais',
        '.env': 'SECRET_KEY=nao-publicar',
        'server/.env': 'SECRET_KEY=nao-publicar',
        'server/__pycache__/app.cpython-312.pyc': 'cache',
        'client/index.html': '<html></html>',
        '.superpowers/plans/local.md': 'plano local',
    }
    for nome, conteudo in arquivos.items():
        path = raiz / nome
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(conteudo, encoding='utf-8')
    destino = tmp_path / 'dist/backend.zip'
    criar_pacote(raiz, destino)
    with ZipFile(destino) as pacote:
        assert set(pacote.namelist()) == {
            'requirements.txt', 'startup.sh', 'server/app.py',
            'server/requirements.txt', 'server/domain/regras.py', 'server/openapi.yaml',
        }
        assert pacote.read('requirements.txt').decode().splitlines() == ['-r server/requirements.txt']
