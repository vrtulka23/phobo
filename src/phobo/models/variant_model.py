from tinydb import TinyDB, Query, where

from .image_model import ImageModel
from ..settings import *

class VariantModel:

    doc: dict
    variant_id: str
    
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        pass
    
    def __init__(self, doc:dict, variant_id:str=None):
        self.doc = doc
        if variant_id is None:
            self.variant_id = self.doc['variant_id']
        else:
            self.variant_id = variant_id

    def data(self):
        for index, variant in enumerate(self.doc['variants']):
            if variant['variant_id'].startswith(self.variant_id):
                break
        else:
            raise Exception("Variant with the given ID could not be found:", self.variant_id)
        return variant

