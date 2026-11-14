# Track timebase resync

Audio and video tracks each report sync points with track ID, epoch, local
tick, match-clock millisecond, rational tick-to-millisecond rate, and revision.
For a query, use the highest-revision sync point at or before that tick in the
requested track's **current epoch**. A future point cannot map a past tick;
points from earlier or later epochs are isolated. Between points, map elapsed
ticks with integer floor of the rational conversion, preserving long-running
precision. If no preceding point exists, return `None`.

`Work` counts sync-point candidates examined by queries. A recent seek on one
track should not rescan years of archived points from other epochs or tracks.
