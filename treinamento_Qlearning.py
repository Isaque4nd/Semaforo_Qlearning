import traci
import pickle
import os
import random
from collections import defaultdict

# Configurações
SUMO_CFG_FILE = "mapa_final_sumo.sumocfg"
TRAFFIC_LIGHT_IDS = ["B2", "C2", "D2"]
GREEN_DURATION = 15  # Reduzido para ciclos mais rápidos
YELLOW_DURATION = 2  # Reduzido para transições rápidas

EPOCHS = 100    # episódios aumentados para convergência melhor
MAX_STEPS = 5000  # limite de passos por episódio reduzido
ALPHA = 0.05      # taxa de aprendizado
GAMMA = 0.9       # desconto
EPSILON = 0.9     # exploração inicial

SIGNALS = {
    "green_vertical": "rrrrGGGGrrrrGGGG",
    "yellow_vertical": "rrrryyyyrrrryyyy",
    "green_horizontal": "GGGGrrrrGGGGrrrr",
    "yellow_horizontal": "yyyyrrrryyyyrrrr",
}

# ---------- FUNÇÕES AUXILIARES ----------

def detect_priority_per_tl():
    data = {}
    for tl in TRAFFIC_LIGHT_IDS:
        priority_score = {"horizontal": 0, "vertical": 0}
        
        for lane in traci.trafficlight.getControlledLanes(tl):
            for vid in traci.lane.getLastStepVehicleIDs(lane):
                try:
                    cls = traci.vehicle.getVehicleClass(vid)
                    if cls == "emergency":
                        pr = 2
                    elif cls == "authority":
                        pr = 1
                    else:
                        continue
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

def get_global_priority():
    # Comunicação entre semáforos: verifica se há prioridade em qualquer semáforo
    priorities = detect_priority_per_tl()
    return any(pr > 0 for _, pr in priorities.values())


def priority_remain():
    for vid in traci.vehicle.getIDList():
        try:
            if traci.vehicle.getVehicleClass(vid) in ("emergency","authority"):
                return True
        except:
            continue
    return False

def get_state(tl):
    lanes = traci.trafficlight.getControlledLanes(tl)
    vert = sum(1 for l in lanes if any(ns in l for ns in ("N","S"))
               for v in traci.lane.getLastStepVehicleIDs(l) if traci.vehicle.getSpeed(v) < 0.1)
    horz = sum(1 for l in lanes if any(ew in l for ew in ("E","W"))
               for v in traci.lane.getLastStepVehicleIDs(l) if traci.vehicle.getSpeed(v) < 0.1)
    # Velocidade média discretizada
    speeds = [traci.vehicle.getSpeed(v) for v in traci.vehicle.getIDList() if traci.vehicle.getSpeed(v) > 0]
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    speed_discrete = min(int(avg_speed // 2), 5)  # Discretizar em intervalos de 2 m/s

    # Informações globais para comunicação
    total_parados_global = sum(
        sum(1 for l in traci.trafficlight.getControlledLanes(tl_other)
            for v in traci.lane.getLastStepVehicleIDs(l) if traci.vehicle.getSpeed(v) < 0.1)
        for tl_other in TRAFFIC_LIGHT_IDS
    )
    total_parados_global_discrete = min(total_parados_global // 10, 10)  # Discretizar

    # Prioridade global
    global_priority = int(any(
        any(traci.vehicle.getVehicleClass(v) in ("emergency", "authority")
            for l in traci.trafficlight.getControlledLanes(tl_other)
            for v in traci.lane.getLastStepVehicleIDs(l))
        for tl_other in TRAFFIC_LIGHT_IDS
    ))

    # discretiza em faixas de 5 veículos
    return (min(horz//5,5), min(vert//5,5), speed_discrete, total_parados_global_discrete, global_priority)

def apply_phase(tl, dir_next, curr_dir):
    steps = 0
    if curr_dir and curr_dir != dir_next:
        traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"yellow_{curr_dir}"])
        for _ in range(YELLOW_DURATION):
            traci.simulationStep(); steps += 1
    traci.trafficlight.setRedYellowGreenState(tl, SIGNALS[f"green_{dir_next}"])
    for _ in range(GREEN_DURATION):
        traci.simulationStep(); steps += 1
    return dir_next, steps

# ---------- TREINAMENTO ----------

def train():
    # Q-table única para todos os semáforos
    Q = defaultdict(lambda: {"horizontal":0.0, "vertical":0.0})

    sumo_bin = os.path.join(os.environ.get("SUMO_HOME",""), "bin", "sumo")
    
    rewards = []
    best_reward = float('-inf')
    patience = 0
    patience_limit = 100
    
    for ep in range(EPOCHS):
        epsilon_current = EPSILON * (1 - ep / EPOCHS)  # Decaimento de epsilon
        traci.start([sumo_bin, "-c", SUMO_CFG_FILE, "--step-length", "1.0"])
        current = {tl: None for tl in TRAFFIC_LIGHT_IDS}
        total_steps = 0
        total_reward = 0

        while traci.simulation.getMinExpectedNumber()>0 and total_steps<MAX_STEPS:
            priority = detect_priority_per_tl()

            for tl in TRAFFIC_LIGHT_IDS:
                state = get_state(tl)

                # Sempre usar epsilon-greedy, sem forçar prioridade
                if random.random()<epsilon_current:
                    action = random.choice(["horizontal","vertical"])
                else:
                    # Escolhe a ação com maior valor Q para o estado atual
                    q_values = Q.get((tl, state), {"horizontal":0.0, "vertical":0.0})
                    action = max(q_values, key=q_values.get)

                new_phase, steps = apply_phase(tl, action, current[tl])
                current[tl] = new_phase
                total_steps += steps

                                # calcula o novo estado e a recompensa
                st2 = get_state(tl)
                # Recompensa focada em fluidez global: penalizar parados globais, recompensar velocidade global, penalizar espera global
                total_parados_global = sum(
                    sum(1 for l in traci.trafficlight.getControlledLanes(tl_other)
                        for v in traci.lane.getLastStepVehicleIDs(l) if traci.vehicle.getSpeed(v) < 0.1)
                    for tl_other in TRAFFIC_LIGHT_IDS
                )
                global_wait_penalty = sum(traci.vehicle.getWaitingTime(v) for v in traci.vehicle.getIDList()) / max(1, len(traci.vehicle.getIDList()))
                global_speeds = [traci.vehicle.getSpeed(v) for v in traci.vehicle.getIDList() if traci.vehicle.getSpeed(v) > 0]
                global_avg_speed = sum(global_speeds) / len(global_speeds) if global_speeds else 0

                reward = - total_parados_global * 10  # Penalizar muito parados globais
                reward -= global_wait_penalty * 5  # Penalizar espera global
                reward += global_avg_speed * 20  # Recompensar velocidade global
                # Penalizar presença de emergência global
                if st2[4]:  # global_priority
                    reward -= 50  # Penalização alta para emergências globais
                # Penalizar espera de veículos prioritários
                priority_wait = sum(traci.vehicle.getWaitingTime(v) for v in traci.vehicle.getIDList() if traci.vehicle.getVehicleClass(v) in ("emergency", "authority"))
                reward -= priority_wait * 100  # Penalização alta para espera de prioridade
                # Penalizar veículos com espera muito longa para prevenir teleport
                long_wait_count = sum(1 for v in traci.vehicle.getIDList() if traci.vehicle.getWaitingTime(v) > 250)
                reward -= long_wait_count * 1000  # Penalização extrema para prevenir teleport

                total_reward += reward

                # Atualizar Q-table
                q_values_st = Q[(tl, state)]
                q_values_st2 = Q[(tl, st2)]
                q_values_st[action] += ALPHA * (reward + GAMMA * max(q_values_st2.values()) - q_values_st[action])

            if total_steps < MAX_STEPS:
                traci.simulationStep()
                total_steps += 1

        traci.close()
        
        rewards.append(total_reward)
        if total_reward > best_reward:
            best_reward = total_reward
            patience = 0
        else:
            patience += 1
        
        print(f"Episódio {ep+1}/{EPOCHS} — passos: {total_steps}, recompensa total: {total_reward:.2f}, melhor: {best_reward:.2f}")
        
        if patience >= patience_limit:
            print(f"Early stopping at episode {ep+1} due to no improvement in {patience_limit} episodes.")
            break

    # salva Q-table única
    with open("q_table.pkl","wb") as f:
        pickle.dump(dict(Q), f)
    print("✅ Q-table salva: q_table.pkl")

if __name__=="__main__":
    train()
