#!/usr/bin/env python
# encoding: utf-8
import scipy.io as scio
import numpy as np
import utils
import sys
sys.path.insert(0,'../caffe-master/python')
sys.path.insert(0,'.')
import caffe
import cv2
import copy
import os
import shutil
from utils import *


# import train_net

###########         config params      ############
data_set_name='paris'
data_flickr = 'flickrs_global.npz'
hash_net=createNet('models/dh_mac_1024_iter_1_0.748_ox.caffemodel',"prototxts/test_.pt",0)
IS_ADD_FLICKRS=True
is_GQE=False
is_rerank=False
is_LQE=False

R_N = 400
QE_N = 4

LQE_N= 4
_N = 20   #for choose best LQE_N
####################################################

caffe.set_mode_gpu()
caffe.set_device(0)
gt_path='/home/xing/py-faster-rcnn/data/drh_data/'+data_set_name+'_gt' #ox_gt for ox_ford
img_path='../data/drh_data/'+data_set_name
global_feats_path= 'outputs/'+data_set_name+'_global.npz'
reg_hash_code_path = data_set_name+'_slide_hashcode_0.6.npz'


mp = globalFeatApply_LW(global_feats_path)
flickr = None
if IS_ADD_FLICKRS:
    flickr=globalFeatApply_LW('outputs/'+data_flickr)
    mp = dict(mp, **flickr)
# print len(mp)
# raw_input()
means = getGlobalFeatMean(mp).transpose()[0]
mp = getHashCode(hash_net,mp,means)

if is_rerank:
    mp_reg= np.ndarray.tolist(np.load('outputs/'+reg_hash_code_path)['regs'])
query_codes = queryRegLWNormMac(gt_path,img_path,dataset=data_set_name)

query_codes = getHashCode(hash_net,query_codes,means)

imgs = utils.querySet(gt_path)

ans = 0
n = 0

if os.path.exists('ranks'):
    shutil.rmtree('ranks')
    os.mkdir('ranks')

for i in imgs:
    f = open(gt_path+'/'+i)
    strs = f.readline().strip().split()
    img_path = None
    if data_set_name == 'ox':
        img_path=strs[0][5:]+'.jpg'
    if data_set_name =='paris':
        img_path=strs[0]+'.jpg'

    n += 1
    print img_path,n
    #qu = mp[img_path]
    qu = query_codes[i]
    rank = None
    if is_GQE == False:
        rank = ranker(qu, mp)
    else:
        rank=ranker(qu,mp,QE=True)[:QE_N]

        rank = QE(rank,mp)
    if is_rerank and is_LQE==False:
        rap = copy.deepcopy(rank[:R_N])
        rap,box = rerank(rap, mp_reg, qu)
        for j in rank[R_N:]:
                rap.append(j)
        rank = rap

    if is_rerank and is_LQE:
        # qu = query_codes[i]
        rap = copy.deepcopy(rank[:_N])
        rap = rerank(rap, mp_reg, qu, True)[:LQE_N]
        rapp = copy.deepcopy(rank[:R_N])
        # rapp.append(qu)
        #rap.append(qu)
        rap, boxs = LQE(rapp, mp_reg, rap)
        for j in rank[R_N:]:
            rap.append(j)
        rank = rap
    f = open("ranks/"+i,'wb')
    for j in rank:
        f.write(j[:-4]+'\n')
    f.close()
    #pos = cal_ap  #  queryPositive(imgs[i],gt_path)
ap=utils.cal_ap(data_set_name)

print ap



