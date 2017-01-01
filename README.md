# Experiments with Glicko-2 to Rate CTF Teams

Author: [niklasb](https://twitter.com/_niklasb)

![Example Glicko-2 CTF Rating 2016](https://kitctf.de/public/glicko2-example.svg)

If you want to play around with your own parameters and see the results, you can use
[my web app](https://kitctf.de/glicko2/).

## What is this?

This is an application of the
[Glicko-2](http://www.glicko.net/glicko/glicko2.pdf) rating system to the
CTFTime data from 2016, using the [multiplayer implementation by
Matt Sewall](https://github.com/ms2300/multiplayer-glicko2). I scraped the
scoreboards from all 2016 CTFs and applied the ranking to it.

To counter the fact that some teams play with vastly different numbers of
players on different events, I applied some modification to the original
scheme:

* Only the top `max_top` teams are considered for each event. The assumption is
that these teams obviously *tried* to achieve a good result, so it's useful to
compare their result against other top teams.
* Optionally, we can exclude teams that achieved less than `score_percentile`
percent of the score achieved by the winning team
* To counter some of the massive rating loss that some teams would experience
by just a few bad events, we add a damping factor that only applies to
negative rating deltas. I.e. if a team would normally lose X rating points,
we multiply that by the damping factor before appying the delta. This leads
to some rating inflation of course, depending on the value.

My own experiments and intuition show that these values might be a good
starting point for experimentation:

* `max_top = 20`
* `score_percentile = 0` (because `max_top` is small enough)
* `negative_damping = 0.7` (negative deltas are only counted 70%)
* `(initrat, initrd, initvol) = (1500, 100, 0.1)` (these are the standard
  Glicko-2 parameters)


## TODO + Known Limitations

* Currently we don't order events by date, but by ID
