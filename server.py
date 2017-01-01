# -*- coding: utf-8 -*-
from collections import defaultdict
from flask import jsonify, Flask, render_template, request
from glicko import *
from utils import *
import json
import sys


MAX_CONTEST_WEIGHT = 90.0

def make_graph(score_percentile=0,
               min_contest_weight=10.0,
               max_top=20,
               initrd=100,
               initvol=0.1,
               negative_damping=0.7):
    """
    score_percentile:   Only count teams that got at least this percentage of
                        points of the winning team
    min_contest_weight: Don't count contests below this weight
    max_top:            Only look at top X
    initrd:             Initial RD value for Glicko2
    initvol:            Initial volatility (sigma) value for Glicko2
    negative_damping:   Multiply negative deltas with this factor
    """
    def recompute(rating, order, contest_weight):
        contest_weight = min(1., contest_weight)

        competitors = []
        for i, user in enumerate(order):
            competitors.append(GlickoPlayer(user, i+1, *rating[user]))

        calculateGlicko(competitors, contest_weight, negative_damping)
        for player in competitors:
            rating[player.name] = (player.rating, player.confidence, player.volatility)

    def print_scores():
        teams = team_names.keys()
        teams.sort(key=lambda t: -(rating[t][0]-rating[t][1]))

        print '==================='
        for i, t in enumerate(teams[:20]):
            print i+1, team_names[t].encode('utf-8'), rating[t][0]-rating[t][1], \
                    rating[t][0], rating[t][1], rating[t][2]
        print '==================='


    events = load_events()
    events.sort(key=lambda evt: evt['id'])

    team_names = {}
    rating = defaultdict(lambda: (INITRAT, initrd, initvol))

    # print events
    xaxis = []
    team_series = defaultdict(list)
    used_events = []
    contest_weight = {}

    for evt in events:
        evt = load_event(evt['id'])
        if not 'scoreboard' in evt or evt['weight'] < min_contest_weight:
            continue

        used_events.append(evt)

        # print evt['title'], ' @', evt['weight']
        xaxis.append(evt['title'])
        score = evt['scoreboard']
        contest_weight[evt['id']] = evt['weight']

        max_score = score[0]['pts']
        order = []
        for s in score[:max_top]:
            if s['pts'] < score_percentile * max_score:
                break
            team_names[s['team']['id']] = s['team']['name']
            order.append(s['team']['id'])

        recompute(rating, order, evt['weight']/MAX_CONTEST_WEIGHT)

        for i, team_id in enumerate(order):
            team_series[team_id].append((evt['id'], rating[team_id], i+1))

        # print_scores()

    datasets = []

    teams = team_names.keys()
    teams.sort(key=lambda t: -rating[t][0])

    def get_evt_idx(eid):
        return next(i for i, e in enumerate(used_events) if e['id'] == eid)

    for idx, t in enumerate(teams):
        series = team_series[t]
        i = 0

        res = [{'x':get_evt_idx(eid),
                'y': r[0],
                'diff': r[0]-INITRAT if i == 0 else r[0] - series[i-1][1][0],
                'rd': r[1],
                'vol': r[2],
                'place': place,
                'contest_weight': contest_weight[eid]
                }
                for i, (eid, r, place) in enumerate(series)]
        # print res
        datasets.append({'name': team_names[t], 'data':res, 'visible': idx < 10})

    with open('templates/graph.html') as f:
        tmpl = f.read()

        tmpl = tmpl.replace('{{TOP}}', str(max_top))
        tmpl = tmpl.replace('{{DEFAULT_RATING}}', str(INITRAT))
        tmpl = tmpl.replace('{{DEFAULT_CONF}}', str(initrd))
        tmpl = tmpl.replace('{{DEFAULT_VOL}}', str(initvol))
        tmpl = tmpl.replace('{{NEGATIVE_DAMPING}}', str(negative_damping))
        tmpl = tmpl.replace('{{SCORE_PERCENTILE}}', str(score_percentile))
        tmpl = tmpl.replace('{{MIN_CONTEST_WEIGHT}}', str(min_contest_weight))

        tmpl = tmpl.replace('{{XAXIS}}', json.dumps([e['title'] for e in used_events]))
        tmpl = tmpl.replace('{{DATA}}', json.dumps(datasets, sort_keys=True, indent=4))
        return tmpl

"""
with open('graph.html', 'w') as f:
    f.write(make_graph(
        score_percentile=0,
        min_contest_weight=10,
        max_top=20,
        initrd=100,
        initvol=0.1,
        negative_damping=0.7,
        ))
        """

app = Flask(__name__)
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/graph")
def graph():
    max_top = int(request.args.get('max_top'))
    score_percentile = float(request.args.get('score_percentile'))
    min_contest_weight = float(request.args.get('min_contest_weight'))
    initrd = float(request.args.get('initrd'))
    initvol = float(request.args.get('initvol'))
    negative_damping = float(request.args.get('negative_damping'))
    return make_graph(
            max_top=max_top,
            score_percentile=score_percentile,
            min_contest_weight=min_contest_weight,
            initrd=initrd,
            initvol=initvol,
            negative_damping=negative_damping)

if __name__ == "__main__":
    app.secret_key = "asodhvhcUHOJJJ8oiudshfaoiuch973qw12hiu3hflkjalksdjoi"
    if len(sys.argv) < 3:
        print >>sys.stderr, "Usage: %s host port [--debug]" % sys.argv[0]
        exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    debug = '--debug' in sys.argv
    app.run(host=host, port=port, debug=debug)
