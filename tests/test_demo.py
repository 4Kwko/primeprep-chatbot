import hashlib
import hmac
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from demo import demo_session, send


class ConversationDemoTests(unittest.TestCase):
    def test_registration_is_saved_only_after_confirmation(self):
        with demo_session() as (bot, messages):
            for value in ("oi", "/MENU_MATRICULA", "Pessoa Exemplo", "18", "São Gabriel", "/ALVO_ESA"):
                send(bot, messages, value)
            self.assertEqual(bot.listar_leads()["total"], 0)
            send(bot, messages, "/MATRICULA_CONFIRMAR")
            lead = bot.listar_leads()["leads"][0]
            self.assertEqual((lead["nome"], lead["idade"], lead["cidade"], lead["concurso"]),
                             ("Pessoa Exemplo", "18", "São Gabriel", "ESA"))
            self.assertEqual(bot.buscar_usuario("offline-demo-user")["estado"], bot.ESTADO_MENU)

    def test_invalid_age_stays_in_age_step(self):
        with demo_session() as (bot, messages):
            for value in ("oi", "/MENU_MATRICULA", "Pessoa Exemplo", "cem"):
                send(bot, messages, value)
            self.assertEqual(bot.buscar_usuario("offline-demo-user")["estado"], bot.ESTADO_MATRICULA_IDADE)
            self.assertEqual(bot.listar_leads()["total"], 0)
            self.assertIn("idade em número", messages[0]["text"])

    def test_handoff_silences_normal_messages_and_menu_resumes(self):
        with demo_session() as (bot, messages):
            send(bot, messages, "oi")
            send(bot, messages, "/MENU_ATENDIMENTO")
            self.assertTrue(bot.esta_pausado(bot.buscar_usuario("offline-demo-user")))
            self.assertEqual(send(bot, messages, "aguardo a equipe"), [])
            send(bot, messages, "menu")
            self.assertFalse(bot.esta_pausado(bot.buscar_usuario("offline-demo-user")))
            self.assertEqual(len(messages[0]["quick_replies"]), 5)

    def test_cancellation_does_not_create_lead(self):
        with demo_session() as (bot, messages):
            for value in ("oi", "/MENU_MATRICULA", "Pessoa Exemplo", "cancelar"):
                send(bot, messages, value)
            self.assertEqual(bot.listar_leads()["total"], 0)
            self.assertEqual(bot.buscar_usuario("offline-demo-user")["estado"], bot.ESTADO_MENU)

    def test_database_environment_and_network_are_isolated(self):
        with patch.dict(os.environ, {"BANCO_PATH": "do-not-touch.db", "APP_SECRET": "original"}):
            with demo_session() as (bot, messages):
                database = Path(bot.BANCO)
                self.assertNotEqual(str(database), "do-not-touch.db")
                self.assertTrue(database.exists())
                send(bot, messages, "oi")
                self.assertTrue(messages)
                with self.assertRaisesRegex(AssertionError, "Network disabled"):
                    bot.requests.get("https://example.invalid")
            self.assertFalse(database.exists())
            self.assertEqual(os.environ["BANCO_PATH"], "do-not-touch.db")
            self.assertEqual(os.environ["APP_SECRET"], "original")

    def test_signature_checks_configured_secret(self):
        with demo_session() as (bot, _):
            body = b'{"entry":[]}'
            digest = hmac.new(b"offline-demo", body, hashlib.sha256).hexdigest()
            self.assertTrue(bot.assinatura_valida(body, "sha256=" + digest))
            self.assertFalse(bot.assinatura_valida(body + b" ", "sha256=" + digest))
            self.assertFalse(bot.assinatura_valida(body, ""))


if __name__ == "__main__":
    unittest.main()
