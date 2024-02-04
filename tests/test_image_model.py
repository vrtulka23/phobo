import pytest
from datetime import datetime
import sys
sys.path.insert(1, 'src')

from phobo.models.image_model import ImageModel
from fixtures import *

def test_file_path_dates():
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
        with ImageModel(f"sub_{date_string}/image_{date_string}.jpg") as img:
            assert img.path_dates() == [
                    datetime.strptime(date_string, dtformat).timestamp(),
                    datetime.strptime(date_string, dtformat).timestamp(),
            ]
            
@pytest.mark.parametrize("sample_photo", [1], indirect=True)
def test_thumbnail(clear_data, sample_photo):
    # create a photo
    file_original = f"{DIR_IMPORT}/{sample_photo[0]}"
    file_thumbnail = f"{DIR_IMPORT}/thumbnail.png"
    with ImageModel(file_original) as img:
        img.thumbnail(file_thumbnail, {'rotation':90})
    # check if thumbnail exists and has correct size
    with Image.open(file_thumbnail) as img:
        assert img.size == (THUMBNAIL_SIZE, THUMBNAIL_SIZE)
