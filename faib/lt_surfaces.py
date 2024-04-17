# -*- coding: utf-8 -*-
"""
Created on Mon Jul 19 11:14:26 2021

@author: SNASONOV
"""
import os, subprocess, datetime
import geopandas as gpd
import pandas as pd
from osgeo import gdal

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

def mosaic_rasters(rasterlist,outpath):
    opts = gdal.WarpOptions(format='GTiff')
    gdal.Warp(outpath,rasterlist)
            

def surfaces(non_dup=None,chm_laz=None,outdir=None,prod_loc=None,opt=None,rez=None):
    #### Lidar Processing, adapted from Geoff Quinn's batch file ####
    lastools = opt['lastools']
    
    t1 = datetime.datetime.now()
    
    #check if non_dup folder exits, if not error out
     
    if not os.path.exists(non_dup):
        return(print("Non-dup folder doesn't exist, exiting"))
    else:
        print('Non-dup exists, continuing')
    
    if not os.path.exists(prod_loc):
        os.mkdir(prod_loc)
            
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    
    print('Input Data: ' + non_dup)
    print('Processing Start: ' + str(t1))
    
    # ##############################################################################
   
    print('Generating BEM')
    f = 'bem_' + str(rez) + 'm'    
    out = os.path.join(outdir,f)
    if not os.path.exists(out):
        os.mkdir(out)
    
    # cmd = os.path.join(lastools,'blast2dem.exe') + ' -i ' + non_dup + '\\*.laz' + \
    #     ' -step ' + opt['pixelsize'] + \
    #     ' -keep_class 2 -use_tile_bb -otif -nad83_csrs -utm 10north -vertical_cgvd2013' + \
    #     ' -odir ' + out
        
    cmd = os.path.join(lastools,'blast2dem.exe') + ' -i ' + non_dup + '\\*.laz' + \
        ' -step ' + str(rez) + \
        ' -keep_class 2 -use_tile_bb -otif' + \
        ' -epsg 3005 -vertical_cgvd2013' + \
        ' -odir ' + out
    run_process(cmd)
        
    print('BEM mosaic')
    rasterlist = getfiles(out,'.tif')
    filename = opt['studyarea'] + '_BEM_mosaic_' + str(rez) + 'm.tif'
    outpath = os.path.join(prod_loc,filename)
    mosaic_rasters(rasterlist,outpath)
    
    print('Generating DSM')
    f = 'dsm_' + str(rez) + 'm'
    out = os.path.join(outdir,f)
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lasgrid.exe') + ' -i ' + non_dup + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -drop_withheld -drop_class 7 -elevation -highest' + \
        ' -step ' + str(rez) + \
        ' -mem 1900 -temp_files "temp" -use_tile_bb -otif' + \
        ' -odir ' + out
    run_process(cmd)
    
    print('DSM mosaic')
    rasterlist = getfiles(out,'.tif')
    filename = opt['studyarea'] + '_DSM_mosaic_' + str(rez) + 'm.tif'
    outpath = os.path.join(prod_loc,filename)
    mosaic_rasters(rasterlist,outpath)
    
    #### Generate point density 
    print('Generating point density')
    f = 'ptden_' + str(rez) + 'm'
    out = os.path.join(outdir,f)
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lasgrid.exe') + ' -i ' + non_dup + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -drop_withheld -drop_class 7 -point_density' + \
        ' -step ' + str(rez) + \
        ' -mem 1900 -temp_files "temp" -use_tile_bb -otif' + \
        ' -odir ' + out
    run_process(cmd)
    
    print('Point density mosaic')
    rasterlist = getfiles(out,'.tif')
    filename = opt['studyarea'] + '_ptden_mosaic_' + str(rez) + 'm.tif'
    outpath = os.path.join(prod_loc,filename)
    mosaic_rasters(rasterlist,outpath)
    
    print('Generating scan angle')
    f = 'scan_' + str(rez) + 'm'
    out = os.path.join(outdir,f)
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lasgrid.exe') + ' -i ' + non_dup + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -drop_withheld -drop_class 7 -scan_angle_abs_average' + \
        ' -step ' + str(rez) + \
        ' -mem 1900 -temp_files "temp" -use_tile_bb -otif' + \
        ' -odir ' + out
    try: 
        run_process(cmd)
        print('Scan angle mosaic')
        rasterlist = getfiles(out,'.tif')
        filename = opt['studyarea'] + '_scan_mosaic_' + str(rez) + 'm.tif'
        outpath = os.path.join(prod_loc,filename)
        mosaic_rasters(rasterlist,outpath)
    except:
        print('Scan angle rasters were not generated')
             
    print('Generating CHM')
    f = 'chm_' + str(rez) + 'm'
    out = os.path.join(outdir,f)
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lasgrid.exe') + ' -i ' + chm_laz + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -drop_withheld -clamp_z_below 0 -elevation -highest' + \
        ' -step ' + str(rez) + \
        ' -mem 1900 -temp_files "temp" -use_tile_bb -otif' + \
        ' -odir ' + out
    run_process(cmd)
    
    print('CHM mosaic')
    rasterlist = getfiles(out,'.tif')
    filename = opt['studyarea'] + '_CHM_mosaic_' + str(rez) + 'm.tif'
    outpath = os.path.join(prod_loc,filename)
    mosaic_rasters(rasterlist,outpath)
   
    ###############################################################################
    t2 = datetime.datetime.now()
    print('Processing time: ' + str(t2-t1))

### end of file 
###############################################################################

## How to run
# non_dup = r'C:\Data\Woodlot_0007\laz_reclass\non_dup'
# outdir = r'C:\Data\Woodlot_0007'
# studyarea = 'Woodlot0007'
# rez = 1
# prod_loc = r'C:\Data\Woodlot_0007\products'
# surfaces(non_dup=non_dup,outdir=outdir,studyarea=studyarea,rez=rez,prod_loc=prod_loc)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    







