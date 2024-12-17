import sys
sys.path.append('./dataclass')

from example1 import Example1
import json

filepath = 'json/example1.json'

example = Example1(json.load(open(filepath)))
print(example)
print(example.pascal_name1)
print(example.pascal_name3)
