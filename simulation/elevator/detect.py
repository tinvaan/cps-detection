
import argparse
import itertools
import pandas as pd
import random

from os import path
from time import perf_counter as timer
from tqdm import tqdm

from elevator import runtime
from elevator.runtime import Config
from elevator.simulator import Elevator
from elevator.utils import group


class StateInspector:
    def verify(self, state):
        try:
            assert state.get('weight') < state.get('MAX_WEIGHT'), "Weight exceeds threshold"
            assert state.get('temp') < state.get('MAX_TEMP'), "Temperature exceeds threshold"

            if bool(state.get('fire_alarm', False)):
                assert state.get('temp') > state.get('MAX_TEMP'),\
                       "Fire alarm raised when temprature is within thresholds"

            if bool(state.get('overweight_alarm', False)):
                assert state.get('weight') > state.get('MAX_WEIGHT'),\
                       "Weight alarm raised when wieght is within thresholds"
        except AssertionError as err:
            # tqdm.write(err.args[0])
            return False

        return True


class ChangeDetector:
    def __init__(self):
        self.duration = -1          # Elapsed time
        self.writer = None          # ChangeWriter instance
        self.inspector = StateInspector()

    def cusum(
        self,
        standard,
        observed,
        readings,
        verify_state=True,
        params={'drift': 0, 'threshold': 0},
        meta={'attacks': {}, 'category': None, 'property': None}
    ):
        spikes = []
        hits, misses = 0, 0
        pos, neg = [0], [0]
        drift, threshold = params.get('drift'), params.get('threshold')

        for ts, (std, obs, state) in enumerate(zip(standard, observed, readings)):
            deviation = abs(std - obs)
            pos.append(max(0, pos[-1] + deviation - drift))
            neg.append(max(0, neg[-1] - deviation - drift))

            if pos[-1] > threshold or neg[-1] > threshold:
                if verify_state and not self.inspector.verify(state):
                    spikes.append(ts)
                    pos[-1], neg[-1] = 0, 0

                    hits += 1 if bool(state.get('attacked', False)) else 0
                    misses += 1 if not bool(state.get('attacked', False)) else 0

        return self.stats({
            'category': meta.get('category'),
            'samples': len(standard),
            'attacks': len(meta.get('attacks', []) or []),
            'attack_points': meta.get('attacks', []) or [],
            'change_points': spikes,
        }, context={'hits': hits, 'misses': misses})

    def run(self, sensor='temp', category=random.choice(Config.ATTACK_TYPES)):
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

                defects = self.cusum(
                    temps if sensor == 'temp' else weights,
                    [r.get(sensor or 'temp') for r in readings],
                    readings,
                    params={'drift': drift, 'threshold': threshold},
                    meta={'property': 'temp', 'category': category, 'cycle': cycle, 'attacks': attacks.get(cycle)}
                )
                defects.update({'round': cycle, 'drift': drift, 'threshold': threshold})
                summary.append(defects)

        self.duration = timer() - begin
        self.writer = ChangeWriter(summary)
        self.writer.log()
        return self.writer.changes, self.duration

    def stats(self, findings, context):
        hits = context.get('hits')
        misses = context.get('misses')

        findings['detected'] = min(hits, findings.get('attacks'))
        findings['attack_points'] = group(findings.get('attack_points', []))
        findings['attacks'] = len(findings.get('attack_points', []))
        findings['false_alarms'] = misses if hits <= findings.get('attacks') else misses + abs(hits - findings.get('attacks'))
        findings['detection_effectiveness'] = round((findings.get('detected') /
                                                     max(1, findings.get('attacks'))) * 100.0, 2)
        findings['false_alarm_rate'] = round((findings.get('false_alarms') /
                                             max(1, (findings.get('samples') - findings.get('attacks')))) * 100.0, 2)
        return findings


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
            'attack_points',
            'change_points',
            'detected',
            'false_alarms',
            'detection_effectiveness',
            'false_alarm_rate'
        ]]

    def get(self, category, best=False):
        if category not in Config.ATTACK_TYPES:
            return self.changes

        rows = self.changes.loc[self.changes.category == category]
        if best:
            rows = rows[rows['detection_effectiveness'] == rows['detection_effectiveness'].max()]
            rows = rows[rows['false_alarm_rate'] == rows['false_alarm_rate'].min()]

        return rows.loc[rows['detection_effectiveness'] > Config.MIN_DETECTION_EFFECTIVENESS]\
                   .loc[rows['false_alarm_rate'] < Config.MAX_FALSE_ALARM_RATE]\
                   .sort_values(by='detection_effectiveness', ascending=False)

    def log(self):
        runs = runtime.setup()
        fname = path.join(runs, "results.csv")
        mode = "a" if (path.exists(fname) and path.getsize(fname) != 0) else "w"
        self.changes.to_csv(fname, mode=mode, index=False, header=not path.exists(fname))

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
    args = A.parse_args()

    defects, duration = ChangeDetector().run(args.sensor, args.attack)
    defects = ChangeWriter(defects).get(args.attack)

    print(defects)
    print(f"\ntime elapsed: {duration} seconds")
