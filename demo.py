"""Exercise the existing conversation router without Instagram or a persistent DB."""

import argparse
from contextlib import contextmanager
import importlib.util
import json
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch


@contextmanager
def demo_session():
    messages = []

    def capture(_url, **kwargs):
        messages.append(kwargs["json"]["message"])
        return SimpleNamespace(status_code=200, text="demo")

    old_logging = logging.root.manager.disable
    with TemporaryDirectory(prefix="primeprep-demo-") as directory:
        with (
            patch.dict(os.environ, {
                "BANCO_PATH": str(Path(directory) / "demo.db"),
                "INSTAGRAM_ACCESS_TOKEN": "offline-demo",
                "VERIFY_TOKEN": "offline-demo",
                "APP_SECRET": "offline-demo",
            }),
            patch("dotenv.load_dotenv", return_value=False),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Network disabled in demo")),
            patch("requests.post", side_effect=capture),
        ):
            logging.disable(logging.CRITICAL)
            try:
                spec = importlib.util.spec_from_file_location("primeprep_offline", Path(__file__).with_name("main.py"))
                bot = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(bot)
                yield bot, messages
            finally:
                logging.disable(old_logging)


def send(bot, messages, value):
    messages.clear()
    message = ({"quick_reply": {"payload": value[1:]}}
               if value.startswith("/") else {"text": value})
    bot.processar_evento({"sender": {"id": "offline-demo-user"}, "message": message})
    return messages


def show(messages):
    options = []
    for message in messages:
        print("\nBot:", message["text"])
        for reply in message.get("quick_replies", []):
            options.append(reply["payload"])
            print(f"  [{len(options)}] {reply['title']}")
    return options


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripted", action="store_true", help="Run a fictional registration and handoff example")
    args = parser.parse_args()
    print("Prime Prep | demonstração local com dados fictícios")
    print("Sem Instagram, sem leitura do .env e com banco temporário.")
    with demo_session() as (bot, messages):
        if args.scripted:
            for value in ("oi", "/MENU_MATRICULA", "Pessoa Exemplo", "18", "São Gabriel",
                          "/ALVO_ESA", "/MATRICULA_CONFIRMAR", "/MENU_ATENDIMENTO", "menu"):
                print("\nVocê:", value)
                show(send(bot, messages, value))
            print("\nRegistro de demonstração:")
            print(json.dumps(bot.listar_leads(), indent=2, ensure_ascii=False))
            return

        print("Digite o número de uma opção ou uma mensagem. /sair encerra.")
        options = show(send(bot, messages, "oi"))
        while True:
            try:
                value = input("\nVocê: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nDemonstração encerrada.")
                break
            if value == "/sair":
                break
            if not value:
                continue
            if value.isdigit() and options:
                index = int(value) - 1
                if not 0 <= index < len(options):
                    print("Escolha um número da lista ou envie uma mensagem.")
                    continue
                value = "/" + options[index]
            options = show(send(bot, messages, value))
            if not messages:
                print("Bot em pausa para atendimento humano. Digite menu para retornar.")


if __name__ == "__main__":
    main()
