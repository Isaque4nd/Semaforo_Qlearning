#!/usr/bin/env python3
import traci
import pandas as pd
import os

# Arquivo de configuração do SUMO que define a rede, rotas e parâmetros da simulação
SUMO_CFG_FILE = "mapa_final_sumo.sumocfg"
# IDs dos semáforos que serão controlados durante a simulação
TRAFFIC_LIGHT_IDS = ["B2", "C2", "D2"]

# Tempos definidos pelo Código de Trânsito Brasileiro (CTB) para fases dos semáforos
GREEN_DURATION = 15    # Tempo de luz verde (em segundos)
YELLOW_DURATION = 2    # Tempo de luz amarela (em segundos)
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
    # Cria o diretório para salvar os resultados, se não existir
    output_dir = "\\com_densidade\\resultados_tempo_fixo"
    os.makedirs(output_dir, exist_ok=True)

    # Inicia o SUMO com interface gráfica, usando o arquivo de configuração especificado
    # e definindo que cada passo da simulação corresponde a 1 segundo real
    traci.start(["sumo-gui", "-c", SUMO_CFG_FILE, "--step-length", "1.0"])
    print("🟢 Simulação com tempo fixo iniciada.")
    
    sim_time = 0  # Inicializa o contador do tempo de simulação
    
    # Lista para armazenar o número de carros parados ao longo do tempo
    carros_parados_por_tempo = []
    total_paradas_por_tempo = []
    tempo_espera_por_tempo = []
    velocidade_media_por_tempo = []
    densidade_por_tempo = []
    tempo_espera_emergency_por_tempo = []
    tempo_espera_authority_por_tempo = []
    # Métricas gerais para prioritários
    carros_parados_prioritarios_por_tempo = []
    total_paradas_prioritarios_por_tempo = []
    tempo_espera_prioritarios_por_tempo = []
    velocidade_media_prioritarios_por_tempo = []

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

        # Coleta dados adicionais
        vehicle_ids = traci.vehicle.getIDList()
        # Estimativa de total de paradas: número de veículos com velocidade muito baixa
        total_paradas = sum(1 for vid in vehicle_ids if traci.vehicle.getSpeed(vid) < 0.1)
        total_tempo_espera = sum(traci.vehicle.getWaitingTime(vid) for vid in vehicle_ids)
        velocidades = [traci.vehicle.getSpeed(vid) for vid in vehicle_ids if traci.vehicle.getSpeed(vid) > 0]
        velocidade_media = sum(velocidades) / len(velocidades) if velocidades else 0

        # Calcular densidade média (veículos/km/faixa)
        densidades = []
        for tl in TRAFFIC_LIGHT_IDS:
            for lane in traci.trafficlight.getControlledLanes(tl):
                num_veiculos = traci.lane.getLastStepVehicleNumber(lane)
                comprimento = traci.lane.getLength(lane)
                if comprimento > 0:
                    densidade_lane = (num_veiculos / comprimento) * 1000  # veículos/km
                    densidades.append(densidade_lane)
        densidade_media = sum(densidades) / len(densidades) if densidades else 0

        # Dados prioritários
        emergency_ids = [vid for vid in vehicle_ids if traci.vehicle.getVehicleClass(vid) == "emergency"]
        authority_ids = [vid for vid in vehicle_ids if traci.vehicle.getVehicleClass(vid) == "authority"]
        num_emergency = len(emergency_ids)
        total_espera_emergency = sum(traci.vehicle.getWaitingTime(vid) for vid in emergency_ids)
        media_espera_emergency = total_espera_emergency / num_emergency if num_emergency else 0
        num_authority = len(authority_ids)
        total_espera_authority = sum(traci.vehicle.getWaitingTime(vid) for vid in authority_ids)
        media_espera_authority = total_espera_authority / num_authority if num_authority else 0

        # Métricas gerais para prioritários
        priority_ids = emergency_ids + authority_ids
        if priority_ids:
            carros_parados_prioritarios = sum(1 for vid in priority_ids if traci.vehicle.getSpeed(vid) < 0.1)
            total_paradas_prioritarios = sum(1 for vid in priority_ids if traci.vehicle.getSpeed(vid) < 0.1)
            tempo_espera_prioritarios = sum(traci.vehicle.getWaitingTime(vid) for vid in priority_ids) / len(priority_ids)
            velocidades_prioritarios = [traci.vehicle.getSpeed(vid) for vid in priority_ids if traci.vehicle.getSpeed(vid) > 0]
            velocidade_media_prioritarios = sum(velocidades_prioritarios) / len(velocidades_prioritarios) if velocidades_prioritarios else 0
        else:
            carros_parados_prioritarios = 0
            total_paradas_prioritarios = 0
            tempo_espera_prioritarios = 0
            velocidade_media_prioritarios = 0

        total_paradas_por_tempo.append({'tempo': sim_time, 'total_paradas': total_paradas})
        tempo_espera_por_tempo.append({'tempo': sim_time, 'tempo_espera': total_tempo_espera})
        velocidade_media_por_tempo.append({'tempo': sim_time, 'velocidade_media': velocidade_media})
        densidade_por_tempo.append({'tempo': sim_time, 'densidade_media': densidade_media})
        tempo_espera_emergency_por_tempo.append({'tempo': sim_time, 'num_emergency': num_emergency, 'total_espera_emergency': total_espera_emergency, 'media_espera_emergency': media_espera_emergency})
        tempo_espera_authority_por_tempo.append({'tempo': sim_time, 'num_authority': num_authority, 'total_espera_authority': total_espera_authority, 'media_espera_authority': media_espera_authority})
        carros_parados_prioritarios_por_tempo.append({'tempo': sim_time, 'carros_parados_prioritarios': carros_parados_prioritarios})
        total_paradas_prioritarios_por_tempo.append({'tempo': sim_time, 'total_paradas_prioritarios': total_paradas_prioritarios})
        tempo_espera_prioritarios_por_tempo.append({'tempo': sim_time, 'tempo_espera_prioritarios': tempo_espera_prioritarios})
        velocidade_media_prioritarios_por_tempo.append({'tempo': sim_time, 'velocidade_media_prioritarios': velocidade_media_prioritarios})

        # Avança a simulação em 1 passo (1 segundo)
        traci.simulationStep()
        sim_time += 1  # Incrementa o tempo da simulação em segundos

    # Finaliza a simulação e fecha o traci
    traci.close()
    print("✅ Simulação finalizada (tempo fixo).")

    # Converte os dados coletados em um DataFrame do pandas para facilitar análise
    df_parados = pd.DataFrame(carros_parados_por_tempo)
    df_paradas = pd.DataFrame(total_paradas_por_tempo)
    df_espera = pd.DataFrame(tempo_espera_por_tempo)
    df_velocidade = pd.DataFrame(velocidade_media_por_tempo)
    df_densidade = pd.DataFrame(densidade_por_tempo)
    df_emergency = pd.DataFrame(tempo_espera_emergency_por_tempo)
    df_authority = pd.DataFrame(tempo_espera_authority_por_tempo)
    df_parados_prioritarios = pd.DataFrame(carros_parados_prioritarios_por_tempo)
    df_paradas_prioritarios = pd.DataFrame(total_paradas_prioritarios_por_tempo)
    df_espera_prioritarios = pd.DataFrame(tempo_espera_prioritarios_por_tempo)
    df_velocidade_prioritarios = pd.DataFrame(velocidade_media_prioritarios_por_tempo)

    # Salva os dados no diretório de saída
    df_parados.to_csv(os.path.join(output_dir, "resultado_tempo_fixo.csv"), index=False)
    df_paradas.to_csv(os.path.join(output_dir, "paradas_tempo_fixo.csv"), index=False)
    df_espera.to_csv(os.path.join(output_dir, "espera_tempo_fixo.csv"), index=False)
    df_velocidade.to_csv(os.path.join(output_dir, "velocidade_tempo_fixo.csv"), index=False)
    df_densidade.to_csv(os.path.join(output_dir, "densidade_tempo_fixo.csv"), index=False)
    df_emergency.to_csv(os.path.join(output_dir, "emergency_tempo_fixo.csv"), index=False)
    df_authority.to_csv(os.path.join(output_dir, "authority_tempo_fixo.csv"), index=False)
    df_parados_prioritarios.to_csv(os.path.join(output_dir, "carros_parados_prioritarios_tempo_fixo.csv"), index=False)
    df_paradas_prioritarios.to_csv(os.path.join(output_dir, "paradas_prioritarios_tempo_fixo.csv"), index=False)
    df_espera_prioritarios.to_csv(os.path.join(output_dir, "espera_prioritarios_tempo_fixo.csv"), index=False)
    df_velocidade_prioritarios.to_csv(os.path.join(output_dir, "velocidade_prioritarios_tempo_fixo.csv"), index=False)
    print(f"📁 Resultados salvos em '{output_dir}'")

# Executa a função principal se o arquivo for executado diretamente
if __name__ == "__main__":
    run_fixed_time_simulation()