# -*- coding: utf-8 -*-
"""
Created on Fri Nov 19 15:40:52 2021

#### 2023-Dec-20: added logging function 

@author: SNASONOV
"""

#TODO: and -cpu64 flag to applicable processing to use 64-bit tools
#TODO: add logging 
#TODO: drop buffers at the end in lt_surfaces.py
#TODO: add lasinfo (check for slope violations for nomalized pt cloud) in lt_surfaces.py

import os 
import sys

loc = r'C:\Dev\git\lidarProcessing\faib' #define
sys.path.append(loc)

from lt_metrics import metrics
from lt_ptcloud_v2 import ptcloud
from lt_surfaces import surfaces
from lt_fncts import *

#Define lastools location
lastools = r'C:\Software\LAStools\bin' #lastools location

#Define processing parameters 
tile_size = 1000 # in meters (default: 1000m)
buffer_size = 20 # in meters (default: 20m)
clean = 'standard' #'aggressive', 'standard', None
cores = '7'

### Define inputs and outputs
studyarea = 'woodlot0007' #name of the study area
outfolder = r'E:\test_data' #parent directory of where outputs will be stored

datloc = os.path.join(outfolder,'laz') #location of the laz files
prod_loc = os.path.join(outfolder,'products') #products directory

### Define logfile, stored in products directory
logfile = os.path.join(prod_loc,'log.txt')
### 

print('Study Area: ' + studyarea)
print('Data Location: ' + datloc)
print('Outfolder: ' + outfolder)
print('Product Location: ' + prod_loc)

### Create processing dictionary
opt = {'tile_size':str(tile_size),'buffer_size':str(buffer_size),'clean':clean,'cores':str(cores),
       'lastools':lastools,
       'logfile':logfile,'studyarea':studyarea}

#print('Processing Options: ' + opt)

### Point Cloud Processing
### Expecting epsg 3005, classes 1, 2, 6 (optional), 7 (optional), 9 (optional), .laz
out_laz,chm_laz = ptcloud(datloc=datloc,outfolder=outfolder,prod_loc=prod_loc,opt=opt)

# ### Generate Surfaces
outsurfaces = os.path.join(outfolder,'outdir')
surfaces(non_dup=out_laz,chm_laz=chm_laz,outdir=outsurfaces,prod_loc=prod_loc,opt=opt,rez=1)

# ### Generate Metrics
outmetrics = os.path.join(outfolder,'outdir','metrics')
metrics(inpath=chm_laz,outdir=outmetrics,prod_loc=prod_loc,opt=opt,metrics_pixelsize=20)

### end of file 


