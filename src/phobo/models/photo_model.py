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
from PIL import Image, ExifTags, ImageOps
from pillow_heif import register_heif_opener
register_heif_opener()

from .variant_model import VariantModel
from .image_model import ImageModel
from ..settings import *

class PhotoModel:
    
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        pass
        
    def __init__(self):
        if not os.path.isdir(DIR_PHOTOS):
            os.makedirs(DIR_PHOTOS)

    def count(self):
        registered = 0
        unregistered = 0
        for data in self.list_files():
            if data['registered']:
                registered += 1
            else:
                unregistered += 1
        return dict(
            registered   = registered,
            unregistered = unregistered,
        )
    
    def get_photo(self, photo_id:int=None, variant_id:int=None):
        with TinyDB(DB_PHOTOS) as db:
            if variant_id is None:
                return db.get(doc_id=photo_id)
            elif photo_id is None:
                Photo = Query()
                def has_variant(val, m):
                    return m in val
                return db.get(Photo.variants.test(has_variant, variant_id))
            else:
                raise Exception("Either photo_id or variant_id has to be given:", photo_id, variant_id)

    def list_photos(self):
        with TinyDB(DB_PHOTOS) as db:
            return db.all()
            
    def list_files(self):
        Variant = Query()
        file_list = []
        var = TinyDB(DB_VARIANTS)
        for file_path in glob.glob(f"{DIR_IMPORT}/**", recursive=True):
            if os.path.isdir(file_path):
                continue
            with ImageModel(file_path) as img:
                if img.im is None:
                    continue
                else:
                    image_format = img.image_format
            file_name = str(Path(file_path).relative_to(DIR_IMPORT))
            if doc:=var.get(Variant.name_original==file_name):
                file_list.append(dict(
                    registered=True,
                    file_name=file_name,
                    image_format=image_format,
                    variant_id = doc.doc_id
                ))
            else:
                file_list.append(dict(
                    registered=False,
                    file_name=file_name,
                    image_format=image_format,
                ))
        var.close()
        return file_list

    def add_from_variant(self, variant_id:int):
        with TinyDB(DB_PHOTOS) as db:
            doc_id = db.insert({
                'variant_id': variant_id,
                'variants': [variant_id],
                'comparison': {
                    'orb': 0.1,
                },
            })
        # return document ID
        return doc_id        
    
    def add(self, file_name_original:str=None, doc_id:int=None):
        if doc_id is not None:
            file_list = self.list_files()
            file_name_original = file_list[doc_id]['file_name']
        elif not file_name_original:
            raise Exception("Filename or file index has to be set:", file_name_original, doc_id)
        # create variant id
        with VariantModel() as var:
            variant_id = var.add(file_name_original)
        return self.add_from_variant(variant_id)
        
    def add_all(self):
        doc_ids = []
        for item in self.list_files():
            if item['registered']:
                continue
            doc_ids.append( self.add(item['file_name']) )
        return doc_ids
    
    def remove_variant(self, variant_id:int=None):
        # Update or remove photo reccord
        photo = self.get_photo(variant_id=variant_id)
        with TinyDB(DB_PHOTOS) as db:
            if len(photo['variants'])>1:
                photo['variants'].remove(variant_id)
                if photo['variant_id'] == variant_id:
                    photo['variant_id'] = photo['variants'][0]
                db.update(photo, doc_ids=[photo.doc_id])
            else:
                db.remove(doc_ids=[photo.doc_id])
        # Remove variant
        with VariantModel() as var:
            var.remove(variant_id)
        return None

    def remove_all_variants(self):
        doc_ids = []
        for item in self.list_files():
            if not item['registered']:
                continue
            doc_ids.append( self.remove_variant( item['variant_id'] ) )
        return doc_ids
        
    def remove_photo(self, photo_id:int=None):
        # remove database reccord
        with TinyDB(DB_PHOTOS) as db:
            db.remove(doc_ids=[int(photo_id)])        
        return None
    
    def update(self, photo_id:int, data:dict):
        with TinyDB(DB_PHOTOS) as db:
            photo = db.get(doc_id=photo_id)
            photo.update(data)
            db.update(photo, doc_ids=[int(photo_id)])
