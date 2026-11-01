"""Cria o artefato mínimo de execução do backend."""

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def criar_pacote(raiz: Path, destino: Path):
    arquivos = [raiz / 'requirements.txt', raiz / 'startup.sh']
    arquivos.extend(
        path for path in sorted((raiz / 'server').rglob('*'))
        if path.is_file() and path.suffix in {'.py', '.txt', '.yaml'}
        and not any(part.startswith('.') or part == '__pycache__'
                    for part in path.relative_to(raiz).parts)
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destino, 'w', ZIP_DEFLATED) as pacote:
        for path in arquivos:
            pacote.write(path, path.relative_to(raiz).as_posix())
    return destino


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('dist/backend-azure.zip'))
    args = parser.parse_args()
    criar_pacote(Path(__file__).resolve().parents[1], args.output)
    print(f'Pacote criado: {args.output}')
