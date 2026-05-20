"""
╔══════════════════════════════════════════════════════════════════╗
║          MedVision AI — Versão Simplificada (FastAPI)            ║
║          Disciplina: Processamento de Imagens e Sinais          ║
╚══════════════════════════════════════════════════════════════════╝

Como rodar:
  1. Instale as dependências básicas:
     pip install fastapi uvicorn opencv-python numpy pillow pydantic
  2. Execute o arquivo:
     python main.py
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import base64
import cv2
import numpy as np
import time
import io
from PIL import Image

# Inicializa o FastAPI
app = FastAPI(title="MedVision AI Simplificado")

# Configura o CORS de forma simples
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "medvision.db"

# ─────────────────────────────────────────────────────────────────────────────
#  FUNÇÃO SIMPLES PARA INICIALIZAR O BANCO DE DADOS (SQLite Comum)
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabela de análises
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analises (
            id TEXT PRIMARY KEY,
            tipo_exame TEXT,
            algoritmo TEXT,
            status TEXT,
            tempo_ms REAL,
            deteccoes TEXT
        )
    """)
    # Tabela de configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY,
            algoritmo_padrao TEXT,
            threshold_padrao REAL
        )
    """)
    # Insere uma configuração padrão se não existir
    cursor.execute("INSERT OR IGNORE INTO configuracoes (id, algoritmo_padrao, threshold_padrao) VALUES (1, 'Filtragem Gaussiana', 0.50)")
    conn.commit()
    conn.close()

# Inicializa o banco de dados logo que o script roda
init_db()

# ─────────────────────────────────────────────────────────────────────────────
#  MODELOS DE DADOS (Pydantic Simples)
# ─────────────────────────────────────────────────────────────────────────────
class AnaliseRequest(BaseModel):
    imagem_base64: str
    tipo_exame: str = "Raio-X"
    algoritmo: str = "Filtragem Gaussiana"
    threshold: float = 0.50
    sensibilidade: float = 0.75

class ConfiguracaoRequest(BaseModel):
    algoritmo_padrao: str
    threshold_padrao: float

# ─────────────────────────────────────────────────────────────────────────────
#  PROCESSAMENTO DE IMAGEM (OpenCV + NumPy)
# ─────────────────────────────────────────────────────────────────────────────
def processar_e_detectar(img_np: np.ndarray, algoritmo: str, threshold: float, tipo_exame: str):
    # 1. Converter para Tons de Cinza se for colorida
    if len(img_np.shape) == 3:
        img_cinza = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
    else:
        img_cinza = img_np

    # 2. Redimensionar para um padrão estável
    img_cinza = cv2.resize(img_cinza, (512, 512))

    # 3. Aplicar o Algoritmo escolhido
    if algoritmo == "Filtragem Gaussiana":
        img_filtrada = cv2.GaussianBlur(img_cinza, (5, 5), 1.5)
    elif algoritmo == "Detecção Canny":
        img_filtrada = cv2.Canny(img_cinza, 50, 150)
    else:
        img_filtrada = img_cinza  # Filtro padrão caso mude o nome

    # 4. Detecção de contornos/anomalias simulada via Thresholding clássico
    _, img_binaria = cv2.threshold(img_cinza, 127, 255, cv2.THRESH_BINARY)
    contornos, _ = cv2.findContours(img_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    anomalias = []
    # Lista simples de achados comuns dependendo do exame para preencher o JSON
    achados_possiveis = {
        "Raio-X": "Opacidade/Nódulo Pulmonar",
        "Mamografia": "Microcalcificação Agrupada",
        "Ressonância": "Lesão Expansiva T2",
        "Tomografia": "Massa Densidade Alterada"
    }
    nome_achado = achados_possiveis.get(tipo_exame, "Região com Alteração de Densidade")

    # Filtra os contornos encontrados por tamanho para simular manchas/nódulos
    for i, c in enumerate(contornos):
        area = cv2.contourArea(c)
        if 500 < area < 15000:  # Evita sujeiras muito pequenas ou o fundo inteiro
            x, y, w, h = cv2.boundingRect(c)
            # Calcula uma confiança fictícia baseada no tamanho da área encontrada
            confianca = min(0.98, threshold + (area / 30000))
            
            anomalias.append({
                "id_regiao": i + 1,
                "achado": nome_achado,
                "confianca": round(confianca, 2),
                "coordenadas": {"x": x, "y": y, "largura": w, "altura": h}
            })
            if len(anomalias) >= 3:  # Limita a no máximo 3 achados para o JSON ficar limpo
                break

    return anomalias

# ─────────────────────────────────────────────────────────────────────────────
#  ROTAS DA API
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/analise")
def analisar_imagem(req: AnaliseRequest):
    tempo_inicial = time.time()
    
    try:
        # Limpa o cabeçalho do base64 se o frontend enviar (ex: "data:image/jpeg;base64,...")
        dados_b64 = req.imagem_base64
        if "," in dados_b64:
            dados_b64 = dados_b64.split(",")[1]

        # Converte a string Base64 de volta para uma imagem utilizável
        img_bytes = base64.b64decode(dados_b64)
        img_pil = Image.open(io.BytesIO(img_bytes))
        img_np = np.array(img_pil)

        # Processa a imagem usando nossa função do OpenCV
        anomalias_detectadas = processar_e_detectar(
            img_np, req.algoritmo, req.threshold, req.tipo_exame
        )

        # Define o diagnóstico clínico com base nas detecções
        status_final = "SUSPEITO" if len(anomalias_detectadas) > 0 else "SAUDAVEL"
        
        # Gera uma recomendação médica padrão de forma inteligente e local
        if status_final == "SUSPEITO":
            recomendacao = f"A análise automática identificou estruturas compatíveis com {anomalias_detectadas[0]['achado']}. Recomenda-se correlação com a história clínica do paciente e avaliação por um médico especialista."
        else:
            recomendacao = "Nenhuma alteração macroscópica ou padrão de anomalia foi detectado pelos algoritmos nesta triagem preliminar."

        tempo_total_ms = round((time.time() - tempo_inicial) * 1000, 2)
        id_analise = str(int(time.time())) # ID simples usando o timestamp atual

        # Salva o resultado no Banco de Dados SQLite Comum
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analises (id, tipo_exame, algoritmo, status, tempo_ms, deteccoes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_analise, req.tipo_exame, req.algoritmo, status_final, tempo_total_ms, str(anomalias_detectadas)))
        conn.commit()
        conn.close()

        # Retorna a resposta limpa para o frontend
        return {
            "id_analise": id_analise,
            "status": status_final,
            "tempo_processamento_ms": tempo_total_ms,
            "diagnostico_local": {
                "resumo": f"Exame de {req.tipo_exame} processado via {req.algoritmo}.",
                "recomendacao": recomendacao
            },
            "anomalias": anomalias_detectadas
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar imagem: {str(e)}")


@app.get("/api/historico")
def listar_historico():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo_exame, algoritmo, status, tempo_ms FROM analises ORDER BY id DESC")
    linhas = cursor.fetchall()
    conn.close()

    historico = []
    for l in linhas:
        historico.append({
            "id": l[0],
            "tipo_exame": l[1],
            "algoritmo": l[2],
            "status": l[3],
            "tempo_ms": l[4]
        })
    return {"total": len(historico), "registros": historico}


@app.get("/api/configuracoes")
def buscar_configuracoes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT algoritmo_padrao, threshold_padrao FROM configuracoes WHERE id = 1")
    linha = cursor.fetchone()
    conn.close()
    
    return {
        "algoritmo_padrao": linha[0],
        "threshold_padrao": linha[1]
    }


@app.put("/api/configuracoes")
def salvar_configuracoes(cfg: ConfiguracaoRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE configuracoes 
        SET algoritmo_padrao = ?, threshold_padrao = ? 
        WHERE id = 1
    """, (cfg.algoritmo_padrao, cfg.threshold_padrao))
    conn.commit()
    conn.close()
    return {"mensagem": "Configurações atualizadas com sucesso!"}


@app.get("/health")
def status_servidor():
    return {"status": "online", "banco_dados": "conectado"}


if __name__ == "__main__":
    import uvicorn
    # Executa o servidor localmente na porta 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)