import os
import re
import json
import hmac
import hashlib
import sqlite3
import logging
import unicodedata

from datetime import datetime, timedelta, timezone

import requests

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
APP_SECRET = os.getenv("APP_SECRET")

API_URL = "https://graph.instagram.com/v26.0/me/messages"

BANCO = os.getenv("BANCO_PATH", "primeprep.db")

FUSO = timezone(timedelta(hours=-3))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger("primeprep")


# =========================================================
# CONTEÚDO — EDITE SÓ ESTA PARTE
#
# Tudo que está marcado com PREENCHER precisa da informação
# real de vocês. O resto do arquivo não precisa ser tocado
# para mudar texto.
# =========================================================

LINK_WHATSAPP = "https://wa.me/5555999451204"
LINK_SITE = ""  # Site ainda não disponível
LINK_INSTAGRAM = "https://instagram.com/primeprep.sg"

ENDERECO = "Local em definição — São Gabriel/RS"

HORARIO_AULAS = "Segunda a sexta, das 18h às 23h, com intervalo às 20h30"

# Atendimento humano: dias da semana (0 = segunda, 6 = domingo)
ATENDIMENTO_DIAS = [0, 1, 2, 3, 4]
ATENDIMENTO_INICIO = 9
ATENDIMENTO_FIM = 18

# Quanto tempo o bot fica calado depois de passar para a equipe
PAUSA_HORAS = 12

TEXTO_BOAS_VINDAS = (
    "Olá! 👋 Bem-vindo à Prime Prep — Curso Preparatório Militar.\n\n"
    "Como podemos te ajudar?"
)

TEXTO_MENU_CURTO = "O que você quer ver agora?"

TEXTO_FALLBACK = (
    "Não entendi 😅\n\n"
    "Escolha uma das opções abaixo ou digite menu a qualquer momento."
)

TEXTO_SOBRE_CURSO = (
    "📚 PRIME PREP — CURSO PREPARATÓRIO MILITAR\n\n"
    "Somos um preparatório focado exclusivamente em concursos militares, "
    "em São Gabriel/RS.\n\n"
    f"🕕 {HORARIO_AULAS}\n"
    "📝 Simulados aproximadamente uma vez por mês e reforço aos fins de semana "
    "quando necessário\n"
    "📊 Acompanhamento individual de desempenho\n\n"
    "Quer saber mais sobre o quê?"
)

TEXTO_METODOLOGIA = (
    "🎯 NOSSA METODOLOGIA\n\n"
    "A preparação é estruturada para atender diferentes concursos militares "
    "simultaneamente, com foco em conteúdo direcionado, resolução de questões "
    "e acompanhamento contínuo do desempenho.\n\n"
    "• Simulados aproximadamente uma vez por mês\n"
    "• Correção individual dos simulados\n"
    "• Planilha individual para acompanhar a evolução de cada aluno\n"
    "• Reforços aos fins de semana quando houver necessidade\n"
    "• Preparação pensada para diferentes concursos militares ao longo do ano"
)

TEXTO_PROFESSORES = (
    "👨‍🏫 NOSSOS PROFESSORES\n\n"

    "📐 Matheus Quadros da Luz\n"
    "Matemática e Física\n"
    "Graduando em Física, com foco em preparação para concursos militares "
    "e estratégias de alto rendimento.\n\n"

    "📖 Tati Viedo\n"
    "Língua Portuguesa\n"
    "Formada em Pedagogia e Letras.\n\n"

    "🇬🇧 João Montagner\n"
    "Inglês\n"
    "Graduando em Análise e Desenvolvimento de Sistemas.\n"
    "Certificações MET (C1) e ECPE (C2)."
)

TEXTO_ESTRUTURA = (
    "📍 ONDE FICA E COMO FUNCIONA\n\n"
    f"Local: {ENDERECO}\n"
    f"Aulas: {HORARIO_AULAS}"
)

TEXTO_DIFERENCIAIS = (
    "⭐ NOSSOS DIFERENCIAIS\n\n"
    "• Acompanhamento individual com planilha de desempenho\n"
    "• Correção individualizada de redações, simulados e questões\n"
    "• Bolsas por desempenho\n"
    "• Bolsas socioeconômicas\n"
    "• Reforço aos fins de semana quando necessário\n"
    "• Preparação voltada para diferentes concursos militares"
)

TEXTO_VALORES = (
    "💰 VALORES\n\n"
    "Os valores da mensalidade e demais condições comerciais ainda estão "
    "em fase de alinhamento.\n\n"
    "💳 FORMAS DE PAGAMENTO PREVISTAS:\n"
    "• Boleto\n"
    "• Cartão\n"
    "• Pagamento à vista com desconto\n\n"
    "Assim que as condições forem finalizadas, as informações serão "
    "atualizadas por aqui.\n\n"
    "Quer conversar com a equipe? É só chamar."
)

TEXTO_BOLSAS = (
    "🎓 BOLSAS DE ESTUDO\n\n"
    "A Prime Prep contará com:\n\n"
    "• Bolsas por desempenho\n"
    "• Bolsas socioeconômicas\n\n"
    "Os critérios, percentuais e formas de candidatura ainda estão sendo "
    "definidos e serão divulgados posteriormente."
)

TEXTO_ATENDIMENTO_ABERTO = (
    "👤 Perfeito! Já avisei nossa equipe — alguém te responde por aqui "
    "em instantes.\n\n"
    f"Se preferir falar agora pelo WhatsApp: {LINK_WHATSAPP}\n\n"
    "Se quiser voltar ao menu automático, é só digitar “menu”."
)

TEXTO_ATENDIMENTO_FECHADO = (
    "👤 Nosso atendimento funciona de segunda a sexta, das "
    f"{ATENDIMENTO_INICIO}h às {ATENDIMENTO_FIM}h.\n\n"
    "Pode deixar sua mensagem aqui que respondemos no próximo horário "
    f"comercial. Se preferir: {LINK_WHATSAPP}\n\n"
    "Para voltar ao menu automático, digite “menu”."
)


# ---------------------------------------------------------
# CONCURSOS
# ---------------------------------------------------------

CONCURSOS = {
    "ESA": {
        "titulo": "🎖️ ESA — Escola de Sargentos das Armas",
        "texto": (
            "Forma sargentos de carreira do Exército Brasileiro.\n\n"

            "📅 PROVA\n"
            "Concurso de Admissão 2026 para os CFGS 2027/2028:\n"
            "26 de julho de 2026.\n\n"

            "📋 REQUISITOS PRINCIPAIS\n"
            "• Área Geral: de 17 a 24 anos.\n"
            "• Ensino Médio concluído ou cursando o 3º ano.\n"
            "• Música e Saúde: limite de até 26 anos e requisitos específicos da área.\n\n"

            "📚 O QUE CAI — ÁREA GERAL\n"
            "• Matemática\n"
            "• Português\n"
            "• História do Brasil\n"
            "• Geografia do Brasil\n"
            "• Inglês\n"
            "• Redação\n\n"

            "ℹ️ As informações acima usam como referência o concurso de 2026. "
            "Datas e regras podem mudar nos próximos editais."
        )
    },

    "ESPCEX": {
        "titulo": "🎖️ EsPCEx — Escola Preparatória de Cadetes do Exército",
        "texto": (
            "É a porta de entrada para a formação dos oficiais combatentes de carreira "
            "do Exército, com continuidade na AMAN.\n\n"

            "📅 PROVAS — 2026\n"
            "12 de setembro:\n"
            "• Português\n"
            "• Física\n"
            "• Química\n"
            "• Redação\n\n"

            "13 de setembro:\n"
            "• Matemática\n"
            "• Geografia\n"
            "• História\n"
            "• Inglês\n\n"

            "📋 REQUISITOS PRINCIPAIS\n"
            "• Ser brasileiro nato.\n"
            "• Ambos os sexos.\n"
            "• Ter de 17 a 22 anos até 31 de dezembro do ano da matrícula.\n"
            "• Ter concluído ou estar cursando o 3º ano do Ensino Médio no ano da inscrição.\n\n"

            "ℹ️ Referência: concurso de 2026 para matrícula em 2027. "
            "Consulte sempre o edital vigente."
        )
    },

    "AFA": {
        "titulo": "✈️ AFA — Academia da Força Aérea",
        "texto": (
            "Forma oficiais Aviadores, Intendentes e de Infantaria da "
            "Força Aérea Brasileira.\n\n"

            "📅 PROVA — EA AFA 2027\n"
            "5 de julho de 2026.\n\n"

            "📚 O QUE CAI\n"
            "• Língua Portuguesa\n"
            "• Física\n"
            "• Matemática\n"
            "• Língua Inglesa\n"
            "• Redação\n\n"

            "📋 REQUISITOS PRINCIPAIS\n"
            "• Ser brasileiro nato.\n"
            "• Ter concluído o Ensino Médio até a matrícula.\n"
            "• Ter no mínimo 17 anos e não completar 23 anos até "
            "31 de dezembro do ano da matrícula.\n\n"

            "ℹ️ Referência: Exame de Admissão AFA 2027. "
            "Consulte sempre o edital vigente."
        )
    },

    "EFOMM": {
        "titulo": "⚓ EFOMM — Escola de Formação de Oficiais da Marinha Mercante",
        "texto": (
            "Forma Oficiais da Marinha Mercante para atuação nos cursos de "
            "Náutica e Máquinas e no setor marítimo.\n\n"

            "📅 PROVAS — EFOMM 2027\n"
            "25 de julho de 2026:\n"
            "• Inglês\n"
            "• Português\n"
            "• Redação\n\n"

            "26 de julho de 2026:\n"
            "• Matemática\n"
            "• Física\n\n"

            "📋 REQUISITOS PRINCIPAIS\n"
            "• Ser brasileiro, para ambos os sexos.\n"
            "• Ter de 17 a 23 anos em 1º de janeiro de 2027.\n"
            "• Ter concluído o Ensino Médio ou equivalente.\n"
            "• Altura entre 1,54 m e 2,00 m.\n\n"

            "ℹ️ Referência: Processo Seletivo EFOMM 2027. "
            "Consulte sempre o edital vigente."
        )
    },

    "EEAR": {
        "titulo": "✈️ EEAR — Escola de Especialistas de Aeronáutica",
        "texto": (
            "Forma sargentos especialistas da Força Aérea Brasileira, em "
            "Guaratinguetá/SP.\n\n"

            "📅 PROVA — CFS 1/2027\n"
            "31 de maio de 2026.\n\n"

            "📚 O QUE CAI\n"
            "• Língua Portuguesa\n"
            "• Matemática\n"
            "• Física\n"
            "• Língua Inglesa\n"
            "  (nível básico ou intermediário, conforme a especialidade)\n\n"

            "📋 REQUISITOS PRINCIPAIS\n"
            "• Ser brasileiro nato.\n"
            "• Ambos os sexos.\n"
            "• Ter concluído o Ensino Médio.\n"
            "• Ter no mínimo 17 anos e não completar 25 anos até "
            "31 de dezembro do ano da matrícula.\n\n"

            "ℹ️ Referência: CFS 1/2027. "
            "Consulte sempre o edital vigente."
        )
    }
}


# =========================================================
# ESTADOS DA CONVERSA
# =========================================================

ESTADO_MENU = "MENU"
ESTADO_MATRICULA_NOME = "MATRICULA_NOME"
ESTADO_MATRICULA_IDADE = "MATRICULA_IDADE"
ESTADO_MATRICULA_CIDADE = "MATRICULA_CIDADE"
ESTADO_MATRICULA_CONCURSO = "MATRICULA_CONCURSO"
ESTADO_MATRICULA_CONFIRMA = "MATRICULA_CONFIRMA"
ESTADO_ATENDIMENTO = "ATENDIMENTO"


# =========================================================
# BANCO DE DADOS
# =========================================================

def conectar():

    conexao = sqlite3.connect(BANCO, timeout=10)
    conexao.row_factory = sqlite3.Row

    return conexao


def criar_tabelas():

    conexao = conectar()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario_id   TEXT PRIMARY KEY,
            estado       TEXT NOT NULL DEFAULT 'MENU',
            dados        TEXT NOT NULL DEFAULT '{}',
            pausado_ate  TEXT,
            atualizado   TEXT
        )
    """)

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT NOT NULL,
            nome       TEXT,
            idade      TEXT,
            cidade     TEXT,
            concurso   TEXT,
            criado_em  TEXT
        )
    """)

    conexao.commit()
    conexao.close()

    log.info("Banco pronto: %s", BANCO)


criar_tabelas()


def buscar_usuario(usuario_id: str) -> dict:

    conexao = conectar()

    linha = conexao.execute(
        "SELECT * FROM usuarios WHERE usuario_id = ?",
        (usuario_id,)
    ).fetchone()

    if linha is None:

        conexao.execute(
            "INSERT INTO usuarios (usuario_id, estado, dados, atualizado) "
            "VALUES (?, ?, ?, ?)",
            (usuario_id, ESTADO_MENU, "{}", agora_texto())
        )

        conexao.commit()
        conexao.close()

        return {
            "estado": ESTADO_MENU,
            "dados": {},
            "pausado_ate": None,
            "novo": True
        }

    conexao.close()

    return {
        "estado": linha["estado"],
        "dados": json.loads(linha["dados"] or "{}"),
        "pausado_ate": linha["pausado_ate"],
        "novo": False
    }


def salvar_usuario(usuario_id: str, estado: str = None,
                   dados: dict = None, pausado_ate: str = "manter"):

    atual = buscar_usuario(usuario_id)

    novo_estado = estado if estado is not None else atual["estado"]
    novos_dados = dados if dados is not None else atual["dados"]

    if pausado_ate == "manter":
        nova_pausa = atual["pausado_ate"]
    else:
        nova_pausa = pausado_ate

    conexao = conectar()

    conexao.execute(
        "UPDATE usuarios SET estado = ?, dados = ?, pausado_ate = ?, "
        "atualizado = ? WHERE usuario_id = ?",
        (
            novo_estado,
            json.dumps(novos_dados, ensure_ascii=False),
            nova_pausa,
            agora_texto(),
            usuario_id
        )
    )

    conexao.commit()
    conexao.close()


def salvar_lead(usuario_id: str, dados: dict):

    conexao = conectar()

    conexao.execute(
        "INSERT INTO leads (usuario_id, nome, idade, cidade, concurso, "
        "criado_em) VALUES (?, ?, ?, ?, ?, ?)",
        (
            usuario_id,
            dados.get("nome"),
            dados.get("idade"),
            dados.get("cidade"),
            dados.get("concurso"),
            agora_texto()
        )
    )

    conexao.commit()
    conexao.close()

    log.info("LEAD SALVO | %s | %s", usuario_id, dados)


# =========================================================
# UTILIDADES
# =========================================================

def agora():
    return datetime.now(FUSO)


def agora_texto():
    return agora().isoformat()


def normalizar(texto: str) -> str:
    """
    Tira acentos, deixa minúsculo, remove pontuação e normaliza espaços.

    Exemplos:
    "Oi!" -> "oi"
    "  Boa   tarde!!! " -> "boa tarde"
    "Quanto custa?" -> "quanto custa"
    """

    if not texto:
        return ""

    limpo = unicodedata.normalize("NFKD", texto)
    limpo = "".join(c for c in limpo if not unicodedata.combining(c))
    limpo = limpo.lower()

    # Troca pontuação e símbolos por espaço.
    limpo = re.sub(r"[^a-z0-9\s]", " ", limpo)

    # Remove espaços duplicados.
    limpo = re.sub(r"\s+", " ", limpo)

    return limpo.strip()


def dentro_do_horario() -> bool:

    momento = agora()

    if momento.weekday() not in ATENDIMENTO_DIAS:
        return False

    return ATENDIMENTO_INICIO <= momento.hour < ATENDIMENTO_FIM


def esta_pausado(usuario: dict) -> bool:

    pausa = usuario.get("pausado_ate")

    if not pausa:
        return False

    try:
        limite = datetime.fromisoformat(pausa)
    except ValueError:
        return False

    return agora() < limite


# =========================================================
# ENVIO
# =========================================================

def _postar(payload: dict, rotulo: str):

    try:

        resposta = requests.post(
            API_URL,
            params={
                "access_token": ACCESS_TOKEN
            },
            json=payload,
            timeout=15
        )

        if resposta.status_code >= 400:
            log.error("%s | %s | %s", rotulo, resposta.status_code,
                      resposta.text)
        else:
            log.info("%s | %s", rotulo, resposta.status_code)

    except requests.RequestException as erro:

        log.error("%s | falha de rede: %s", rotulo, erro)


def enviar_mensagem(usuario_id: str, texto: str):

    payload = {
        "recipient": {
            "id": usuario_id
        },
        "message": {
            "text": texto
        }
    }

    _postar(payload, "ENVIO")


def enviar_opcoes(usuario_id: str, texto: str, opcoes: list):
    """
    opcoes = [("🎖️ Concursos", "MENU_CONCURSOS"), ...]

    A Meta aceita no máximo 13 quick replies por mensagem e
    títulos de até 20 caracteres.
    """

    quick_replies = []

    for titulo, payload_botao in opcoes[:13]:

        quick_replies.append({
            "content_type": "text",
            "title": titulo[:20],
            "payload": payload_botao
        })

    payload = {
        "recipient": {
            "id": usuario_id
        },
        "message": {
            "text": texto,
            "quick_replies": quick_replies
        }
    }

    _postar(payload, "OPCOES")


# =========================================================
# MENUS
# =========================================================

def enviar_menu_principal(usuario_id: str, texto: str = None):

    salvar_usuario(usuario_id, estado=ESTADO_MENU)

    enviar_opcoes(
        usuario_id,
        texto or TEXTO_BOAS_VINDAS,
        [
            ("🎖️ Concursos", "MENU_CONCURSOS"),
            ("📚 Nosso curso", "MENU_CURSO"),
            ("💰 Valores", "MENU_VALORES"),
            ("📝 Matrícula", "MENU_MATRICULA"),
            ("👤 Atendimento", "MENU_ATENDIMENTO")
        ]
    )


def enviar_menu_concursos(usuario_id: str):

    salvar_usuario(usuario_id, estado=ESTADO_MENU)

    enviar_opcoes(
        usuario_id,
        "Qual concurso você quer conhecer?",
        [
            ("ESA", "CONCURSO_ESA"),
            ("EsPCEx", "CONCURSO_ESPCEX"),
            ("AFA", "CONCURSO_AFA"),
            ("EFOMM", "CONCURSO_EFOMM"),
            ("EEAR", "CONCURSO_EEAR"),
            ("↩️ Voltar", "MENU_PRINCIPAL")
        ]
    )


def enviar_info_concurso(usuario_id: str, sigla: str):

    concurso = CONCURSOS.get(sigla)

    if not concurso:
        enviar_menu_concursos(usuario_id)
        return

    enviar_mensagem(
        usuario_id,
        f"{concurso['titulo']}\n\n{concurso['texto']}"
    )

    enviar_opcoes(
        usuario_id,
        "E agora?",
        [
            ("📝 Quero matrícula", "MENU_MATRICULA"),
            ("🎖️ Outro concurso", "MENU_CONCURSOS"),
            ("👤 Falar com a equipe", "MENU_ATENDIMENTO"),
            ("🏠 Menu principal", "MENU_PRINCIPAL")
        ]
    )


def enviar_menu_curso(usuario_id: str):

    salvar_usuario(usuario_id, estado=ESTADO_MENU)

    enviar_opcoes(
        usuario_id,
        TEXTO_SOBRE_CURSO,
        [
            ("🎯 Metodologia", "CURSO_METODOLOGIA"),
            ("👨‍🏫 Professores", "CURSO_PROFESSORES"),
            ("📍 Local e horários", "CURSO_ESTRUTURA"),
            ("⭐ Diferenciais", "CURSO_DIFERENCIAIS"),
            ("↩️ Voltar", "MENU_PRINCIPAL")
        ]
    )


def enviar_detalhe_curso(usuario_id: str, texto: str):

    enviar_mensagem(usuario_id, texto)

    enviar_opcoes(
        usuario_id,
        "Quer ver mais alguma coisa?",
        [
            ("📚 Sobre o curso", "MENU_CURSO"),
            ("💰 Valores", "MENU_VALORES"),
            ("📝 Matrícula", "MENU_MATRICULA"),
            ("🏠 Menu principal", "MENU_PRINCIPAL")
        ]
    )


def enviar_menu_valores(usuario_id: str):

    salvar_usuario(usuario_id, estado=ESTADO_MENU)

    enviar_mensagem(usuario_id, TEXTO_VALORES)

    enviar_opcoes(
        usuario_id,
        TEXTO_MENU_CURTO,
        [
            ("🎓 Bolsas", "VALORES_BOLSAS"),
            ("📝 Matrícula", "MENU_MATRICULA"),
            ("👤 Falar com a equipe", "MENU_ATENDIMENTO"),
            ("🏠 Menu principal", "MENU_PRINCIPAL")
        ]
    )


def enviar_bolsas(usuario_id: str):

    enviar_mensagem(usuario_id, TEXTO_BOLSAS)

    enviar_opcoes(
        usuario_id,
        TEXTO_MENU_CURTO,
        [
            ("📝 Matrícula", "MENU_MATRICULA"),
            ("👤 Falar com a equipe", "MENU_ATENDIMENTO"),
            ("🏠 Menu principal", "MENU_PRINCIPAL")
        ]
    )


# =========================================================
# MATRÍCULA — COLETA PASSO A PASSO
# =========================================================

def iniciar_matricula(usuario_id: str):

    salvar_usuario(
        usuario_id,
        estado=ESTADO_MATRICULA_NOME,
        dados={}
    )

    enviar_mensagem(
        usuario_id,
        "📝 Que bom! Vou pegar alguns dados rapidinho — são 4 perguntas.\n\n"
        "A qualquer momento você pode digitar cancelar."
    )

    enviar_mensagem(usuario_id, "1️⃣ Qual é o seu nome completo?")


def matricula_receber_nome(usuario_id: str, dados: dict, texto: str):

    dados["nome"] = texto.strip()

    salvar_usuario(usuario_id, estado=ESTADO_MATRICULA_IDADE, dados=dados)

    enviar_mensagem(
        usuario_id,
        f"Prazer, {dados['nome'].split()[0]}! 👋\n\n"
        "2️⃣ Quantos anos você tem?"
    )


def matricula_receber_idade(usuario_id: str, dados: dict, texto: str):

    numeros = "".join(c for c in texto if c.isdigit())

    if not numeros or not (10 <= int(numeros) <= 60):

        enviar_mensagem(
            usuario_id,
            "Pode me mandar só a idade em número? (ex.: 18)"
        )

        return

    dados["idade"] = numeros

    salvar_usuario(usuario_id, estado=ESTADO_MATRICULA_CIDADE, dados=dados)

    enviar_mensagem(usuario_id, "3️⃣ De qual cidade você é?")


def matricula_receber_cidade(usuario_id: str, dados: dict, texto: str):

    dados["cidade"] = texto.strip()

    salvar_usuario(usuario_id, estado=ESTADO_MATRICULA_CONCURSO, dados=dados)

    enviar_opcoes(
        usuario_id,
        "4️⃣ Qual concurso é o seu objetivo?",
        [
            ("ESA", "ALVO_ESA"),
            ("EsPCEx", "ALVO_ESPCEX"),
            ("AFA", "ALVO_AFA"),
            ("EFOMM", "ALVO_EFOMM"),
            ("EEAR", "ALVO_EEAR"),
            ("Ainda não sei", "ALVO_INDECISO")
        ]
    )


def matricula_receber_concurso(usuario_id: str, dados: dict, alvo: str):

    dados["concurso"] = alvo

    salvar_usuario(usuario_id, estado=ESTADO_MATRICULA_CONFIRMA, dados=dados)

    enviar_opcoes(
        usuario_id,
        "Confere se está tudo certo:\n\n"
        f"👤 Nome: {dados.get('nome')}\n"
        f"🎂 Idade: {dados.get('idade')}\n"
        f"📍 Cidade: {dados.get('cidade')}\n"
        f"🎯 Objetivo: {dados.get('concurso')}",
        [
            ("✅ Confirmar", "MATRICULA_CONFIRMAR"),
            ("🔄 Refazer", "MENU_MATRICULA"),
            ("❌ Cancelar", "MATRICULA_CANCELAR")
        ]
    )


def finalizar_matricula(usuario_id: str, dados: dict):

    salvar_lead(usuario_id, dados)

    salvar_usuario(usuario_id, estado=ESTADO_MENU, dados={})

    enviar_mensagem(
        usuario_id,
        "✅ Prontinho! Seus dados foram registrados.\n\n"
        "Nossa equipe entra em contato para combinar os próximos passos.\n\n"
        f"Se quiser adiantar, chama no WhatsApp: {LINK_WHATSAPP}"
    )

    enviar_opcoes(
        usuario_id,
        TEXTO_MENU_CURTO,
        [
            ("🏠 Menu principal", "MENU_PRINCIPAL"),
            ("👤 Falar agora", "MENU_ATENDIMENTO")
        ]
    )


def cancelar_matricula(usuario_id: str):

    salvar_usuario(usuario_id, estado=ESTADO_MENU, dados={})

    enviar_menu_principal(
        usuario_id,
        "Sem problema, cancelei a matrícula. 👍\n\nComo posso te ajudar?"
    )


# =========================================================
# ATENDIMENTO HUMANO
# =========================================================

def acionar_atendimento(usuario_id: str):

    limite = (agora() + timedelta(hours=PAUSA_HORAS)).isoformat()

    salvar_usuario(
        usuario_id,
        estado=ESTADO_ATENDIMENTO,
        pausado_ate=limite
    )

    if dentro_do_horario():
        enviar_mensagem(usuario_id, TEXTO_ATENDIMENTO_ABERTO)
    else:
        enviar_mensagem(usuario_id, TEXTO_ATENDIMENTO_FECHADO)

    log.info("ATENDIMENTO HUMANO ACIONADO | %s | pausa até %s",
             usuario_id, limite)


def encerrar_pausa(usuario_id: str):

    salvar_usuario(
        usuario_id,
        estado=ESTADO_MENU,
        pausado_ate=None
    )


# =========================================================
# ROTEADOR DOS BOTÕES
# =========================================================

def tratar_opcao(usuario_id: str, opcao: str, usuario: dict):

    log.info("BOTÃO | %s | %s", usuario_id, opcao)

    # ---- navegação principal ----

    if opcao == "MENU_PRINCIPAL":
        encerrar_pausa(usuario_id)
        enviar_menu_principal(usuario_id, TEXTO_MENU_CURTO)
        return

    if opcao == "MENU_CONCURSOS":
        enviar_menu_concursos(usuario_id)
        return

    if opcao == "MENU_CURSO":
        enviar_menu_curso(usuario_id)
        return

    if opcao == "MENU_VALORES":
        enviar_menu_valores(usuario_id)
        return

    if opcao == "MENU_MATRICULA":
        iniciar_matricula(usuario_id)
        return

    if opcao == "MENU_ATENDIMENTO":
        acionar_atendimento(usuario_id)
        return

    # ---- concursos ----

    if opcao.startswith("CONCURSO_"):
        enviar_info_concurso(usuario_id, opcao.replace("CONCURSO_", ""))
        return

    # ---- curso ----

    if opcao == "CURSO_METODOLOGIA":
        enviar_detalhe_curso(usuario_id, TEXTO_METODOLOGIA)
        return

    if opcao == "CURSO_PROFESSORES":
        enviar_detalhe_curso(usuario_id, TEXTO_PROFESSORES)
        return

    if opcao == "CURSO_ESTRUTURA":
        enviar_detalhe_curso(usuario_id, TEXTO_ESTRUTURA)
        return

    if opcao == "CURSO_DIFERENCIAIS":
        enviar_detalhe_curso(usuario_id, TEXTO_DIFERENCIAIS)
        return

    # ---- valores ----

    if opcao == "VALORES_BOLSAS":
        enviar_bolsas(usuario_id)
        return

    # ---- matrícula ----

    if opcao.startswith("ALVO_"):

        if usuario["estado"] != ESTADO_MATRICULA_CONCURSO:
            enviar_menu_principal(usuario_id, TEXTO_MENU_CURTO)
            return

        alvo = opcao.replace("ALVO_", "")

        if alvo == "INDECISO":
            alvo = "Ainda não decidiu"

        matricula_receber_concurso(usuario_id, usuario["dados"], alvo)
        return

    if opcao == "MATRICULA_CONFIRMAR":
        finalizar_matricula(usuario_id, usuario["dados"])
        return

    if opcao == "MATRICULA_CANCELAR":
        cancelar_matricula(usuario_id)
        return

    # ---- botão desconhecido ----

    log.warning("PAYLOAD DESCONHECIDO | %s", opcao)

    enviar_menu_principal(usuario_id, TEXTO_FALLBACK)


# =========================================================
# ROTEADOR DE TEXTO LIVRE
# =========================================================

PALAVRAS_MENU = {
    "menu", "inicio", "start", "voltar", "comecar", "recomecar"
}

PALAVRAS_SAUDACAO = {
    "oi", "ola", "opa", "eai", "e ai", "salve",
    "bom dia", "boa tarde", "boa noite",
    "hello", "hey", "hi"
}

PALAVRAS_CANCELAR = {"cancelar", "parar", "sair"}

PALAVRAS_ATENDENTE = {
    "atendente", "humano", "pessoa", "falar com alguem", "whatsapp"
}

PALAVRAS_VALORES = {
    "valor", "valores", "preco", "precos", "mensalidade",
    "quanto custa", "quanto e"
}

PALAVRAS_MATRICULA = {
    "matricula", "matricular", "inscricao", "inscrever", "quero estudar"
}


def eh_saudacao(texto_normalizado: str) -> bool:
    """
    Reconhece saudações simples e saudações acompanhadas de complemento.

    Exemplos:
    "oi" -> True
    "oi tudo bem" -> True
    "boa tarde pessoal" -> True
    """

    if texto_normalizado in PALAVRAS_SAUDACAO:
        return True

    return any(
        texto_normalizado.startswith(saudacao + " ")
        for saudacao in PALAVRAS_SAUDACAO
    )


def pode_reativar_bot(texto_normalizado: str) -> bool:
    """Comandos que tiram o bot do modo de atendimento humano."""

    return (
        texto_normalizado in PALAVRAS_MENU
        or eh_saudacao(texto_normalizado)
    )



def tratar_texto(usuario_id: str, texto: str, usuario: dict):

    limpo = normalizar(texto)
    estado = usuario["estado"]
    dados = usuario["dados"]

    log.info("TEXTO | %s | estado=%s | %s", usuario_id, estado, texto)

    # ---- primeira interação ----
    # Qualquer primeira mensagem abre o chatbot com uma saudação,
    # em vez de responder com "não entendi".
    if usuario.get("novo"):
        enviar_menu_principal(usuario_id, TEXTO_BOAS_VINDAS)
        return

    # ---- comandos que funcionam em qualquer estado ----

    if limpo in PALAVRAS_CANCELAR:

        if estado.startswith("MATRICULA"):
            cancelar_matricula(usuario_id)
            return

    if eh_saudacao(limpo):
        encerrar_pausa(usuario_id)
        enviar_menu_principal(
            usuario_id,
            "Olá! 👋\n\nComo podemos te ajudar?"
        )
        return

    if limpo in PALAVRAS_MENU:
        encerrar_pausa(usuario_id)
        enviar_menu_principal(
            usuario_id,
            "🏠 Voltamos ao menu principal.\n\nComo podemos te ajudar?"
        )
        return

    # ---- fluxo de matrícula em andamento ----

    if estado == ESTADO_MATRICULA_NOME:
        matricula_receber_nome(usuario_id, dados, texto)
        return

    if estado == ESTADO_MATRICULA_IDADE:
        matricula_receber_idade(usuario_id, dados, texto)
        return

    if estado == ESTADO_MATRICULA_CIDADE:
        matricula_receber_cidade(usuario_id, dados, texto)
        return

    if estado == ESTADO_MATRICULA_CONCURSO:

        enviar_opcoes(
            usuario_id,
            "Escolhe uma das opções abaixo, por favor 👇",
            [
                ("ESA", "ALVO_ESA"),
                ("EsPCEx", "ALVO_ESPCEX"),
                ("AFA", "ALVO_AFA"),
                ("EFOMM", "ALVO_EFOMM"),
                ("EEAR", "ALVO_EEAR"),
                ("Ainda não sei", "ALVO_INDECISO")
            ]
        )

        return

    if estado == ESTADO_MATRICULA_CONFIRMA:

        enviar_opcoes(
            usuario_id,
            "Confirma os dados para eu finalizar? 👇",
            [
                ("✅ Confirmar", "MATRICULA_CONFIRMAR"),
                ("🔄 Refazer", "MENU_MATRICULA"),
                ("❌ Cancelar", "MATRICULA_CANCELAR")
            ]
        )

        return

    # ---- atalhos por palavra-chave ----

    if limpo in PALAVRAS_ATENDENTE:
        acionar_atendimento(usuario_id)
        return

    if limpo in PALAVRAS_VALORES:
        enviar_menu_valores(usuario_id)
        return

    if limpo in PALAVRAS_MATRICULA:
        iniciar_matricula(usuario_id)
        return

    for sigla in CONCURSOS:
        if normalizar(sigla) in limpo:
            enviar_info_concurso(usuario_id, sigla)
            return

    # ---- não entendeu ----

    enviar_menu_principal(usuario_id, TEXTO_FALLBACK)


# =========================================================
# DECIDIR O QUE FAZER
# =========================================================

def processar_evento(evento: dict):

    sender = evento.get("sender", {})
    usuario_id = sender.get("id")

    if not usuario_id:
        return

    mensagem = evento.get("message")

    # Ignora mensagens enviadas pelo próprio bot
    if mensagem and mensagem.get("is_echo"):
        return

    usuario = buscar_usuario(usuario_id)

    # -----------------------------------------------------
    # QUICK REPLY
    # -----------------------------------------------------

    if mensagem:

        quick_reply = mensagem.get("quick_reply")

        if quick_reply:

            # Clicar num botão sempre reativa o bot
            if esta_pausado(usuario):
                encerrar_pausa(usuario_id)
                usuario = buscar_usuario(usuario_id)

            tratar_opcao(usuario_id, quick_reply.get("payload"), usuario)

            return

        # -------------------------------------------------
        # MENSAGEM DE TEXTO NORMAL
        # -------------------------------------------------

        texto = mensagem.get("text")

        if texto:

            # Bot em silêncio: a equipe está atendendo
            if esta_pausado(usuario) and not pode_reativar_bot(normalizar(texto)):

                log.info("BOT PAUSADO | %s | %s", usuario_id, texto)

                return

            tratar_texto(usuario_id, texto, usuario)

            return

        # -------------------------------------------------
        # ANEXOS (foto, áudio, story reply)
        # -------------------------------------------------

        if mensagem.get("attachments"):

            if esta_pausado(usuario):
                return

            enviar_menu_principal(
                usuario_id,
                "Recebi seu arquivo! 📎 Para eu te ajudar mais rápido, "
                "escolha uma opção — ou fale com nossa equipe."
            )

            return

    # -----------------------------------------------------
    # POSTBACK
    # -----------------------------------------------------

    postback = evento.get("postback")

    if postback:

        if esta_pausado(usuario):
            encerrar_pausa(usuario_id)
            usuario = buscar_usuario(usuario_id)

        tratar_opcao(usuario_id, postback.get("payload"), usuario)


# =========================================================
# META VERIFICA O WEBHOOK
# =========================================================

@app.get("/webhook")
async def verificar_webhook(request: Request):

    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:

        log.info("WEBHOOK VERIFICADO PELA META")

        return PlainTextResponse(challenge)

    return PlainTextResponse(
        "Token inválido",
        status_code=403
    )


# =========================================================
# RECEBER EVENTOS DO INSTAGRAM
# =========================================================

def assinatura_valida(corpo: bytes, cabecalho: str) -> bool:
    """Confere o X-Hub-Signature-256 usando o APP_SECRET."""

    if not APP_SECRET:
        return True   # sem secret configurado, não valida

    if not cabecalho or not cabecalho.startswith("sha256="):
        return False

    esperado = hmac.new(
        APP_SECRET.encode(),
        corpo,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(esperado, cabecalho.split("=", 1)[1])


@app.post("/webhook")
async def receber_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):

    corpo = await request.body()

    if not assinatura_valida(corpo, request.headers.get("X-Hub-Signature-256")):

        log.warning("ASSINATURA INVÁLIDA — evento descartado")

        return PlainTextResponse("Assinatura inválida", status_code=403)

    dados = json.loads(corpo or b"{}")

    log.info("WEBHOOK RECEBIDO | %s", dados)

    try:

        for entry in dados.get("entry", []):

            for evento in entry.get("messaging", []):

                background_tasks.add_task(
                    processar_evento,
                    evento
                )

    except Exception as erro:

        log.error("ERRO AO PROCESSAR WEBHOOK: %s", erro)

    # Responde rapidamente para a Meta
    return {
        "status": "ok"
    }


# =========================================================
# PAINEL SIMPLES DE LEADS
# =========================================================

@app.get("/leads")
def listar_leads():

    conexao = conectar()

    linhas = conexao.execute(
        "SELECT * FROM leads ORDER BY id DESC LIMIT 200"
    ).fetchall()

    conexao.close()

    return {
        "total": len(linhas),
        "leads": [dict(linha) for linha in linhas]
    }


# =========================================================
# TESTE
# =========================================================

@app.get("/")
def home():

    return {
        "status": "Prime Prep Bot online"
    }