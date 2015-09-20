import SimpleHTTPServer
import SocketServer
import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict
from clarifai.client import ClarifaiApi
from urlparse import urlparse, parse_qs
try:
    import cPickle as pickle
except:
    import pickle

import operator

os.environ["CLARIFAI_APP_SECRET"] = "Jf6Sm2o8bY-MopRVJUjPeTzfJvTPtNC9nW20rVoL"
os.environ["CLARIFAI_APP_ID"] = "BQv24SbZOmKS-LE1I7z_xXc01AX32luGBy84OKDI"
        


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

    def add_image(self, imgurl):
        if imgurl in all_images:
            return
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
        return tags

    def search(self, search_term):
        terms = search_term.split()
        counts = defaultdict(int)
        for term in terms:
            results = self.index[term]
            for img in results:
                counts[img] += 1
        sorted_counts = sorted(counts.items(), key=operator.itemgetter(1))
        return sorted_counts

            
index = SearchIndex([])  
with open('urls.txt', 'r') as f:
    index.index = pickle.load(f)
    f.close()

all_images = reduce(lambda x,y: x | y, index.index.values())


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
            index.add_image(args.get('imageURL')[0])
        
        elif(parsed.path == "/search"):
            args = self.parse_args(self.path)
            total = index.search(args.get('term')[0])
            self.wfile.write([x for (x,y) in total])


        

def run():
  print('http server is starting...')
 
  #ip and port of servr
  #by default http server port is 80
  server_address = ('0.0.0.0', int(os.environ.get("PORT", 3000)))
  httpd = HTTPServer(server_address, MemoriesHandler)
  print('http server is running...')
  httpd.serve_forever()

run()