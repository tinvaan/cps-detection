
def merge(intervals):
    if len(intervals) <= 1:
        return intervals

    intervals.sort()
    m = [intervals[0]]
    for curr in intervals[1:]:
        last = m.pop()

        if (last[1] in range(curr[0], curr[1] + 1) or
            curr[1] in range(last[0], last[1] + 1)
        ):
            m.append((min(last[0], curr[0]), max(last[1], curr[1])))
        else:
            m.extend([last, curr])
    return m


def group(ts):
    points = [(-1, -1)]
    for t in ts:
        if t == points[-1][1] + 1:
            points[-1] = (points[-1][0], t)
        else:
            points.append((t, t))

    del points[0]
    return merge(points)


if __name__ == '__main__':
    assert merge([(5, 19), (7, 19)]) == [(5, 19)]
    assert merge([(2, 17), (3, 19), (15, 19)]) == [(2, 19)]
    assert merge([(1, 19), (4, 16), (5, 19), (13, 19)]) == [(1, 19)]
    assert merge([(0, 12), (1, 17), (1, 19), (1, 19), (11, 19)]) == [(0, 19)]
