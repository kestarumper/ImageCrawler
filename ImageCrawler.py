import sys
import re
import os
import mimetypes
from html.parser import HTMLParser
from urllib import request as URLRequest, parse as URLParser

class Log:
    @staticmethod
    def info(msg):
        msg = str(msg)
        if msg:
            return "\033[94m[INFO]\033[0m " + "\n\033[94m[INFO]\033[0m ".join(msg.split("\n"))
        else:
            return ""

    @staticmethod
    def warn(msg):
        msg = str(msg)
        if msg:
            return "\033[38;5;208m[WARN]\033[0m " + "\n\033[93m[WARN]\033[0m ".join(msg.split("\n"))
        else:
            return ""

    @staticmethod
    def err(msg):
        msg = str(msg)
        if msg:
            return "\033[91m[ERR ]\033[0m " + "\033[91m[ERR ]\033[0m ".join(msg.split("\n"))
        else:
            return ""

class ImageSrcParser(HTMLParser):
    """ Extracts all src parameters from <img> tags """
    def __init__(self, url):
        self.url = url
        self.images = []
        super(ImageSrcParser, self).__init__()

    def __iter__(self):
        return self.images.__iter__()

    def _absolutePath(self, path):
        return URLParser.urljoin(self.url, path)

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img":
            for key, value in attrs:
                if key.lower() == "src":
                    value = self._absolutePath(value)
                    self.images.append(value)

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass

    def error(self, message):
        print(Log.err(message))
    
class ImageUrl:
    """ Downloads image remote file and saves it to disk """
    def __init__(self, url):
        self.safe = False
        self.directories = []
        try:
            self.source = URLRequest.urlopen(url)
            self.url = URLParser.urlparse(url)
        except Exception as e:
            raise e
        else:
            with self.source as src:
                self.data = src.read()
                self.extension = mimetypes.guess_extension(src.info()["Content-Type"])
                self.filename = self.url.path.split("/")[-1]
                self.directories = self.url.path.split("/")[1:-1]
                self.directories.insert(0,self.url.netloc)
                self.safe = True       
                
    def nextDirectory(self):            
        dirstr = ""
        for directory in self.directories:
            dirstr += directory + "/"
            yield dirstr

    def saveToFile(self, path = ""):
        if not self.safe:
            return

        if path:
            self.directories.insert(0,path)

        self.dirpath = "/".join(self.directories) + "/"

        filepath = self.dirpath + self.filename

        for directory in self.nextDirectory():
            try:
                if not os.path.exists(directory):
                    print(Log.warn("Creating directory: \033[93m%s\033[0m" % directory))
                    os.makedirs(directory)
            except Exception as e:
                raise e

        try:
            fp = open(filepath, "w+b")
        except PermissionError as e:
            raise e
        else:
            print(Log.info("Saving \033[32m%s\033[0m as \033[33m%s\033[0m" % (self.source.geturl() ,filepath)))
            fp.write(self.data)
        finally:
            fp.close()
            


def usage():
    print(Log.warn("\033[93mNot enough arguments\033[0m"), file=sys.stderr)
    print(Log.info("\033[1m\033[94mUsage:\033[0m\n\tImageCrawler -url <\033[92murl\033[0m>"))

def argvKeyPair(args):
    """ Returns dictionary with settings params passed to program """
    settings = {}
    while args:
        value = args.pop()
        if value.startswith("-"):
            key = value
            value = True
        elif len(args) > 0:
            key = args.pop()
        key = key.replace("-","")
        settings[key] = value
    return settings

#########################################__MAIN__############################################
if len(sys.argv) > 1:
    del sys.argv[0]

    ARGS = {
        "url":"",
        "recursive":False,
        "path":""
    }
    ARGS.update(argvKeyPair(sys.argv))
    
    try:
        source = URLRequest.urlopen(ARGS["url"])
    except Exception as e:
        print(Log.err(e))
        exit()
    
    data = source.read()

    if source.getcode() != 200:
        print(Log.err("Bad response code %s" % source.getcode() ) )
        exit()
    else:
        # print(Log.info("Headers:"))
        # for item in source.info().items():
        #     print(Log.info(item))
        images = ImageSrcParser(source.geturl())
        images.feed(str(data))
        images.close()

        print(Log.info("Downloaded source from \033[34m%s\033[0m [\033[36m%i\033[0m bytes]" % (source.geturl(), len(data))))

        for imageurl in images:
            try:
                img = ImageUrl(imageurl)
                img.saveToFile(ARGS["path"])
            except Exception as e:
                print(Log.err(e))
                continue

else:
    usage()
    exit()