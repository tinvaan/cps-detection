import datetime as dt
import os
import random
import shutil
import time
from dataclasses import dataclass, field
from time import perf_counter as timer

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# MODES
ATTACK_TYPES = ["NONE", "ATTACK_MAX_TEMP", "ATTACK_MAX_WEIGHT", "BUTTON_ATTACK","BIAS", "SURGE", "RANDOM"]
DEBUG = True
SHOW_PLOTS = False
SAVE_PLOTS = True
ML = True
BIAS_SELECTION = list(range(-17,-14)) + list(range(14,17))

# Elevator initial values
MAX_TEMP = 100
MAX_WEIGHT = 1200
INITIAL_CURRENT_LEVEL = 1
RUNS = 10
SIMULATION_TIME = 500

# Create folders to save plots and results 创造文件夹来存放结果
def init_folders():
    if not os.path.exists("output"):
        print("Creating output folder...")
        os.makedirs("output")
        for attack in ATTACK_TYPES:
            os.makedirs(f"output/ATTACK_TYPE_{attack}")
    else:
        print("Output folder already exists. Skipping creation of output folder.")

@dataclass
# Instantiate some elevator data
class ElevatorState:
    ThresTemp: int = field(default_factory=lambda: random.randint(30, 99))
    ButtonLevel1: int = 0
    ButtonLevel2: int = 0
    currentLevel: int = INITIAL_CURRENT_LEVEL
    moving: int = 0
    doorOpen: int = 0
    doorOpening: int = 0
    doorClosing: int = 0
    fireAlarm: int = 0
    weight: int = field(default_factory=lambda: random.randint(0, 1500))
    movingToLevel1: int = 0
    movingToLevel2: int = 0
    MAX_WEIGHT: int = 1200
    MAX_TEMP: int = 100

# Get the elevator status
def get_elevator_actuators(state):
    return {
        "moving": state.moving,
        "doorOpening": state.doorOpening,
        "movingToLevel2": state.movingToLevel2,
        "doorClosing": state.doorClosing,
        "movingToLevel1": state.movingToLevel1,
        "currentLevel1": state.currentLevel == 1,
        "doorOpen": state.doorOpen,
        "fireAlarm": state.fireAlarm,
    }

# Generate noise normal deviation value
def generate_noise(lower=-5, upper=0.5):
    return np.random.uniform(lower, upper)

# Get the elevator status under noise
def get_noisy_elevator_state(state):
    noise = {key: generate_noise() for key in ["ThresTemp", "moving", "movingToLevel1", "movingToLevel2", "doorOpen", "weight"]}
    fire_alarm = state.ThresTemp + noise["ThresTemp"] > state.MAX_TEMP
    overweight_alarm = state.weight + noise["weight"] > state.MAX_WEIGHT
    return {
        "fire_alarm": fire_alarm,
        "overweight_alarm": overweight_alarm,
        "ThresTemp": state.ThresTemp + noise["ThresTemp"],
        "moving": int(state.moving + noise["moving"] > 0.5) if not (fire_alarm or overweight_alarm) else 0,
        "movingToLevel1": int(state.movingToLevel1 + noise["movingToLevel1"] > 0.5),
        "movingToLevel2": int(state.movingToLevel2 + noise["movingToLevel2"] > 0.5),
        "doorOpen": int(state.doorOpen + noise["doorOpen"] > 0.5),
        "weight": state.weight + noise["weight"],
    }

# Generate pictures
def generate_plot(MAX_TEMP, MAX_WEIGHT, sensor_measurements, actuators_status, title=("NONE", False), detection_status=None):
    if SHOW_PLOTS or SAVE_PLOTS:
        fig, axs = plt.subplots(2, figsize=(12, 12))
        axs[0].set_title(f"Raw sensor measurements (Attack type: {title[0]})")

        if title[0] == "ATTACK_MAX_TEMP":
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="MAX_TEMP")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="Temp")
        elif title[0] == "ATTACK_MAX_WEIGHT":
            weights = [status['weight'] for status in actuators_status]
            max_weights = [status['MAX_WEIGHT'] for status in actuators_status]
            axs[0].plot(MAX_WEIGHT, linestyle="-", linewidth=5, label="MAX_WEIGHT")
            axs[0].plot(weights, linestyle="-", linewidth=0.8, label="Weight")
        elif title[0] == "BUTTON_ATTACK":
            button_level1 = [status['ButtonLevel1'] for status in actuators_status]
            button_level2 = [status['ButtonLevel2'] for status in actuators_status]
            current_level1 = [1 if status['currentLevel'] == 1 else 0 for status in actuators_status]
            axs[0].plot(current_level1, linestyle="-", linewidth=1, label="CurrentLevel1")
            axs[0].plot(button_level1, linestyle="-", linewidth=0.8, label="ButtonLevel1")
            axs[0].plot(button_level2, linestyle="-", linewidth=0.8, label="ButtonLevel2")
        elif title[0]=="BIAS":
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="thresholds")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="actual")
        elif title[0]=="SURGE":
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="thresholds")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="actual")
        elif title[0]=="RANDOM":
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="thresholds")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="actual")
        else:
            axs[0].plot(MAX_TEMP, linestyle="-", linewidth=5, label="thresholds")
            axs[0].plot(sensor_measurements, linestyle="-", linewidth=0.8, label="actual")

        if detection_status:
            attack_indices = [i for i, status in enumerate(detection_status) if status == "attack"]
            axs[0].scatter(attack_indices, [sensor_measurements[i] for i in attack_indices], color='red', label='Attack detected', zorder=5)

        axs[0].legend()

        fire_alarm_status = [status["fire_alarm"] for status in actuators_status]
        moving_status = [status["moving"] for status in actuators_status]
        overweight_alarm = [status["overweight_alarm"] for status in actuators_status]
        axs[1].plot(fire_alarm_status, linestyle="-", linewidth=5, label="fire_alarm")
        axs[1].plot(overweight_alarm, linestyle="-", linewidth=5, label="overweight_alarm")
        axs[1].plot(moving_status, linestyle="-", linewidth=0.8, label="moving")
        axs[1].set_title("Fire Alarm, Overweight Alarm, and Moving Status")
        axs[1].legend()

        plt.tight_layout()
        if SHOW_PLOTS:
            plt.show(block=False)
        if SAVE_PLOTS:
            filepath = f"output/ATTACK_TYPE_{title[0]}"
            num = len([f for f in os.listdir(filepath) if os.path.isfile(os.path.join(filepath, f))]) + 1
            fig.savefig(f"{filepath}/{num}.png")
            plt.close()

# Simulation
def simulate_elevator(state: ElevatorState, cycles: int = 10, attack_type: str = "NONE", attack_start: int = 1, attack_end: int = 100):
    MAX_TEMP, MAX_WEIGHT, sensor_measurements, estimated_measurements, actuators_status = [], [], [], [], []
    BIAS_VALUE:int = 30
    BIAS_VALUE:int == random.choice(BIAS_SELECTION)

    for i in range(cycles):
        if not state.moving and random.randint(1, 10) == 1:
            if random.randint(1, 2) == 1:
                state.ButtonLevel1 = 1
            else:
                state.ButtonLevel2 = 1

        if attack_type == "ATTACK_MAX_TEMP":
            state.MAX_TEMP = 20
        elif attack_type == "ATTACK_MAX_WEIGHT":
            state.MAX_WEIGHT = 10
        elif attack_type == "BUTTON_ATTACK":
            if state.ButtonLevel1:
                if state.currentLevel == 1:
                    state.movingToLevel2 = 1
                    state.moving = 1
                else:
                    state.movingToLevel1 = 0
                    state.moving = 0
            elif state.ButtonLevel2:
                if state.currentLevel == 2:
                    state.movingToLevel1 = 1
                    state.moving = 1
                else:
                    state.movingToLevel2 = 0
                    state.moving = 0

        noisy_state = get_noisy_elevator_state(state)
        # Consider doing it here
        if attack_type == "BIAS" and attack_start <= i < attack_end:
            noisy_state["ThresTemp"] = noisy_state["ThresTemp"] + BIAS_VALUE

        if attack_type == "SURGE" and attack_start <= i < attack_end:
            noisy_state["ThresTemp"] = 120

        if attack_type == "RANDOM" and attack_start <= i < attack_end:
            BIAS_VALUE:int == random.randint(-30,30)
            noisy_state["ThresTemp"] = noisy_state["ThresTemp"] + BIAS_VALUE

        estimated_measurements.append(state.ThresTemp)
        sensor_measurements.append(noisy_state["ThresTemp"])
        actuators_status.append({
            "fire_alarm": noisy_state["fire_alarm"],
            "overweight_alarm": noisy_state["overweight_alarm"],
            "moving": noisy_state["moving"],
            "doorOpen": state.doorOpen,
            "movingToLevel1": noisy_state["movingToLevel1"],
            "movingToLevel2": noisy_state["movingToLevel2"],
            "temp": noisy_state["ThresTemp"],
            "MAX_TEMP": state.MAX_TEMP,
            "weight": noisy_state["weight"],
            "MAX_WEIGHT": state.MAX_WEIGHT,
            "currentLevel": state.currentLevel,
            "ButtonLevel1": state.ButtonLevel1,
            "ButtonLevel2": state.ButtonLevel2,
        })

        MAX_TEMP.append(state.MAX_TEMP)
        MAX_WEIGHT.append(state.MAX_WEIGHT)
        update_state(state, noisy_state)

    return MAX_TEMP, MAX_WEIGHT, estimated_measurements, sensor_measurements, actuators_status

def update_state(state, noisy_state):
    is_value_changed = False

    if state.weight > 0:
        state.fireAlarm = 1 if state.weight > state.MAX_WEIGHT else 0

    if state.doorOpen:
        state.doorOpening = 0
        state.doorClosing = 0

    if state.doorOpening:
        state.doorOpen = 0

    if state.doorClosing:
        state.doorOpen = 0

    if state.doorOpening and not is_value_changed:
        is_value_changed = True
        state.doorOpening = 0
        state.doorOpen = 1

    if state.doorClosing and not is_value_changed:
        is_value_changed = True
        state.doorClosing = 0
        state.doorOpen = 0
        if state.movingToLevel1 or state.movingToLevel2:
            state.moving = 1

    if state.doorClosing and state.fireAlarm:
        state.doorClosing = 0

    if not state.fireAlarm and state.doorOpen and not is_value_changed:
        if state.weight > state.MAX_WEIGHT:
            state.doorOpen = 1
        else:
            is_value_changed = True
            state.doorOpen = 0
            state.doorClosing = 1

    if state.moving and not is_value_changed:
        is_value_changed = True
        state.moving = 0
        state.doorOpening = 1
        if state.movingToLevel1:
            state.currentLevel = 1
            state.movingToLevel1 = 0
        else:
            state.currentLevel = 2
            state.movingToLevel2 = 0

    if state.moving and (state.fireAlarm or noisy_state["overweight_alarm"]):
        state.moving = 0

    if not state.moving:
        if state.fireAlarm:
            if not state.doorOpening and not state.doorOpen:
                state.doorOpening = 1
                state.doorClosing = 0
        elif not state.doorOpen and not state.doorOpening and not is_value_changed:
            is_value_changed = True
            if state.ButtonLevel2:
                if state.currentLevel != 2:
                    state.movingToLevel2 = 1
                    state.moving = 1
                else:
                    state.movingToLevel1 = 1
                    state.doorOpening = 1
            elif state.ButtonLevel1:
                if state.currentLevel != 1:
                    state.movingToLevel1 = 1
                    state.moving = 1
                else:
                    state.movingToLevel2 = 1
                    state.doorOpening = 1

    state.ButtonLevel1 = 0
    state.ButtonLevel2 = 0

# The function that actually performs the attack
def run_simulation(timer, attack_type="NONE", attack_start:int =1 , attack_end:int = 100):
    state = ElevatorState()
    return simulate_elevator(state, timer, attack_type, attack_start, attack_end)

# Determine the simulation parameters mainly to determine whether there is an intermediate function of the attack
def run_simulations_with_attacks():
    attack_type = random.choice(ATTACK_TYPES)
    attack_start = random.randint(0, 300)
    attack_duration = random.randint(1, 100)
    attack_end = attack_start + attack_duration

    if attack_type != "NONE":
        print(f"Attack type: {attack_type}")
        print(f"Attack started at t: {attack_start}")
        print(f"Attack ended at t: {attack_end}")
    else:
        print("Normal operation. No attack simulated.")

    MAX_TEMP, MAX_WEIGHT, estimated_measurements, sensor_measurements, actuators_status = run_simulation(SIMULATION_TIME, attack_type, attack_start, attack_end)

    # Ensure actuators_status is assigned before it is used
    detection_status = ["begin"] * len(actuators_status)
    for i in range(len(actuators_status)):
        if actuators_status[i]["MAX_TEMP"] != 100 or actuators_status[i]["MAX_WEIGHT"] != 1200:
            detection_status[i] = "attack"

    generate_plot(MAX_TEMP, MAX_WEIGHT, sensor_measurements, actuators_status, title=(attack_type, False), detection_status=detection_status)
    return sensor_measurements, actuators_status, attack_type, detection_status

# Main program
if __name__ == "__main__":
    if os.path.exists("output"):
        shutil.rmtree("output/")
    init_folders()

    start = timer()
    attacks_generated = 0

    for i in range(RUNS):
        print(f"\n******  Simulation Run #{i + 1} *****")
        sensor_measurements, actuators_status, attack_type, detection_status = run_simulations_with_attacks()
        df = pd.DataFrame(actuators_status)
        df["attack"] = attack_type
        df["detection"] = detection_status

        mode = "a" if i > 0 or (os.path.exists("output/results.csv") and os.path.getsize("output/results.csv") != 0) else "w"
        df.to_csv("output/results.csv", mode=mode, index=False, header=not os.path.exists("output/results.csv"))

        if attack_type != "NONE":
            attacks_generated += 1

    end = timer()
    print(f"\nNumber of simulations with attacks: {attacks_generated}\nTime elapsed: {end - start} seconds")
