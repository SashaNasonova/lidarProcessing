# -*- coding: utf-8 -*-
"""
Created on Fri Nov 19 15:40:52 2021

@author: SNASONOV
"""
import os 
import sys

loc = r'C:\Dev\Python\lidar\lastools' #define
sys.path.append(loc)

from lt_metrics import metrics
from lt_prep import lasInfo
from lt_ptcloud_v2 import ptcloud
from lt_surfaces import surfaces
from shutil import rmtree

#### UBC SPECIFIC PROCESSING TO SEND MESSAGES TO SLACK CHANNEL
from lt_ptcloud_ubc import ptcloud_ubc
from lt_surfaces_ubc import surfaces_ubc
from lt_metrics_ubc import metrics_ubc
from msgslack import msgslack
#### UBC SPECIFIC PROCESSING TO SEND MESSAGES TO SLACK CHANNEL

#Define inputs 
clean = 'standard' #'aggressive', 'standard', None

### delete outdir after processing if `delete = True`
delete = False

basedir = r'E:\GOODBODY\PROCESSING\INPUT'

dirs = os.listdir(basedir)
res_surface = [5,20,25] #1,2
res_metrics = [20] #5
product = ['CHM','DEM','DSM','ptden','scan'] 

#for d in dirs:5
    ### Define
studyarea = 'Stage2_Koot_Cran_Inver' #name of the study area
datloc = os.path.join(basedir,studyarea) #location of the laz files
outfolder = r'E:\GOODBODY\PROCESSING\OUTPUT' #parent directory of where outputs will be stored
cores = 12
### 

### Point Cloud Processing
### Expecting epsg 3005, classes 1, 2, 6 (optional), 7 (optional), 9 (optional), .laz
"""
ptcloud_ubc(studyarea=studyarea, 
        datloc=datloc,
        outfolder=outfolder,
        clean=clean,
        tile_size=1000,
        buffer_size=100,
        height_cutoff=80,
        cores=cores)


for r in res_surface:
    surfaces_ubc(studyarea=studyarea,
                outfolder=outfolder,
                res=r,
                cores=cores) 
"""                

for r in res_metrics:
    metrics_ubc(studyarea=studyarea,
            outfolder=outfolder,
            res=r,
            cores=cores)

msgslack(MESSAGE = ':beers:  ALL DONE! :beers:')

### Delete outdir directory
if delete == True:
    rmtree(os.path.join(outfolder,'outdir'), ignore_errors=True)

elif delete == False:
    print(os.path.join(outfolder,'outdir') + ' not deleted.')

### end of file 


