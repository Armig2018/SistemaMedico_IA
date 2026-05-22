📋 Documentação Completa — MedVision AI
1. Introdução e Contexto do Projeto
O MedVision AI nasceu como um desafio da disciplina de Processamento de Imagens e Sinais (P.I.S.), com o objetivo de criar um sistema inteligente capaz de auxiliar médicos na detecção precoce de anomalias em imagens médicas como Raio-X, Ressonância Magnética, Mamografia e Retinografia.
O projeto foi construído em três camadas:

Frontend — Interface visual em HTML/CSS/JavaScript puro, rodando no navegador
Backend — API REST em Python com FastAPI
IA — Integração com o modelo Claude (Anthropic) para geração de laudos reais


2. Como o Projeto Foi Construído
2.1 Ponto de partida — o Frontend
O desenvolvimento começou pelo frontend. A primeira versão tinha apenas a tela de Análise, com upload de imagem, seleção de algoritmo, sliders de parâmetros e exibição de métricas. As imagens eram todas sintéticas — geradas matematicamente no canvas do navegador usando elipses, gradientes e ruído, simulando Raio-X, RM, Mamografia e Retinografia.
Nessa fase, todos os cálculos aconteciam no próprio JavaScript, sem backend.
2.2 Expansão do Frontend
Depois vieram as abas que estavam faltando: Histórico, Relatórios e Configurações. Cada uma trouxe seus próprios desafios:
O Histórico precisava de um mecanismo de busca e filtro em tempo real, além de um modal de detalhes. Foi implementado como um array em memória (analysisHistory), com função de exportação para CSV.
Os Relatórios exigiram gráficos feitos em SVG puro (sem bibliotecas externas), incluindo barras de precisão por análise e gráfico de rosca (donut) com a distribuição por modalidade.
As Configurações foram as mais trabalhosas. O problema principal era que os sliders tinham id nos <span> de exibição, e não nos <input> de fato. Então quando o código tentava ler .value, recebia undefined — porque span não tem valor. Isso causava NaN em todos os cálculos.
2.3 Os Três Bugs Críticos
Durante o desenvolvimento surgiram três bugs que exigiram atenção especial:
Bug 1 — Sempre Suspeito: O status era definido por d.anomalies.length > 0, ou seja, como o conjunto de demonstração sempre tinha anomalias cadastradas, todo resultado era "Suspeito" independentemente do limiar configurado. A solução foi filtrar as anomalias pelo threshold real antes de definir o status.
Bug 2 — Sempre Normal: Ao corrigir o bug anterior, surgiu o oposto. O limiar padrão estava em 0.80, mas as confiançaas das anomalias variavam entre 0.61 e 0.91. Com sensibilidade padrão de 0.75, o bias deslocava as confiançaas para baixo, fazendo quase tudo ficar abaixo do limiar. A solução foi recalibrar o limiar padrão para 0.50 e ajustar o bias de sensibilidade.
Bug 3 — Métricas sempre 100%: Era o bug mais sutil. Quando nenhuma anomalia era detectada, o código calculava TP / (TP + FP) com TP=0 e FP=0, resultando em divisão por zero. O fallback estava configurado como 1.0 (100%) em vez de 0.0. Além disso, o conjunto de avaliação era minúsculo (2 ou 3 anomalias), fazendo qualquer acerto virar 100%. A solução foi simular um conjunto de ~200 regiões, como modelos reais são avaliados.
2.4 Os Algoritmos
Cada algoritmo processa os pixels de forma diferente e isso afeta diretamente o resultado:
Filtragem Gaussiana é o mais equilibrado. Usa convolução com kernel gaussiano, onde o tamanho do kernel é calculado como sigma × 6 (regra dos 3-sigma), sempre arredondado para número ímpar. Quanto maior a intensidade do filtro, maior o sigma e mais suave fica a imagem. É bom para remover ruído mas pode apagar detalhes finos.
Segmentação Watershed compara cada pixel com a média da sua vizinhança local (threshold adaptativo), em vez de um valor global. Isso é mais eficiente para imagens com iluminação desigual, comum em mamografias. Depois aplica morfologia para limpar ruídos.
CNN Multiclasse simula um mapa de ativação neural calculando o Laplaciano da imagem (segunda derivada, que detecta regiões de alta variação de intensidade) e aplicando colormap JET para visualização. Em um sistema real, aqui entraria uma rede neural treinada com dataset rotulado.
Detecção Canny é o mais preciso para bordas mas o que gera mais falsos positivos. Suaviza com Gaussiano, calcula gradiente com Sobel, aplica supressão não-máxima e threshold duplo (histerese). Os thresholds hi e lo são ajustados pela sensibilidade configurada.
2.5 A Integração com IA Real
A maior evolução do projeto foi substituir a detecção puramente simulada por análise real via API do Claude. Quando o usuário faz upload de uma imagem real (não demo), o sistema converte para base64 e envia para o Claude com um prompt estruturado que exige resposta em JSON com campos definidos: status, confiança, achados, regiões suspeitas, recomendação e resumo.
Um cuidado importante foi usar re.search(r'\{[\s\S]*\}', raw) para extrair o JSON da resposta, porque o modelo às vezes inclui texto antes ou depois do JSON, e um json.loads() direto quebraria nesses casos.
2.6 O Backend
O backend foi construído como um arquivo único main.py em FastAPI, com decisão consciente de não separar em múltiplos arquivos — facilitando o uso no Colab e no GitHub sem gerenciar pastas. Tem seis partes principais:
Banco de dados em SQLite com aiosqlite (versão assíncrona). A escolha do SQLite foi por não exigir instalação de servidor. As métricas e anomalias são guardadas como JSON dentro de colunas TEXT, em vez de tabelas relacionadas separadas, para dar flexibilidade caso novos campos sejam adicionados no futuro.
Pré-processamento com CLAHE (equalização adaptativa de histograma com clipLimit=2.0 em janelas de 8×8 pixels). O clipLimit evita amplificar ruído — problema que a equalização global de histograma causa.
Detecção por contornos com findContours do OpenCV. Cada contorno é filtrado por área (mínimo 300px², máximo 40.000px²) e por confiança calculada com base na intensidade média da região.
Validação com Pydantic que bloqueia automaticamente valores fora do range sem precisar de nenhum if manual no código. Se threshold vier como 2.0 (acima do máximo 0.95), a API retorna erro 422 com a descrição exata do problema.
CORS configurado para aceitar qualquer origem (*), necessário para o frontend HTML se comunicar com o backend rodando em porta diferente.

3. Estrutura das Rotas
MétodoRotaO que fazPOST/api/analiseAnálise completa via JSON com base64POST/api/analise/uploadAnálise via upload de arquivoGET/api/historicoLista com filtros por status, tipo e buscaGET/api/historico/{id}Detalhe completo de uma análiseDELETE/api/historico/{id}Remove uma análiseDELETE/api/historicoLimpa tudoGET/api/relatoriosKPIs e breakdown por modalidadeGET/api/configuracoesLê configurações salvasPUT/api/configuracoesSalva configuraçõesGET/healthStatus do servidor

4. Fluxo Completo de uma Análise
Usuário faz upload da imagem
         │
         ▼
Frontend converte para base64
         │
         ▼
POST /api/analise (JSON)
         │
         ▼
Pydantic valida os campos
         │
         ▼
PIL decodifica base64 → numpy array
         │
         ▼
preprocessar() → CLAHE + normalização [0,1]
         │
         ▼
aplicar_algoritmo() → transforma pixels conforme algoritmo escolhido
         │
         ▼
detectar_anomalias() → findContours → filtra por área e confiança
         │
         ▼
calcular_metricas() → TP/FP/FN/TN → Precisão / Recall / F1
         │
         ▼
analisar_com_ia() → envia para Claude → recebe laudo JSON
         │
         ▼
SQLite INSERT → persiste tudo
         │
         ▼
Retorna JSON completo para o frontend

5. As Partes Mais Importantes
5.1 O Threshold (Limiar de Confiança)
É o coração do sistema. Controla o equilíbrio entre sensibilidade (detectar mais, com risco de falsos positivos) e especificidade (detectar menos, com risco de falsos negativos). Em medicina, falsos negativos são mais perigosos que falsos positivos — não detectar uma doença é pior que suspeitar de algo que não existe. Por isso o padrão foi calibrado em 0.50 e não em valores mais altos.
5.2 As Métricas Clínicas
As três métricas implementadas têm significado clínico real:
Precisão responde: dos casos que o sistema sinalizou como suspeitos, quantos eram realmente suspeitos? Precisão baixa significa muitos alarmes falsos, sobrecarregando médicos.
Recall (Sensibilidade) responde: de todos os casos doentes existentes, quantos o sistema encontrou? Recall baixo é o mais perigoso clinicamente — significa que doenças estão passando despercebidas.
F1-Score é a média harmônica dos dois. É a métrica mais importante quando as classes são desbalanceadas (muito mais casos normais que suspeitos, como é na prática médica).
5.3 O Laudo por IA
A integração com o Claude transformou o sistema de um simulador em uma ferramenta com potencial real. O prompt foi cuidadosamente construído para:

Especificar o tipo de exame (contexto para o modelo)
Exigir JSON estruturado sem texto extra
Pedir que o modelo seja conservador e use "INCONCLUSIVO" quando a imagem não for clara o suficiente

5.4 O Banco de Dados Assíncrono
Usar aiosqlite em vez do sqlite3 padrão é fundamental para o FastAPI funcionar corretamente. O FastAPI é um framework assíncrono — se você usar uma biblioteca síncrona para banco de dados, ela bloqueia o servidor inteiro enquanto espera a resposta do banco. Com async/await, o servidor continua atendendo outras requisições enquanto espera o banco.

6. Dificuldades Encontradas
Leitura errada dos sliders foi a dificuldade mais recorrente. O problema de colocar id no <span> em vez do <input> causou o bug das métricas 100% e o bug "sempre normal", porque span.value retorna undefined e parseFloat(undefined) vira NaN, quebrando todos os cálculos silenciosamente.
Calibração do threshold exigiu várias iterações. O sistema precisa ser sensível o suficiente para detectar doenças reais, mas não tão sensível que classifique tudo como suspeito. O equilíbrio entre o bias de sensibilidade, o bias por algoritmo e o threshold padrão foi ajustado empiricamente.
Extração de JSON da resposta da IA foi necessária porque o modelo às vezes envolve o JSON em blocos de código markdown (```json ```) ou adiciona texto explicativo. O regex r'\{[\s\S]*\}' resolve isso extraindo apenas o objeto JSON independentemente do que vier antes ou depois.
Algoritmos de imagem no canvas vs. backend criou uma duplicação necessária: os algoritmos precisaram ser implementados duas vezes — uma em JavaScript (para o canvas do frontend) e uma em Python com OpenCV (para o backend). As implementações são equivalentes mas usam APIs completamente diferentes.
Persistência de dados entre sessões no frontend era inexistente — o histórico sumia ao fechar o navegador. Isso foi resolvido com o backend e o SQLite, que persiste tudo em disco.

7. Tecnologias Utilizadas e Por Que Cada Uma
TecnologiaMotivo da escolhaFastAPIFramework mais moderno para APIs Python, nativo assíncrono, gera documentação automática no /docsSQLite + aiosqliteZero configuração, arquivo local, perfeito para protótipos; fácil de migrar para PostgreSQL em produçãoOpenCVPadrão da indústria para visão computacional, implementa todos os algoritmos necessários de forma otimizadaPydanticValidação automática de dados, elimina boilerplate de if/else para checar camposAnthropic ClaudeModelo com forte capacidade de análise de imagens médicas e retorno estruturado em JSONHTML/CSS/JS puroSem frameworks — o arquivo funciona abrindo direto no navegador, sem instalar nada

8. Aviso Importante
Todo o sistema foi desenvolvido para fins educacionais, como exigido pelo desafio da disciplina P.I.S. Os laudos gerados pela IA, as métricas calculadas e as anomalias detectadas não substituem avaliação médica profissional. Em um ambiente clínico real, o sistema precisaria ser validado com datasets rotulados por especialistas, ter aprovação regulatória (ANVISA no Brasil, FDA nos EUA) e passar por testes clínicos extensivos antes de qualquer uso diagnóstico.
