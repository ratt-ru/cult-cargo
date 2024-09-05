
import requests
from ruamel.yaml import YAML
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
import cultcargo

mpath = cultcargo.__file__.rstrip('__init__.py') + 'genesis/pfb-imaging/latest'

branch = 'outputs'
content_path = f'https://raw.githubusercontent.com/ratt-ru/pfb-imaging/{branch}/pfb/parser'

# returns list of files in subfolder
response = requests.get(f'https://api.github.com/repos/ratt-ru/pfb-imaging/contents/pfb/parser?ref={branch}')
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
