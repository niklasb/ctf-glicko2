import requests
import os
import multiprocessing
from bs4 import BeautifulSoup as BS

from utils import *

if not os.path.exists('data/events.html'):
    with open('data/events.html', 'wb') as f:
        r = requests.get('https://ctftime.org/event/list/past')
        f.write(r.text.encode('utf-8'))

if not os.path.exists('data/events.json'):
    events = []
    with open('data/events.html') as f:
        soup = BS(f.read(), 'lxml')
        tbl = soup.find('table')
        for row in tbl.find_all('tr'):
            # print row.prettify()
            try:
                link = row.find('a')
                href = link['href']
                name = link.string
            except:
                continue
            id_ = int(href.split('/')[-1])
            date = row.find_all('td')[1].string
            if '2016' in date:
                #print name
                events.append({'title':name, 'id': id_})
    events.reverse()
    with open('data/events.json', 'wb') as f:
        json.dump(events, f)

events = load_events()

def get(evt):
    path = 'data/events/{}.json'.format(evt['id'])
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    print 'Loading event {}'.format(evt['id'])

    r = requests.get(
            'https://ctftime.org/event/{}'.format(evt['id']))
    if 'Rating weight: ' in r.text:
        weight = float(r.text.split('Rating weight: ')[1].split('&nbsp')[0])
    else:
        weight = 0.0
    soup = BS(r.text, 'lxml')
    tbl = soup.find('table')
    if not tbl:
        with open(path, 'wb') as f:
            json.dump(evt, f)
        return evt

    data = []
    for row in tbl.find_all('tr')[1:]:
        team_id = int(row.find('a')['href'].split('/')[-1])
        team_name = row.find('a').string
        pts = float(row.find_all('td')[3].string)
        data.append({'team':{'id':team_id, 'name':team_name},
                     'pts':pts})

    evt['scoreboard'] = data
    evt['weight'] = weight
    with open(path, 'wb') as f:
        json.dump(evt, f)
    print 'Saved event {}'.format(evt['id'])
    return json.dumps(evt)

p = multiprocessing.Pool(10)

events = p.map(get, events)
