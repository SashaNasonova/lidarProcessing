# -*- coding: utf-8 -*-
"""
Created on Mon Jul 19 11:14:26 2021

@author: SNASONOV & TGOODBODY
"""
import os, subprocess, datetime, shutil
import geopandas as gpd
import pandas as pd
from osgeo import gdal
from lt_surfaces import remove_empty

#####
from msgslack import msgslack
#####

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

    
def metrics_ubc(studyarea,cores,outfolder=None,res=None,lastools = r"C:/LAStools/bin"):
    #### LiDAR Processing, adapted from Geoff Quinn's batch file ####        
    #### Define options
    opt = {}
    opt['cores'] = str(cores)
    
    if res is None:
        print(str(datetime.datetime.now()) + ': ' + 'No pixel size selected for metrics, using 20m')
        res = str(20)
    else:
        opt['pixelsize'] = str(res)
        print(str(datetime.datetime.now()) + ': ' + 'metrics pixel size is ' + opt['pixelsize'] + 'm')
    
    #### Create ouputdir if doesn't exist
    outdir = os.path.join (outfolder,studyarea) #outputs, deliver these
    prod_loc = os.path.join(outdir,'products','metrics',opt['pixelsize'] + 'm') #deliver these
    pointclouds = os.path.join(outdir,'products','pointclouds','norm')
    wdir = os.path.join(outdir,'intermediate','metrics',opt['pixelsize'] + 'm') # modified point cloud location, can be deleted if space is an issue
 
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    
    if not os.path.exists(prod_loc):
        os.makedirs(prod_loc)

    if not os.path.exists(wdir):
        os.makedirs(wdir)

    # create logfile for processing
    logfile = os.path.join(outdir, studyarea + '_log' + '.txt')
    log = open(logfile, "a")

    t1 = datetime.datetime.now()
    print(str(datetime.datetime.now()) + ': ' + '#### ' + str(datetime.datetime.now()) + ': ' + 'START ' + str(res) + ' METRICS PROCESSING: ' + str(t1) + ' ####', file = log)    
    
    msgslack(MESSAGE = str(datetime.datetime.now()) + ': ' + '#### ' + str(datetime.datetime.now()) + ': ' + 'START ' + str(res) + ' METRICS PROCESSING: ' + str(t1) + ' ####')
    ##############################################################################
    print(str(datetime.datetime.now()) + ': ' + 'Calculating lidar metrics', file = log)
    #default pixel size is 20m, change using -step parameter  
    
    try:
        print(str(datetime.datetime.now()) + ': ' + 'Height metrics (min, max, avg, std, ske, kur, qav)', file = log)
        out = os.path.join(wdir,'height_metrics')
        if not os.path.exists(out):
            os.makedirs(out)
        
        cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + pointclouds + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
            ' -all -min -max -avg -std -ske -kur -qav' + \
            ' -step ' + opt['pixelsize'] + \
            ' -odir ' + out + ' -otif -cpu64'
        
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)
        
        suflist = ['all','min','max', 'avg', 'std', 'ske', 'kur', 'qav']
        for suf in suflist:
            print(str(datetime.datetime.now()) + ': ' + 'START: Mosaicing ' + suf, file = log)
            end = suf + '.tif'
            rasterlist = getfiles(out, end)
            
            #make output folder if it doesnt exist
            odir = os.path.join(prod_loc,'height_metrics')
            if not os.path.exists(odir):
                os.makedirs(odir)
            
            name = suf + '_mosaic_' + opt['pixelsize'] +'m.tif'
            outpath = os.path.join(odir, name)
            mosaic_rasters(rasterlist,outpath)
            print(str(datetime.datetime.now()) + ': ' + 'END: Mosaicing ' + suf, file = log)
            msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `height_metrics` " + str(res) + " metrics " + suf + " complete."
            msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise
    
    try:
        print(str(datetime.datetime.now()) + ': ' + 'Height percentiles (2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98)', file = log)
        out = os.path.join(wdir,'height_percentiles')
        if not os.path.exists(out):
            os.makedirs(out)
        
        cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + pointclouds + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
            ' -p 2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98' + \
            ' -fractions'  + \
            ' -step ' + opt['pixelsize'] + \
            ' -odir ' + out + ' -otif -cpu64'
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)
        
        suflist = ['p02','p05','p10','p15','p20','p25','p30','p40','p50','p60',
                    'p70','p75','p80','p85','p90','p95','p98']
        for suf in suflist:
            print(str(datetime.datetime.now()) + ': ' + 'START: Mosaicing ' + suf, file = log)
            end = suf + '.tif'
            rasterlist = getfiles(out, end)

            #make output folder if it doesnt exist
            odir = os.path.join(prod_loc,'height_percentiles')
            if not os.path.exists(odir):
                os.makedirs(odir)
            
            name = suf + '_mosaic_' + opt['pixelsize'] +'m.tif'
            outpath = os.path.join(odir, name)
            mosaic_rasters(rasterlist,outpath)
            print(str(datetime.datetime.now()) + ': ' + 'END: Mosaicing ' + suf, file = log)
            msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `height_percentiles` " + str(res) + " metrics " + suf + " complete."
            msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise

    try:
        print(str(datetime.datetime.now()) + ': ' + 'Canopy cover metrics (inverse of cov and dns)', file = log)
        out = os.path.join(wdir,'canopy_cover')
        if not os.path.exists(out):
            os.makedirs(out)
        
        cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + pointclouds + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
            ' -cov -dns -gap' + \
            ' -fractions' + \
            ' -step ' + opt['pixelsize'] + \
            ' -odir ' + out + ' -otif -cpu64'
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)
        
        suflist = ['cov_gap','dns_gap']
        for suf in suflist:
            print(str(datetime.datetime.now()) + ': ' + 'START: Mosaicing ' + suf, file = log)
            end = suf + '.tif'
            rasterlist = getfiles(out, end)

            #make output folder if it doesnt exist
            odir = os.path.join(prod_loc,'canopy_cover')
            if not os.path.exists(odir):
                os.makedirs(odir)
            
            name = suf + '_mosaic_' + opt['pixelsize'] +'m.tif'
            outpath = os.path.join(odir, name)
            mosaic_rasters(rasterlist,outpath)
            print(str(datetime.datetime.now()) + ': ' + 'END: Mosaicing ' + suf, file = log)
            msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `canopy_cover` " + str(res) + " metrics " + suf + " complete."
            msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise
    
    try:
        print(str(datetime.datetime.now()) + ': ' + 'Bincentiles (2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98)', file = log)
        out = os.path.join(wdir,'bincentiles')
        if not os.path.exists(out):
            os.makedirs(out)
        
        cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + pointclouds + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0 -height_cutoff 0' + \
            ' -b 2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98' + \
            ' -fractions' + \
            ' -step ' + opt['pixelsize'] + \
            ' -odir ' + out + ' -otif -cpu64'
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)
        
        suflist = ['b02','b05','b10','b15','b20','b25','b30','b40','b50','b60',
                    'b70','b75','b80','b85','b90','b95','b98']
        for suf in suflist:
            print(str(datetime.datetime.now()) + ': ' + 'START: Mosaicing ' + suf, file = log)
            end = suf + '.tif'
            rasterlist = getfiles(out, end)

            #make output folder if it doesnt exist
            odir = os.path.join(prod_loc,'bincentiles')
            if not os.path.exists(odir):
                os.makedirs(odir)
            
            name = suf + '_mosaic_' + opt['pixelsize'] +'m.tif'
            outpath = os.path.join(odir, name)
            mosaic_rasters(rasterlist,outpath)
            print(str(datetime.datetime.now()) + ': ' + 'END: Mosaicing ' + suf, file = log)
            msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `bincentiles` " + str(res) + " metrics " + suf + " complete."
            msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        exit   
    
    try:
        print(str(datetime.datetime.now()) + ': ' + 'Intensity metrics (min, max, avg, std, ske, kur, qav)', file = log)
        out = os.path.join(wdir,'intensity_metrics')
        if not os.path.exists(out):
            os.makedirs(out)
    
        cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + pointclouds + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -first_only -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
            ' -int_min -int_max -int_avg -int_std -int_ske -int_kur -int_qav' + \
            ' -step ' + opt['pixelsize'] + \
            ' -odir ' + out + ' -otif -cpu64'
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)

        suflist = ['int_min','int_max','int_avg','int_std','int_ske','int_kur','int_qav']
        for suf in suflist:
            print(str(datetime.datetime.now()) + ': ' + 'START: Mosaicing ' + suf, file = log)
            end = suf + '.tif'
            rasterlist = getfiles(out, end)

            #make output folder if it doesnt exist
            odir = os.path.join(prod_loc,'intensity_metrics')
            if not os.path.exists(odir):
                os.makedirs(odir)
            
            name = suf + '_mosaic_' + opt['pixelsize'] +'m.tif'
            outpath = os.path.join(odir, name)
            mosaic_rasters(rasterlist,outpath) 
            print(str(datetime.datetime.now()) + ': ' + 'END: Mosaicing ' + suf, file = log)
            msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `intensity_metrics` " + str(res) + " metrics " + suf + " complete."
            msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        exit   
    
    try:
        print(str(datetime.datetime.now()) + ': ' + 'Intensity percentiles (2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98)', file = log) 
        out = os.path.join(wdir,'intensity_percentiles')
        if not os.path.exists(out):
            os.makedirs(out)
        
        cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + pointclouds + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -first_only -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
            ' -int_p 2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98' + \
            ' -fractions' + \
            ' -step ' + opt['pixelsize'] + \
            ' -odir ' + out + ' -otif -cpu64'
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)
        
        suflist = ['int_p02','int_p05','int_p10','int_p15','int_p20','int_p25',
                    'int_p30','int_p40','int_p50','int_p60','int_p70','int_p75',
                    'int_p80','int_p85','int_p90','int_p95','int_p98']
        
        for suf in suflist:
            print(str(datetime.datetime.now()) + ': ' + 'START: Mosaicing ' + suf, file = log)
            end = suf + '.tif'
            rasterlist = getfiles(out, end)

            #make output folder if it doesnt exist
            odir = os.path.join(prod_loc,'intensity_percentiles')
            if not os.path.exists(odir):
                os.makedirs(odir)
            
            name = suf + '_mosaic_' + opt['pixelsize'] +'m.tif'
            outpath = os.path.join(odir, name)
            mosaic_rasters(rasterlist,outpath)
            print(str(datetime.datetime.now()) + ': ' + 'END: Mosaicing ' + suf, file = log)
            msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `intensity_percentiles` " + str(res) + " metrics " + suf + " complete."
            msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        exit  

    
    try:
        print(str(datetime.datetime.now()) + ': ' + 'Vertical complexity index (vertical bins 1, 5, 10, 15)', file = log)
        out = os.path.join(wdir,'vci')
        if not os.path.exists(out):
            os.makedirs(out)
        
        cmd = os.path.join(lastools,'lascanopy.exe') + ' -i ' + pointclouds + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -keep_class 1 3 4 5 -drop_withheld -clamp_z_below 0' + \
            ' -vci 1 5 10 15' + \
            ' -step ' + opt['pixelsize'] + \
            ' -odir ' + out + ' -otif -cpu64'
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)
        
        suflist = ['vc0','vc1','vc2','vc3']
        
        for suf in suflist:
            print(str(datetime.datetime.now()) + ': ' + 'START: Mosaicing ' + suf, file = log) 
            end = suf + '.tif'
            rasterlist = getfiles(out, end)

            #make output folder if it doesnt exist
            odir = os.path.join(prod_loc,'vci')
            if not os.path.exists(odir):
                os.makedirs(odir)
            
            name = suf + '_mosaic_' + opt['pixelsize'] +'m.tif'
            outpath = os.path.join(odir, name)
            mosaic_rasters(rasterlist,outpath)
            print(str(datetime.datetime.now()) + ': ' + 'END: Mosaicing ' + suf, file = log)
            msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `vci` " + str(res) + " metrics " + suf + " complete."
            msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        exit     
             
    
       
        
    ###############################################################################
    t2 = datetime.datetime.now()
    print('#### ' + str(datetime.datetime.now()) + ': ' + 'END ' + str(res) + ' METRICS PROCESSING - TOTAL TIME: ' + str(t2-t1) + ' ####', file = log)

    msgslack(MESSAGE = '#### ' + str(datetime.datetime.now()) + ': ' + 'END ' + str(res) + ' METRICS PROCESSING - TOTAL TIME: ' + str(t2-t1) + ' ####')


    log.close()


### end of file 
###############################################################################

## How to run
# inpath = r'E:\IDF_all\outdir\chm\laz'
# ps2 = 20.0
# outfolder = r'E:\IDF_all\outdir\chm\metrics' 
# prod_loc = r'E:\IDF_all\products\metrics'
# metrics(inpath=inpath,outdir=outfolder,res=ps2,prod_loc=prod_loc) 