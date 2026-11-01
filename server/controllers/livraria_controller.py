"""Apresentação HTTP: sessão, formato das requisições e respostas."""

from datetime import timedelta

from flask import Blueprint, g, jsonify, request

from server.domain.regras import ErroLivraria
from server.identity import emitir_sessao, identificar_cliente


def registrar_controladores(app, *, demonstracao=False):
    """Registra um Blueprint com o serviço próprio desta aplicação."""
    loja = app.extensions["livraria"]
    blueprint = Blueprint("livraria", __name__)

    @blueprint.before_request
    def preparar_cliente():
        if request.endpoint not in {'livraria.index', 'livraria.health', 'livraria.sessoes'}:
            g.cliente_id = identificar_cliente()
        if request.method in {'POST', 'PATCH'} and request.get_data(cache=True):
            dados()

    def cliente():
        return g.cliente_id

    def dados(*obrigatorios):
        if not request.is_json:
            raise ErroLivraria("Envie um objeto JSON.")
        corpo = request.get_json()
        if not isinstance(corpo, dict):
            raise ErroLivraria("Envie um objeto JSON.")
        for campo in obrigatorios:
            if not isinstance(corpo.get(campo), str) or not corpo[campo].strip():
                raise ErroLivraria(f"Informe {campo}.")
        return corpo

    @blueprint.get('/')
    def index():
        return jsonify(servico='Entrelinhas API', health='/api/health')

    @blueprint.get('/api/health')
    def health():
        return jsonify(status='ok')

    @blueprint.post('/api/sessoes')
    def sessoes():
        if request.get_data(cache=True) and dados():
            raise ErroLivraria('A sessão não aceita campos de identificação.')
        cliente_id, sessao = emitir_sessao()
        if demonstracao:
            agora = loja.agora()
            loja.registrar_compra(cliente_id, '1984', 20,
                                  expira_em=(agora + timedelta(days=3)).isoformat(),
                                  avisar_em=agora.isoformat())
            loja.conceder_cupom(cliente_id, 'BOASLEITURAS',
                               'Cupom ilustrativo: consulte as condições no caixa.')
        return jsonify(sessao), 201

    @blueprint.get("/api/estado")
    def estado():
        return jsonify(loja.estado(cliente()))

    @blueprint.get("/api/livros")
    def livros():
        return jsonify(loja.buscar(request.args.get("q", ""), request.args.get("genero", ""),
                                  request.args.get("lancamentos") == "1"))

    @blueprint.get("/api/livros/<livro_id>")
    def livro(livro_id):
        return jsonify(loja.livro(livro_id, cliente()))

    @blueprint.post("/api/livros/<livro_id>/avaliacoes")
    def avaliar(livro_id):
        corpo = dados("texto")
        if set(corpo) - {"nota", "texto"}:
            raise ErroLivraria("Envie apenas nota e texto da avaliação.")
        return jsonify(loja.publicar_avaliacao(
            cliente(), livro_id, corpo.get("nota"), corpo["texto"],
        )), 201

    @blueprint.get("/api/codigo/<codigo>")
    def codigo(codigo):
        return jsonify(loja.por_codigo(codigo))

    @blueprint.post("/api/avisos-estoque")
    def avisos_estoque():
        corpo = dados("livro_id")
        return jsonify(loja.acompanhar_estoque(cliente(), corpo["livro_id"])), 201

    @blueprint.post("/api/reservas")
    def reservar():
        corpo = dados("livro_id", "prazo")
        return jsonify(loja.reservar(cliente(), corpo["livro_id"], corpo["prazo"],
                                    corpo.get("embrulho", False))), 201

    @blueprint.patch("/api/reservas/<reserva_id>")
    def alterar_reserva(reserva_id):
        return jsonify(loja.alterar_prazo(cliente(), reserva_id, dados("prazo")["prazo"]))

    @blueprint.post("/api/reservas/<reserva_id>/cancelar")
    def cancelar(reserva_id):
        return jsonify(loja.cancelar_reserva(cliente(), reserva_id))

    @blueprint.post("/api/fila")
    def fila():
        return jsonify(loja.entrar_fila(cliente())), 201

    @blueprint.post("/api/agendamentos")
    def agendar():
        return jsonify(loja.agendar(cliente(), dados("horario_id")["horario_id"])), 201

    @blueprint.post("/api/eventos/<evento_id>/inscricoes")
    def inscrever(evento_id):
        return jsonify(loja.inscrever(cliente(), evento_id)), 201

    @blueprint.post("/api/clubes/<clube_id>/participar")
    def participar(clube_id):
        return jsonify(loja.participar_clube(cliente(), clube_id)), 201

    @blueprint.post("/api/clubes/<clube_id>/opinioes")
    def opinar(clube_id):
        return jsonify(loja.publicar_opiniao(cliente(), clube_id, dados("texto")["texto"])), 201

    @blueprint.post("/api/desejos")
    def desejo():
        return jsonify(loja.adicionar_desejo(cliente(), dados("livro_id")["livro_id"])), 201

    @blueprint.patch("/api/preferencias")
    def preferencias():
        corpo = dados()
        if not corpo or set(corpo) - {"generos", "temas_notificacao"}:
            raise ErroLivraria("Informe gêneros e/ou temas de notificação.")
        return jsonify(loja.preferencias(cliente(), **corpo))

    app.register_blueprint(blueprint)
