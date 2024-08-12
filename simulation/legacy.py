import datetime as dt
import os
import random
import shutil
import time
from dataclasses import dataclass, field
from time import perf_counter as timer
import itertools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Attack types and configuration
ATTACK_TYPES = ["NONE", "ATTACK_MAX_TEMP", "ATTACK_MAX_WEIGHT", "BUTTON_ATTACK", "BIAS", "SURGE", "RANDOM"]
DEBUG = True
SHOW_PLOTS = False
SAVE_PLOTS = True
BIAS_SELECTION = list(range(-17, -14)) + list(range(14, 17))

# Initial elevator values
MAX_TEMP = 100
MAX_WEIGHT = 1200
INITIAL_CURRENT_LEVEL = 1
RUNS = 10
SIMULATION_TIME = 500

# Create folders to save plots and results
def init_folders():
    if not os.path.exists("output"):
        print("Creating output folder...")
        os.makedirs("output")
        for attack in ATTACK_TYPES:
            os.makedirs(f"output/ATTACK_TYPE_{attack}")
    else:
        print("Output folder already exists. Skipping creation of output folder.")

@dataclass
class ElevatorState:
    """Class to hold the state of the elevator."""
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

def get_elevator_actuators(state):
    """Retrieve the actuator status of the elevator."""
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

def generate_noise(lower=-5, upper=0.5):
    """Generate random noise within a specified range."""
    return np.random.uniform(lower, upper)

def get_noisy_elevator_state(state):
    """Get the elevator state with added noise."""
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

def generate_plot(MAX_TEMP, MAX_WEIGHT, sensor_measurements, actuators_status, title=("NONE", False), detection_status=None):
    """Generate and save plots of the simulation results."""
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

def simulate_elevator(state: ElevatorState, cycles: int = 10, attack_type: str = "NONE", attack_start: int = 1, attack_end: int = 100):
    """Simulate the elevator operation with possible attacks."""
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

        noisy_state = get_noisy_elevator_state(state)

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
    """Update the state of the elevator based on the noisy state."""
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

def run_simulation(timer, attack_type="NONE", attack_start:int =1 , attack_end:int = 100):
    """Run the elevator simulation with possible attacks."""
    state = ElevatorState()
    return simulate_elevator(state, timer, attack_type, attack_start, attack_end)

def cusum(estimated_measurements, sensor_measurements, attacks, threshold=2, drift=0.5):
    """CUSUM algorithm for attack detection."""
    num_detected = 0
    false_alarm = 0 
    s_i = [0]
    for y_esti, y_bar in zip(estimated_measurements, sensor_measurements):
        z_k = abs(y_esti - y_bar) - drift 
        s_k = max(0, s_i[-1] + z_k)
        s_i.append(s_k)
        if s_k > threshold:
            if attacks == 1:
                num_detected += 1
            else:
                false_alarm += 1
            break
    return num_detected, false_alarm

def peak_detection(sensor_measurements, threshold=3):
    """Peak detection algorithm."""
    detected = 0
    for i in range(1, len(sensor_measurements)):
        if abs(sensor_measurements[i] - sensor_measurements[i - 1]) > threshold:
            detected += 1
            break
    return detected

def variance_analysis(sensor_measurements, threshold=5):
    """Variance analysis for anomaly detection."""
    variance = np.var(sensor_measurements)
    return 1 if variance > threshold else 0

def rule_checking(state, sensor_measurements):
    """Simple rule-based checking."""
    detected = 0
    for measurement in sensor_measurements:
        if measurement < 50 or state.MAX_WEIGHT < 600:  # Example thresholds
            print(f"Rule check triggered: measurement {measurement}, MAX_WEIGHT {state.MAX_WEIGHT}")
            detected += 1
            break
    return detected

def signal_consistency_checking(actuators_status):
    """Check for consistency in signal states."""
    detected = 0
    for status in actuators_status:
        if status['ButtonLevel1'] != status['currentLevel'] and status['ButtonLevel2'] != status['currentLevel']:
            detected += 1
            break
    return detected

def run_simulations_with_attacks(cusum_threshold=2, cusum_drift=0.5, peak_threshold=2, variance_threshold=4):
    """Run multiple simulations to evaluate the system with different attacks."""
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

    state = ElevatorState()  
    MAX_TEMP, MAX_WEIGHT, estimated_measurements, sensor_measurements, actuators_status = run_simulation(SIMULATION_TIME, attack_type, attack_start, attack_end)

    # Combine multiple detection methods
    rule_detected = rule_checking(state, sensor_measurements)
    cusum_detected, cusum_false_alarm = cusum(estimated_measurements, sensor_measurements, attacks=1, threshold=cusum_threshold, drift=cusum_drift)
    peak_detected = peak_detection(sensor_measurements, threshold=peak_threshold)
    variance_detected = variance_analysis(sensor_measurements, threshold=variance_threshold)
    signal_detected = signal_consistency_checking(actuators_status)

    detected = any([cusum_detected, peak_detected, variance_detected, rule_detected, signal_detected])

    if attack_type != "NONE":
        return detected, cusum_false_alarm
    else:
        return 0, cusum_false_alarm

def evaluate_detection_params(cusum_threshold, cusum_drift, peak_threshold, variance_threshold):
    """Evaluate the detection performance for a given set of parameters."""
    num_detected_total = 0
    false_alarm_total = 0
    attacks_generated = 0

    for i in range(RUNS):
        detected, false_alarm = run_simulations_with_attacks(
            cusum_threshold=cusum_threshold,
            cusum_drift=cusum_drift,
            peak_threshold=peak_threshold,
            variance_threshold=variance_threshold
        )

        if detected:
            num_detected_total += 1
        if false_alarm:
            false_alarm_total += 1

        attacks_generated += 1

    detection_rate = (num_detected_total / attacks_generated) * 100 if attacks_generated > 0 else 0
    false_alarm_rate = (false_alarm_total / (RUNS - attacks_generated)) * 100 if (RUNS - attacks_generated) > 0 else 0

    return detection_rate, false_alarm_rate

def grid_search_parameters():
    """Perform grid search to find the best parameters for attack detection."""
    best_detection_rate = 0
    best_false_alarm_rate = float('inf')
    best_params = None

    results = []

    # Define the range of parameters
    cusum_thresholds = [1, 2, 3, 4, 5]
    cusum_drifts = [0.2, 0.5, 0.7, 1.0]
    peak_thresholds = [1, 2, 3, 4]
    variance_thresholds = [2, 3, 4, 5]

    # Iterate over all parameter combinations
    for cusum_threshold, cusum_drift, peak_threshold, variance_threshold in itertools.product(cusum_thresholds, cusum_drifts, peak_thresholds, variance_thresholds):
        print(f"\nTesting combination: CUSUM_THRESHOLD={cusum_threshold}, CUSUM_DRIFT={cusum_drift}, PEAK_THRESHOLD={peak_threshold}, VARIANCE_THRESHOLD={variance_threshold}")
        detection_rate, false_alarm_rate = evaluate_detection_params(cusum_threshold, cusum_drift, peak_threshold, variance_threshold)

        # Record the results
        results.append({
            "CUSUM_THRESHOLD": cusum_threshold,
            "CUSUM_DRIFT": cusum_drift,
            "PEAK_THRESHOLD": peak_threshold,
            "VARIANCE_THRESHOLD": variance_threshold,
            "Detection_Rate (%)": detection_rate,
            "False_Alarm_Rate (%)": false_alarm_rate
        })

        # Find the best combination of parameters
        if detection_rate > best_detection_rate or (detection_rate == best_detection_rate and false_alarm_rate < best_false_alarm_rate):
            best_detection_rate = detection_rate
            best_false_alarm_rate = false_alarm_rate
            best_params = (cusum_threshold, cusum_drift, peak_threshold, variance_threshold)

    # Print results as a table
    df = pd.DataFrame(results)
    print("\nResults Table:")
    print(df)

    print(f"\nBest Parameters: CUSUM_THRESHOLD={best_params[0]}, CUSUM_DRIFT={best_params[1]}, PEAK_THRESHOLD={best_params[2]}, VARIANCE_THRESHOLD={best_params[3]}")
    print(f"Best Detection Rate: {best_detection_rate:.2f}%, Best False Alarm Rate: {best_false_alarm_rate:.2f}%")

    return best_params

if __name__ == "__main__":
    if os.path.exists("output"):
        shutil.rmtree("output/")
    init_folders()

    start = timer()

    best_params = grid_search_parameters()

    end = timer()
    print(f"\nTime elapsed: {end - start:.2f} seconds")
