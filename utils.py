
import codecs as cd

def decode_unicode_url(url):
    return cd.decode(url.encode('ascii','replace'),'utf-8')

