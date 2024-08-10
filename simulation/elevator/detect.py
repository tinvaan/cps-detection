
import argparse
import itertools
import os
import pandas as pd

from time import perf_counter as timer
from tqdm import tqdm

from elevator import runtime
from elevator.runtime import Config
from elevator.simulator import Elevator


class ChangeDetector:
    def __init__(self):
        self.duration = -1          # Elapsed time
        self.writer = None          # ChangeWriter instance

    def cusum(
        self,
        standard,
        observed,
        params={'drift': 0, 'threshold': 0},
        meta={'attacks': {}, 'category': None, 'property': None}
    ):
        spikes = []
        hits, misses = 0, 0
        pos, neg = [0], [0]
        drift, threshold = params.get('drift'), params.get('threshold')

        for idx, (std, obs) in enumerate(zip(standard, observed)):
            deviation = abs(std - obs)
            pos.append(max(0, pos[-1] + deviation - drift))
            neg.append(max(0, neg[-1] - deviation - drift))

            if pos[-1] > threshold or neg[-1] > threshold:
                spikes.append(idx)
                pos[-1], neg[-1] = 0, 0

                hits += 1 if meta.get('category') != 'NONE' else 0
                misses += 1 if meta.get('category') == 'NONE' else 0

        found = {'samples': len(standard), 'category': meta.get('category'), 'change_points': spikes}
        found['attacks'] = len(meta.get('attacks', []))
        found['detected'] = min(hits, found.get('attacks'))
        found['false_alarms'] = misses if hits <= found.get('attacks') else misses + abs(hits - found.get('attacks'))
        found['detection_effectiveness'] = round((found.get('detected') /
                                                  max(1, found.get('attacks'))) * 100.0, 2)
        found['false_alarm_rate'] = round((found.get('false_alarms') /
                                           max(1, (found.get('samples') - found.get('attacks')))) * 100.0, 2)
        return found

    def run(self, sensor='temp'):
        runtime.setup()

        summary = []
        thresholds = [4, 6, 8]
        drifts = [0.3, 0.5, 0.7, 0.9]
        attacks = {rnd: [] for rnd in range(Config.SIMULATION_ROUNDS)}

        begin = timer()
        for drift, threshold in itertools.product(drifts, thresholds):
            sim = Elevator()
            for cycle in tqdm(range(Config.SIMULATION_RUNS), ascii=True, desc=f"Cusum(drift={drift}, threshold={threshold}) - "):
                category, temps, weights, readings = sim.attack()
                for state in readings:
                    if state.get('attacked', False):
                        attacks[cycle] = attacks.get(cycle) + [state.get('cycle')]

                defects = self.cusum(
                    temps if sensor == 'temp' else weights,
                    [r.get(sensor or 'temp') for r in readings],
                    {'drift': drift, 'threshold': threshold},
                    {'property': 'temp', 'category': category, 'cycle': cycle, 'attacks': attacks.get(cycle)}
                )
                defects.update({'round': cycle, 'drift': drift, 'threshold': threshold})
                summary.append(defects)

        self.duration = timer() - begin
        self.writer = ChangeWriter(summary)
        return self.writer.changes, self.duration


class ChangeWriter:
    def __init__(self, data: dict):
        self.changes = self.process(data)
        self.changes = self.changes[[
            'round',
            'category',
            'drift',
            'threshold',
            'samples',
            'attacks',
            'detected',
            'false_alarms',
            'detection_effectiveness',
            'false_alarm_rate'
        ]]

    def get(self, category, sort=None):
        if category not in Config.ATTACK_TYPES:
            return self.changes

        rows = self.changes.loc[self.changes.category == category]
        return rows if not sort else rows.sort_values(by=sort, ascending=False)

    def log(self, run, values, states, attack_type, detections):
        df = pd.DataFrame(states)
        df.update({'attack': attack_type, 'detection': detections})

        mode = "a" if run > 0 or (os.path.exists("runs/results.csv") and os.path.getsize("runs/results.csv") != 0) else "w"
        df.to_csv("runs/results.csv", mode=mode, index=False, header=not os.path.exists("runs/results.csv"))

    def process(self, summary):
        for idx, record in enumerate(summary):
            try:
                total = record.get('samples')
                attacks = record.get('attacks')
                detected = record.get('detected')
                falseDetects = record.get('false_detects')

                if attacks == 0 and detected > attacks:
                    falseDetects += abs(attacks - detected)

                if attacks > 0 and detected > attacks:
                    falseDetects += abs(attacks - detected)
                    detected = attacks

                record.update({
                    'detected': detected,
                    'false_alarms': falseDetects,
                    'detection_effectiveness': float(100) if attacks == 0 else (detected / attacks) * 100,
                    'false_alarm_rate': float(0) if (total - attacks) == 0 else (falseDetects / (total - attacks)) * 100
                })
                summary[idx] = record
            except Exception:
                pass

        return pd.DataFrame(summary)


if __name__ == "__main__":
    A = argparse.ArgumentParser()
    A.add_argument("-a", "--attack", help="target attack category")
    A.add_argument("-s", "--sensor", help="target system sensor", default='temp')
    A.add_argument("-m", "--metric", help="detection metric", default='detection_effectiveness')
    args = A.parse_args()

    defects, duration = ChangeDetector().run(args.sensor)
    print(ChangeWriter(defects).get(args.attack, args.metric))
    print(f"\nTime elapsed: {duration} seconds")
