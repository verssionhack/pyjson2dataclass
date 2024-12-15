# Parse json to python dataclass
## Usage
```sh
./__main__.py <json file1> <json file2> ...
```
```sh
python -m pyjson2dataclass <json file1> <json file2> ...
```

```python
from pyjson2dataclass import parse
import json


filepath = 'json/example1.json'

parse_text = parse('Example', json.load(open(filepath)))
open('example.py', 'w').write(parse_text)
```
