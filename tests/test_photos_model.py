import numpy 
from PIL import Image
from tinydb import TinyDB, Query
from datetime import datetime
import glob
import pytest
import os
import shutil
import sys
sys.path.insert(1, 'src')

from phobo.settings import *
from phobo.models.photos import PhotoModel, DATETIME_PATTERNS

@pytest.fixture
def clear_data():
    if os.environ.get('PHOBO_ENV') != "pytest":
        raise Exception('Wrong environment settings:', os.environ.get('PHOBO_ENV'))
    if os.path.isdir(DIR_PHOBO):
        shutil.rmtree(DIR_PHOBO)

@pytest.fixture
def sample_photo(request):
    count = request.param
    if os.environ.get('PHOBO_ENV') != "pytest":
        raise Exception('Wrong environment settings:', os.environ.get('PHOBO_ENV'))
    if not os.path.isdir(DIR_IMPORT):
        os.makedirs(DIR_IMPORT, exist_ok=True)
    imarray = numpy.random.rand(100,200,3) * 255
    im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')
    file_names = [f"sample{i}.png" for i in range(count)]
    for i in range(count):
        file_path = f"{DIR_IMPORT}/{file_names[i]}"
        print(file_path)
        im.save(file_path)
    return file_names  

def test_initialisation(clear_data):
    PhotoModel()
    assert os.path.isdir(DIR_PHOBO)
    assert os.path.isdir(DIR_PHOTOS)
    assert os.path.isfile(DB_FILE)
    
def check_added_photo(doc_id):
    # test data in a database
    with TinyDB(DB_FILE) as db:
        table = db.table(DB_TABLE_PHOTOS)
        assert table.contains(doc_id=doc_id)
        doc = table.get(doc_id=doc_id)
        assert len(doc['variants'])==1
        variant = doc['variants'][0]
        dir_variant = f"{DIR_PHOTOS}/photo-{doc_id}/variant-{doc['variant_id']}"
        assert variant['variant_id'] == doc['variant_id']
        assert variant['name_original'].startswith("sample")
        assert variant['name'] == "original.png"
        assert os.path.isfile(f"{dir_variant}/{variant['name']}")
        assert os.path.isfile(f"{dir_variant}/{THUMBNAIL_NAME}")

def check_removed_photo(doc_id):
    # test if reccord is deleted
    with TinyDB(DB_FILE) as db:
        table = db.table(DB_TABLE_PHOTOS)
        assert not table.contains(doc_id=doc_id)
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
        
def test_file_path_dates():
    with PhotoModel() as p:
        examples = {
            # YMD
            "2023-03-13": "%Y-%m-%d", # different delimiters
            "2023_03_13": "%Y_%m_%d", 
            "2023 03 13": "%Y %m %d", 
            "20230313":   "%Y%m%d", 
            # DMY & MDY
            "13-02-2023": "%d-%m-%Y", # DMY
            "03-02-2023": "%d-%m-%Y", # DMY if not specified
            "03-13-2023": "%m-%d-%Y", # MDY if date higher than 12
            # single digit month and date
            "2023-3-4":   "%Y-%m-%d",
            # YMD HM
            "2023-03-13 12:33": "%Y-%m-%d %H:%M", # different delimiters
            "2023-03-13 12-33": "%Y-%m-%d %H-%M", 
            "2023-03-13 12_33": "%Y-%m-%d %H_%M", 
            "2023-03-13 12 33": "%Y-%m-%d %H %M", 
            "2023-03-13 1233":  "%Y-%m-%d %H%M", 
            # YMD HMS
            "2023-03-13 12:33:34": "%Y-%m-%d %H:%M:%S",
            # spacing between date and time
            "2023-03-13__12:33:34": "%Y-%m-%d__%H:%M:%S",
        }
        for date_string, dtformat in examples.items():
            print(date_string, dtformat)
            assert p._path_dates(f"sub_{date_string}/image_{date_string}.jpg") == [
                    datetime.strptime(date_string, dtformat).timestamp(),
                    datetime.strptime(date_string, dtformat).timestamp(),
            ]

@pytest.mark.parametrize("sample_photo", [1], indirect=True)
def test_update_variant(clear_data, sample_photo):
    # create a photo
    with PhotoModel() as p:
        doc_id = p.add(sample_photo[0])
        doc = p.get_photo(doc_id)
        p.update_variant(doc_id, doc['variant_id'], {'datetime':'changed'})
        doc = p.get_photo(doc_id)
        assert doc['variants'][0]['datetime'] == 'changed'
        
