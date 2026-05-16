import json

data = json.load(open('data/colleges_josaa.json', encoding='utf-8'))
trichy = [c for c in data if 'Trichy' in c['name']]
print(f'Found {len(trichy)} Trichy entries')
for c in trichy[:10]:
    print(f"{c['name']} {c['branch']}: {c['cutoff_rank']} ({c['rank_type']})")
