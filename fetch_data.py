import dataclasses
import json
import config 
import pandas as pd
import utils
import requests
import os
from bs4 import BeautifulSoup as bs
import logging
from random import randint
import time
from itertools import count
import pickle

@dataclasses.dataclass
class Myntra:
    landingPageUrl:str
    additionalInfo:str
    brand:str
    category:str
    gender:str
    images:list[dict]
    primaryColour:str
    productName:str
    productMeta:str
    searchImage:str
    season:str
    status:int=config.STATUS_NOT_DOWNLOADED


class HandBagCollection(object):
    def __init__(self,dataset_type=Myntra):
        self.logger = logging.getLogger(
                        'download.log'
                      )
        self.logger.setLevel(level=logging.DEBUG) 
        self._count = count()

        
    def from_html(self):
        '''
            Extract the all html files from a folder
        '''
        from_dir = os.path.join(config.HOME,config.PAGES)

        if not os.path.exists(from_dir):
            self.logger.error('Directory doesn\'t exist')

        #func = lambda x: int(x.split("=")[1].split('.')[0])
        self.files = os.listdir(from_dir)


    def parse_html(self,dataset_type=Myntra,url_root='https://myntra.com'):
        '''
            From each html, parse the data
        '''
        self.products = {}      
        for efile in self.files:
            
            file_path = os.path.join(config.HOME,config.PAGES,efile)
            if not os.path.exists(file_path):
                self.logger.error(f'File not found {efile}')

            try:
                f = open(file_path,'r')
                raw_product_info = json.load(f)
                
                fields = [f.name for f in dataclasses.fields(dataset_type)]
                
                for _,products in raw_product_info.items():
                    for product in products:                  
                        myntra = Myntra(**{k:v for k,v in product.items() if k in fields})                        
                        myntra.searchImage = utils.decode_unicode_url(myntra.searchImage)                        
                        myntra.landingPageUrl = utils.decode_unicode_url(os.path.join(url_root,
                            myntra.landingPageUrl))
                        product_id = next(self._count)
                        self.products[product_id] = myntra
                           
            except ValueError as Err:
                self.logger.error(f'Exception thrown at reading the file {efile}')

        return self.products
          
    def write(self,data,filename='raw_product.json'):
        
        serialize_data = json.dumps(data,default=vars)

        with open(filename,'w') as f:
            f.write(serialize_data)


class Download(object):
    '''
        - Reads the json file and saves the product info
    '''
    def __init__(self,fName=None,img_dir=None,label_dir=None): 
        self.logger = logging.getLogger(
                        'product_download.log',
                      )     
        self.logger.setLevel(level=logging.DEBUG)          
        if fName:
            try:
                products = None
                products_path = os.path.join(config.HOME,fName)
                with open(products_path,'r') as f:
                    products = f.read()
                self.products_info = json.loads(products)
            except err:
                self.logger.error('Error in parsing the file')

        
        if img_dir:
            if not os.path.exists(img_dir):
                self.logger.error('Image Directory doesn\'t exist')
            self.p_img_dir = img_dir
            
        if label_dir:
            if not os.path.exists(label_dir):
                self.logger.error('Label Directory doesn\'t exist')
            self.p_label_dir = label_dir

    def get(self,idx):
        return self.products_info[str(idx)]

    def fetch(self,mode='all',indexes=None):
        
        dwn_range = []
        
        if mode == 'all':
            idx_pkl = os.path.join(config.HOME,'rng_ix.pkl')
            if not os.path.exists(idx_pkl):
                for product_id,product_info in self.products_info.items():
                    if product_info['status'] == 0:
                        dwn_range.append(product_id)            
                with open(idx_pkl,'wb') as f:
                    pickle.dump(dwn_range,f)
            else:
                f = open(idx_pkl,'rb')
                dwn_range  = list(pickle.load(f))
        
        elif mode == 'range':
            initial,final = None,None
            if len(indexes) == 2:
                initial,final = indexes

                final = min(final,14949)
                dwn_range = list(range(initial,final+1))
            else:
                dwn_range = indexes
          
        self._fetch_files(dwn_range)
        self.save()
           

    def _fetch_files(self,rng_indxs=[],sleep=randint(0,10)):

        headers = {'User-Agent':
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'}
        for idx in rng_indxs:            
            product = self.get(idx)
            time.sleep(sleep)            
            page = requests.get(product['landingPageUrl'],headers=headers)
            soup = bs(page.text,'html.parser')
            
            script = soup.find_all('script')[11].text

            if script:                
                meta_info = json.loads(script.split('=',1)[1])
                product['meta_info'] = meta_info
            
                lbl_path = os.path.join(self.p_label_dir,str(idx)+'.json')
                self.write({idx:product},lbl_path)

                img_path = os.path.join(self.p_img_dir,str(idx)+'.jpg')
                response = requests.get(product['searchImage'])
                self.write_img(response,img_path)
            
                self.products_info[str(idx)]['status'] = '1'
                self.logger.debug(f'Downloading product-{idx}')



    def write(self,data,filename='raw_product.json'):
        serialize_data = json.dumps(data,default=vars)
        with open(filename,'w') as f:
            f.write(serialize_data) 

    def save(self):
        self.write(self.products_info)   

    def write_img(self,response,filename=None):
        if not filename:
            self.logger.error('Please provide the path to save the image')
            return 
        with open(filename,'wb') as f:
            f.write(response.content)
        


#collection = HandBagCollection()
#collection.from_html()
#products = collection.parse_html()
#collection.write(products)

d = Download(fName=config.fName,
        img_dir=config.img_dir,
        label_dir=config.label_dir)

d.fetch(mode='range',indexes=[1,100])

