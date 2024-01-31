from flask import Blueprint, render_template, jsonify
from flask import request, url_for, send_file
from datetime import datetime

from ..settings import *
from ..models.photos import PhotoModel

photo_page = Blueprint(
    'photo_page', 
    __name__,
    template_folder='templates'
)

def url_thumbnail(doc_id, variant_id):
    return url_for(
       'photo_page.file_thumbnail', 
        doc_id=doc_id, 
        variant_id=variant_id[:VARIANT_ID_CUT]
    )
def url_variant(doc_id, variant_id):
    return url_for(
        'photo_page.photo_preview',
        doc_id=doc_id,
        variant_id=variant_id[:VARIANT_ID_CUT],
    )
    
@photo_page.route('/photo')
def photo_view():
    
    with PhotoModel() as p:
        data = []
        for doc in p.list_registered():
            data.append(dict(
                file_path = url_thumbnail(doc.doc_id, doc['variant_id']),
                link = url_variant(doc.doc_id, doc['variant_id'])
            ))
    return render_template(
        PAGE_INDEX, 
        content_page = 'photo.html', 
        photo_list = data,
    )
    
@photo_page.route("/photo/<doc_id>/<variant_id>")
def photo_preview(doc_id, variant_id):
    
    with PhotoModel() as p:
        doc = p.get_photo(doc_id)
        variant = None
        for v in doc['variants']:
            if v['variant_id'].startswith(variant_id):
                variant = v
    
    dates = {     
        "File Created": datetime.fromtimestamp(variant['file_created']).strftime(FORMAT_DATE),
        "File Modified": datetime.fromtimestamp(variant['file_modified']).strftime(FORMAT_DATE),
    }
    if variant['exif']:
        tags = ['DateTime', 'ModifyDate', 'CreateDate', 'DateTimeOriginal','DateTimeDigitized']
        for tag in tags:
            if tag not in variant['exif']:
                continue
            dates[f"Exif {tag}"] = datetime.strptime(variant['exif'][tag], FORMAT_DATE_EXIF).strftime(FORMAT_DATE)

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
        url_overview = url_for('photo_page.photo_view'),
        dates = dates,
        variant_id = variant['variant_id'],
        file_path = variant['name_original'],
        file_size = sizeof_fmt(variant['file_size']),
        image_size = variant['image_size'],
        api_photo_data = url_for('photo_page.api_photo_data', doc_id=doc_id),
        api_variant_data = url_for('photo_page.api_variant_data', doc_id=doc_id, variant_id=variant_id),
    )
    
@photo_page.route("/file/thumbnail/<doc_id>/<variant_id>")
def file_thumbnail(doc_id, variant_id):
    with PhotoModel() as p:
        variant = p.get_variant(doc_id, variant_id)
        dir_variant = p.get_dir(doc_id, variant['variant_id'])
        file_path = f"{dir_variant}/{THUMBNAIL_NAME}"
    if os.path.isfile(file_path):
        return send_file(f"../../{file_path}", mimetype=THUMBNAIL_MIMETYPE)
    else:
        raise Exception("Thumbnail file could not be found:", file_path)
    
@photo_page.route("/api/photo/<doc_id>/data")
def api_photo_data(doc_id):
    with PhotoModel() as p:
        doc = p.get_photo(doc_id)
        variants = []
        for v in doc['variants']:
            variants.append(dict(
                file_path = url_thumbnail(doc_id, v['variant_id']), 
                variant_link = url_variant(doc_id, v['variant_id']),
            ))
    return jsonify(dict(
        variants = variants
    ))
    
@photo_page.route("/api/photo/<doc_id>/variant/<variant_id>/data")
def api_variant_data(doc_id, variant_id):
    with PhotoModel() as p:
        variant = p.get_variant(doc_id, variant_id)
    return jsonify(dict(
        url_image = url_thumbnail(doc_id, variant['variant_id']),
    ))