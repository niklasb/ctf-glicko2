import contextlib
import json
import os

@contextlib.contextmanager
def produce(fname):
    if os.path.exists(fname):
        return
    print 'Producing {}'.format(fname)
    with open(fname) as f:
        yield f

def load_events():
    with open('data/events.json') as f:
        return json.load(f)

def load_event(id_):
    with open('data/events/{}.json'.format(id_)) as f:
        return json.load(f)
