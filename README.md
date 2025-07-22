
# Controle Inteligente de Semáforos com Q-Learning 🚦

Este projeto implementa e compara dois métodos de controle de semáforos urbanos utilizando o simulador **SUMO (Simulation of Urban MObility)**:

- **Controle de Tempo Fixo (CTB)**: Semáforos seguem tempos pré-definidos, conforme normas do CTB.
- **Controle Inteligente com Q-Learning**: Um agente de aprendizado por reforço ajusta os semáforos dinamicamente, priorizando veículos de emergência (vclass `emergency` e `authority`).

O objetivo é analisar a eficiência do Q-Learning em relação ao método tradicional de tempo fixo, visando reduzir congestionamentos e melhorar o fluxo de veículos.

---

## 🚀 Funcionalidades

- Detecção de veículos prioritários, garantindo passagem imediata.
- Treinamento de agentes Q-Learning para controle semafórico dinâmico.
- Comparação de métricas entre controle fixo e Q-Learning.
- Visualização de resultados através de arquivos CSV (logs de desempenho).
- Configuração de cenários personalizados no SUMO.

---

## 📂 Estrutura do Repositório

- `tempo_fixo.py` — Controle baseado em tempos fixos.
- `treinamento_Qlearning.py` — Treinamento do agente Q-Learning.
- `simulacao_Qlearning.py` — Simulação do modelo treinado.
- `comparar_resultados.py` — Comparação de métricas entre os dois métodos.
- `teste4_sumo.sumocfg`, `teste4_sumo.net.xml`, `teste4_sumo.rou.xml` — Cenário de tráfego utilizado no SUMO.
- Arquivos `.pkl` — Tabelas Q-Learning treinadas.
- Arquivos `.csv` — Logs e resultados de simulações.

---

## 🛠 Tecnologias Utilizadas

- **Python 3**
- **SUMO (Simulation of Urban MObility)**
- **Q-Learning (Reinforcement Learning)**
- **Pandas, NumPy, Matplotlib** (para análise e visualização de dados)

---

## ⚙️ Instalação e Execução

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/controle-semaforos-ql.git
cd controle-semaforos-ql
```

### 2. Crie um ambiente virtual (opcional, mas recomendado)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute o treinamento Q-Learning
```bash
python treinamento_Qlearning.py
```

### 5. Rode a simulação com o modelo treinado
```bash
python simulacao_Qlearning.py
```

### 6. Compare os resultados
```bash
python comparar_resultados.py
```

---

## 📊 Resultados
Os resultados das simulações (tempo médio de espera, fluxo de veículos, etc.) são armazenados em arquivos CSV, como:
- `resultado_tempo_fixo.csv`
- `traffic_results_fast_reaction.csv`
- `priority_log.csv`

---
