import SimpleHTTPServer
import SocketServer
import os
import json
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict
from clarifai.client import ClarifaiApi
from urlparse import urlparse, parse_qs
try:
    import cPickle as pickle
except:
    import pickle

import operator
from fuzzywuzzy import process

os.environ["CLARIFAI_APP_SECRET"] = "Jf6Sm2o8bY-MopRVJUjPeTzfJvTPtNC9nW20rVoL"
os.environ["CLARIFAI_APP_ID"] = "BQv24SbZOmKS-LE1I7z_xXc01AX32luGBy84OKDI"

class User(object):
    """Represents a single user"""
    def __init__(self, name):
        """"""
        self.name = name
        self.imgurls = set()

    def addImageToUser(self, img):
        self.imgurls.add(img)

    def __repr__(self):
        return self.imgurls.__str__()

class SearchIndex(object):
    """Index search creator tool thing blah cool"""
    def __init__(self, image_list):
        """
        Params:

        image_list(list[ImageLink])
        """
        self.clarifai = ClarifaiApi()
        self.index = defaultdict(set)
        self.image_list = image_list

    def add_image(self, imgurl, user="default"):
        if imgurl in all_images:
            users[user].addImageToUser(imgurl)
            return
        all_images.add(imgurl)

        users[user].addImageToUser(imgurl)

        tags = self.tag_photo(imgurl)
        for tag in tags:
            self.index[tag].add(imgurl)
        
        with open('urls.txt', 'w') as f:
            pickle.dump(self.index, f)
            f.close()

    def gen_index(self):
        for img in self.image_list:
            tags = self.tag_photo(img)
            for tag in tags:
                self.index[tag].add(img)

    def tag_photo(self, image):
        result = self.clarifai.tag_image_urls(image)
        tags = result['results'][0]['result']['tag']['classes']
        print tags
        return tags

    def search(self, search_term, user="default"):
        terms = search_term.split()
        counts = defaultdict(int)
        for term in terms:
            (closest, num) = process.extractOne(term, self.index.keys())
            print closest, num
            if num > 50:
                results = self.index[closest]
                for img in results:
                    if img in users[user].imgurls:
                        counts[img] += 1
        sorted_counts = sorted(counts.items(), key=operator.itemgetter(1))

        
        print users
        return sorted_counts 

            
index = SearchIndex([])  
with open('urls.txt', 'r') as f:
    index.index = pickle.load(f)
    f.close()

all_images = reduce(lambda x,y: x | y, index.index.values())



users = {
    "default": User("default")
}

users["default"].imgurls = all_images


class MemoriesHandler(BaseHTTPRequestHandler):
    """"""
    def do_HEAD(self):
       self.send_response(200)
       self.send_header("Content-type", "text/html")
       self.end_headers()

    def parse_args(self, path):
        return parse_qs(urlparse(path).query)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        parsed = urlparse(self.path)
        if(parsed.path == "/add"):
            args = self.parse_args(self.path)
            if 'user' in args: 
                if args['user'][0] not in users:
                    users[args['user'][0]] = User(args['user'])
            else:
                args['user'] = ['default']
            index.add_image(args.get('imageURL')[0], user=args['user'][0])
        
        elif(parsed.path == "/search"):
            args = self.parse_args(self.path)
            if 'user' in args: 
                if args['user'][0] not in users:
                    users[args['user'][0]] = User(args['user'][0])
            else:
                args['user'] = ['default']

            total = index.search(args.get('term')[0], user=args['user'][0])
            json.dump([x for (x,y) in total], self.wfile)


        

def run():
  print('http server is starting...')
 
  #ip and port of servr
  #by default http server port is 80
  server_address = ('0.0.0.0', int(os.environ.get("PORT", 3000)))
  httpd = HTTPServer(server_address, MemoriesHandler)
  print('http server is running...')
  httpd.serve_forever()

run()