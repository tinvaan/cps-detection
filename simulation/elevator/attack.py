
import os
import shutil
import pandas as pd

from time import perf_counter as timer

from .runtime import Config
from .simulator import Elevator


# Create folders to save plots and results
def init_folders():
    if os.path.exists("runs"):
        shutil.rmtree("runs/")

    if not os.path.exists("runs"):
        print("Creating runtime folder...")
        os.makedirs("runs")
        for attack in Config.ATTACK_TYPES:
            os.makedirs(f"runs/ATTACK_TYPE_{attack}")
    else:
        print("Runs folder already exists.")

# Main program
if __name__ == "__main__":
    init_folders()

    ex = Elevator()
    attacked = 0

    begin = timer()
    for i in range(Config.RUNS):
        print(f"\n******  Simulation Run #{i + 1} *****")
        sensor_measurements, actuators_status, attack_type, detection_status = ex.attack()
        df = pd.DataFrame(actuators_status)
        df["attack"] = attack_type
        df["detection"] = detection_status

        mode = "a" if i > 0 or (os.path.exists("runs/results.csv") and os.path.getsize("runs/results.csv") != 0) else "w"
        df.to_csv("runs/results.csv", mode=mode, index=False, header=not os.path.exists("runs/results.csv"))

        if attack_type != "NONE":
            attacked += 1
    end = timer()

    print(f"\nNumber of simulations with attacks: {attacked}\nTime elapsed: {end - begin} seconds")
