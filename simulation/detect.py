
from elevator.utils import group


def verify(state):
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


def analyze(changes, context):
    hits = context.get('hits')
    misses = context.get('misses')

    attack_duration = changes.get('attack_points', [])
    attack_intervals = group(changes.get('attack_points', []))
    changes.update({'attacks': len(attack_intervals), 'attack_points': attack_intervals})

    # If we have detected more attacks than launched, move the residue to false positives
    changes.update({
        'detected': min(hits, changes.get('attacks')),
        'false_alarms': misses if hits <= changes.get('attacks') else misses + abs(hits - changes.get('attacks'))
    })

    # Calculate the detection effectiveness and false alarm rates
    changes.update({
        'detection_effectiveness': round((changes.get('detected') / max(1, changes.get('attacks'))) * 100.0, 2),
        'false_alarm_rate': round((
            changes.get('false_alarms') /
            max(1, (changes.get('samples') - len(attack_duration)))
        ) * 100.0, 2)
    })
    return changes


def cusum(
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
            if verify_state and not verify(state):
                spikes.append(ts)
                pos[-1], neg[-1] = 0, 0

                hits += 1 if bool(state.get('attacked', False)) else 0
                misses += 1 if not bool(state.get('attacked', False)) else 0

    return analyze({
        'category': meta.get('category'),
        'samples': len(standard),
        'attacks': len(meta.get('attacks', []) or []),
        'attack_points': meta.get('attacks', []) or [],
        'change_points': spikes,
    }, context={'hits': hits, 'misses': misses})
