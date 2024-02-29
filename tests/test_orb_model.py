import pytest
import sys
sys.path.insert(1, 'src')
from PIL import Image
import numpy as np

from phobo.models.orb_model import ORBModel

def test_dump_load():
    file_image = 'tests/img/sample_400_600.jpeg'
    file_orb = 'tests/tmp/orb_data.pkl'
    im = Image.open(file_image).convert('L')
    im_data = np.asarray(im)
    with ORBModel() as orb:
        kp0,des0 = orb.dump(im_data, file_orb)
        kp1,des1 = orb.load(file_orb)
    assert np.all([kp0[i].angle==kp1[i].angle for i in range(len(kp0))])
    assert np.all([kp0[i].class_id==kp1[i].class_id for i in range(len(kp0))])
    assert np.all(des0==des1)

def test_comparision():
    pass
