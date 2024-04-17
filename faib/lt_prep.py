# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 13:49:16 2022

@author: snasonov
"""

import os, subprocess

lastools = r'C:\Software\lastools\LAStools\bin'

#executes a string command
#cmd (string), no output
def run_process(cmd):
    subprocess.run(cmd,shell=True)

#lastools, converts .las to .laz, writes to an existing output directory
# datloc (string), outfolder (string)
def compress_data(datloc,outfolder):
    
    cmd = os.path.join(lastools,'laszip.exe') + ' -i ' + datloc + '\\*.las' + \
        ' -cores 7' + \
        ' -odir ' + outfolder + ' -olaz'
    run_process(cmd)

#lastools, gets metadata for each laz file in datloc and outputs txt files to
# outfolder directory. Can be the same directories.
# datloc (string), outfolder (string)
def lasInfo(datloc,outfolder):
    cmd = os.path.join(lastools,'lasinfo.exe') + ' -i ' + datloc + '\\*.laz' + \
            ' -odir ' + outfolder + \
            ' -cd -gw -repair -otxt'
    run_process(cmd)

#lastools, reprojects .laz files to bc albers
# datloc (string), outfolder (string)
def bcalb(datloc,outfolder):
    
    cmd = os.path.join(lastools,'las2las.exe') + ' -i ' + datloc + '\\*.laz' + \
                ' -cores 7 -drop_withheld ' + '-nad83_csrs -set_version_minor 4' + \
                ' -target_epsg 3005 -vertical_cgvd2013 -set_ogc_wkt' + \
                ' -odir ' + outfolder + ' -odix ' + '_epsg3005' + ' -olaz'  
    print(cmd) #debug
    run_process(cmd)

#lastools, reclasses point classification
#In this case 17 to 1, and 5 to 1. May need to change this.
# datloc (string), outfolder (string)
def reclassPoints(datloc,outfolder):
    cmd = os.path.join(lastools,'las2las.exe') + ' -i ' + datloc + '\\*.laz' + \
        ' -cores 7 -change_classification_from_to 17 1 -change_classification_from_to 5 1 -set_version_minor 4' + \
        ' -odir ' + outfolder + ' -odix "_reclass" -olaz' 
    # print(cmd) #debug
    run_process(cmd) 

#lastools, reprojects to bcalbers and reclassifies (17 to 1 and 5 to 1)    
# datloc (string), outfolder (string)
def reclass_bcalb(datloc,outfolder):
    cmd = os.path.join(lastools,'las2las.exe') + ' -i ' + datloc + '\\*.laz' + \
        ' -cores 7 -change_classification_from_to 17 1 -change_classification_from_to 5 1' + \
        ' -target_epsg 3005 -vertical_cgvd2013 -set_ogc_wkt -set_version_minor 4' + \
        ' -odir ' + outfolder + ' -odix "_reclass_epsg3005" -olaz'
    # print(cmd) #debug
    run_process(cmd) 
    

##############################################################################
datloc = r'C:\Data\Woodlot_0007\lidar_processing_v3\laz'

### Example 1: Reproject 
outdir = r'C:\Data\Woodlot_0007\lidar_processing_v3\laz_bcalb'
bcalb(datloc,outdir)
lasInfo(outdir,outdir) #check outputs

### Example 2: Reclass points 5 to 1, 17 to 1, keep noise as 7
outdir = r'C:\Data\Woodlot_0007\laz_reclass'
reclassPoints(datloc,outdir)
lasInfo(outdir,outdir) #check outputs

### Example 3: Reclass points 5 to 1, 17 to 1, keep noise as 7 and reproject to bcalb
outdir = r'C:\Data\Woodlot_0007\laz_bcalb_reclass'
reclass_bcalb(datloc,outdir)
lasInfo(outdir,outdir) #check outputs



