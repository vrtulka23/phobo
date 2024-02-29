from tinydb import TinyDB, Query, where
from tinydb.operations import set
from tinydb.table import Document
from datetime import datetime
import shutil

from .image_model import ImageModel, ROTATIONS, MIRRORS
from ..settings import *

class VariantModel:

    variant_id: int = None
    
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        pass
    
    def __init__(self, variant_id:str=None):
        if variant_id is not None:
            self.variant_id = variant_id
            
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

        if data['exif'] and 'Orientation' in data['exif']:
            data['orientation'] = int(data['exif']['Orientation'])
        else:
            data['orientation'] = 1
            
        return data

    def add(self, file_name:str):
        file_original = self.file_original(file_name)
        if not os.path.isfile(file_original):
            raise Exception('Followng file is not present in the inport directory:', file_name)
        # add variant data to the database
        data = {
            'name_original': file_name,
            'rating_overall': 3,
            'rating_aesthetics': 3,
            'rating_emotions': 3,
            'rating_rarity': 3,
        } | self._image_info(file_original)
        with TinyDB(DB_VARIANTS) as db:
            variant_id = db.insert(data)
        # create variant directory
        dir_variant = self.dir_variant(variant_id)
        os.makedirs(dir_variant)
        # create a thumbnail image
        file_thumbnail = self.file_thumbnail(variant_id)
        with ImageModel(file_original) as img:
            dir_variant = self.dir_variant(variant_id)
            img.thumbnail(dir_variant, data['orientation'])
        return variant_id

    def remove(self, variant_id:int):
        with TinyDB(DB_VARIANTS) as db:
            db.remove(doc_ids=[variant_id])
        # delete variant directory
        dir_variant = self.dir_variant(variant_id)
        if os.path.isdir(dir_variant):
            shutil.rmtree(dir_variant)

    def get(self, variant_id:int):
        with TinyDB(DB_VARIANTS) as db:
            return db.get(doc_id=variant_id)

    def update(self, variant_id:int, data:dict):
        variant = self.get(variant_id)
        # modify new data
        if 'datetime' in data:
            try:
                data['datetime'] = datetime.strptime(data['datetime'], FORMAT_DATE).timestamp()
            except:
                raise Exception("Invalid datetime format:", data['datetime'], FORMAT_DATE)
        if 'rotation' in data or 'mirror' in data:
            rotation = ROTATIONS[str(variant['orientation'])]
            mirror   = MIRRORS[str(variant['orientation'])]
            if 'rotation' in data:
                rotation += data['rotation']
                if rotation<0: rotation += 360
                if rotation>=360: rotation -= 360
                del data['rotation']
            if 'mirror' in data:
                mirror = data['mirror']
                del data['mirror']
            for i in range(1,9):
                if ROTATIONS[str(i)]==rotation and MIRRORS[str(i)]==mirror:
                    data['orientation'] = i
                    break
            else:
                raise Exception('Orientation could not be determined', data['rotation'], data['mirror'])
        # update document
        with TinyDB(DB_VARIANTS) as db:
            variant = db.get(doc_id=variant_id)
            variant.update(data)
            db.update(variant, doc_ids=[int(variant_id)])
            
        if 'orientation' in data:
            file_original = self.file_original(variant['name_original'])
            file_thumbnail = self.file_thumbnail(variant_id)
            with ImageModel(file_original) as img:
                dir_variant = self.dir_variant(variant_id)
                img.thumbnail(dir_variant, variant['orientation'])
        
    def dir_variant(self, variant_id:int):
        return f"{DIR_PHOTOS}/variant-{variant_id}"
    
    def file_thumbnail(self, variant_id:int):
        dir_variant = self.dir_variant(variant_id)
        file_thumbnail = f"{dir_variant}/{THUMBNAIL_NAME}"
        return file_thumbnail

    def file_comparison(self, variant_id:int):
        dir_variant = self.dir_variant(variant_id)
        file_comparison = f"{dir_variant}/{COMPARISON_NAME}"
        return file_comparison
    
    def file_original(self, file_name:str):
        return f"{DIR_IMPORT}/{file_name}"
        
