
import os
import shutil


def setup(dirs=False):
    """ Prepare the directory structure """
    sims = os.path.join(os.path.dirname(__file__), "../..")
    runs = os.path.join(sims, "runs")
    if os.path.exists(runs):
        shutil.rmtree(runs)

    os.makedirs(runs)
    if dirs:
        for attack in Config.ATTACK_TYPES:
            os.makedirs(os.path.join(runs, f"ATTACK_TYPE_{attack}"))
    return runs


class Config:
    ML = True
    DEBUG = True
    SAVE_PLOTS = False
    SHOW_PLOTS = True
    BIAS_SELECTION = list(range(-17, -14)) + list(range(14, 17))

    # Elevator initial values
    MAX_TEMP = 100
    MAX_WEIGHT = 1200
    INITIAL_CURRENT_LEVEL = 1
    SIMULATION_RUNS = int(os.getenv('SIM_RUNS', 10))                # Number of times simulation is run
    SIMULATION_ROUNDS = int(os.getenv('SIM_ROUNDS', 500))           # Number of samples generated

    MAX_FALSE_ALARM_RATE = float(os.getenv('MAX_ALARM', 10))
    MIN_DETECTION_EFFECTIVENESS = float(os.getenv('MIN_DETECTION', 90))

    ATTACK_TYPES = [
        "NONE",
        "BIAS",
        "SURGE",
        "RANDOM",
        "BUTTON_ATTACK",
        "ATTACK_MAX_TEMP",
        "ATTACK_MAX_WEIGHT",
    ]
