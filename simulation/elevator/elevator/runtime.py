
import os
import shutil


def setup():
    """ Prepare the directory structure """
    if os.path.exists('runs'):
        shutil.rmtree('runs/')

    os.makedirs("runs")
    for attack in Config.ATTACK_TYPES:
        os.makedirs(f"runs/ATTACK_TYPE_{attack}")


class Config:
    ML = True
    DEBUG = True
    SAVE_PLOTS = True
    SHOW_PLOTS = False
    BIAS_SELECTION = list(range(-17,-14)) + list(range(14,17))

    # Elevator initial values
    MAX_TEMP = 100
    MAX_WEIGHT = 1200
    INITIAL_CURRENT_LEVEL = 1
    SIMULATION_RUNS = int(os.getenv('SIM_RUNS', 10))                # Number of times simulation is run
    SIMULATION_ROUNDS = int(os.getenv('SIM_ROUNDS', 500))           # Number of samples generated

    ATTACK_TYPES = [
        "NONE",
        "BIAS",
        "SURGE",
        "RANDOM",
        "BUTTON_ATTACK",
        "ATTACK_MAX_TEMP",
        "ATTACK_MAX_WEIGHT",
    ]
