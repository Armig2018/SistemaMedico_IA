# Documentação Técnica — MedVision AI 


---

O MedVision AI é um sistema de análise de imagens médicas desenvolvido para identificar automaticamente anomalias em exames como Raio-X, Ressonância Magnética, Mamografia e Retinografia. O sistema combina algoritmos clássicos de processamento de imagem com inteligência artificial para gerar laudos automáticos, auxiliando profissionais de saúde na detecção precoce de doenças. O projeto foi construído em três camadas integradas: uma interface visual interativa no navegador, um servidor em Python com FastAPI e uma integração com o modelo de linguagem Claude da Anthropic para análise por IA.

---

## A1 — Requisitos e Ferramentas

Antes de qualquer linha de código, foram levantados os requisitos funcionais do sistema. O sistema precisaria aceitar imagens nos formatos JPEG, PNG e DICOM, processar essas imagens com pelo menos quatro algoritmos distintos, identificar regiões suspeitas com confiança mensurável, calcular métricas de validação clínica e exibir os resultados de forma visual e interativa.

As ferramentas foram escolhidas com justificativa técnica para cada uma. No frontend, a decisão foi usar HTML, CSS e JavaScript puros, sem frameworks, para que o sistema funcionasse abrindo diretamente no navegador sem nenhuma instalação. A API Canvas do navegador foi usada para renderizar e processar as imagens visualmente em tempo real. No backend, o Python foi escolhido por ser a linguagem padrão do ecossistema de visão computacional e machine learning. O FastAPI foi selecionado em vez do Flask por ser nativamente assíncrono, o que permite atender múltiplas requisições simultâneas sem travar o servidor enquanto espera operações de banco de dados ou chamadas externas à API de IA.

Para processamento de imagem, o OpenCV foi a escolha central por implementar todos os algoritmos necessários de forma otimizada e documentada. O NumPy complementa o OpenCV para operações matriciais sobre os arrays de pixels. O Pillow foi adicionado para garantir compatibilidade na leitura de múltiplos formatos de entrada antes de passar a imagem para o OpenCV. O banco de dados escolhido foi o SQLite com aiosqlite, sua versão assíncrona, por não exigir instalação de servidor separado e ser suficiente para o volume de dados do projeto. Para a integração com inteligência artificial, o SDK oficial da Anthropic foi usado para comunicação com o modelo Claude. O Pydantic foi adotado para validação automática de todos os dados recebidos pelo servidor, eliminando a necessidade de verificações manuais no código.

---

## A2 — Algoritmo de Processamento

O pipeline de processamento foi dividido em quatro estágios encadeados, onde a saída de cada etapa alimenta a próxima.

O primeiro estágio é o pré-processamento, responsável por padronizar qualquer imagem recebida antes de processá-la. A imagem é convertida para escala de cinza, pois imagens médicas são analisadas em tons de cinza. Em seguida é redimensionada para 512x512 pixels usando interpolação bicúbica, que preserva melhor os detalhes finos que outros métodos. Depois é aplicado o CLAHE, sigla para Contrast Limited Adaptive Histogram Equalization, que melhora o contraste de forma localizada em janelas de 8x8 pixels com um limite de amplificação de 2.0 para evitar que o ruído seja amplificado junto com o sinal útil. Por fim a imagem é normalizada para valores entre 0 e 1, formato esperado pelos algoritmos seguintes.

O segundo estágio aplica o algoritmo selecionado pelo usuário. A Filtragem Gaussiana realiza uma convolução com kernel gaussiano cujo tamanho é calculado como sigma multiplicado por 6, arredondado para número ímpar pela regra dos 3-sigma. Reduz ruído gaussiano preservando estruturas maiores, sendo indicada para imagens de Ressonância Magnética que tendem a ter ruído distribuído uniformemente. A Segmentação Watershed aplica threshold adaptativo, comparando cada pixel com a média da sua vizinhança local em vez de um valor global, seguido de morfologia de abertura para eliminar pequenos ruídos. É mais eficiente para imagens com iluminação não uniforme como mamografias. A CNN Multiclasse calcula o Laplaciano da imagem, que é a segunda derivada espacial e detecta regiões de alta variação de intensidade, gerando um mapa de saliência com colormap JET que simula visualmente o que seria um mapa de ativação de uma rede neural. A Detecção Canny suaviza a imagem com filtro Gaussiano, calcula o gradiente com operadores Sobel nas direções horizontal e vertical, aplica supressão não-máxima para afinar as bordas a um pixel de espessura e finaliza com threshold duplo por histerese, onde bordas fortes acima do limiar alto são confirmadas e bordas fracas entre os dois limiares são incluídas apenas se conectadas a bordas fortes.

O terceiro estágio é a detecção de anomalias por contornos. A imagem processada é binarizada com threshold de Otsu, método estatístico que encontra automaticamente o ponto de corte ótimo entre regiões claras e escuras. Morfologia de abertura remove pequenos pontos de ruído e morfologia de fechamento preenche buracos internos. O findContours do OpenCV identifica as bordas de cada região conectada. Para cada contorno encontrado, a área é calculada e regiões menores que 300 pixels quadrados são descartadas como ruído, assim como regiões maiores que 40.000 pixels quadrados que representam o fundo ou o corpo inteiro. Para as regiões que passam no filtro de área, a confiança é calculada com base na intensidade média dos pixels daquela região, ajustada pela sensibilidade configurada e por uma pequena variação aleatória para simular incerteza do modelo. Apenas anomalias com confiança acima do limiar configurado são reportadas, com no máximo cinco por análise.

O quarto estágio é a análise por inteligência artificial. Quando o usuário carrega uma imagem real via upload, o sistema envia essa imagem em base64 para o Claude junto com um prompt que especifica o tipo de exame, exige resposta exclusivamente em formato JSON estruturado e instrui o modelo a ser conservador, usando o status INCONCLUSIVO quando a qualidade da imagem não permitir análise confiável. O retorno é processado com uma expressão regular para extrair apenas o objeto JSON independentemente de qualquer texto adicional que o modelo possa incluir. O laudo retornado contém o status do paciente entre SAUDAVEL, SUSPEITO e INCONCLUSIVO, o percentual de confiança do diagnóstico, a lista de achados identificados, as regiões suspeitas, uma recomendação clínica e um resumo descritivo da imagem.

---

## A3 — Teste e Validação

A validação do sistema foi construída sobre as métricas padrão de avaliação de modelos de classificação médica, com fórmulas definidas desde o início do projeto.

A Precisão é calculada como TP dividido pela soma de TP e FP, onde TP são os verdadeiros positivos, ou seja, anomalias reais detectadas corretamente, e FP são os falsos positivos, regiões saudáveis incorretamente sinalizadas. Uma Precisão baixa significa que o sistema gera muitos alarmes desnecessários, sobrecarregando profissionais com investigações de casos normais.

O Recall, também chamado de Sensibilidade, é calculado como TP dividido pela soma de TP e FN, onde FN são os falsos negativos, anomalias reais que o sistema deixou passar. O Recall é a métrica mais crítica clinicamente, porque um Recall baixo significa que doenças estão sendo ignoradas pelo sistema, o que é mais perigoso que gerar alarmes falsos.

O F1-Score é a média harmônica entre Precisão e Recall, calculado como 2 multiplicado por Precisão multiplicado por Recall, dividido pela soma de Precisão e Recall. É a métrica mais relevante para avaliar o sistema como um todo em contextos onde as classes são desbalanceadas, que é exatamente o caso médico, onde exames normais são muito mais frequentes que suspeitos.

Para calcular essas métricas de forma realista, o sistema avalia o modelo sobre um conjunto simulado de aproximadamente 200 regiões da imagem, não apenas sobre as anomalias visíveis. Os falsos positivos são calculados proporcionalmente ao tamanho desse conjunto, com uma taxa base que varia por algoritmo — a Detecção Canny tem taxa maior por naturalmente encontrar mais bordas espúrias, enquanto a CNN tem taxa menor por ser mais seletiva. A sensibilidade configurada pelo usuário também influencia essa taxa, simulando o comportamento de um modelo ajustado para diferentes pontos de operação na curva ROC.

Durante o desenvolvimento, três problemas de validação foram identificados e corrigidos. O sistema inicialmente classificava todos os exames como suspeitos porque o status era derivado da presença de anomalias no conjunto de demonstração, independentemente do limiar. Depois da primeira correção, o sistema passou a classificar tudo como normal porque o limiar padrão de 0.80 era alto demais para as confianças geradas. E as métricas mostravam 100% em todos os casos porque a divisão por zero em situações sem detecção usava 1.0 como fallback em vez de 0.0. Cada um desses problemas foi corrigido e documentado, gerando um sistema progressivamente mais calibrado.

---

## A4 — Protótipo Interativo

O protótipo foi desenvolvido como uma aplicação web completa com quatro seções funcionais acessíveis pelo menu de navegação superior.

A tela de Análise é o núcleo do sistema. O usuário pode carregar uma imagem real via upload ou arrastar o arquivo, ou selecionar uma das quatro imagens de demonstração geradas sinteticamente. Após selecionar o tipo de exame, o algoritmo e ajustar os três parâmetros de sensibilidade, limiar de confiança e intensidade de filtro, o botão de análise inicia o pipeline completo. Durante o processamento, uma barra de progresso exibe as cinco etapas em tempo real com animação de scanner sobre a imagem. Ao concluir, as métricas de Precisão, Recall e F1-Score são exibidas com barras animadas, a matriz de confusão é preenchida com os valores reais calculados, as anomalias detectadas aparecem listadas com seus percentuais de confiança e bounding boxes coloridos são desenhados sobre a imagem nas regiões suspeitas. Para imagens reais, o painel de Laudo por IA exibe o diagnóstico gerado pelo Claude com status, confiança e recomendação clínica.

O Histórico registra automaticamente cada análise realizada durante a sessão, com busca em tempo real por tipo de exame ou status, filtros combinados e contador de totais. Cada registro mostra o tipo de exame, algoritmo utilizado, precisão, recall, limiar usado e quantidade de achados. Clicar em qualquer registro abre um modal com todos os detalhes incluindo o laudo da IA quando disponível. O histórico pode ser exportado para CSV e registros individuais podem ser removidos ou todo o histórico pode ser limpo.

Os Relatórios consolidam os dados de todas as análises em painéis visuais com quatro indicadores principais de total de exames, total de suspeitos, precisão média e tempo médio de processamento. Um gráfico de barras em SVG mostra a evolução da precisão a cada análise e um gráfico de rosca exibe a distribuição por modalidade de exame. Duas tabelas complementam os gráficos com desempenho detalhado por modalidade e listagem das análises mais recentes. O relatório pode ser exportado para impressão em PDF diretamente pelo navegador.

As Configurações permitem personalizar quinze parâmetros organizados em quatro categorias. Em Modelo e IA estão o algoritmo padrão, o limiar de confiança padrão, a sensibilidade padrão e a opção de análise automática ao carregar imagem. Em Interface estão a cor das marcações de anomalia com cinco opções, a visibilidade do log do sistema, a animação de scanner, a exibição de bounding boxes e a exibição de rótulos de confiança sobre as marcações. Em Notificações estão os alertas ao detectar anomalia, a notificação de conclusão de análise e o limiar para alertas críticos. Em Privacidade estão o controle de salvamento do histórico, anonimização de metadados e conformidade com LGPD. Todas as configurações são aplicadas imediatamente ao salvar, sincronizando os controles da tela de análise com os novos valores definidos.

---

## A5 — Documentação Final

O MedVision AI demonstrou na prática que é possível construir um sistema de apoio ao diagnóstico médico funcional combinando algoritmos clássicos de visão computacional com modelos de linguagem de grande escala. O projeto evoluiu de uma simulação puramente visual para um sistema com backend persistente, análise de imagem real e laudo gerado por inteligência artificial.

As principais lições técnicas do projeto foram sobre a importância da calibração de parâmetros em sistemas de classificação médica, onde o ponto de operação do modelo define diretamente o equilíbrio entre falsos positivos e falsos negativos e essa escolha tem consequências clínicas reais. A integração entre processamento clássico de imagem e IA generativa mostrou que as duas abordagens são complementares: o OpenCV identifica regiões com características visuais alteradas enquanto o Claude interpreta o contexto clínico da imagem como um todo.

O código completo do projeto está disponível publicamente no GitHub, organizado em frontend com o arquivo HTML da interface e backend com o arquivo Python do servidor, acompanhado do arquivo de requisitos para instalação das dependências. O sistema pode ser executado localmente com Python 3.10 ou superior, ou no Google Colab seguindo as instruções do repositório.

É fundamental destacar que o MedVision AI foi desenvolvido exclusivamente para fins educacionais no contexto da disciplina de Processamento de Imagens e Sinais. Os laudos gerados pelo sistema, mesmo aqueles produzidos pelo modelo de inteligência artificial, não possuem validade clínica e não devem ser utilizados para diagnóstico médico real. Um sistema com essa finalidade exigiria validação com datasets certificados rotulados por especialistas, aprovação por órgãos regulatórios competentes como a ANVISA no Brasil e o FDA nos Estados Unidos, e testes clínicos extensivos antes de qualquer contato com pacientes reais.
