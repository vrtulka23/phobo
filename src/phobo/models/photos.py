from tinydb import TinyDB, Query, where
import hashlib
import os
from datetime import datetime
import glob
import json
import shutil
import time
import numpy as np
from pathlib import Path
from PIL import Image, ExifTags

from ..settings import *

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
            file_name = str(Path(file_path).relative_to(DIR_IMPORT))
            if os.path.isdir(file_name):
                continue
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
        json_string = json.dumps({
            'name':      file_name_original,
            'timestamp': time.time()
        }, sort_keys=True)
        hash_object = hashlib.sha256()
        hash_object.update(json_string.encode())
        variant_id = hash_object.hexdigest()
        # insert reccord into the database
        file_name_registered = "original" + Path(file_name_original).suffix
        with Image.open(file_original) as img:
            if exif := img._getexif():
                exif = {ExifTags.TAGS[k]: str(v) for k, v in exif.items() if k in ExifTags.TAGS}
            else:
                exif = None
            image_size = img.size
        variant = {
            'variant_id': variant_id,
            'name': file_name_registered,
            'name_original': file_name_original,
            'file_created':  os.path.getctime(file_original),
            'file_modified': os.path.getmtime(file_original),
            'file_size': os.path.getsize(file_original),
            'image_size': image_size,
            'exif': exif,
        }
        doc_id = self.table.insert({
            'variant_id': variant_id,
            'variants': [variant]
        })
        # create reccord and variant directories
        dir_variant = self.get_dir(doc_id, variant_id)
        os.makedirs(dir_variant)
        # move imported file into the variant directory
        file_registered = f"{dir_variant}/{file_name_registered}"
        shutil.copy(file_original, file_registered)
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
        