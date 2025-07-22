import traci
import pickle
import os
import random
from collections import defaultdict

# Configurações
SUMO_CFG_FILE = "teste4_sumo.sumocfg"
TRAFFIC_LIGHT_IDS = ["B2", "C2", "D2"]
GREEN_DURATION = 30
YELLOW_DURATION = 3
RED_DURATION = 3

EPOCHS = 100     # número de episódios de treinamento
MAX_STEPS = 10000
ALPHA = 0.1      # taxa de aprendizado
GAMMA = 0.9      # fator de desconto
EPSILON = 0.1    # taxa de exploração

SIGNALS = {
    "green_vertical": "rrrrGGGGrrrrGGGG",
    "yellow_vertical": "rrrryyyyrrrryyyy",
    "green_horizontal": "GGGGrrrrGGGGrrrr",
    "yellow_horizontal": "yyyyrrrryyyyrrrr",
    "all_red": "rrrrrrrrrrrrrrrr"
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
                    if cls in ("emergency", "authority"):
                        pr = 2 if cls == "emergency" else 1
                        ang = traci.vehicle.getAngle(vid)
                        dirc = "vertical" if (45 < ang < 135 or 225 < ang < 315) else "horizontal"
                        # Mantém o maior valor de prioridade por direção
                        priority_score[dirc] = max(priority_score[dirc], pr)
                except traci.TraCIException:
                    continue
        
        # Decide a direção com maior prioridade
        if priority_score["horizontal"] > priority_score["vertical"]:
            data[tl] = (None, "horizontal", priority_score["horizontal"])
        elif priority_score["vertical"] > priority_score["horizontal"]:
            data[tl] = (None, "vertical", priority_score["vertical"])
        else:
            data[tl] = (None, None, 0)  # nenhum veículo prioritário

    return data


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
    # discretiza em faixas de 5 veículos
    return (min(horz//5,5), min(vert//5,5))

def apply_phase(tl, dir_next, curr_dir):
    steps = 0
    traci.trafficlight.setRedYellowGreenState(tl, SIGNALS["all_red"])
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
    # Q-tables independentes
    Q = {tl: defaultdict(lambda: {"horizontal":0.0, "vertical":0.0}) for tl in TRAFFIC_LIGHT_IDS}

    sumo_bin = os.path.join(os.environ.get("SUMO_HOME",""), "bin", "sumo")
    for ep in range(EPOCHS):
        traci.start([sumo_bin, "-c", SUMO_CFG_FILE, "--step-length", "1.0"])
        current = {tl: None for tl in TRAFFIC_LIGHT_IDS}
        total_steps = 0

        while traci.simulation.getMinExpectedNumber()>0 and total_steps<MAX_STEPS:
            priority = detect_priority_per_tl()

            for tl in TRAFFIC_LIGHT_IDS:
                vid, pdir, pr = priority[tl]
                state = get_state(tl)

                if pr>0:
                    action = pdir
                else:
                    if random.random()<EPSILON:
                        action = random.choice(["horizontal","vertical"])
                    else:
                        # Escolhe a ação com maior valor Q para o estado atual
                        action = max(Q[tl][state], key=Q[tl][state].get)

                new_phase, steps = apply_phase(tl, action, current[tl])
                current[tl] = new_phase
                total_steps += steps

                # calcula o novo estado e a recompensa
                st2 = get_state(tl)
                reward = - (st2[0] + st2[1])  # penaliza veículos parados

                # Atualiza Q-valor usando o valor máximo da próxima ação
                old = Q[tl][state][action]
                nxt_max = max(Q[tl][st2].values())  # <- correção aqui
                Q[tl][state][action] = old + ALPHA * (reward + GAMMA * nxt_max - old)

            if total_steps < MAX_STEPS:
                traci.simulationStep()
                total_steps += 1

        traci.close()
        print(f"Episódio {ep+1}/{EPOCHS} — passos: {total_steps}")

    # salva Q-tables individuais
    for tl in TRAFFIC_LIGHT_IDS:
        with open(f"q_table_{tl}.pkl","wb") as f:
            pickle.dump(dict(Q[tl]), f)
        print(f"✅ Q-table salva: q_table_{tl}.pkl")

if __name__=="__main__":
    train()
