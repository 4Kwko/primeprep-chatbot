# Execução local e integração

[Voltar ao README](../README.md) · [Meta: Instagram Platform](https://developers.facebook.com/docs/instagram-platform/)

## Avaliação sem credenciais

Siga a instalação do README e execute `python demo.py --scripted`. Esse é o caminho recomendado para examinar a conversa. O simulador usa o roteador existente e um banco temporário, com chamadas HTTP interceptadas.

## Iniciar a aplicação FastAPI

Depois de instalar `requirements.txt`, copie `.env.example` para `.env`. No PowerShell:

```powershell
Copy-Item .env.example .env
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

No macOS ou Linux, use `cp .env.example .env` antes do mesmo comando do Uvicorn.

Abra `http://127.0.0.1:8000/` para consultar o status ou `http://127.0.0.1:8000/docs` para examinar as rotas locais. Isso inicia a API; não conecta o Instagram automaticamente.

| Variável | Utilização |
| --- | --- |
| `INSTAGRAM_ACCESS_TOKEN` | Token utilizado nas chamadas de saída à API. |
| `VERIFY_TOKEN` | Valor escolhido para conferir o desafio de verificação do webhook. |
| `APP_SECRET` | Segredo do aplicativo usado na validação HMAC do corpo recebido. |
| `BANCO_PATH` | Caminho do banco SQLite. Padrão: `primeprep.db`. |

O `.env.example` tem valores vazios. Para conectar eventos reais, preencha todos os segredos exigidos. `.env` e arquivos de banco estão no `.gitignore`.

## Conectar uma conta real

O acesso depende de conta, aplicativo, permissões e configuração na Meta. Consulte a [documentação oficial atual da Instagram Platform](https://developers.facebook.com/docs/instagram-platform/) para o tipo de login usado no seu aplicativo.

1. Configure a conta e o aplicativo de acordo com a modalidade de integração escolhida.
2. Defina token de acesso, segredo do aplicativo e token de verificação nas variáveis de ambiente.
3. Publique um callback HTTPS para `/webhook`, com as correções de acesso e validação descritas abaixo.
4. Configure no painel da Meta o callback, seu token de verificação e os eventos de mensagens correspondentes.
5. Teste com contas de teste autorizadas no aplicativo e confirme recebimento e envio nos dois sentidos.

O endpoint de envio e a versão da API estão em `API_URL`. O repositório não fixa uma configuração completa de aplicativo Meta nem fornece um token. Não execute `subscribe.py` esperando que ele inscreva o app nos eventos: ele apenas consulta a conta associada ao token e imprime a resposta.

## Antes de expor o serviço

A versão atual precisa de autenticação ou bloqueio externo para `/leads`, rejeição de eventos quando o segredo não estiver configurado e revisão dos logs com dados pessoais. Essas limitações existem no código; a documentação e a demonstração não as removem.

Revise também os textos comerciais e dados sobre concursos no início de `main.py`. O negócio está em pausa, e esses textos não devem ser tratados como oferta ou calendário atual de um curso em operação.
