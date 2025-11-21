# Controle Inteligente de Semáforos com Q-Learning 🚦

Este projeto implementa e compara dois métodos de controle de semáforos urbanos utilizando o simulador **SUMO (Simulation of Urban MObility)**:

- **Controle de Tempo Fixo (CTB)**: Semáforos seguem tempos pré-definidos, conforme normas do CTB.
- **Controle Inteligente com Q-Learning**: Um agente de aprendizado por reforço ajusta os semáforos dinamicamente, priorizando veículos de emergência (vclass `emergency` e `authority`).

O objetivo é analisar a eficiência do Q-Learning em relação ao método tradicional de tempo fixo, visando reduzir congestionamentos e melhorar o fluxo de veículos.

## 📋 Sumário

- [Funcionalidades](#-funcionalidades)
- [Metodologia](#-metodologia)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Métricas Avaliadas](#-métricas-avaliadas)
- [Resultados](#-resultados)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

---

## 🚀 Funcionalidades

- Detecção automática de veículos prioritários (emergência e autoridade), garantindo passagem imediata.
- Treinamento de agentes Q-Learning para controle semafórico dinâmico baseado em densidade de tráfego.
- Simulação comparativa entre controle fixo e Q-Learning.
- Geração de relatórios visuais (HTML e PDF) com gráficos comparativos.
- Logs detalhados em CSV para análise de desempenho.
- Configuração de cenários personalizados no SUMO.

---

## 🧠 Metodologia

### Controle de Tempo Fixo
- Segue ciclos pré-definidos: 15s verde, 2s amarelo, 30s vermelho.
- Não adapta ao tráfego em tempo real.

### Q-Learning
- **Estado**: Densidade de veículos nas vias horizontais e verticais de cada semáforo.
- **Ações**: Alternar para verde horizontal ou vertical.
- **Recompensa**: Penaliza tempo de espera e paradas; bonifica fluxo.
- **Parâmetros**: α=0.05 (aprendizado), γ=0.9 (desconto), ε=0.9 (exploração inicial).
- Treinamento com 100 episódios, cada um com até 5000 passos.

Veículos prioritários têm prioridade máxima, interrompendo ciclos normais.

---

## 📂 Estrutura do Repositório

```
com_densidade_final_qlearning/
├── tempo_fixo.py                    # Simulação com controle de tempo fixo
├── treinamento_Qlearning.py         # Treinamento do agente Q-Learning
├── simulacao_Qlearning.py           # Simulação com modelo Q-Learning treinado
├── comparar_resultados.py           # Comparação de métricas e geração de relatórios
├── requirements.txt                 # Dependências Python
├── README.md                        # Este arquivo
├── mapa_final_sumo.sumocfg              # Configuração principal do SUMO
├── mapa_final_sumo.net.xml              # Rede viária
├── mapa_final_sumo.rou.xml              # Rotas de veículos
├── mapa_final_sumo.netecfg              # Configuração adicional da rede
├── edgeData.xml                     # Dados de arestas (saída SUMO)
├── laneData.xml                     # Dados de faixas (saída SUMO)
├── tripinfo.xml                     # Informações de viagens (saída SUMO)
├── output.txt                       # Log de saída
├── priority_log.csv                 # Log de prioridades
├── __pycache__/                     # Cache Python
├── relatorio/                       # Relatórios gerados
│   ├── relatorio_comparativo_prioritarios.html
│   ├── relatorio_comparativo.html
│   ├── relatorio_prioritarios_qlearning.html
│   └── relatorio_prioritarios_tempo_fixo.html
├── resultados_qlearning/            # Resultados Q-Learning
│   ├── authority_qlearning.csv
│   ├── carros_parados_prioritarios_qlearning.csv
│   ├── densidade_prioritarios_qlearning.csv
│   ├── densidade_qlearning.csv
│   ├── emergency_qlearning.csv
│   ├── espera_prioritarios_qlearning.csv
│   ├── espera_qlearning.csv
│   ├── metricas_qlearning.csv
│   ├── paradas_prioritarios_qlearning.csv
│   ├── paradas_qlearning.csv
│   ├── resultado_qlearning.csv
│   ├── traffic_results_fast_reaction.csv
│   ├── velocidade_prioritarios_qlearning.csv
│   └── velocidade_qlearning.csv
└── resultados_tempo_fixo/           # Resultados Tempo Fixo
    ├── authority_tempo_fixo.csv
    ├── carros_parados_prioritarios_tempo_fixo.csv
    ├── densidade_prioritarios_tempo_fixo.csv
    ├── densidade_tempo_fixo.csv
    ├── emergency_tempo_fixo.csv
    ├── espera_prioritarios_tempo_fixo.csv
    ├── espera_tempo_fixo.csv
    ├── metricas_tempo_fixo.csv
    ├── paradas_prioritarios_tempo_fixo.csv
    ├── paradas_tempo_fixo.csv
    ├── resultado_tempo_fixo.csv
    ├── velocidade_prioritarios_tempo_fixo.csv
    └── velocidade_tempo_fixo.csv
```

---

## 📋 Pré-requisitos

- **Python 3.8+**
- **SUMO (Simulation of Urban MObility)**: Baixe e instale do [site oficial](https://www.eclipse.org/sumo/).
  - Adicione o SUMO ao PATH do sistema.
- **Git** (para clonar o repositório)

---

## ⚙️ Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/controle-semaforos-ql.git
cd controle-semaforos-ql
```

### 2. Instale o SUMO
- Baixe a versão mais recente do [SUMO](https://www.eclipse.org/sumo/download.php).
- Siga as instruções de instalação para seu sistema operacional.
- Verifique se `sumo` e `sumo-gui` estão no PATH:
  ```bash
  sumo --version
  ```

### 3. Crie um ambiente virtual (recomendado)
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac
```

### 4. Instale as dependências Python
```bash
pip install -r requirements.txt
```

---

## 🚀 Uso

### 1. Treinamento do Agente Q-Learning
Executa o treinamento e salva a tabela Q em `q_table.pkl`:
```bash
python treinamento_Qlearning.py
```

### 2. Simulação com Controle de Tempo Fixo
Executa a simulação com tempos fixos e gera logs:
```bash
python tempo_fixo.py
```

### 3. Simulação com Q-Learning
Carrega o modelo treinado e executa a simulação:
```bash
python simulacao_Qlearning.py
```

### 4. Comparação de Resultados
Gera relatórios comparativos em HTML e PDF:
```bash
python comparar_resultados.py
```

Os relatórios serão salvos na pasta `relatorio/`.

---

## 📊 Métricas Avaliadas

- **Tempo Médio de Espera**: Tempo que veículos aguardam nos semáforos.
- **Número de Paradas**: Total de paradas por veículo.
- **Velocidade Média**: Velocidade média dos veículos.
- **Densidade de Tráfego**: Número de veículos por unidade de espaço.
- **Métricas para Prioritários**: Métricas específicas para veículos de emergência e autoridade.

---

## 📈 Resultados

Os resultados mostram que o Q-Learning reduz significativamente o tempo de espera e o número de paradas em comparação ao controle fixo, especialmente em cenários de tráfego variável. Veículos prioritários têm prioridade garantida em ambos os métodos.

Exemplos de arquivos de saída:
- `resultado_tempo_fixo.csv`: Métricas gerais para tempo fixo.
- `traffic_results_fast_reaction.csv`: Resultados detalhados do Q-Learning.
- `priority_log.csv`: Logs de ativação de prioridade.

Visualize os relatórios HTML na pasta `relatorio/` para gráficos comparativos.

---

## 🛠 Tecnologias Utilizadas

- **Python 3**: Linguagem principal.
- **SUMO**: Simulador de tráfego.
- **Q-Learning**: Algoritmo de aprendizado por reforço.
- **Pandas**: Manipulação de dados.
- **NumPy**: Computações numéricas.
- **Matplotlib**: Geração de gráficos.
- **ReportLab**: Criação de PDFs.

---

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estes passos:

1. Fork o projeto.
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`).
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`).
4. Push para a branch (`git push origin feature/nova-feature`).
5. Abra um Pull Request.

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

Para dúvidas ou sugestões, abra uma issue no GitHub.