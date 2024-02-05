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
        return dict(
            registered   = len(self.list_registered()),
            unregistered = len(self.list_unregistered())
        )
    
    def get_dir(self, doc_id:int, variant_id:str=None):
        if variant_id:
            return f"{DIR_PHOTOS}/photo-{doc_id}/variant-{variant_id}"
        else:
            return f"{DIR_PHOTOS}/photo-{doc_id}"
    
    def get_photo(self, doc_id:int):
        with TinyDB(DB_PHOTOS) as db:
            return db.get(doc_id=doc_id)
        
    def update_variant(self, doc_id:int, variant_id:str, data:dict):
        # find variant and its current index
        with TinyDB(DB_PHOTOS) as db:
            doc = db.get(doc_id=doc_id)
        for i,variant in enumerate(doc['variants']):
            if variant['variant_id'].startswith(variant_id):
                break
        else:
            raise Exception("Photo variant could not be found:", doc_id, variant_id)
        # modify new data
        if 'datetime' in data:
            try:
                data['datetime'] = datetime.strptime(data['datetime'], FORMAT_DATE).timestamp()
            except:
                raise Exception("Invalid datetime format:", data['datetime'], FORMAT_DATE)
        if 'rotation' in data:
            data['rotation'] += doc['variants'][i]['rotation']
            if data['rotation']<0: data['rotation'] += 360
            if data['rotation']>=360: data['rotation'] -= 360
        # update document
        Photo = Query()
        def update_variant(data, i):
            def transform(doc):
                doc['variants'][i].update(data)
            return transform
        with TinyDB(DB_PHOTOS) as db:
            db.update(update_variant(data, i), doc_ids=[int(doc_id)])
            if 'rotation' in data or 'flip_vertically' in data or 'flip_horizontally' in data:
                doc = db.get(doc_id=doc_id)
                with VariantModel(doc, variant_id) as var:
                    variant = var.data()
                file_original = f"{DIR_IMPORT}/{variant['name_original']}"
                dir_variant = self.get_dir(doc_id, variant['variant_id'])
                file_thumbnail = f"{dir_variant}/{THUMBNAIL_NAME}"
                with ImageModel(file_original) as img:
                    img.thumbnail(file_thumbnail, {
                        'rotation': variant['rotation'],
                        'flip_vertically': variant['flip_vertically'],
                        'flip_horizontally': variant['flip_horizontally'],
                    })
        
    def list_registered(self, variant:bool=False):
        with TinyDB(DB_PHOTOS) as db:
            docs = db.all()
        if variant:
            for i in range(len(docs)):
                doc[i]['variant_index'], doc[i]['variant'] = self._find_variant(doc[i])
        return docs
        
    def list_unregistered(self):
        Photo, Variant = Query(), Query()
        file_list = []
        with TinyDB(DB_PHOTOS) as db:
            for file_path in glob.glob(f"{DIR_IMPORT}/**", recursive=True):            
                if os.path.isdir(file_path):
                    continue
                with ImageModel(file_path) as img:
                    if img.im is None:
                        continue
                    else:
                        image_format = img.image_format
                file_name = str(Path(file_path).relative_to(DIR_IMPORT))
                if db.count(Photo.variants.any(Variant.name_original==file_name)):
                    continue
                file_list.append(dict(file_name=file_name, image_format=image_format))
        return file_list

    def _variant_id(self, file_name:str):
        json_string = json.dumps({
            'name':      file_name,
            'timestamp': time.time()
        }, sort_keys=True)
        hash_object = hashlib.sha256()
        hash_object.update(json_string.encode())
        return hash_object.hexdigest()
       
    def _image_info(self, file_original:str):
        # Get basic image data
        with ImageModel(file_original) as img:
            data = dict(
                image_size      = img.image_size,
                image_format    = img.image_format,
                file_created    = img.file_created,
                file_modified   = img.file_modified,
                file_size       = img.file_size,
                exif            = img.exif_data(),
                file_path_dates = img.path_dates(),
            )
        # Set the most relevat photo datetime
        if data['exif'] and 'DateTime' in data['exif'] and data['exif']['DateTime']:
            data['datetime'] = datetime.strptime(data['exif']['DateTime'], FORMAT_DATE_EXIF).timestamp()
        elif data['exif'] and 'CreateDate' in data['exif'] and data['exif']['CreateDate']:
            data['datetime'] = datetime.strptime(data['exif']['CreateDate'], FORMAT_DATE_EXIF).timestamp()
        elif data['exif'] and 'DateTimeOriginal' in data['exif'] and data['exif']['DateTimeOriginal']:
            data['datetime'] = datetime.strptime(data['exif']['DateTimeOriginal'], FORMAT_DATE_EXIF).timestamp()
        elif data['file_path_dates']:
            data['datetime'] = float(min(data['file_path_dates']))
        else:
            data['datetime'] = float(data['file_created'])
        return data
    
    def add(self, file_name_original:str=None, doc_id:int=None):
        if doc_id is not None:
            file_list = self.list_unregistered()
            file_name_original = file_list[doc_id]['file_name']
        elif not file_name_original:
            raise Exception("Filename or file index has to be set:", file_name_original, doc_id)
        file_original = f"{DIR_IMPORT}/{file_name_original}"
        if not os.path.isfile(file_original):
            raise Exception('Followng file is not present in the inport directory:', file_name_original)
        # create variant id
        variant_id = self._variant_id(file_name_original)
        # insert reccord into the database
        with TinyDB(DB_PHOTOS) as db:
            doc_id = db.insert({
                'variant_id': variant_id,
                'variants': [{
                    'variant_id': variant_id,
                    'name_original': file_name_original,
                    'rotation': 0,
                    'flip_vertically': False,
                    'flip_horizontally': False,
                } | self._image_info(file_original)]
            })
        # create photos and variant directories
        dir_variant = self.get_dir(doc_id, variant_id)
        os.makedirs(dir_variant)
        # create a thumbnail image
        file_thumbnail = f"{dir_variant}/{THUMBNAIL_NAME}"
        with ImageModel(file_original) as img:
            img.thumbnail(file_thumbnail)
        # return document ID
        return doc_id
        
    def add_all(self):
        doc_ids = []
        file_list = self.list_unregistered()
        for item in file_list:
            doc_ids.append( self.add(item['file_name']) )
        return doc_ids
        
    def remove(self, doc_id:int=None):
        # remove database reccord
        with TinyDB(DB_PHOTOS) as db:
            if db.contains(doc_id=doc_id):
                db.remove(doc_ids=[doc_id])
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
        
