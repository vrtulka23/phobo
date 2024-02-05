from tinydb import TinyDB, Query
from datetime import datetime
import pytest
import os
import sys
sys.path.insert(1, 'src')

from phobo.settings import *
from phobo.models.photo_model import PhotoModel
from fixtures import *

def test_initialisation(clear_data):
    PhotoModel()
    assert os.path.isdir(DIR_PHOBO)
    assert os.path.isdir(DIR_PHOTOS)
    
def check_added_photo(doc_id):
    # test data in a database
    with TinyDB(DB_PHOTOS) as db:
        assert db.contains(doc_id=doc_id)
        doc = db.get(doc_id=doc_id)
        assert len(doc['variants'])==1
        variant = doc['variants'][0]
        dir_variant = f"{DIR_PHOTOS}/photo-{doc_id}/variant-{doc['variant_id']}"
        assert variant['variant_id'] == doc['variant_id']
        assert variant['name_original'].startswith("sample")
        assert os.path.isfile(f"{dir_variant}/{THUMBNAIL_NAME}")

def check_removed_photo(doc_id):
    # test if reccord is deleted
    with TinyDB(DB_PHOTOS) as db:
        assert not db.contains(doc_id=doc_id)
    # test if photo files are deleted
    assert not os.path.isdir(f"{DIR_PHOTOS}/photo-{doc_id}")

@pytest.mark.parametrize("sample_photo", [1], indirect=True)
def test_add_remove(clear_data, sample_photo):
    # create a photo
    with PhotoModel() as pm:
        doc_id = pm.add(sample_photo[0])
    check_added_photo(doc_id)
    # remove a photo
    with PhotoModel() as pm:
        pm.remove(doc_id)
    check_removed_photo(doc_id)
    
@pytest.mark.parametrize("sample_photo", [3], indirect=True)
def test_add_remove_all(clear_data, sample_photo):
    # create multiple photos
    with PhotoModel() as pm:
        doc_ids = pm.add_all()
    assert len(doc_ids)==3
    for doc_id in doc_ids:
        check_added_photo(doc_id)
    # remove multiple photos
    with PhotoModel() as pm:
        doc_ids = pm.remove_all()
    assert len(doc_ids)==3
    for doc_id in doc_ids:
        check_removed_photo(doc_id)

@pytest.mark.parametrize("sample_photo", [3], indirect=True)
def test_counts(clear_data, sample_photo):
    with PhotoModel() as pm:
        doc_ids = pm.add(sample_photo[0])
        assert len(pm.list_registered()) == 1
        assert len(pm.list_unregistered()) == 2
    

@pytest.mark.parametrize("sample_photo", [1], indirect=True)
def test_get_photo(clear_data, sample_photo):
    # create a photo
    with PhotoModel() as pm:
        doc_id = pm.add(sample_photo[0])
        doc = pm.get_photo(doc_id)
        assert doc.doc_id == doc_id        

@pytest.mark.parametrize("sample_photo", [1], indirect=True)
def test_update_variant(clear_data, sample_photo):
    # create a photo
    with PhotoModel() as p:
        doc_id = p.add(sample_photo[0])
        doc = p.get_photo(doc_id)
        p.update_variant(doc_id, doc['variant_id'], {'datetime':'2023-11-23 12:34:00'})
        doc = p.get_photo(doc_id)
        assert doc['variants'][0]['datetime'] == 1700739240.0
        
