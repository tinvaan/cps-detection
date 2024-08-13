
import pandas as pd

from os import path
from tqdm import tqdm

from simulation import plots
from simulation.elevator import runtime
from simulation.elevator.runtime import Config


class ChangeWriter:
    def __init__(self, changesets):
        self.changes = self.process(changesets)
        self.changes = self.changes[[
            'cycle',
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
            'false_alarm_rate',
            'readings'
        ]]

    def get(self, category, best=False):
        if len(category.split(',')) == 1:
            if category not in Config.ATTACK_TYPES:
                return self.changes

        rs = self.changes.loc[self.changes.category == category]
        if best:
            rs = rs.loc[rs['detection_effectiveness'] == rs['detection_effectiveness'].max()]
            rs = rs.loc[rs['false_alarm_rate'] == rs['false_alarm_rate'].min()]

        return rs.loc[rs['detection_effectiveness'] > Config.MIN_DETECTION_EFFECTIVENESS]\
                 .loc[rs['false_alarm_rate'] < Config.MAX_FALSE_ALARM_RATE]\
                 .sort_values(by='detection_effectiveness', ascending=False)

    def log(self):
        runs = runtime.setup()
        fname = path.join(runs, "results.csv")
        mode = "a" if (path.exists(fname) and path.getsize(fname) != 0) else "w"
        self.changes.to_csv(fname, mode=mode, index=False, header=not path.exists(fname))

        if Config.SHOW_PLOTS or Config.SAVE_PLOTS:
            df = self.changes.loc[self.changes['detection_effectiveness'] ==
                                  self.changes['detection_effectiveness'].max()]
            df = df.loc[df['false_alarm_rate'] == df['false_alarm_rate'].min()]\
                    .sort_values(by='attacks', ascending=False).iloc[:1]
            plots.draw(df)

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
