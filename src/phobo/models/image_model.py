from pathlib import Path
import re
import os
import numpy as np
from datetime import datetime
from PIL import Image, ExifTags, ImageOps
from pillow_heif import register_heif_opener
register_heif_opener()

from ..settings import *
from .orb_model import ORBModel

ROTATIONS = {"1":0,"2":180,"3":180,"4":0,"5":90,"6":90,"7":270,"8":270}
MIRRORS = {"1":False,"2":True,"3":False,"4":True,"5":True,"6":False,"7":True,"8":False}

class ImageModel:

    file_path: str
    im: Image = None
    image_format: str = None
    image_size: str = None
    file_created: float = None
    file_modified: float = None
    file_size: float = None
    
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        if self.im:
            self.im.close()
        
    def __init__(self, file_path:str):
        self.file_path     = file_path
        try:
            im = Image.open(file_path)
            if im.format in SUPPORTED_FORMATS:
                self.im            = im
                self.image_format  = im.format
                self.image_size    = im.size
                self.file_created  = os.path.getctime(file_path)
                self.file_modified = os.path.getmtime(file_path)
                self.file_size     = os.path.getsize(file_path)
            else:
                im.close()
        except:
            pass

    def thumbnail(self, dir_variant:str, orientation:int):
        # resize original image
        if self.im.size[0]>self.im.size[1]:
            size1 = THUMBNAIL_SIZE
            size2 = int(THUMBNAIL_SIZE*self.im.size[1]/self.im.size[0])
            self.im = self.im.resize((size1, size2))
        else:
            size1 = int(THUMBNAIL_SIZE*self.im.size[0]/self.im.size[1])
            size2 = THUMBNAIL_SIZE
            self.im = self.im.resize((size1, size2))
        # retrieve feature detection data
        im = np.asarray(self.im.convert('L'))
        with ORBModel() as orb:
            orb.dump(im, f"{dir_variant}/{ORB_DATA_FILE}")
        # create rescaled version for comparison
        im = self.im.resize((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
        if MIRRORS[str(orientation)]:
            im = ImageOps.mirror(im)
        if ROTATIONS[str(orientation)]:
            im = im.rotate(-ROTATIONS[str(orientation)])
        im.convert('L').save(f"{dir_variant}/{COMPARISON_NAME}", "PNG")
        # create thumbnail on a white background
        with Image.new('RGB', (THUMBNAIL_SIZE,THUMBNAIL_SIZE), color='white') as thumb:
            thumb.paste(self.im, (
                int((THUMBNAIL_SIZE-self.im.size[0])/2), 
                int((THUMBNAIL_SIZE-self.im.size[1])/2)
            ))
            if MIRRORS[str(orientation)]:
                thumb = ImageOps.mirror(thumb)
            if ROTATIONS[str(orientation)]:
                thumb = thumb.rotate(-ROTATIONS[str(orientation)])
            thumb.save(f"{dir_variant}/{THUMBNAIL_NAME}", THUMBNAIL_TYPE)

    def exif_data(self):
        if self.im.format=='HEIF':
            if exif := self.im.getexif():
                return {ExifTags.TAGS[k]: str(v) for k, v in exif.items() if k in ExifTags.TAGS}
        elif exif := self.im._getexif():
            return {ExifTags.TAGS[k]: str(v) for k, v in exif.items() if k in ExifTags.TAGS}
        return None

    def _pattern_time(self, m):
        string, delim, time, hms1, delim1, hms2, delim2, hms3, hm1, delim3, hm2 = m
        if hms3:
            return f"{delim}%H{delim1}%M{delim2}%S"
        elif hm2:
            return f"{delim}%H{delim3}%M"
        else:
            return ""

    def _pattern_date_YMD(self, m):
        string, year, delim1, dm1, delim2, dm2 = m[:6]
        if delim1!=delim2: return False
        time = self._pattern_time(m[6:])
        return datetime.strptime(string, f"%Y{delim1}%m{delim2}%d{time}").timestamp()

    def _pattern_date_DMY_MDY(self, m):
        string, dm1, delim2, dm2, delim1, year = m[:6]
        if delim1!=delim2: return False
        dm1, dm2 = ("%m", "%d") if int(dm2)>12 else ("%d", "%m")
        time = self._pattern_time(m[6:])
        return datetime.strptime(string, f"{dm1}{delim1}{dm2}{delim2}%Y{time}").timestamp()
    
    def path_dates(self):
        YEAR   = "(19[0-9]{2}|20[0-9]{2})"
        DM     = "([0-9]{1,2})"
        HMS    = "([0-9]{2})"
        DELIM1 = "([-_\s]{1}|)"  # delimiters / and . should not be used in an URL
        DELIM2 = "([-_:\s]{1}|)" # time part has an additional delimiter :
        TIME   = "([-_\s]+|)("+HMS+DELIM2+HMS+DELIM2+HMS+"|"+HMS+DELIM2+HMS+")"
        DATETIME_PATTERNS = {
            "("+YEAR+DELIM1+DM+DELIM1+DM+"("+TIME+"|))": self._pattern_date_YMD,
            "("+DM+DELIM1+DM+DELIM1+YEAR+"("+TIME+"|))": self._pattern_date_DMY_MDY,
        }
        dates = []
        for regexp, dtformat in DATETIME_PATTERNS.items():
            if ms := re.findall(regexp, self.file_path):
                for m in ms:
                    if dt := dtformat(m):   
                        dates.append(dt)
        return dates
