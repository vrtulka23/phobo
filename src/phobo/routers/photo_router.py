from flask import Blueprint, render_template, jsonify
from flask import request, url_for, send_file
from datetime import datetime

from ..settings import *
from ..models.photo_model import PhotoModel
from ..models.variant_model import VariantModel
from ..models.image_model import ROTATIONS, MIRRORS

PhotoRouter = Blueprint(
    'PhotoRouter', 
    __name__,
    template_folder='templates'
)

def url_thumbnail(variant_id:int):
    return url_for(
       'PhotoRouter.api_file_thumbnail', 
        variant_id=variant_id
    )
def url_variant(doc_id:int, variant_id:int):
    return url_for(
        'PhotoRouter.photo_preview',
        doc_id=doc_id,
        variant_id=variant_id,
    )
    
@PhotoRouter.route('/photo')
def photo_view():
    
    with PhotoModel() as p:
        data = []
        for doc in p.list_photos():
            data.append(dict(
                file_path = url_thumbnail(doc['variant_id']),
                link = url_variant(doc.doc_id, doc['variant_id']),
                num_variants = len(doc['variants']),
            ))
    return render_template(
        PAGE_INDEX, 
        content_page = 'photo.html', 
        photo_list = data,
    )
    
@PhotoRouter.route("/photo-<doc_id>/variant-<variant_id>")
def photo_preview(doc_id:int, variant_id:int):
    
    with PhotoModel() as p:
        docs = p.list_photos()
    variant = None
    for d,doc in enumerate(docs):
        if int(doc.doc_id)!=int(doc_id):
            continue
        with VariantModel() as var:
            variant = var.get(variant_id)
        break
    url_previous_photo = url_variant(docs[d-1].doc_id, docs[d-1]['variant_id']) if (d-1)>=0 else None
    url_next_photo = url_variant(docs[d+1].doc_id, docs[d+1]['variant_id']) if (d+1)<len(docs) else None
    
    dates = [
        ["File Created", datetime.fromtimestamp(variant['file_created']).strftime(FORMAT_DATE)],
        ["File Modified", datetime.fromtimestamp(variant['file_modified']).strftime(FORMAT_DATE)],
    ]
    if variant['exif']:
        tags = ['DateTime', 'ModifyDate', 'CreateDate', 'DateTimeOriginal','DateTimeDigitized']
        for tag in tags:
            if tag not in variant['exif'] or variant['exif'][tag]=='':
                continue
            dates.append([f"Exif {tag}", datetime.strptime(variant['exif'][tag], FORMAT_DATE_EXIF).strftime(FORMAT_DATE)])
    if variant['file_path_dates']:
        for ts, timestamp in enumerate(variant['file_path_dates']):
            dates.append([f"Path DateTime #{ts+1:d}", datetime.fromtimestamp(timestamp).strftime(FORMAT_DATE)])
    dates = [[f"datetime_{d}"]+date for d,date in enumerate(dates)]

    def sizeof_fmt(num, suffix="B"):
        for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Yi{suffix}"
    
    return render_template(
        PAGE_INDEX, 
        content_page = 'photo_preview.html', 
        doc_id = doc_id,
        url_overview = url_for('PhotoRouter.photo_view'),
        url_previous_photo = url_previous_photo,
        url_next_photo = url_next_photo,
        url_photo_comparison = url_for('ComparisonRouter.photo_comparison', doc_id=doc_id),
        dates = dates,
        variant_id = variant_id,
        file_path = variant['name_original'],
        file_size = sizeof_fmt(variant['file_size']),
        image_size = variant['image_size'],
        image_format = variant['image_format'],
        api_file_original = url_for('PhotoRouter.api_file_original', variant_id=variant_id),
        api_photo_data    = url_for('PhotoRouter.api_photo_get', doc_id=doc_id),
        api_variant_get   = url_for('PhotoRouter.api_variant_get', variant_id=variant_id),
        api_variant_set   = url_for('PhotoRouter.api_variant_set', variant_id=variant_id),
    )
    
@PhotoRouter.route("/api/imports/<file_name>")
def api_imports(file_name):
    file_path = f"{DIR_IMPORT}/{file_name}"
    if os.path.isfile(file_path):
        if file_path[0]=='/':
            return send_file(file_path)
        else:
            return send_file(f"../../{file_path}")
    else:
        raise Exception("File could not be found:", file_path)

@PhotoRouter.route("/api/variant-<variant_id>/file/original")
def api_file_original(variant_id:int):
    with VariantModel() as var:
        variant = var.get(variant_id)
        file_path = var.file_original(variant['name_original'])
    if os.path.isfile(file_path):
        if file_path[0]=='/':
            return send_file(file_path)
        else:
            return send_file(f"../../{file_path}")
    else:
        raise Exception("Original file could not be found:", file_path)
    
@PhotoRouter.route("/api/variant-<variant_id>/file/thumbnail")
def api_file_thumbnail(variant_id:int):
    with VariantModel() as var:
        variant = var.get(variant_id)
        file_path = var.file_thumbnail(variant_id)
    if os.path.isfile(file_path):
        return send_file(f"../../{file_path}", mimetype=THUMBNAIL_MIMETYPE)
    else:
        raise Exception("Thumbnail file could not be found:", file_path)
    
@PhotoRouter.route("/api/photo-<doc_id>/get")
def api_photo_get(doc_id):
    with PhotoModel() as p:
        doc = p.get_photo(doc_id)
        variants = []
        for variant_id in doc['variants']:
            variants.append(dict(
                file_path = url_thumbnail(variant_id), 
                variant_link = url_variant(doc_id, variant_id),
            ))
    return jsonify(dict(
        variants = variants
    ))
    
@PhotoRouter.route("/api/variant-<variant_id>/get")
def api_variant_get(variant_id:int):
    with VariantModel() as var:
        variant = var.get(variant_id)
    return jsonify(dict(
        url_image = url_thumbnail(variant_id),
        datetime = datetime.fromtimestamp(variant['datetime']).strftime(FORMAT_DATE),
        rotation = ROTATIONS[str(variant['orientation'])],
        mirror = MIRRORS[str(variant['orientation'])],
        ratings_overall = variant['rating_overall'],
        ratings_aesthetics = variant['rating_aesthetics'],
        ratings_emotions = variant['rating_emotions'],
        ratings_rarity = variant['rating_rarity'],
    ))
    
@PhotoRouter.route("/api/variant-<variant_id>/set", methods=['POST'])
def api_variant_set(variant_id:int):
    with VariantModel() as var:
        var.update(variant_id, request.json)
    return api_variant_get(variant_id)
