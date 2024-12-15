#!/bin/python3


from utils import parse
from illust import Illust
import json



if __name__ == '__main__':
    s = json.load(open('../pixiv/json/illust.json'))
    i = Illust(s)
    print(i)
