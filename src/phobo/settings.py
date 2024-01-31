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
DIR_IMPORT = settings.DIR_IMPORT
DIR_PHOBO = settings.DIR_PHOBO
DIR_PHOTOS = f"{DIR_PHOBO}/photos"

PAGE_INDEX = "index.html"                 # main page template

DB_NAME = "phobo_database.json"           # database file name
DB_FILE= f"{DIR_PHOBO}/{DB_NAME}"         # path to the database file
DB_TABLE_PHOTOS = 'photos'                # database table containing photos

VARIANT_ID_CUT = 10                       # number of variant_id letters that are show in url

FORMAT_DATE      = "%Y-%m-%d %H:%M:%S"    # output date and time format
FORMAT_DATE_EXIF = "%Y:%m:%d %H:%M:%S"    # date and time formation exif data

THUMBNAIL_SIZE     = 400                  # resolution of a thumbnail image
THUMBNAIL_NAME     = "thumbnail.png"      # thumbnail image name
THUMBNAIL_TYPE     = "PNG"                # PIL image type
THUMBNAIL_MIMETYPE = 'image/png'          # image mime type