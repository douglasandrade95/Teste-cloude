# Rodar o AutoVideoEditor no Replit

Para acessar do celular, de qualquer lugar, sem instalar nada.

O app inteiro roda numa **URL só**: o backend serve a interface e a API juntos.
Não tem porta separada nem endereço de API para configurar.

---

## 1. Importar o repositório

1. Abra https://replit.com
2. **+ Create** → **Import from GitHub**
3. Cole: `https://github.com/douglasandrade95/Teste-cloude`
4. **Import**

O Replit lê o `.replit` e já sabe o que fazer.

---

## 2. Configurar os dois segredos

Abra o painel **Secrets** (ícone de cadeado) e adicione:

| Nome | Para que serve |
|---|---|
| `AVE_MASTER_KEY` | A chave que criptografa o cofre. **Sem ela, toda vez que o Replit reiniciar o cofre ganha uma chave nova e a sua chave de API salva vira ilegível.** |
| `AVE_ADMIN_TOKEN` | Libera a tela de Integrações fora da máquina local. Sem ele, o navegador do celular recebe 403 e você não consegue salvar chave nenhuma. |

**Não precisa inventar os valores.** Clique **Run** uma vez: o script detecta que
estão faltando e imprime dois valores prontos no console. Copie, cole em
Secrets, e clique Run de novo.

Se preferir gerar por conta própria:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"   # AVE_MASTER_KEY
python -c "import secrets; print(secrets.token_urlsafe(24))"                                 # AVE_ADMIN_TOKEN
```

> As chaves de API (Kie.ai, Anthropic…) **não** vão aqui. Elas entram pela tela
> de Integrações, que as guarda criptografadas. Ver `INTEGRACOES_API.md`.

---

## 3. Rodar

Clique **Run**. O script:

1. instala as dependências do backend e do frontend;
2. **compila** o frontend (`npm run build`);
3. sobe o FastAPI servindo tudo na porta 8000.

A primeira vez demora alguns minutos, principalmente as bibliotecas de vídeo.

---

## 4. Usar do celular

O Replit mostra uma URL tipo `https://seu-repl.replit.dev`. Abra no navegador
do celular.

| Caminho | O que é |
|---|---|
| `/integracoes` | Cadastrar e testar as chaves de API |
| `/gerar` | O Studio: escolher modelo e gerar vídeo |
| `/editor` | O editor de vídeo |
| `/docs` | Documentação da API |

**Na primeira vez que abrir Integrações**, a tela vai pedir o token de
administração. Cole o valor de `AVE_ADMIN_TOKEN`. Ele fica só naquela aba do
navegador e some quando você fecha — então terá que colar de novo em cada
aparelho.

Depois disso: escolha o provedor, cole a chave de API, **Salvar com segurança**.

---

## O que pode dar errado

**"Editor routes unavailable" no console.** As bibliotecas de vídeo
(moviepy, librosa, numpy) são pesadas e às vezes falham num host pequeno. O app
sobe do mesmo jeito, e o Studio e as Integrações funcionam — só o `/editor`
fica fora. Clicar Run de novo costuma resolver.

**Tela de Integrações dá 403.** Falta `AVE_ADMIN_TOKEN` em Secrets, ou você
ainda não colou o token na tela.

**A chave de API sumiu depois de um restart.** Falta `AVE_MASTER_KEY` em
Secrets. Configure e cadastre a chave de novo.

**Página em branco.** O build ainda não terminou. Veja o console até aparecer
`Serving on port 8000`.

---

## Limites do Replit gratuito

- Hiberna após um tempo sem uso; a primeira visita depois disso é lenta
- Armazenamento pequeno — vídeos grandes podem não caber
- Tarefas de fundo longas podem ser interrompidas

Para uso sério, Railway ou Render seguram melhor. O mesmo script serve nos dois:
eles só precisam rodar `scripts/replit-start.sh` e expor a porta `$PORT`.
