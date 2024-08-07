
import os
import shutil
import pandas as pd

from time import perf_counter as timer

from elevator.runtime import Config
from elevator.simulator import Elevator


def setup():
    """ Prepare the directory structure """
    if os.path.exists('runs'):
        shutil.rmtree('runs/')

    os.makedirs("runs")
    for attack in Config.ATTACK_TYPES:
        os.makedirs(f"runs/ATTACK_TYPE_{attack}")


def run():
    setup()
    ex = Elevator()
    attacks = 0

    begin = timer()
    for run in range(Config.RUNS):
        print(f"\n******  Simulation Run #{run + 1} *****")
        sensors, actuators, attack_type, detection = ex.attack()
        df = pd.DataFrame(actuators)
        df.update({'attack': attack_type, 'detection': detection})

        mode = "a" if run > 0 or (os.path.exists("runs/results.csv") and os.path.getsize("runs/results.csv") != 0) else "w"
        df.to_csv("runs/results.csv", mode=mode, index=False, header=not os.path.exists("runs/results.csv"))

        attacks += 1 if attack_type != "NONE" else 0
    end = timer()

    print(f"\nNumber of simulations with attacks: {attacks}\nTime elapsed: {end - begin} seconds")


if __name__ == '__main__':
    run()
