
import os
import pandas as pd

from time import perf_counter as timer

from elevator import runtime
from elevator.runtime import Config
from elevator.simulator import Elevator


def run():
    runtime.setup()
    attacks, ex = 0, Elevator()

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
    return attacks, (end - begin)


if __name__ == "__main__":
    attacks, elapsed = run()
    print(f"\nNumber of simulations with attacks: {attacks}\nTime elapsed: {elapsed} seconds")
