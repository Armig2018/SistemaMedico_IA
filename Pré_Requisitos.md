## Pré-requisitos

Você precisa ter instalado:
- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads)
- **VSCode** com a extensão **Python** (Microsoft)

---

## Passo a passo

### 1. Criar ambiente virtual

Abra o terminal no VSCode (`Ctrl + '`) e rode:

```bash
# Criar o ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Ativar (Mac/Linux)
source venv/bin/activate
```

Você saberá que funcionou quando aparecer `(venv)` no início do terminal.

---

### 2. Instalar todas as bibliotecas

Com o ambiente virtual ativado:

```bash
pip install fastapi uvicorn[standard] pydantic aiosqlite anthropic opencv-python-headless numpy Pillow python-multipart
```

O que cada uma faz no projeto:

| Biblioteca | Para que serve no código |
|---|---|
| `fastapi` | Framework que cria as rotas (`@app.get`, `@app.post`) |
| `uvicorn[standard]` | Servidor que roda o FastAPI (`uvicorn main:app`) |
| `pydantic` | Valida os dados recebidos (`AnaliseRequest`, `ConfiguracaoRequest`) |
| `aiosqlite` | Conecta ao banco SQLite de forma assíncrona (`async with aiosqlite.connect(...)`) |
| `anthropic` | SDK do Claude para o laudo por IA (`client.messages.create(...)`) |
| `opencv-python-headless` | Todos os algoritmos de imagem (`cv2.GaussianBlur`, `cv2.Canny`, etc.) |
| `numpy` | Operações nos pixels (`np.array`, `np.float32`) |
| `Pillow` | Lê o arquivo de imagem antes de passar pro OpenCV (`Image.open(...)`) |
| `python-multipart` | Necessário para o upload de arquivo funcionar (`UploadFile`) |

---

### 3. Configurar a API Key do Claude

No terminal, antes de rodar:

```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY = "sua-chave-aqui"

# Windows (CMD)
set ANTHROPIC_API_KEY=sua-chave-aqui

# Mac/Linux
export ANTHROPIC_API_KEY="sua-chave-aqui"
```

Ou crie um arquivo `.env` na raiz do projeto:

```
ANTHROPIC_API_KEY=sua-chave-aqui
```

E instale o `python-dotenv` para carregar automaticamente:

```bash
pip install python-dotenv
```

Adicione no topo do `main.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

### 4. Rodar o servidor

```bash
uvicorn main:app --reload
```

Você verá algo assim no terminal:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
✅ Banco de dados pronto
🚀 MedVision AI iniciando...
```

---

### 5. Verificar se está funcionando

Abra no navegador:

- **`http://localhost:8000/health`** — deve retornar `{"status": "online", ...}`
- **`http://localhost:8000/docs`** — abre o Swagger UI com todas as rotas para testar

---

### Estrutura de arquivos esperada no VSCode

```
medvision/
│
├── main.py              ← o código do backend
├── .env                 ← sua API key (não suba no GitHub!)
├── .gitignore           ← adicione .env e venv/ aqui
├── medvision.db         ← criado automaticamente ao rodar
│
└── venv/                ← ambiente virtual (não suba no GitHub!)
```

---

### `.gitignore` recomendado

```
venv/
.env
medvision.db
__pycache__/
*.pyc
.DS_Store
```

Isso garante que sua API key e o banco de dados não vão parar no GitHub.
