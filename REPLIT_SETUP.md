# 🚀 AutoVideoEditor no Replit

Rodando tudo na nuvem, sem precisar de computador!

## 1️⃣ Criar Replit

### Opção A: Do GitHub (Mais Fácil)

1. Vá para: https://replit.com
2. Clique **+ Create** 
3. Selecione **Import from GitHub**
4. Cole: `https://github.com/douglasandrade95/Teste-cloude`
5. Clique **Import**

Pronto! Replit vai:
- ✅ Clonar o repositório
- ✅ Instalar dependências
- ✅ Detectar a configuração `.replit`

---

## 2️⃣ Configurar API Key

1. No Replit, abra o painel **Secrets** (ícone de cadeado)
2. Clique **+ Add Secret**
3. Nome: `ANTHROPIC_API_KEY`
4. Valor: `sk-ant-v0-xxxxx...` (sua chave Claude)
5. Clique **Add**

---

## 3️⃣ Rodar o App

Clique no botão **Run** (▶️) no topo.

O Replit vai:
1. Instalar FFmpeg
2. Instalar dependências Python
3. Instalar dependências Node
4. **Abrir o frontend em http://localhost:5173**

Após alguns segundos, você verá a interface no navegador! ✨

---

## 4️⃣ Como Usar (Do Celular)

1. O Replit abre automaticamente em uma **aba nova**
2. Você verá a interface do AutoVideoEditor
3. Pode fazer upload de vídeo direto!

---

## 🎬 URLs de Acesso

| Serviço | URL |
|---------|-----|
| Frontend | Abre automaticamente |
| Backend API | `https://seu-replit-url/api/v1` |
| API Docs | `https://seu-replit-url/docs` |

---

## ⚠️ Limitações do Replit Gratuito

- ⏱️ Timeout após 1 hora de inatividade
- 📁 500MB de armazenamento
- 💾 Videos muito grandes podem dar erro
- 🔄 Algumas features de background task podem não funcionar

**Para produção**, considere:
- Railway
- Render
- Heroku

---

## 🔧 Troubleshooting

### "Module not found"
```
Replit às vezes não instala tudo correto.
Clique em Run novamente.
```

### "Port already in use"
```
Replit gerencia as portas automaticamente.
Não precisa fazer nada - é normal.
```

### Frontend carrega em branco
```
Aguarde 30-60 segundos na primeira vez.
Replit está compilando o React.
```

### Upload não funciona
```
Certifique-se que ANTHROPIC_API_KEY está em Secrets.
```

---

## 📱 Usando do Celular

A URL do Replit funciona direto no navegador do celular:

1. Seu Replit vai gerar uma URL tipo:
   ```
   https://seu-nome-autovideoeditor.replit.dev
   ```

2. Acesse essa URL no Safari/Chrome do celular

3. Pronto! Pode usar o app normalmente.

---

## 🚀 Próximos Passos

1. ✅ App rodando no Replit
2. 🎬 Teste com um vídeo
3. 💾 Considere upgrade para:
   - **Railway** (recomendado)
   - **Render**
   - **Fly.io**

---

## 💡 Dicas

- Replit salva automaticamente
- Você pode acessar pelo celular em qualquer lugar
- Para compartilhar com amigos, dê a URL do Replit

Aproveita! 🎉
