from flask import Blueprint, render_template, jsonify, request, url_for
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error
from PIL import Image
import numpy as np
from scinumtools import RowCollector
import cv2

from ..settings import *
from ..models.photo_model import PhotoModel
from ..models.variant_model import VariantModel
from ..models.orb_model import ORBModel

# ORB: https://stackoverflow.com/questions/50217364/sift-comparison-calculate-similarity-score-python
#      https://mikhail-kennerley.medium.com/a-comparison-of-sift-surf-and-orb-on-opencv-59119b9ec3d0
# SIFT: https://docs.opencv.org/3.4/da/df5/tutorial_py_sift_intro.html

ComparisonRouter = Blueprint(
    'ComparisonRouter', 
    __name__,
    template_folder='templates'
)

@ComparisonRouter.route("/photo-<doc_id>/comparison")
def photo_comparison(doc_id:int):
    with PhotoModel() as phot:
        photo = phot.get_photo(doc_id)
    return render_template(
        PAGE_INDEX,
        content_page = 'comparison.html',
        url_photo_preview = url_for('PhotoRouter.photo_preview', doc_id=doc_id, variant_id=photo['variant_id']),
        api_list_variants = url_for('ComparisonRouter.api_list_variants', doc_id=doc_id),
        api_add_variant = url_for('ComparisonRouter.api_add_variant', photo_id=doc_id),
        api_remove_variant = url_for('ComparisonRouter.api_remove_variant', photo_id=doc_id),
        api_set_variant = url_for('ComparisonRouter.api_set_variant', photo_id=doc_id),
        api_set_filter = url_for('ComparisonRouter.api_set_filter', photo_id=doc_id),
    )

@ComparisonRouter.route("/api/photo-<doc_id>/list/variants")
def api_list_variants(doc_id:int):
    with PhotoModel() as phot:
        photo = phot.get_photo(doc_id)
        similar = phot.list_photos()
    with VariantModel() as var:
        file_photo0 = var.file_comparison(photo['variant_id'])
        dir_variant = var.dir_variant(photo['variant_id'])
    im0 = np.asarray(Image.open(file_photo0))
    orb = ORBModel()
    kp0,des0 = orb.load(f"{dir_variant}/{ORB_DATA_FILE}")
    variant_list = []
    for variant_id in photo['variants']:
        variant_list.append(dict(
            variant_id = variant_id,
            url_image = url_for('PhotoRouter.api_file_thumbnail', variant_id=variant_id),
            main = variant_id==photo['variant_id'],
            url_variant_preview=url_for('PhotoRouter.photo_preview', variant_id=variant_id, doc_id=doc_id),
        ))
    rc = RowCollector([
        'photo_id','variant_id','num_variants',
        'url_image','url_comparison','url_photo',
        'mse_score','ssim_score','orb_score',
    ])
    for sim in similar:
        if sim['variant_id']==photo['variant_id']:
            continue
        with VariantModel() as var:
            file_photo1 = var.file_comparison(sim['variant_id'])
            dir_variant = var.dir_variant(sim['variant_id'])
        im1 = np.asarray(Image.open(file_photo1))
        kp1,des1 = orb.load(f"{dir_variant}/{ORB_DATA_FILE}")
        orb_score = orb.compare(kp0,des0,kp1,des1)
        mse_score = mean_squared_error(im0, im1)
        ssim_score = ssim(im0, im1, data_range=im1.max() - im1.min())
        rc.append([
            sim.doc_id,
            sim['variant_id'],
            len(sim['variants']),
            url_for('PhotoRouter.api_file_thumbnail', variant_id=sim['variant_id']),
            url_for('ComparisonRouter.photo_comparison', doc_id=sim.doc_id),
            url_for('PhotoRouter.photo_preview', variant_id=sim['variant_id'], doc_id=sim.doc_id),
            round(mse_score,1),
            round(ssim_score,2),
            round(orb_score,2),
        ])
    df = rc.to_dataframe()
    #df = df.sort_values(['orb_score','ssim_score','mse_score'],ascending=[False,False,True])
    similar_list = []
    comparison = photo['comparison']
    if comparison['sortby']=='mse':
        df = df.sort_values(['mse_score'],ascending=[True])
    elif comparison['sortby']=='ssim':
        df = df.sort_values(['ssim_score'],ascending=[False])
    elif comparison['sortby']=='orb':
        df = df.sort_values(['orb_score'],ascending=[False])
    for index, row in df.iterrows():
        if comparison['sortby']=='mse' and row.mse_score>=comparison['mse']:
            continue
        if comparison['sortby']=='ssim' and row.ssim_score<=comparison['ssim']:
            continue
        if comparison['sortby']=='orb' and row.orb_score<=comparison['orb']:
            continue
        similar_list.append(dict(row))
    return jsonify(dict(
        url_image = url_for('PhotoRouter.api_file_thumbnail', variant_id=photo['variant_id']),
        variant_list = variant_list,
        similar_list = similar_list,
        comparison = photo['comparison'],
    ))

@ComparisonRouter.route("/api/photo-<photo_id>/variant/add", methods=['POST'])
def api_add_variant(photo_id:int):
    variant_photo_id = request.json['photo_id']
    with PhotoModel() as p:
        photo_from = p.get_photo(variant_photo_id)
        photo_to = p.get_photo(photo_id)
        variants = photo_to['variants']
        for variant_id in photo_from['variants']:
            if variant_id in variants:
                continue
            variants.append(variant_id)
        p.update(photo_id, {'variants':variants})
        p.remove_photo(variant_photo_id)
    return api_list_variants(photo_id)

@ComparisonRouter.route("/api/photo-<photo_id>/variant/remove", methods=['POST'])
def api_remove_variant(photo_id:int):
    variant_id = request.json['variant_id']
    with PhotoModel() as p:
        photo_from = p.get_photo(photo_id)
        variants = photo_from['variants']
        variants.remove(variant_id)
        if photo_from['variant_id']==variant_id:
            p.update(photo_id, {'variant_id':variants[0],'variants':variants})
        else:
            p.update(photo_id, {'variants':variants})
        p.add_from_variant(variant_id)
    return api_list_variants(photo_id)

@ComparisonRouter.route("/api/photo-<photo_id>/variant/set", methods=['POST'])
def api_set_variant(photo_id:int):
    variant_id = request.json['variant_id']
    with PhotoModel() as p:
        print(photo_id, variant_id)
        p.update(photo_id, {'variant_id':variant_id})
    return api_list_variants(photo_id)

@ComparisonRouter.route("/api/photo-<photo_id>/filter/set", methods=['POST'])
def api_set_filter(photo_id:int):
    comparison = {'sortby': request.json['sortby']}
    for sim in ['mse','ssim','orb']:
        if sim in request.json:
            comparison[sim] = float(request.json[sim]['threshold'])
    with PhotoModel() as p:
        p.update(photo_id, {'comparison':comparison})
    return api_list_variants(photo_id)
