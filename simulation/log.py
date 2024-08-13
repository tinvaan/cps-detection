
import pandas as pd

from os import path

from simulation import plots
from simulation.elevator import runtime
from simulation.elevator.runtime import Config


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
        if len(category.split(',')) == 1:
            if category not in Config.ATTACK_TYPES:
                return self.changes

        rs = self.changes.loc[self.changes.category == category]
        if best:
            rs = rs[rs['detection_effectiveness'] == rs['detection_effectiveness'].max()]
            rs = rs[rs['false_alarm_rate'] == rs['false_alarm_rate'].min()]

        return rs.loc[rs['detection_effectiveness'] > Config.MIN_DETECTION_EFFECTIVENESS]\
                 .loc[rs['false_alarm_rate'] < Config.MAX_FALSE_ALARM_RATE]\
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
