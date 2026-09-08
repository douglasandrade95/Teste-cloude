# Integrações de API — onde colocar a sua chave

Resposta curta: **você não coloca a chave em lugar nenhum do código.**
Você abre `http://localhost:5173/integracoes`, cola a chave no campo, clica em
**Salvar com segurança**, e pronto. A chave vai criptografada para um cofre
fora do repositório.

---

## 1. Subir o app

```bash
# backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend (outro terminal)
cd frontend
npm install
npm run dev
```

Depois abra **http://localhost:5173/integracoes**.

---

## 2. Cadastrar a chave

Na tela você vê, para cada provedor:

| Elemento | O que é |
|---|---|
| Bolinha verde | já tem chave configurada |
| Selo **Grátis** | provedor com camada gratuita |
| **Onde pegar a chave** | link direto para o painel do provedor |
| **Testar conexão** | bate no provedor de verdade e diz se a chave é válida |
| **Salvar com segurança** | testa e só então grava criptografada |
| **Modelo → Ativar** | escolhe qual modelo o editor vai usar |

O fluxo é: escolher o provedor à esquerda → colar a chave → **Salvar com
segurança** → escolher o modelo → **Ativar**.

Se a chave estiver errada, o app se recusa a salvar e diz o motivo. Nada de
descobrir só na hora de editar o vídeo.

---

## 3. Opções gratuitas

Se você não quer colocar cartão agora, comece por uma destas:

| Provedor | Como é o grátis | Onde pegar |
|---|---|---|
| **Google Gemini** | camada gratuita no AI Studio, com limite por minuto/dia | https://aistudio.google.com/app/apikey |
| **Groq** | camada gratuita, inferência muito rápida | https://console.groq.com/keys |
| **OpenRouter** | modelos com sufixo `:free` não consomem crédito | https://openrouter.ai/keys |
| **Ollama** | roda na sua máquina: zero custo, zero chave, nada sai do computador | https://ollama.com/download |

> Hoje a análise criativa do editor fala a API da Anthropic (Claude). Os outros
> provedores já ficam cadastrados, testados e prontos no cofre — a troca do
> motor de análise entra na próxima fase.

---

## 4. Como a chave fica segura

**Criptografada em repouso.** A chave é gravada com Fernet
(AES-128-CBC + HMAC-SHA256) em `~/.autovideoeditor/secrets.enc`, com permissão
`0600` — só o seu usuário lê. A chave de criptografia fica em
`~/.autovideoeditor/master.key`, também `0600`.

**Nunca volta pela tela.** Nenhum endpoint devolve a chave em texto puro. A
interface recebe só os 4 últimos caracteres (`••••••••1234`), o suficiente para
você reconhecer qual é.

**Fora do Git.** O cofre mora fora do repositório, e o `.gitignore` ainda
bloqueia `master.key`, `secrets.enc`, `*.enc` e `.env`. Não tem como subir sem
querer.

**Fechada por padrão.** As rotas de credenciais só respondem para a própria
máquina. Para liberar acesso de fora é preciso definir `AVE_ADMIN_TOKEN` no
servidor — aí a tela pede esse token, que fica só na aba do navegador e some
quando você fecha.

**Só chave válida entra.** Antes de gravar, o backend testa a chave num
endpoint de leitura do provedor. Chave recusada não é salva.

---

## 5. Em servidor (Replit, Railway, Render, Docker)

Duas coisas mudam:

**a) Fixe a chave de criptografia.** Sem isso, cada container gera uma nova e o
cofre antigo fica ilegível.

```bash
# gere uma vez
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Coloque o resultado em `AVE_MASTER_KEY` nos secrets da plataforma. Assim quem
só tiver o arquivo `secrets.enc` não consegue abrir nada.

**b) Proteja a tela.** Defina `AVE_ADMIN_TOKEN` com um valor forte. Sem ele, o
backend só aceita alterações vindas de `localhost`.

---

## 6. Caminho alternativo: variável de ambiente

Se preferir não usar a tela, dá no mesmo definir a variável no `.env` ou nos
secrets da hospedagem:

```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
REPLICATE_API_TOKEN=r8_...
```

A tela mostra essas chaves como **“via Variável de ambiente”**. O cofre tem
prioridade: se existir chave nos dois lugares, vale a do cofre.

---

## 7. Endpoints (para referência)

Todos sob `/api/v1/settings`, todos protegidos pelo guarda de acesso:

| Método | Rota | O que faz |
|---|---|---|
| `GET` | `/integrations` | catálogo de provedores, modelos e status das chaves |
| `PUT` | `/providers/{id}/key` | testa e grava a chave criptografada |
| `POST` | `/providers/{id}/test` | testa uma chave (nova ou a já guardada) |
| `DELETE` | `/providers/{id}/key` | apaga a chave do cofre |
| `GET/PUT` | `/active-model` | lê/define provedor + modelo ativos |
| `GET` | `/vault` | onde e como o cofre está guardado |

Nenhum deles devolve chave em texto puro — nem o `GET`.
