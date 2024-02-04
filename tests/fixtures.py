from PIL import Image
import numpy 
import os
import pytest
import shutil
import sys
sys.path.insert(1, 'src')

from phobo.settings import *

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
        im.save(file_path)
    return file_names  
