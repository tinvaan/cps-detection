
import os


class Config:
    ATTACK_TYPES = ["NONE", "ATTACK_MAX_TEMP", "ATTACK_MAX_WEIGHT", "BUTTON_ATTACK","BIAS", "SURGE", "RANDOM"]
    ML = True
    DEBUG = True
    SAVE_PLOTS = True
    SHOW_PLOTS = False
    BIAS_SELECTION = list(range(-17,-14)) + list(range(14,17))

    # Elevator initial values
    MAX_TEMP = 100
    MAX_WEIGHT = 1200
    SIMULATION_TIME = 500
    INITIAL_CURRENT_LEVEL = 1
    RUNS = os.getenv('SIM_RUNS', 10)
