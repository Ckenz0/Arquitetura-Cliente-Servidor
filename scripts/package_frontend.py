"""Prepara somente os assets públicos para Azure Static Web Apps."""

import argparse
import ipaddress
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit


def criar_pacote(raiz: Path, destino: Path, api_url: str):
    url = urlsplit(api_url)
    host = (url.hostname or '').lower()
    try:
        local = ipaddress.ip_address(host).is_loopback
    except ValueError:
        local = host == 'localhost' or host.endswith('.localhost')
    if (any(char.isspace() or ord(char) < 32 for char in api_url)
            or url.scheme != 'https' or not host or local or url.username or url.password
            or url.path not in {'', '/'} or url.query or url.fragment):
        raise ValueError('Informe a origem HTTPS pública da API, sem /api ou credenciais.')
    # Acessar port também valida portas malformadas antes de escrever arquivos.
    url.port
    raiz = raiz.resolve()
    destino = destino.resolve()
    if not destino.is_relative_to(raiz / 'dist') or destino == raiz / 'dist':
        raise ValueError('O destino deve ser uma subpasta de dist/, separada das fontes.')

    arquivos = ('index.html', 'css/app.css', 'js/api.js', 'js/app.js')
    destino.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destino.parent) as temporario:
        preparado = Path(temporario) / 'client'
        preparado.mkdir()
        for nome in arquivos:
            fonte = raiz / 'client' / nome
            if fonte.is_symlink():
                raise ValueError('Assets publicados devem ser arquivos do cliente.')
            alvo = preparado / nome
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(fonte, alvo)
        config = {'API_BASE_URL': api_url.rstrip('/'), 'TIMEOUT_MS': 10000}
        (preparado / 'config.js').write_text(
            'window.LIVRARIA_CONFIG = ' + json.dumps(config) + ';\n', encoding='utf-8',
        )
        if destino.exists():
            shutil.rmtree(destino)
        preparado.rename(destino)
    return destino


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-url', required=True)
    parser.add_argument('--output', type=Path, default=Path('dist/client'))
    args = parser.parse_args()
    try:
        resultado = criar_pacote(Path(__file__).resolve().parents[1], args.output, args.api_url)
    except ValueError as erro:
        parser.error(str(erro))
    print(f'Frontend preparado: {resultado}')
