#!/usr/bin/env python3
import traci
import pandas as pd

# Arquivo de configuração do SUMO que define a rede, rotas e parâmetros da simulação
SUMO_CFG_FILE = "teste4_sumo.sumocfg"
# IDs dos semáforos que serão controlados durante a simulação
TRAFFIC_LIGHT_IDS = ["B2", "C2", "D2"]

# Tempos definidos pelo Código de Trânsito Brasileiro (CTB) para fases dos semáforos
GREEN_DURATION = 30    # Tempo de luz verde (em segundos)
YELLOW_DURATION = 3    # Tempo de luz amarela (em segundos)
RED_DURATION = 30      # Tempo de luz vermelha (não usado diretamente, mas parte do ciclo)
# Tempo total de um ciclo completo (verde + amarelo + vermelho)
CYCLE = GREEN_DURATION + YELLOW_DURATION + RED_DURATION

# Representação dos sinais dos semáforos em formato string,
# onde cada caractere corresponde a uma faixa controlada:
# 'r' = vermelho, 'G' = verde, 'y' = amarelo
SIGNALS = {
    "green_vertical": "rrrrGGGGrrrrGGGG",     # Verde para vias verticais, vermelho para horizontais
    "yellow_vertical": "rrrryyyyrrrryyyy",    # Amarelo para vias verticais
    "green_horizontal": "GGGGrrrrGGGGrrrr",   # Verde para vias horizontais, vermelho para verticais
    "yellow_horizontal": "yyyyrrrryyyyrrrr",  # Amarelo para vias horizontais
}

def run_fixed_time_simulation():
    # Inicia o SUMO com interface gráfica, usando o arquivo de configuração especificado
    # e definindo que cada passo da simulação corresponde a 1 segundo real
    traci.start(["sumo-gui", "-c", SUMO_CFG_FILE, "--step-length", "1.0"])
    print("🟢 Simulação com tempo fixo iniciada.")
    
    sim_time = 0  # Inicializa o contador do tempo de simulação
    
    # Lista para armazenar o número de carros parados ao longo do tempo
    carros_parados_por_tempo = []

    # Enquanto houver veículos previstos para estar na rede (simulação ativa)
    while traci.simulation.getMinExpectedNumber() > 0:
        # Calcula o tempo atual dentro do ciclo dos semáforos (0 até CYCLE-1)
        phase_time = sim_time % CYCLE

        # Para cada semáforo na lista, define o estado da luz baseado no tempo do ciclo
        for tl_id in TRAFFIC_LIGHT_IDS:
            if phase_time < GREEN_DURATION:
                # Fase verde para a direção vertical
                traci.trafficlight.setRedYellowGreenState(tl_id, SIGNALS["green_vertical"])
            elif phase_time < GREEN_DURATION + YELLOW_DURATION:
                # Fase amarela para a direção vertical
                traci.trafficlight.setRedYellowGreenState(tl_id, SIGNALS["yellow_vertical"])
            elif phase_time < GREEN_DURATION + YELLOW_DURATION + GREEN_DURATION:
                # Fase verde para a direção horizontal
                traci.trafficlight.setRedYellowGreenState(tl_id, SIGNALS["green_horizontal"])
            else:
                # Fase amarela para a direção horizontal
                traci.trafficlight.setRedYellowGreenState(tl_id, SIGNALS["yellow_horizontal"])

        # Conta o total de veículos parados em todas as faixas controladas pelos semáforos
        total_parados = sum(
            traci.lane.getLastStepHaltingNumber(lane)  # Quantidade de veículos parados na faixa
            for tl in TRAFFIC_LIGHT_IDS                 # Para cada semáforo
            for lane in traci.trafficlight.getControlledLanes(tl)  # Para cada faixa controlada pelo semáforo
        )
        # Registra o tempo atual da simulação e a quantidade de carros parados naquele instante
        carros_parados_por_tempo.append({'tempo': sim_time, 'carros_parados': total_parados})

        # Avança a simulação em 1 passo (1 segundo)
        traci.simulationStep()
        sim_time += 1  # Incrementa o tempo da simulação em segundos

    # Finaliza a simulação e fecha o traci
    traci.close()
    print("✅ Simulação finalizada (tempo fixo).")

    # Converte os dados coletados em um DataFrame do pandas para facilitar análise
    df_parados = pd.DataFrame(carros_parados_por_tempo)
    # Salva os dados em um arquivo CSV para análise futura
    df_parados.to_csv("resultado_tempo_fixo.csv", index=False)
    print("📁 Resultados salvos em 'resultado_tempo_fixo.csv'")

# Executa a função principal se o arquivo for executado diretamente
if __name__ == "__main__":
    run_fixed_time_simulation()
