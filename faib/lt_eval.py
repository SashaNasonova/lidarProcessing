# -*- coding: utf-8 -*-
"""
Created on Mon Dec  6 16:34:04 2021

@author: SNASONOV
"""

import os, subprocess, datetime
import geopandas as gpd
import pandas as pd
from osgeo import gdal

lastools = r'C:\Software\lastools\LAStools\bin'

def getfiles(d,ext):
    paths = []
    for file in os.listdir(d):
        if file.endswith(ext):
            paths.append(os.path.join(d, file))
    return(paths) 

def run_process(cmd):
    subprocess.run(cmd,shell=True)
    #print(val)
        
def merge_shapefiles(shplist,outpath):
    gdflist = []
    for shp in shplist:
        gdf = gpd.read_file(shp)
        gdflist.append(gdf)

    gdf_out = gpd.GeoDataFrame(pd.concat(gdflist))
    gdf_out.to_file(driver = 'ESRI Shapefile', filename = outpath)

def las_reproject(datloc,outdir,outepsg,filetype):
    
    filetype_str = r'\\*.' + filetype
    #inepsg_str = ' -epsg ' + str(inepsg)
    outepsg_str = ' -target_epsg ' + str(outepsg)
    suf = '_espg' + str(outepsg)
    
    cmd = os.path.join(lastools,'las2las.exe') + ' -i ' + datloc + filetype_str + \
                ' -cores 7 -drop_class 6 7 -drop_withheld' + ' -nad83_csrs' + outepsg_str + \
                ' -vertical_cgvd2013' + \
                ' -odir ' + outdir + ' -odix' + suf + ' -olaz'  
    print(cmd)
    run_process(cmd)

def compress_data(datloc,outdir):
    
    cmd = os.path.join(lastools,'laszip.exe') + ' -i ' + datloc + '\\*.las' + \
        ' -drop_class 6 7 -cores 7' + \
        ' -odir ' + outdir + ' -olaz'
    run_process(cmd)
    
 
def repair_headers(datloc):
    print('trying a repair')
    cmd = os.path.join(lastools,'lasinfo.exe') + ' -i ' + datloc + '\\*.laz' + \
        ' -repair'
    run_process(cmd)

def assign_projection(datloc,outfolder):
    cmd = os.path.join(lastools,'las2las.exe') + ' -i ' + datloc + '\\*.laz' + \
        ' -cores 7 -drop_class 6 7 9  -change_classification_from_to 17 1 -drop_withheld -target_epsg 3005 -set_version_minor 4 -set_ogc_wkt' + \
        ' -odir ' + outfolder + ' -odix "_epsg3005" -olaz' 
    print(cmd)
    run_process(cmd) 

def data_eval(datloc,outdir,filetype): 
   
    filetypestr = r'\\*.' + filetype
    
    #run lasinfo
    cmd = os.path.join(lastools,'lasinfo.exe') + ' -i ' + datloc + filetypestr + \
            ' -drop_class 6 7 -merged' + ' -odir ' + outdir + \
            ' -o "lasinfo.txt" -cd'
            
    print(cmd)
    run_process(cmd)
        
    #create shapefile
    print('Creating a pre-tiling shapefile')
    
    out = os.path.join(outdir,'tile_shp')
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lasboundary.exe') + ' -i ' + datloc + filetypestr + \
        ' -use_bb -labels -cores 7' + \
        ' -odir ' + out
    run_process(cmd)
 
    print('Merging pre-tiling shapefiles') 
    shplist = getfiles(out,'.shp')
    outpath = os.path.join(outdir,'tile_shp\pretile_merged.shp')
    merge_shapefiles(shplist,outpath)
    

#evaluate the data
# datloc = r'K:\LiDAR\IDF\bcts_IDF\Moose_Valley\Las_v12_ASPRS'
# outdir = os.path.join(datloc,'eval')
# if not os.path.exists(outdir):
#         os.mkdir(outdir)
# filetype = 'laz'        
# data_eval(datloc,outdir,filetype)



#prep data
#compress?
#reproject?
    




