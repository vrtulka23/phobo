from tinydb import TinyDB, Query, where
import hashlib
import os
from datetime import datetime
import glob
import json
import shutil
import time
import re
import numpy as np
from pathlib import Path
from PIL import Image, ExifTags

from ..settings import *

def pattern_time(m):
    string, delim, time, hms1, delim1, hms2, delim2, hms3, hm1, delim3, hm2 = m
    if hms3:
        return f"{delim}%H{delim1}%M{delim2}%S"
    elif hm2:
        return f"{delim}%H{delim3}%M"
    else:
        return ""

def pattern_date_YMD(m):
    string, year, delim1, dm1, delim2, dm2 = m[:6]
    if delim1!=delim2: return False
    time = pattern_time(m[6:])
    return datetime.strptime(string, f"%Y{delim1}%m{delim2}%d{time}").timestamp()
    
def pattern_date_DMY_MDY(m):
    string, dm1, delim2, dm2, delim1, year = m[:6]
    if delim1!=delim2: return False
    dm1, dm2 = ("%m", "%d") if int(dm2)>12 else ("%d", "%m")
    time = pattern_time(m[6:])
    return datetime.strptime(string, f"{dm1}{delim1}{dm2}{delim2}%Y{time}").timestamp()

YEAR   = "(19[0-9]{2}|20[0-9]{2})"
DM     = "([0-9]{1,2})"
HMS    = "([0-9]{2})"
DELIM1 = "([-_\s]{1}|)"  # delimiters / and . should not be used in an URL
DELIM2 = "([-_:\s]{1}|)" # time part has an additional delimiter :
TIME   = "([-_\s]+|)("+HMS+DELIM2+HMS+DELIM2+HMS+"|"+HMS+DELIM2+HMS+")"
DATETIME_PATTERNS = {
    "("+YEAR+DELIM1+DM+DELIM1+DM+"("+TIME+"|))": pattern_date_YMD,
    "("+DM+DELIM1+DM+DELIM1+YEAR+"("+TIME+"|))": pattern_date_DMY_MDY,
}

class PhotoModel:
    
    db = None
    db_list = None
    
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        self.db.close()
        
    def __init__(self):
        if not os.path.isdir(DIR_PHOTOS):
            os.makedirs(DIR_PHOTOS)
        self.db = TinyDB(DB_FILE)
        self.table = self.db.table(DB_TABLE_PHOTOS)

    def count(self):
        return dict(
            registered   = len(self.list_registered()),
            unregistered = len(self.list_unregistered())
        )
    
    def get_dir(self, doc_id:int, variant_id:str=None):
        if variant_id:
            return f"{DIR_PHOTOS}/photo-{doc_id}/variant-{variant_id}"
        else:
            return f"{DIR_PHOTOS}/photo-{doc_id}"
    
    def _find_variant(self, doc:dict, variant_id:str=None):
        if variant_id is None:
            variant_id = doc['variant_id']
        for index, variant in enumerate(doc['variants']):
            if variant['variant_id'].startswith(variant_id):
                break
        else:
            raise Exception("Variant with the given ID could not be found:", variant_id)
        return index, variant
    
    def get_photo(self, doc_id:int, variant:bool=False, variant_id:str=None):
        doc = self.table.get(doc_id=doc_id)
        if variant or variant_id:
            doc['variant_index'], doc['variant'] = self._find_variant(doc, variant_id)
        return doc
        
    def get_variant(self, doc_id:int, variant_id:str=None):
        doc = self.table.get(doc_id=doc_id)
        index, variant = self._find_variant(doc, variant_id)
        return variant
        
    def update_variant(self, doc_id:int, variant_id:str, data:dict):
        Photo = Query()
        def update_variant(data, variant_id):
            def transform(doc):
                for i in range(len(doc['variants'])):
                    if doc['variants'][i]['variant_id'].startswith(variant_id):
                        break
                else:
                    raise Exception("Photo variant could not be found:", doc_id, variant_id)
                doc['variants'][i].update(data)
            return transform
        self.table.update(update_variant(data, variant_id), doc_ids=[int(doc_id)])
        
    def list_registered(self, variant:bool=False):
        docs = self.table.all()
        if variant:
            for i in range(len(docs)):
                doc[i]['variant_index'], doc[i]['variant'] = self._find_variant(doc[i])
        return docs
        
    def list_unregistered(self):
        Photo, Variant = Query(), Query()
        file_names = []
        for file_path in glob.glob(f"{DIR_IMPORT}/**", recursive=True):            
            if os.path.isdir(file_path):
                continue
            file_name = str(Path(file_path).relative_to(DIR_IMPORT))
            if self.table.count(Photo.variants.any(Variant.name_original==file_name)):
                continue
            file_names.append(file_name)
        return file_names

    def create_thumbnail(self, file_original:str, file_thumbnail:str):
        with Image.open(file_original) as photo:
            if photo.size[0]>photo.size[1]:
                photo = photo.resize((THUMBNAIL_SIZE, int(THUMBNAIL_SIZE*photo.size[1]/photo.size[0])))
            else:
                photo = photo.resize((int(THUMBNAIL_SIZE*photo.size[0]/photo.size[1]), THUMBNAIL_SIZE))
            with Image.new('RGB', (THUMBNAIL_SIZE,THUMBNAIL_SIZE), color='white') as thumb:
                thumb.paste(photo, (
                    int((THUMBNAIL_SIZE-photo.size[0])/2), 
                    int((THUMBNAIL_SIZE-photo.size[1])/2)
                ))
                thumb.save(file_thumbnail, THUMBNAIL_TYPE)

    def _variant_id(self, file_name:str):
        json_string = json.dumps({
            'name':      file_name,
            'timestamp': time.time()
        }, sort_keys=True)
        hash_object = hashlib.sha256()
        hash_object.update(json_string.encode())
        return hash_object.hexdigest()

    def _path_dates(self, file_original:str):
        dates = []
        for regexp, dtformat in DATETIME_PATTERNS.items():
            if ms := re.findall(regexp,file_original):
                for m in ms:
                    print(m)
                    if dt := dtformat(m):   
                        dates.append(dt)
        return dates

    def _image_info(self, file_original:str):
        # Extract general information
        data = dict(
            file_created  = os.path.getctime(file_original),
            file_modified = os.path.getmtime(file_original),
            file_size     = os.path.getsize(file_original),
            exif          = None,
        )
        with Image.open(file_original) as img:
            # Extract EXIF information
            if exif := img._getexif():
                data['exif'] = {ExifTags.TAGS[k]: str(v) for k, v in exif.items() if k in ExifTags.TAGS}
            # Get image resolution
            data['image_size'] = img.size
            data['image_format'] = img.format
        # Extract dates from image file path
        data['file_path_dates'] = self._path_dates(file_original)
        # Set the most relevat photo datetime
        if data['exif'] and 'DateTime' in data['exif']:
            data['datetime'] = datetime.strptime(data['exif']['DateTime'], FORMAT_DATE_EXIF).timestamp()
        elif data['exif'] and 'CreateDate' in data['exif']:
            data['datetime'] = datetime.strptime(data['exif']['CreateDate'], FORMAT_DATE_EXIF).timestamp()
        elif data['exif'] and 'DateTimeOriginal' in data['exif']:
            data['datetime'] = datetime.strptime(data['exif']['DateTimeOriginal'], FORMAT_DATE_EXIF).timestamp()
        elif data['file_path_dates']:
            data['datetime'] = float(min(data['file_path_dates']))
        else:
            data['datetime'] = float(data['file_created'])
        return data
    
    def add(self, file_name_original:str=None, doc_id:int=None):
        if doc_id is not None:
            file_names = self.list_unregistered()
            file_name_original = file_names[doc_id]
        elif not file_name_original:
            raise Exception("Filename or file index has to be set:", file_name_original, doc_id)
        file_original = f"{DIR_IMPORT}/{file_name_original}"
        if not os.path.isfile(file_original):
            raise Exception('Followng file is not present in the inport directory:', file_name_original)
        # create variant id
        variant_id = self._variant_id(file_name_original)
        # insert reccord into the database
        doc_id = self.table.insert({
            'variant_id': variant_id,
            'variants': [{
                'variant_id': variant_id,
                'name_original': file_name_original,
            } | self._image_info(file_original)]
        })
        # create reccord and variant directories
        dir_variant = self.get_dir(doc_id, variant_id)
        os.makedirs(dir_variant)
        # create a thumbnail image
        file_thumbnail = f"{dir_variant}/{THUMBNAIL_NAME}"
        self.create_thumbnail(file_original, file_thumbnail)
        # return document ID
        return doc_id
        
    def add_all(self):
        doc_ids = []
        file_names = self.list_unregistered()
        for file_name in file_names:
            doc_ids.append( self.add(file_name) )
        return doc_ids
        
    def remove(self, doc_id:int=None):
        # remove database reccord
        if self.table.contains(doc_id=doc_id):
            self.table.remove(doc_ids=[doc_id])
        # delete directory
        dir_photo = self.get_dir(doc_id)
        if os.path.isdir(dir_photo):
            shutil.rmtree(dir_photo)
        return doc_id

    def remove_all(self):
        doc_ids = []
        for doc in self.list_registered():
            doc_ids.append( self.remove( doc.doc_id ) )
        return doc_ids
        