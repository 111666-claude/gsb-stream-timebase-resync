import unittest

from clock import ClockMapper


def make(track="video", epoch=1, tick=0, wall_ms=0, numerator=1, denominator=1, revision=1):
    return {
        "track": track,
        "epoch": epoch,
        "tick": tick,
        "wall_ms": wall_ms,
        "numerator": numerator,
        "denominator": denominator,
        "revision": revision,
    }


class ClockMapperBasicTests(unittest.TestCase):
    def test_exact_anchor(self):
        m = ClockMapper()
        m.add(make(tick=100, wall_ms=2000))
        self.assertEqual(m.map("video", 1, 100), 2000)

    def test_future_point_cannot_map_past_tick(self):
        # tick0 -> 1000ms and tick10 -> 2000ms; querying tick9 must use the
        # point not later than the query, never the tick10 reading.
        m = ClockMapper()
        m.add(make(tick=0, wall_ms=1000))
        m.add(make(tick=10, wall_ms=2000))
        self.assertEqual(m.map("video", 1, 9), 1009)

    def test_no_earlier_point_returns_none(self):
        m = ClockMapper()
        m.add(make(tick=10, wall_ms=2000))
        self.assertIsNone(m.map("video", 1, 9))

    def test_empty_mapper_returns_none(self):
        self.assertIsNone(ClockMapper().map("video", 1, 0))

    def test_integer_floor_rate(self):
        # 3 ticks at rate 2/3 ms per tick: 6/3 -> 2ms; 1 tick -> floor(2/3) -> 0ms
        m = ClockMapper()
        m.add(make(tick=0, wall_ms=1000, numerator=2, denominator=3))
        self.assertEqual(m.map("video", 1, 3), 1002)
        self.assertEqual(m.map("video", 1, 1), 1000)
        # 2 ticks -> floor(4/3) = 1ms, never rounded up to 2
        self.assertEqual(m.map("video", 1, 2), 1001)

    def test_higher_revision_wins_at_same_tick(self):
        m = ClockMapper()
        m.add(make(tick=0, wall_ms=1000, revision=1))
        m.add(make(tick=0, wall_ms=1500, revision=2))
        self.assertEqual(m.map("video", 1, 5), 1505)

    def test_lower_revision_ignored_at_same_tick(self):
        m = ClockMapper()
        m.add(make(tick=0, wall_ms=1500, revision=3))
        m.add(make(tick=0, wall_ms=1000, revision=2))
        self.assertEqual(m.map("video", 1, 5), 1505)

    def test_epoch_isolation_restart(self):
        m = ClockMapper()
        m.add(make(epoch=1, tick=0, wall_ms=1000))
        m.add(make(epoch=2, tick=0, wall_ms=5000))
        # Querying the new epoch must not see old-epoch points.
        self.assertEqual(m.map("video", 2, 7), 5007)
        # The old epoch is still readable on its own.
        self.assertEqual(m.map("video", 1, 7), 1007)
        # An epoch with no point at or before the tick yields nothing.
        self.assertIsNone(m.map("video", 3, 0))

    def test_track_isolation(self):
        m = ClockMapper()
        m.add(make(track="audio", tick=0, wall_ms=1000))
        m.add(make(track="video", tick=0, wall_ms=2000))
        self.assertEqual(m.map("audio", 1, 4), 1004)
        self.assertEqual(m.map("video", 1, 4), 2004)
        self.assertIsNone(m.map("subtitles", 1, 4))

    def test_unsorted_addition_still_maps_correctly(self):
        m = ClockMapper()
        for tick, wall in [(10, 2000), (0, 1000), (5, 1500)]:
            m.add(make(tick=tick, wall_ms=wall))
        # tick5 -> 1500ms is the newest point not later than tick9
        self.assertEqual(m.map("video", 1, 9), 1504)
        self.assertEqual(m.map("video", 1, 10), 2000)

    def test_work_budget_3000_points_200_queries(self):
        m = ClockMapper()
        for tick in range(3000):
            m.add(make(track="video", epoch=1, tick=tick, wall_ms=1000 + tick))
        # Other epochs/tracks add archive noise that must never be rescanned.
        for tick in range(3000):
            m.add(make(track="video", epoch=9, tick=tick, wall_ms=tick))
            m.add(make(track="audio", epoch=1, tick=tick, wall_ms=tick))

        before = m.Work
        for tick in range(2800, 3000):
            self.assertEqual(m.map("video", 1, tick), 1000 + tick)
        self.assertLessEqual(m.Work, 6000)
        self.assertGreater(m.Work, before)


if __name__ == "__main__":
    unittest.main()
