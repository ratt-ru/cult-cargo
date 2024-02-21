
import requests
from ruamel.yaml import YAML
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
import cultcargo

mpath = cultcargo.__file__.rstrip('__init__.py') + 'genesis/pfb-clean/latest'

# import ipdb; ipdb.set_trace()
content_path = 'https://raw.githubusercontent.com/ratt-ru/pfb-clean/awskube/pfb/parser'

# returns list of files in subfolder
response = requests.get('https://api.github.com/repos/ratt-ru/pfb-clean/contents/pfb/parser?ref=awskube')
for r in response.json():
    name = r['name']
    print(name)
    if name.endswith('yml') or name.endswith('yaml'):
        # get file content
        config = requests.get(f'{content_path}/{name}')
        # round trip to get correct formatting
        data = yaml.load(config.text)
        # dump to yaml
        with open(f'{mpath}/{name}', 'w') as f:
            yaml.dump(data, f)

print('Done')
