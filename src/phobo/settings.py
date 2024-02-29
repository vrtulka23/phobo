import os
from dynaconf import Dynaconf

# import environmental settings
settings = Dynaconf(
    envvar_prefix="PHOBO",
    settings_files=["settings.toml"],
    environments=True,
    load_dotenv=True,
    env_switcher="PHOBO_ENV"
)

# prepare rest of the settings
DIR_IMPORT         = settings.DIR_IMPORT
DIR_PHOBO          = settings.DIR_PHOBO
DIR_PHOTOS         = f"{DIR_PHOBO}/photos"

PAGE_INDEX         = "index.html"                # main page template

DB_PHOTOS          = f"{DIR_PHOBO}/db_photos.json"
DB_VARIANTS        = f"{DIR_PHOBO}/db_variants.json"

VARIANT_ID_CUT     = 10                          # number of variant_id letters that are show in url

SUPPORTED_FORMATS  = ['PNG','JPEG','GIF','PPM','TIFF','BMP','HEIF']

FORMAT_DATE        = "%Y-%m-%d %H:%M:%S"         # output date and time format
FORMAT_DATE_EXIF   = "%Y:%m:%d %H:%M:%S"         # date and time formation exif data

THUMBNAIL_SIZE     = 400                         # resolution of a thumbnail image
THUMBNAIL_NAME     = "thumbnail.png"             # thumbnail image name
THUMBNAIL_TYPE     = "PNG"                       # PIL image type
THUMBNAIL_MIMETYPE = 'image/png'                 # image mime type

COMPARISON_NAME    = "comparison.png"
ORB_DATA_FILE      = "orb_data.pkl"
ORB_THRESHOLD      = 0.01

VUE_MIMETYPE       = 'text/javascript'
