import traci
import pickle
import os
import pandas as pd

# CONFIGURAÇÕES
SUMO_CFG_FILE = "mapa_final_sumo.sumocfg"
TRAFFIC_LIGHT_IDS = ["B2", "C2", "D2"]
GREEN_DURATION = 15
YELLOW_DURATION = 2
YELLOW_DURATION = 3


SIGNALS = {
    "green_vertical": "rrrrGGGGrrrrGGGG",
    "yellow_vertical": "rrrryyyyrrrryyyy",
    "green_horizontal": "GGGGrrrrGGGGrrrr",
    "yellow_horizontal": "yyyyrrrryyyyrrrr",

}

def detect_priority_per_tl():
    data = {}
    for tl in TRAFFIC_LIGHT_IDS:
        priority_score = {"horizontal": 0, "vertical": 0}

        for lane in traci.trafficlight.getControlledLanes(tl):
            for vid in traci.lane.getLastStepVehicleIDs(lane):
                try:
                    cls = traci.vehicle.getVehicleClass(vid)
                    if cls in ("emergency", "authority"):
                        pr = 2 if cls == "emergency" else 1
                        ang = traci.vehicle.getAngle(vid)
                        dirc = "vertical" if (45 < ang < 135 or 225 < ang < 315) else "horizontal"
                        priority_score[dirc] = max(priority_score[dirc], pr)
                except traci.TraCIException:
                    continue

        if priority_score["horizontal"] > priority_score["vertical"]:
            data[tl] = ("horizontal", priority_score["horizontal"])
        elif priority_score["vertical"] > priority_score["horizontal"]:
            data[tl] = ("vertical", priority_score["vertical"])
        else:
            data[tl] = (None, 0)

    return data

def priority_remain():
    for vid in traci.vehicle.getIDList():
        try:
            if traci.vehicle.getVehicleClass(vid) in ["emergency", "authority"]:
                return True
        except traci.TraCIException:
            continue
    return False

def get_state(tl_id):
    vertical_lanes = [l for l in traci.trafficlight.getControlledLanes(tl_id) if 'N' in l or 'S' in l]
    horizontal_lanes = [l for l in traci.trafficlight.getControlledLanes(tl_id) if 'E' in l or 'W' in l]

    vertical = sum(
        1 for l in vertical_lanes for v in traci.lane.getLastStepVehicleIDs(l) if traci.vehicle.getSpeed(v) < 0.1
    )
    horizontal = sum(
        1 for l in horizontal_lanes for v in traci.lane.getLastStepVehicleIDs(l) if traci.vehicle.getSpeed(v) < 0.1
    )

    # Velocidade média discretizada
    speeds = [traci.vehicle.getSpeed(v) for v in traci.vehicle.getIDList() if traci.vehicle.getSpeed(v) > 0]
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    speed_discrete = min(int(avg_speed // 2), 5)

    # Informações globais
    total_parados_global = sum(
        sum(1 for l in traci.trafficlight.getControlledLanes(tl_other)
            for v in traci.lane.getLastStepVehicleIDs(l) if traci.vehicle.getSpeed(v) < 0.1)
        for tl_other in TRAFFIC_LIGHT_IDS
    )
    total_parados_global_discrete = min(total_parados_global // 10, 10)

    global_priority = int(any(
        any(traci.vehicle.getVehicleClass(v) in ("emergency", "authority")
            for l in traci.trafficlight.getControlledLanes(tl_other)
            for v in traci.lane.getLastStepVehicleIDs(l))
        for tl_other in TRAFFIC_LIGHT_IDS
    ))

    return (min(horizontal // 5, 5), min(vertical // 5, 5), speed_discrete, total_parados_global_discrete, global_priority)

def apply_phase(tl, dir_next, curr_dir):
    # Esta função agora apenas define as fases, não avança a simulação
    # O avanço da simulação será feito no loop principal de run_simulation
    if curr_dir and curr_dir != dir_next:
        traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"yellow_{curr_dir}"])
        # A duração do amarelo é tratada no loop principal
    traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"green_{dir_next}"])
    # A duração do verde é tratada no loop principal
    return dir_next

def run_simulation(max_steps=5000):
    print("Iniciando simulação com controle Q-learning por semáforo.")

    # Cria o diretório para salvar os resultados, se não existir
    output_dir = "\\com_densidade\\resultados_qlearning"
    os.makedirs(output_dir, exist_ok=True)

    q_table = {}
    try:
        with open("q_table.pkl", "rb") as f:
            q_table = pickle.load(f)
        print("✅ Q-table carregada")
    except FileNotFoundError:
        print("⚠️ Q-table não encontrada. Usando estratégia padrão.")
        q_table = {}

    sumo_gui_binary = os.path.join(os.environ.get("SUMO_HOME", ""), "bin", "sumo-gui") if "SUMO_HOME" in os.environ else "sumo-gui"
    traci.start([sumo_gui_binary, "-c", SUMO_CFG_FILE, "--step-length", "1.0"])

    current_phase = {tl: "vertical" for tl in TRAFFIC_LIGHT_IDS}
    total_sim_steps = 0

    # Contadores para tempo vermelho por direção
    red_time = {tl: {"horizontal": 0, "vertical": 0} for tl in TRAFFIC_LIGHT_IDS}

    # Listas para coletar dados
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

    # Coleta dados iniciais no tempo 0
    vehicle_ids = traci.vehicle.getIDList()
    total_parados = sum(
        traci.lane.getLastStepHaltingNumber(lane)
        for tl in TRAFFIC_LIGHT_IDS
        for lane in traci.trafficlight.getControlledLanes(tl)
    )
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

    carros_parados_por_tempo.append({'tempo': 0, 'carros_parados': total_parados})
    total_paradas_por_tempo.append({'tempo': 0, 'total_paradas': total_paradas})
    tempo_espera_por_tempo.append({'tempo': 0, 'tempo_espera': total_tempo_espera})
    velocidade_media_por_tempo.append({'tempo': 0, 'velocidade_media': velocidade_media})
    densidade_por_tempo.append({'tempo': 0, 'densidade_media': densidade_media})
    tempo_espera_emergency_por_tempo.append({'tempo': 0, 'num_emergency': num_emergency, 'total_espera_emergency': total_espera_emergency, 'media_espera_emergency': media_espera_emergency})
    tempo_espera_authority_por_tempo.append({'tempo': 0, 'num_authority': num_authority, 'total_espera_authority': total_espera_authority, 'media_espera_authority': media_espera_authority})
    carros_parados_prioritarios_por_tempo.append({'tempo': 0, 'carros_parados_prioritarios': carros_parados_prioritarios})
    total_paradas_prioritarios_por_tempo.append({'tempo': 0, 'total_paradas_prioritarios': total_paradas_prioritarios})
    tempo_espera_prioritarios_por_tempo.append({'tempo': 0, 'tempo_espera_prioritarios': tempo_espera_prioritarios})
    velocidade_media_prioritarios_por_tempo.append({'tempo': 0, 'velocidade_media_prioritarios': velocidade_media_prioritarios})

    while traci.simulation.getMinExpectedNumber() > 0 and total_sim_steps < max_steps:
        # Aplica fases para todos os semáforos com base na Q-table
        for tl in TRAFFIC_LIGHT_IDS:
            state = get_state(tl)
            q_values = q_table.get((tl, state), {"horizontal": 0, "vertical": 0})
            next_dir = max(q_values, key=q_values.get)

            if current_phase[tl] != next_dir:
                # Aplica a fase YELLOW
                traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"yellow_{current_phase[tl]}"])
                for _ in range(YELLOW_DURATION):
                    traci.simulationStep()
                    total_sim_steps += 1
                    # Atualizar tempo vermelho
                    for dir in ["horizontal", "vertical"]:
                        if dir != current_phase[tl]:
                            red_time[tl][dir] += 1

            current_phase[tl] = next_dir
            # Aplica a fase GREEN
            traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"green_{next_dir}"])

            # Resetar tempo vermelho para a direção verde
            red_time[tl][next_dir] = 0

        # Avança a simulação para a duração do verde
        for _ in range(GREEN_DURATION):
            traci.simulationStep()
            total_sim_steps += 1
            # Atualizar tempo vermelho para direções não verdes
            for tl in TRAFFIC_LIGHT_IDS:
                for dir in ["horizontal", "vertical"]:
                    if dir != current_phase[tl]:
                        red_time[tl][dir] += 1

        # Coleta dados após cada ciclo
        vehicle_ids = traci.vehicle.getIDList()
        total_parados = sum(
            traci.lane.getLastStepHaltingNumber(lane)
            for tl in TRAFFIC_LIGHT_IDS
            for lane in traci.trafficlight.getControlledLanes(tl)
        )
        total_paradas = sum(1 for vid in vehicle_ids if traci.vehicle.getSpeed(vid) < 0.1)  # Estimativa
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

        carros_parados_por_tempo.append({'tempo': total_sim_steps, 'carros_parados': total_parados})
        total_paradas_por_tempo.append({'tempo': total_sim_steps, 'total_paradas': total_paradas})
        tempo_espera_por_tempo.append({'tempo': total_sim_steps, 'tempo_espera': total_tempo_espera})
        velocidade_media_por_tempo.append({'tempo': total_sim_steps, 'velocidade_media': velocidade_media})
        densidade_por_tempo.append({'tempo': total_sim_steps, 'densidade_media': densidade_media})
        tempo_espera_emergency_por_tempo.append({'tempo': total_sim_steps, 'num_emergency': num_emergency, 'total_espera_emergency': total_espera_emergency, 'media_espera_emergency': media_espera_emergency})
        tempo_espera_authority_por_tempo.append({'tempo': total_sim_steps, 'num_authority': num_authority, 'total_espera_authority': total_espera_authority, 'media_espera_authority': media_espera_authority})

        # Métricas gerais para prioritários
        prioritarios_ids = emergency_ids + authority_ids
        if prioritarios_ids:
            carros_parados_prioritarios = sum(1 for vid in prioritarios_ids if traci.vehicle.getSpeed(vid) < 0.1)
            total_paradas_prioritarios = sum(1 for vid in prioritarios_ids if traci.vehicle.getSpeed(vid) < 0.1)
            tempo_espera_prioritarios = sum(traci.vehicle.getWaitingTime(vid) for vid in prioritarios_ids) / len(prioritarios_ids)
            velocidades_prioritarios = [traci.vehicle.getSpeed(vid) for vid in prioritarios_ids if traci.vehicle.getSpeed(vid) > 0]
            velocidade_media_prioritarios = sum(velocidades_prioritarios) / len(velocidades_prioritarios) if velocidades_prioritarios else 0
        else:
            carros_parados_prioritarios = 0
            total_paradas_prioritarios = 0
            tempo_espera_prioritarios = 0
            velocidade_media_prioritarios = 0

        carros_parados_prioritarios_por_tempo.append({'tempo': total_sim_steps, 'carros_parados_prioritarios': carros_parados_prioritarios})
        total_paradas_prioritarios_por_tempo.append({'tempo': total_sim_steps, 'total_paradas_prioritarios': total_paradas_prioritarios})
        tempo_espera_prioritarios_por_tempo.append({'tempo': total_sim_steps, 'tempo_espera_prioritarios': tempo_espera_prioritarios})
        velocidade_media_prioritarios_por_tempo.append({'tempo': total_sim_steps, 'velocidade_media_prioritarios': velocidade_media_prioritarios})

    traci.close()
    print(f"✅ Simulação finalizada com {total_sim_steps} passos.")

    # Salva os dados
    df_parados = pd.DataFrame(carros_parados_por_tempo)
    df_paradas = pd.DataFrame(total_paradas_por_tempo)
    df_espera = pd.DataFrame(tempo_espera_por_tempo)
    df_velocidade = pd.DataFrame(velocidade_media_por_tempo)
    df_emergency = pd.DataFrame(tempo_espera_emergency_por_tempo)
    df_authority = pd.DataFrame(tempo_espera_authority_por_tempo)
    df_parados_prioritarios = pd.DataFrame(carros_parados_prioritarios_por_tempo)
    df_paradas_prioritarios = pd.DataFrame(total_paradas_prioritarios_por_tempo)
    df_espera_prioritarios = pd.DataFrame(tempo_espera_prioritarios_por_tempo)
    df_velocidade_prioritarios = pd.DataFrame(velocidade_media_prioritarios_por_tempo)
    df_densidade = pd.DataFrame(densidade_por_tempo)
    
    df_parados.to_csv(os.path.join(output_dir, "resultado_qlearning.csv"), index=False)
    df_paradas.to_csv(os.path.join(output_dir, "paradas_qlearning.csv"), index=False)
    df_espera.to_csv(os.path.join(output_dir, "espera_qlearning.csv"), index=False)
    df_velocidade.to_csv(os.path.join(output_dir, "velocidade_qlearning.csv"), index=False)
    df_densidade.to_csv(os.path.join(output_dir, "densidade_qlearning.csv"), index=False)
    df_emergency.to_csv(os.path.join(output_dir, "emergency_qlearning.csv"), index=False)
    df_authority.to_csv(os.path.join(output_dir, "authority_qlearning.csv"), index=False)
    df_parados_prioritarios.to_csv(os.path.join(output_dir, "carros_parados_prioritarios_qlearning.csv"), index=False)
    df_paradas_prioritarios.to_csv(os.path.join(output_dir, "paradas_prioritarios_qlearning.csv"), index=False)
    df_espera_prioritarios.to_csv(os.path.join(output_dir, "espera_prioritarios_qlearning.csv"), index=False)
    df_velocidade_prioritarios.to_csv(os.path.join(output_dir, "velocidade_prioritarios_qlearning.csv"), index=False)
    print(f"📁 Resultados salvos em '{output_dir}'.")

if __name__ == "__main__":
    run_simulation()