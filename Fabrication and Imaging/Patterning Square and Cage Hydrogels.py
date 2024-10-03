  # -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 14:31:51 2021

@author: rmish
"""
from pycromanager import Bridge
import numpy as np
from skimage.transform import resize
import time
import skimage.draw as skdraw
#%% Initialization:
h = 684
w = 608

bridge = Bridge(convert_camel_case=False)
core = bridge.get_core()
DMD = core.getSLMDevice()
core.setProperty(DMD,'TriggerType',1)
# core.setSLMPixelsTo(DMD,100) #show all pixels
h = core.getSLMHeight(DMD)
w = core.getSLMWidth(DMD)
core.setProperty('UserDefinedStateDevice-1','Label','Patterning ON (dichroic mirror)')
core.setProperty('UserDefinedStateDevice','Label','BF')
# core.setProperty('HamamatsuHam_DCAM','Binning','2x2')
core.setProperty('UserDefinedShutter-1','State',1)
core.setProperty('UserDefinedShutter','State',1)

#Channel 4: UV LED
core.setProperty('Mightex_BLS(USB)','mode','NORMAL')
core.setProperty('Mightex_BLS(USB)','channel',1)
core.setProperty(DMD,'AffineTransform.m00',0)
core.setProperty(DMD,'AffineTransform.m01',-0.7988)
core.setProperty(DMD,'AffineTransform.m02',1231.7751)
core.setProperty(DMD,'AffineTransform.m10',1.1149)
core.setProperty(DMD,'AffineTransform.m11',0.0000)
core.setProperty(DMD,'AffineTransform.m12',-904.0098)
#current set: 0-1000
core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0)

#%%Functions: 
def square_mask_generator(h,w,ex,CF):
    ex = ex / CF
    rr,cc = skdraw.rectangle(((h-ex)/2,(w-ex)/2),extent=(ex,ex),shape=[h,w])
    mask2 = np.zeros((h,w),dtype='uint8')
    mask2[rr.astype('int'),cc.astype('int')] = 255
    return mask2
    
def rectangle_mask_generator(h,w,lx,ly,cx=0,cy=0,CF=1):
    """Returns rectangular mask with a rectangle in the center for use with a DMD.
    h,w: height, width of mask.
    lx,ly: length,width of rectangle.
    cx,cy: x and y offset from center of mask
    CF: DMD correction factor based off of the objective being used"""
    lx = lx / CF
    ly = ly / CF
    cx = cx / CF
    cy = cy / CF
    midx = h/2
    midy = w/2
    lx = lx/2
    ly = ly/2
    startx = midx-lx
    starty = midy-ly
    endx = midx + lx
    endy = midy + ly
    rr,cc = skdraw.rectangle((startx+cx, starty+cy),end=(endx+cx, endy+cy),shape=[h,w])
    mask2 = np.zeros((h,w),dtype='uint8')
    mask2[rr.astype('int'),cc.astype('int')] = 255
    return mask2

def hollow_rr_mask_generator(h,w,lxl,lyl,lxs,lys,cxl=0,cyl=0,cxs=0,cys=0,CF=1):
    """Returns rectangular mask with a rectangular hole in the center for use with a DMD.
    h,w: height, width of mask.
    lxl,lyl: length,width of large rectangle.
    lxs,lys: length,width of small rectanglar hole
    cxl,cyl: center offset for larger rectangle
    cxs,cys: center offset for smaller rectangle
    CF: DMD correction factor based off of the objective being used"""
    llarge = rectangle_mask_generator(h, w, lxl, lyl,cx=cxl,cy=cyl, CF=CF)
    lsmall = rectangle_mask_generator(h, w, lxs, lys,cx=cxs,cy=cys, CF=CF)    
    lcomb = llarge - lsmall
    return lcomb
    
def mask_rescaler(in1):
    y1 = resize(in1,(h,w/2))
    wpad = int(w/4)
    ypad = np.pad(y1,((0,0),(wpad,wpad)),'constant', constant_values=(0))
    ypad=np.array(ypad,dtype='uint8')
    ypad[ypad==1]=255
    return ypad

def position_list():
    mm = bridge.get_studio()
    pm = mm.positions()
    pos_list = pm.getPositionList()
    numpos = pos_list.getNumberOfPositions()
    np_list = np.zeros((numpos,2))
    for idx in range(numpos):
        pos = pos_list.getPosition(idx)
        stage_pos = pos.get(0)
        np_list[idx,0] = stage_pos.x
        np_list[idx,1] = stage_pos.y          
    return np_list

def patterning(UVexposure,slimage,channel=4,intensity=1000):
    core.setSLMImage(DMD,slimage)
    time.sleep(1.5)
    core.setProperty('Mightex_BLS(USB)','channel',channel)
    core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',intensity)
    time.sleep(UVexposure)
    core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0)
    time.sleep(1)
    core.setProperty('Mightex_BLS(USB)','normal_CurrentSet',0)

#%% Patterning Shape

# DMD Properties
h = 684
w = 608

# 10X Objective 
# 1 pixel = 0.45 um
# 100 um gel = 100/0.45 = 222 pixels
# CF = 0.45

# 20X UV Objective 
# 1 pixel = 0.28 um
# 100 um rec. gel = 100/0.28 = 357 pixels
# CF = 0.28

# Square and Objective Parameters
draw_square = square_mask_generator(h,w,ex=50,CF=0.28)

# Rectangle and Objective Parameters
draw_rectangle = rectangle_mask_generator(h, w, lx=50, ly=50, CF=0.45)

# Hollow Rectangle and Objective Parameters
draw_left_cage = hollow_rr_mask_generator(h,w,lxl=150,lyl=250,lxs=80,lys=250,cxl=0,cyl=0,cxs=0,cys=40,CF=0.45)
draw_right_cage = hollow_rr_mask_generator(h,w,lxl=150,lyl=250,lxs=80,lys=250,cxl=0,cyl=0,cxs=0,cys=-40,CF=0.45)

#%% Pattern four square gels in a line at each position

# Square hydrogels are all patterned 30 units below focus with 20X NUV objective

# Mark center position of DMD at center positions of desired first hydrogels in channels
xy_up = position_list()
uv_exposure = 0.3

for i in range(len(xy_up)):
    core.setXYPosition(xy_up[i,0],xy_up[i,1])
    output = draw_square  
    SLim = mask_rescaler(output)
    patterning(uv_exposure,SLim,channel=4,intensity=1000)
    for j in range(3):
        core.setRelativeXYPosition(100.0, 0) 
        time.sleep(1.5)
        output = draw_square  
        SLim = mask_rescaler(output)
        patterning(uv_exposure,SLim,channel=4,intensity=1000)
    
#%% Pattern left cage gels at each position

# Cage hydrogels are patterned 50 units below focus with 10X objective

# Mark center position of DMD at 135um from left ends of channels
xy_up = position_list()

uv_exposure = 0.3
for i in range(len(xy_up)):
    core.setXYPosition(xy_up[i,0],xy_up[i,1])
    output = draw_left_cage  
    SLim = mask_rescaler(output)
    patterning(uv_exposure,SLim,channel=4,intensity=1000)
    
#%% Pattern right cage gels at each position

# Cage hydrogels are patterned 50 units below focus with 10X objective

# Mark center position of DMD at 140um from right ends of channels
xy_up = position_list()
uv_exposure = 0.3

for i in range(len(xy_up)):
    core.setXYPosition(xy_up[i,0],xy_up[i,1])
    output = draw_right_cage  
    SLim = mask_rescaler(output)
    patterning(uv_exposure,SLim,channel=4,intensity=1000)
