import traci
import pickle
import os

# CONFIGURAÇÕES
SUMO_CFG_FILE = "teste4_sumo.sumocfg"
TRAFFIC_LIGHT_IDS = ["B2", "C2", "D2"]
GREEN_DURATION = 30
YELLOW_DURATION = 3
RED_DURATION = 3

SIGNALS = {
    "green_vertical": "rrrrGGGGrrrrGGGG",
    "yellow_vertical": "rrrryyyyrrrryyyy",
    "green_horizontal": "GGGGrrrrGGGGrrrr",
    "yellow_horizontal": "yyyyrrrryyyyrrrr",
    "all_red": "rrrrrrrrrrrrrrrr"
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

    return (min(horizontal // 5, 5), min(vertical // 5, 5))

def apply_phase(tl, dir_next, curr_dir):
    # Esta função agora apenas define as fases, não avança a simulação
    # O avanço da simulação será feito no loop principal de run_simulation
    traci.trafficlight.setRedYellowGreenState(tl, SIGNALS["all_red"])
    # A duração do vermelho é tratada no loop principal
    if curr_dir and curr_dir != dir_next:
        traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"yellow_{curr_dir}"])
        # A duração do amarelo é tratada no loop principal
    traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"green_{dir_next}"])
    # A duração do verde é tratada no loop principal
    return dir_next

def run_simulation(max_steps=10000):
    print("Iniciando simulação com controle Q-learning por semáforo.")

    q_tables = {}
    for tl in TRAFFIC_LIGHT_IDS:
        try:
            with open(f"q_table_{tl}.pkl", "rb") as f:
                q_tables[tl] = pickle.load(f)
            print(f"✅ Q-table carregada para {tl}")
        except FileNotFoundError:
            print(f"⚠️ Q-table para {tl} não encontrada. Usando estratégia padrão para este semáforo.")
            q_tables[tl] = {}

    sumo_gui_binary = os.path.join(os.environ.get("SUMO_HOME", ""), "bin", "sumo-gui") if "SUMO_HOME" in os.environ else "sumo-gui"
    traci.start([sumo_gui_binary, "-c", SUMO_CFG_FILE, "--step-length", "1.0"])

    current_phase = {tl: "vertical" for tl in TRAFFIC_LIGHT_IDS}
    total_sim_steps = 0

    while traci.simulation.getMinExpectedNumber() > 0 and total_sim_steps < max_steps:
        priorities = detect_priority_per_tl()
        has_priority = any(pr > 0 for _, pr in priorities.values())

        if has_priority:
            for tl in TRAFFIC_LIGHT_IDS:
                direction, pr = priorities[tl]
                if pr > 0:
                    print(f"🚨 Prioritário ({direction}, pr={pr}) em {tl} no passo {total_sim_steps}")
                    # Aplica a fase ALL_RED
                    traci.trafficlight.setRedYellowGreenState(tl, SIGNALS["all_red"])
                    for _ in range(RED_DURATION):
                        traci.simulationStep()
                        total_sim_steps += 1

                    if current_phase[tl] != direction:
                        # Aplica a fase YELLOW
                        traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"yellow_{current_phase[tl]}"])
                        for _ in range(YELLOW_DURATION):
                            traci.simulationStep()
                            total_sim_steps += 1
                    current_phase[tl] = direction
                    # Aplica a fase GREEN
                    traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"green_{direction}"])

            # Avança a simulação para a duração do verde
            for _ in range(GREEN_DURATION):
                traci.simulationStep()
                total_sim_steps += 1

        else:
            # Aplica fases para todos os semáforos com base na Q-table ou padrão
            for tl in TRAFFIC_LIGHT_IDS:
                state = get_state(tl)
                q_table = q_tables.get(tl, {})

                if state in q_table and q_table[state]:
                    next_dir = max(q_table[state], key=q_table[state].get)
                else:
                    next_dir = "horizontal" if current_phase[tl] == "vertical" else "vertical"

                # Aplica a fase ALL_RED
                traci.trafficlight.setRedYellowGreenState(tl, SIGNALS["all_red"])
                for _ in range(RED_DURATION):
                    traci.simulationStep()
                    total_sim_steps += 1

                if current_phase[tl] != next_dir:
                    # Aplica a fase YELLOW
                    traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"yellow_{current_phase[tl]}"])
                    for _ in range(YELLOW_DURATION):
                        traci.simulationStep()
                        total_sim_steps += 1

                current_phase[tl] = next_dir
                # Aplica a fase GREEN
                traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"green_{next_dir}"])

            # Avança a simulação para a duração do verde
            for _ in range(GREEN_DURATION):
                traci.simulationStep()
                total_sim_steps += 1

    traci.close()
    print(f"✅ Simulação finalizada com {total_sim_steps} passos.")

if __name__ == "__main__":
    run_simulation()


