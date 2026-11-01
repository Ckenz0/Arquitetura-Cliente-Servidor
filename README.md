# Entrelinhas

Aplicação de livraria com frontend independente e API Flask, conectados por
HTTP/JSON. A interface permite descobrir livros, planejar visitas e
acompanhar reservas, fidelidade e comunidade.

## Arquitetura

O cliente em `client/` contém HTML, CSS e JavaScript. O backend em `server/`
centraliza as regras e os dados, com controllers HTTP, serviços, domínio e
repositórios. As duas partes podem ser hospedadas separadamente.

```text
Navegador ⇄ HTTP/JSON + Bearer ⇄ API Flask
                                  ↓
                           Serviços e domínio
                                  ↓
                         Repositórios em memória
```

O contrato da API está em [server/openapi.yaml](server/openapi.yaml).

## Funcionalidades

- Catálogo, busca, filtros, detalhes e avaliações de livros.
- Reservas com prazo, embrulho, alteração e cancelamento.
- Fila virtual, atendimento com livreiro e informações da loja.
- Pontos, cartão fidelidade, cupons e histórico ilustrativo.
- Eventos, inscrições e clubes de leitura.
- Lista de desejos, recomendações e preferências.

## Tecnologias e configuração

Python, Flask e Waitress no backend; HTML, CSS e JavaScript no frontend.
As dependências de execução estão em `requirements.txt`, que referencia
`server/requirements.txt`; as de validação estão em `requirements-dev.txt`.
`startup.sh` inicia o backend WSGI em um processo com quatro threads.

O backend usa `APP_ENV`, `SECRET_KEY` e `ALLOWED_ORIGINS`. A configuração
pública do frontend fica em `client/config.js`. A identificação anônima usa
um token assinado com validade de 24 horas, enviado por Bearer e mantido em
`sessionStorage`. Não há cadastro ou login.

## Limites

Os dados são demonstrativos e ficam em memória. Reiniciar o backend apaga
as alterações. O servidor executa em um único processo com threads;
réplicas exigiriam armazenamento compartilhado. Não há pagamentos,
integração com caixa ou envio externo de notificações.

A suíte em `tests/` cobre domínio, cenários de negócio, API, contrato,
concorrência e interface em navegador real.
