
import argparse
import itertools
import random

from tqdm import tqdm
from time import perf_counter as timer

from elevator import runtime
from elevator.runtime import Config
from elevator.simulator import Elevator

from simulation.detect import cusum
from simulation.log import ChangeWriter


def run(sensor='temp', category=random.choice(Config.ATTACK_TYPES)):
    runtime.setup()

    summary = []
    thresholds = [4, 6, 8]
    drifts = [0.3, 0.5, 0.7, 0.9]
    attacks = {rnd: [] for rnd in range(Config.SIMULATION_ROUNDS)}

    begin = timer()
    for drift, threshold in itertools.product(drifts, thresholds):
        sim = Elevator()
        for cycle in tqdm(range(Config.SIMULATION_RUNS), ascii=True, desc=f"Cusum(drift={drift}, threshold={threshold}) - "):
            category, temps, weights, readings = sim.attack(category)
            for state in readings:
                if state.get('attacked', False):
                    attacks[cycle] = attacks.get(cycle, []) + [state.get('cycle')]

            defects = cusum(
                temps if sensor == 'temp' else weights,
                [r.get(sensor or 'temp') for r in readings],
                readings,
                params={'drift': drift, 'threshold': threshold},
                meta={'property': 'temp', 'category': category, 'cycle': cycle, 'attacks': attacks.get(cycle)}
            )
            defects.update({'round': cycle, 'drift': drift, 'threshold': threshold})
            summary.append(defects)

    duration = timer() - begin
    writer = ChangeWriter(summary)
    writer.log()
    return writer.changes, duration


if __name__ == "__main__":
    A = argparse.ArgumentParser()
    A.add_argument("-a", "--attack", help="target attack category")
    A.add_argument("-s", "--sensor", help="target system sensor", default='temp')
    args = A.parse_args()

    defects, duration = run(args.sensor, args.attack)
    defects = ChangeWriter(defects).get(args.attack)

    print(defects)
    print(f"\ntime elapsed: {duration} seconds")