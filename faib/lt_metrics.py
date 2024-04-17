# -*- coding: utf-8 -*-
"""
Created on Mon Jul 19 11:14:26 2021

@author: SNASONOV
"""
import os, subprocess, datetime, shutil
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
        
def mosaic_rasters(rasterlist,outpath):
    opts = gdal.WarpOptions(format='GTiff')
    gdal.Warp(outpath,rasterlist)

    
def metrics(inpath=None,outdir=None,metrics_pixelsize=None,prod_loc=None,opt=None,logfile=None):
    #### LiDAR Processing, adapted from Geoff Quinn's batch file ####
    lastools = opt['lastools']
    
    t1 = datetime.datetime.now()
    
    if metrics_pixelsize is None:
        print('No pixel size selected for canopy metrics, using 20m')
        pixelsize = str(20)
    else:
        pixelsize = str(metrics_pixelsize)
        print('CHM metrics pixel size is ' + str(metrics_pixelsize) + 'm')
        
 
    #### Create ouputdir if doesn't exist
    print(outdir)
 
    if not os.path.exists(outdir):
        os.mkdir(outdir)
        
    #### Create mosaic folder for metrics
    mosaic_loc_metrics = os.path.join(prod_loc,'metrics')
    if not os.path.exists(mosaic_loc_metrics):
        os.mkdir(mosaic_loc_metrics)
    
    print('Input Data: ' + inpath)
    print('Processing Start: ' + str(t1))
    
    ##############################################################################
    print('Calculating canopy metrics')
    #default pixel size is 20m, change using -step parameter  
    
    print('Height metrics (min, max, avg, std, ske, kur, qav)')
    out = os.path.join(outdir,'height_metrics')
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + inpath + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
        ' -all -min -max -avg -std -ske -kur -qav' + \
        ' -step ' + pixelsize + \
        ' -odir ' + out + ' -otif'
    #print(cmd) #for debug
    
    run_process(cmd)
    
    suflist = ['all','min','max', 'avg', 'std', 'ske', 'kur', 'qav']
    for suf in suflist:
        end = suf + '.tif'
        rasterlist = getfiles(out, end)
        
        name = suf + '_mosaic.tif'
        outpath = os.path.join(out, name)
        mosaic_rasters(rasterlist,outpath)
        #copy to mosaic folder
        odir = os.path.join(mosaic_loc_metrics,'height_metrics')
        if not os.path.exists(odir):
            os.mkdir(odir)
        shutil.copy(outpath,odir)
    
    print('Height percentiles (2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98)')
    out = os.path.join(outdir,'height_percentiles')
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + inpath + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
        ' -p 2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98' + \
        ' -fractions'  + \
        ' -step ' + pixelsize + \
        ' -odir ' + out + ' -otif'
    run_process(cmd)
    
    suflist = ['p02','p05','p10','p15','p20','p25','p30','p40','p50','p60',
                'p70','p75','p80','p85','p90','p95','p98']
    for suf in suflist:
        end = suf + '.tif'
        rasterlist = getfiles(out, end)
        
        name = suf + '_mosaic.tif'
        outpath = os.path.join(out, name)
        mosaic_rasters(rasterlist,outpath)
        #copy to mosaic folder
        odir = os.path.join(mosaic_loc_metrics,'height_percentiles')
        if not os.path.exists(odir):
            os.mkdir(odir)
        shutil.copy(outpath,odir)
    
    print('Canopy cover metrics (inverse of cov and dns)')
    out = os.path.join(outdir,'canopy_cover')
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + inpath + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
        ' -cov -dns -gap' + \
        ' -fractions' + \
        ' -step ' + pixelsize + \
        ' -odir ' + out + ' -otif'
    run_process(cmd)
    
    suflist = ['cov_gap','dns_gap']
    for suf in suflist:
        end = suf + '.tif'
        rasterlist = getfiles(out, end)
        
        name = suf + '_mosaic.tif'
        outpath = os.path.join(out, name)
        mosaic_rasters(rasterlist,outpath)
        #copy to mosaic folder
        odir = os.path.join(mosaic_loc_metrics,'canopy_cover')
        if not os.path.exists(odir):
            os.mkdir(odir)
        shutil.copy(outpath,odir)
    
    print('Bincentiles (2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98)')
    out = os.path.join(outdir,'bincentiles')
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + inpath + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0 -height_cutoff 0' + \
        ' -b 2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98' + \
        ' -fractions' + \
        ' -step ' + pixelsize + \
        ' -odir ' + out + ' -otif'
    run_process(cmd)
    
    suflist = ['b02','b05','b10','b15','b20','b25','b30','b40','b50','b60',
                'b70','b75','b80','b85','b90','b95','b98']
    for suf in suflist:
        end = suf + '.tif'
        rasterlist = getfiles(out, end)
        
        name = suf + '_mosaic.tif'
        outpath = os.path.join(out, name)
        mosaic_rasters(rasterlist,outpath)
        
        #copy to mosaic folder
        odir = os.path.join(mosaic_loc_metrics,'bincentiles')
        if not os.path.exists(odir):
            os.mkdir(odir)
        shutil.copy(outpath,odir)
    
    print('Intensity metrics (min, max, avg, std, ske, kur, qav)')
    out = os.path.join(outdir,'intensity_metrics')
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + inpath + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -first_only -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
        ' -int_min -int_max -int_avg -int_std -int_ske -int_kur -int_qav' + \
        ' -step ' + pixelsize + \
        ' -odir ' + out + ' -otif'
    run_process(cmd)
    
    suflist = ['int_min','int_max','int_avg','int_std','int_ske','int_kur','int_qav']
    for suf in suflist:
        end = suf + '.tif'
        rasterlist = getfiles(out, end)
        
        name = suf + '_mosaic.tif'
        outpath = os.path.join(out, name)
        mosaic_rasters(rasterlist,outpath)
        
        #copy to mosaic folder
        odir = os.path.join(mosaic_loc_metrics,'intensity_metrics')
        if not os.path.exists(odir):
            os.mkdir(odir)
        shutil.copy(outpath,odir)
    
    print('Intensity percentiles (2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98)') 
    out = os.path.join(outdir,'intensity_percentiles')
    if not os.path.exists(out):
        os.mkdir(out)
       
    cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + inpath + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -first_only -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
        ' -int_p 2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98' + \
        ' -fractions' + \
        ' -step ' + pixelsize + \
        ' -odir ' + out + ' -otif'
    run_process(cmd)
    
    suflist = ['int_p02','int_p05','int_p10','int_p15','int_p20','int_p25',
                'int_p30','int_p40','int_p50','int_p60','int_p70','int_p75',
                'int_p80','int_p85','int_p90','int_p95','int_p98']
    
    for suf in suflist:
        end = suf + '.tif'
        rasterlist = getfiles(out, end)
        
        name = suf + '_mosaic.tif'
        outpath = os.path.join(out, name)
        mosaic_rasters(rasterlist,outpath)
        
        #copy to mosaic folder
        odir = os.path.join(mosaic_loc_metrics,'intensity_percentiles')
        if not os.path.exists(odir):
            os.mkdir(odir)
        shutil.copy(outpath,odir)
        
    
    print('Vertical complexity index (vertical bins 1, 5, 10, 15)')
    out = os.path.join(outdir,'vci')
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + inpath + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
        ' -vci 1 5 10 15' + \
        ' -step ' + pixelsize + \
        ' -odir ' + out + ' -otif'
    run_process(cmd)
    
    suflist = ['vc0','vc1','vc2','vc3']
    
    for suf in suflist:
        end = suf + '.tif'
        rasterlist = getfiles(out, end)
        
        name = suf + '_mosaic.tif'
        outpath = os.path.join(out, name)
        mosaic_rasters(rasterlist,outpath)    
        
        #copy to mosaic folder
        odir = os.path.join(mosaic_loc_metrics,'vci')
        if not os.path.exists(odir):
            os.mkdir(odir)
        shutil.copy(outpath,odir)
        
    ###############################################################################
    t2 = datetime.datetime.now()
    print('Processing time: ' + str(t2-t1))


### end of file 
###############################################################################

## How to run
# inpath = r'E:\IDF_all\outdir\chm\laz'
# ps2 = 20.0
# outfolder = r'E:\IDF_all\outdir\chm\metrics' 
# prod_loc = r'E:\IDF_all\products\metrics'
# metrics(inpath=inpath,outdir=outfolder,metrics_pixelsize=ps2,prod_loc=prod_loc)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    







