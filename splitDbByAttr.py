import os
import json
from shutil import copy

imgs = "./images"
labls = "./labels"
dest = "./dest"


def split_data_into_folders():
    json_files = []
    if not os.path.exists(labls) or not os.path.exists(imgs):
        return 
    if not os.path.exists(dest):
        os.mkdir(dest)

    json_files = os.listdir(labls)

    for ef in json_files:
        f = json.load(open(os.path.join(labls,ef),'r'))
        *key, = f.keys()
        if key:
            data = f[key[0]]
            meta_info = data.get('meta_info',False)
            if meta_info:
                pdpdata = meta_info.get('pdpData',False)
                if pdpdata:
                    attr = pdpdata.get('articleAttributes',False)
                    pType = attr['Print or Pattern Type']
                    filename = key[0]+'.jpg'
                    f_url = os.path.join(imgs,filename)
                    if os.path.isfile(f_url):
                        f_dest = os.path.join(dest,pType)
                        if not os.path.exists(f_dest):
                            os.mkdir(f_dest)
                        copy(f_url,os.path.join(f_dest,filename))
                        
            else:
                print('Couldn\'t parse meta info')
                return

split_data_into_folders()

        





