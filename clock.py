"""Map media-track ticks to a shared match clock.

Sync points are scoped to a (track, epoch) pair: a track restart begins a new
epoch whose points are isolated from every other epoch, and tracks never share
points. For a query, only points at or before the queried tick are eligible;
a future point cannot map a past tick. The newest eligible tick anchors the
mapping, and when several readings share a tick the highest revision wins.
Elapsed ticks past that point are converted with the integer floor of the
point's rational rate.

The per-(track, epoch) points are kept sorted so a query is a binary search:
``Work`` counts the sync-point candidates examined while searching, keeping a
recent seek O(log n) instead of rescanning the whole archive.
"""


class ClockMapper:
    def __init__(self):
        self.points = []
        self.Work = 0
        # track -> epoch -> entries sorted by tick; each entry is the winning
        # point for its tick (highest revision seen for that tick).
        self._index = {}

    def add(self, point):
        point = dict(point)
        self.points.append(point)

        epoch_points = self._index.setdefault(point["track"], {}).setdefault(
            point["epoch"], []
        )

        # Find the sorted position for this tick.
        lo, hi = 0, len(epoch_points)
        while lo < hi:
            mid = (lo + hi) // 2
            if epoch_points[mid]["tick"] < point["tick"]:
                lo = mid + 1
            else:
                hi = mid

        if lo < len(epoch_points) and epoch_points[lo]["tick"] == point["tick"]:
            # A later revision for the same tick supersedes the earlier one.
            if point["revision"] >= epoch_points[lo]["revision"]:
                epoch_points[lo] = point
            return
        epoch_points.insert(lo, point)

    def map(self, track, epoch, tick):
        epoch_points = self._index.get(track, {}).get(epoch)
        if not epoch_points:
            # No point in this track's current epoch: nothing to anchor on.
            return None

        # Rightmost point whose tick is <= the queried tick. A future point can
        # never map a past tick, so an insertion position of 0 means no
        # eligible point exists and the query has no result.
        lo, hi = 0, len(epoch_points)
        while lo < hi:
            mid = (lo + hi) // 2
            self.Work += 1
            if epoch_points[mid]["tick"] <= tick:
                lo = mid + 1
            else:
                hi = mid
        if lo == 0:
            return None

        best = epoch_points[lo - 1]
        elapsed_ticks = tick - best["tick"]
        elapsed_ms = (elapsed_ticks * best["numerator"]) // best["denominator"]
        return best["wall_ms"] + elapsed_ms
