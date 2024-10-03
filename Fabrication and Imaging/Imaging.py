# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 12:55:57 2020

@author: schulmanlab
"""

import numpy as np
from pycromanager import Bridge
import cv2 
import os
import time

bridge = Bridge(convert_camel_case=False)
core = bridge.get_core()
core.setAutoShutter(True)
core.setProperty('UserDefinedStateDevice-1','Label','Empty')

#%%Functionalized XY position list extracter
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

#%% Parameter setting: xy positions, exposure time (ms)

brightness = 100 #XCite lamp intensity in %

filename = 'Solution_10nMrR2_0.00446U-uLRNaseH_Hydrogel_200nMG1t-G1S1_'
exposure = (0, 1000, 10) #exposure in ms
core.setProperty('HamamatsuHam_DCAM','Binning','4x4')
light_pillar = 0.2 # for patterning off/Empty

posi = ('200nMThresh_', '2000nMThresh_')
fluorophore = ("skip", 'Cy3', 'BF') #Fluorophore to use
cycles = 150  #number of cycles
delay = 300 #time between each cycle in s 


core.setProperty('UserDefinedStateDevice-1','Label','Empty')
core.setProperty('UserDefinedShutter-1','State',1)
core.setProperty('UserDefinedShutter','State',1)
core.setProperty('XCite-Exacte','Lamp-Intensity', brightness)
#%%use position list when marking positions in GUI
xy_up = position_list()
#always savve position list!!!

#%%Cycling through positions and times:    
t1 = time.time()
for j in range(1, cycles):
    for n in range(len(xy_up)):
        core.setXYPosition(xy_up[n,0],xy_up[n,1])
        for i in range(len(fluorophore)):
            if fluorophore[i] == "skip":
                continue
            if fluorophore[i] == "BF":
                core.setProperty('DTOL-DAC-0', 'Volts', light_pillar)
                core.setProperty('XCite-Exacte','Lamp-Intensity', 10)
            else:
                core.setProperty('DTOL-DAC-0', 'Volts', 0)
                core.setProperty('XCite-Exacte','Lamp-Intensity', brightness)
            core.setProperty('UserDefinedStateDevice','Label',fluorophore[i])
            core.setExposure(exposure[i])
            time.sleep(3)
            core.snapImage()
            tagged_image = core.getTaggedImage()
            pixels = np.reshape(tagged_image.pix,newshape=[tagged_image.tags['Height'], tagged_image.tags['Width']])
            t2 = np.around(time.time()-t1,decimals=2)
            cv2.imwrite(filename +str(posi[n])+str(fluorophore[i])+'_cycle_'+str(j)+'_time_'+str(t2)+'.tif', pixels.astype(np.uint16) )
            core.setProperty('DTOL-DAC-0', 'Volts', 0)
            time.sleep(2)
    
    for k in range(int(delay-(t2%delay))):#removing total image taking time
        time.sleep(1)     