"""Map media-track ticks to a shared match clock."""


class ClockMapper:
    def __init__(self):
        self.points = []
        self.Work = 0

    def add(self, point):
        self.points.append(dict(point))

    def map(self, track, epoch, tick):
        best = None
        for point in self.points:
            self.Work += 1
            if point["track"] != track or point["epoch"] > epoch:
                continue
            if best is None or abs(point["tick"] - tick) < abs(best["tick"] - tick):
                best = point
        if best is None:
            return None
        elapsed = (tick - best["tick"]) * best["numerator"] / best["denominator"]
        return best["wall_ms"] + round(elapsed)
