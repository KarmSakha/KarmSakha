"""Refresh a profile using exclusively unauthenticated, public GitHub data."""
import datetime as dt
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = 'KarmSakha'

def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'KarmSakha-public-profile', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode()

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        if 'data-date' in a and 'data-level' in a:
            self.days[a['data-date']] = int(a['data-level'])

def svg(body, height, label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-label="{html.escape(label)}"><rect width="1200" height="{height}" rx="12" fill="#101c21"/>{body}</svg>'

def text(x,y,value,size=16,color='#dce6dd',family='system-ui, -apple-system, Segoe UI, sans-serif'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-family="{family}">{html.escape(str(value))}</text>'

def refresh():
    # Deliberately no PAT, GITHUB_TOKEN, gh CLI, authenticated GraphQL, or private endpoint.
    repos=[]
    page=1
    while True:
        batch=json.loads(fetch(f'https://api.github.com/users/{USER}/repos?type=owner&per_page=100&page={page}'))
        if not isinstance(batch,list):
            raise ValueError('Unexpected repository API response')
        repos.extend(r for r in batch if r.get('private') is False)
        if len(batch)<100:
            break
        page+=1
    public=fetch(f'https://github.com/users/{USER}/contributions')
    calendar=Calendar()
    calendar.feed(public)
    match=re.search(r'([\d,]+)\s+contributions?\s+in the last year',public)
    if not calendar.days or not match:
        raise ValueError('Public contribution format changed; preserving previous assets')
    total=match.group(1)
    dates=sorted(calendar.days)
    start=dt.date.fromisoformat(dates[0])
    colors=['#213138','#446259','#638b69','#a4bf79','#d3f492']
    body=text(42,43,'THE PRACTICE / ONE DAY AT A TIME',14,'#d3f492',family='monospace')+text(42,91,'Small steps. A visible trail.',34,family='Georgia,serif')
    body+=text(42,124,f'{total} visible contributions · {dates[0]} — {dates[-1]}',15,'#a6b7b6')
    active=0
    for date in dates:
        days=(dt.date.fromisoformat(date)-start).days
        level=calendar.days[date]
        if not 0<=level<=4:
            raise ValueError('Unknown contribution level')
        active+=level>0
        x=45+(days//7)*20.7
        y=158+(days%7)*20
        body+=f'<rect x="{x:.1f}" y="{y}" width="15" height="15" rx="3" fill="{colors[level]}"><title>{date}: activity level {level}/4</title></rect>'
    body+=text(42,327,f'{active} active days  /  Includes private activity when shared',13,'#a6b7b6')
    body+=text(883,327,'LESS',11,'#a6b7b6')
    for i,c in enumerate(colors):
        body+=f'<rect x="{931+i*25}" y="315" width="16" height="16" rx="3" fill="{c}"/>'
    body+=text(1064,327,'MORE',11,'#a6b7b6')
    # Decorative snake follows rows without changing the underlying activity cells.
    last_x=45+((len(dates)-1)//7)*20.7+7.5
    route=[]
    for row in range(7):
        y=165.5+row*20
        left,right=52.5,last_x
        if row==0:
            route.append(f'M{left:.1f} {y:.1f}')
        route.append(f'H{right if row%2==0 else left:.1f}')
        if row<6:
            route.append(f'V{y+20:.1f}')
    # A closed perimeter return keeps the crawl seamless between loops.
    route.append(f'V298 H32 V145.5 H52.5 V165.5')
    route=' '.join(route)
    body+=f'''<style>
      @keyframes crawl {{ from {{stroke-dashoffset:1000}} to {{stroke-dashoffset:0}} }}
      .snake {{animation:crawl 80s linear infinite;fill:none;stroke-linecap:round;stroke-linejoin:round}}
      @media(prefers-reduced-motion:reduce) {{.snake{{display:none}}}}
    </style><g aria-hidden="true">
      <path class="snake" d="{route}" pathLength="1000" stroke="#0b1519" stroke-width="15" stroke-dasharray="12 988"/>
      <path class="snake" d="{route}" pathLength="1000" stroke="#d3f492" stroke-width="9" stroke-dasharray="12 988"/>
      <path class="snake" d="{route}" pathLength="1000" style="animation-delay:-.88s" stroke="#ef9a70" stroke-width="9" stroke-dasharray="1 999"/>
    </g>'''
    body+=text(42,369,'A little snake, a lot of practice.',16,'#dce6dd',family='Georgia,serif')
    body+=text(42,392,'Decorative animation · contribution values remain unchanged',12,'#a6b7b6')
    activity=svg(body,420,'GitHub contribution calendar with a decorative crawling snake; detailed accessible calendar linked below')
    originals=sorted((r for r in repos if not r['fork'] and r['name'].lower()!=USER.lower()),key=lambda r:r['name'].lower())
    forks=sorted((r for r in repos if r['fork']),key=lambda r:r['name'].lower())
    curated={
      'karmx-agent':'Terminal coding agent with context retrieval, prompt enhancement, browser preview, and configurable models.',
      'truck-log':'HOS Desk: route planning and daily duty-log visualization. Planning prototype; not a certified ELD.',
      'TinyQuery-140M':'139.7M-parameter experimental model trained from scratch for multilingual SQL and tool-call generation.',
      'Qwen3.8-27B-OBLITERATED-Mixed-128K-GGUF':'Community mixed-precision GGUF release with calibration, MTP preservation, and reproduction evidence.',
      'Qwen3.6-35B-A3B-Uncensored-Mixed-128K-GGUF':'Community GGUF quantization pipelines and evaluation artifacts for 16 GB GPU experiments.',
      'Nex-N2.5-mini-Mixed-Q2Q3-128K-GGUF':'Community quantization, deployment recipes, and documented evaluation tradeoffs.',
      'karmsakha-web-intelligence':'Public web-intelligence repository; README links to the project homepage.',
    }
    def row(r):
        desc=curated.get(r['name']) or r.get('description') or 'Explore the repository for implementation and documentation.'
        desc=html.escape(desc).replace('|','&#124;').replace('\n',' ')
        return f"| [{r['name']}]({r['html_url']}) | {desc} | {r.get('language') or 'Documentation'} |"
    block='\n| Project | What lives here | Primary language |\n| :--- | :--- | :--- |\n'+'\n'.join(map(row,originals))
    block+='\n\n<details>\n<summary><strong>Forks & learning library — upstream work, clearly credited</strong></summary>\n\n'
    for r in forks:
        block+=f"- [{r['name']}]({r['html_url']}) — fork; original authorship belongs to the upstream project.\n"
    block+='\n</details>\n\n<sub>Public repository inventory refreshed '+dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')+' UTC. Languages are repository metadata, not proficiency scores.</sub>\n'
    readme=(ROOT/'README.md').read_text()
    readme,n=re.subn(r'<!-- PUBLIC-INDEX:START -->.*?<!-- PUBLIC-INDEX:END -->','<!-- PUBLIC-INDEX:START -->\n'+block+'\n<!-- PUBLIC-INDEX:END -->',readme,flags=re.S)
    if n!=1:
        raise ValueError('Expected exactly one public index region')
    (ROOT/'assets/activity.svg').write_text(activity)
    (ROOT/'README.md').write_text(readme)
    print(f'Refreshed {len(originals)} original public repositories, {len(forks)} forks, and public contribution calendar.')

if __name__=='__main__':
    refresh()
