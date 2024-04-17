# -*- coding: utf-8 -*-
"""
Created on Mon Jul 19 11:14:26 2021

@author: SNASONOV & TGOODBODY
"""
import os, subprocess, datetime
import geopandas as gpd
import pandas as pd
from osgeo import gdal

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

def create_file_lists(basedir, dirs, res, product):
    file_lists = {}
    for r in res:
        for p in product:
            file_lists[f"{r}_{p}"] = []
            for d in dirs:
                directory = os.path.join(basedir, d, "products", "surfaces", f"{r}m")
                filename = f"{d}_{p}_{r}m.tif"
                file_path = os.path.join(directory, filename)
                print(f"Checking {file_path}...")
                if os.path.isfile(file_path):
                    file_lists[f"{r}_{p}"].append(file_path)
                    print(f"Added {file_path} to file list {r}_{p}.")
    return file_lists

def remove_empty(path):
    print(list(os.walk(path)))
    for (dirpath, folder_names, files) in os.walk(path):
        for filename in files:
            file_location = dirpath + '/' + filename  #file location is location is the location of the file
            if os.path.isfile(file_location):
                if os.path.getsize(file_location) == 0:#Checking if the file is empty or not
                    os.remove(file_location)  #If the file is empty then it is deleted using remove method
            

def surfaces_ubc(cores,outfolder=None,studyarea=None,res=None,lastools = r"C:/LAStools/bin"):
    #### LiDAR Processing, adapted from Geoff Quinn's batch file ####
  
    #### Define options
    opt = {}
    opt['pixelsize'] = str(res)
    opt['cores'] = str(cores)

    ### Create and set directories
    #datloc is the location of the input data, will be unaltered
    outdir = os.path.join (outfolder,studyarea) #outputs, deliver these 
    prod_loc = os.path.join(outdir,'products','surfaces',opt['pixelsize'] + 'm') #deliver these
    pointclouds = os.path.join(outdir,'products','pointclouds')
    wdir = os.path.join(outdir,'intermediate','surfaces') # modified point cloud location, can be deleted if space is an issue
        
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    
    if not os.path.exists(prod_loc):
        os.makedirs(prod_loc)

    if not os.path.exists(wdir):
        os.mkdir(wdir)

    # create logfile for processing
    logfile = os.path.join(outdir, studyarea + '_log' + '.txt')
    log = open(logfile, "a")

    t1 = datetime.datetime.now()
    print('#### ' + str(datetime.datetime.now()) + ': ' + 'START ' + str(res) + ' SURFACES PROCESSING: ' + str(t1) + ' ####', file = log)

    msgslack(MESSAGE = '#### ' + str(datetime.datetime.now()) + ': ' + 'START ' + str(res) + ' SURFACES PROCESSING: ' + str(t1) + ' ####')
   
    #check if non_norm folder exits, if not error out
    non_norm = os.path.join(pointclouds,'non_norm')
    norm = os.path.join(pointclouds,'norm')

    if not os.path.exists(non_norm):
        return(print(str(datetime.datetime.now()) + ': ' +"Non-normalized folder doesn't exist -- exiting", file = log))
    else:
        print(str(datetime.datetime.now()) + ': ' +'Non-normalized files found -- continuing', file = log)
    
    print(str(datetime.datetime.now()) + ': ' +'Input Data: ' + non_norm, file = log)
    print(str(datetime.datetime.now()) + ': ' +'Processing Start: ' + str(t1), file = log)
    
    # ##############################################################################
   
    try:
        # check that the right number of lax files exist
        print(str(datetime.datetime.now()) + ': ' +'Generating DEMs', file = log)
        f = 'dem_' + str(res) + 'm'    
        out = os.path.join(wdir,f)
        if not os.path.exists(out):
            os.mkdir(out)
        
        #las2dem
        cmd = os.path.join(lastools,'las2dem.exe') + ' -i ' + non_norm + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -extra_pass -step ' + opt['pixelsize'] + \
            ' -keep_class 2 -use_tile_bb -otif -utm 11N -nad83 -odir ' + out
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)
            
        print(str(datetime.datetime.now()) + ': ' +'DEM mosaic', file = log)
        rasterlist = getfiles(out,'.tif')
        filename = studyarea + '_DEM_' + str(res) + 'm.tif'
        outpath = os.path.join(prod_loc,filename)
        mosaic_rasters(rasterlist,outpath)

        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `DEM` " + str(res) + " complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise
    
    try:
        print(str(datetime.datetime.now()) + ': ' +'Generating DSM', file = log)
        f = 'dsm_' + str(res) + 'm'
        out = os.path.join(wdir,f)
        if not os.path.exists(out):
            os.mkdir(out)
        
        #lasgrid
        cmd = os.path.join(lastools,'lasgrid.exe') + ' -i ' + non_norm + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -drop_class 7 -elevation -highest' + \
            ' -step ' + opt['pixelsize'] + \
            ' -mem 1900 -cpu64 -temp_files "temp" -use_tile_bb -otif -utm 11N -nad83' + \
            ' -odir ' + out
        run_process(cmd)
        
        print(str(datetime.datetime.now()) + ': ' +'DSM mosaic', file = log)
        rasterlist = getfiles(out,'.tif')
        filename = studyarea + '_DSM_' + str(res) + 'm.tif'
        outpath = os.path.join(prod_loc,filename)
        mosaic_rasters(rasterlist,outpath)
        
        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `DSM` " + str(res) + " complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise

    try:
        #### Generate point density 
        print(str(datetime.datetime.now()) + ': ' +'Generating point density rasters', file = log)
        f = 'ptden_' + str(res) + 'm'
        out = os.path.join(wdir,f)
        if not os.path.exists(out):
            os.mkdir(out)
        
        cmd = os.path.join(lastools,'lasgrid.exe') + ' -i ' + non_norm + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -drop_class 7 -point_density' + \
            ' -step ' + opt['pixelsize'] + \
            ' -mem 1900 -cpu64 -temp_files "temp" -use_tile_bb -otif -utm 11N -nad83' + \
            ' -odir ' + out
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)
        
        print(str(datetime.datetime.now()) + ': ' +'point density mosaic', file = log)
        rasterlist = getfiles(out,'.tif')
        filename = studyarea + '_ptden_' + str(res) + 'm.tif'
        outpath = os.path.join(prod_loc,filename)
        mosaic_rasters(rasterlist,outpath)
        
        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `ptdens` " + str(res) + " complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise
    
    try:
        print(str(datetime.datetime.now()) + ': ' +'Generating scan angle rasters', file = log)
        f = 'scan_' + str(res) + 'm'
        out = os.path.join(wdir,f)
        if not os.path.exists(out):
            os.mkdir(out)
        
        cmd = os.path.join(lastools,'lasgrid.exe') + ' -i ' + non_norm + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -drop_class 7 -scan_angle_abs_average' + \
            ' -step ' + opt['pixelsize'] + \
            ' -mem 1900 -cpu64 -temp_files "temp" -use_tile_bb -otif -utm 11N -nad83' + \
            ' -odir ' + out

        #remove any potentially empty files to avoid errors
        remove_empty(out)
        try: 
            run_process(cmd)
            print(str(datetime.datetime.now()) + ': ' +'scan angle mosaic', file = log)
            rasterlist = getfiles(out,'.tif')
            filename = studyarea + '_scan_' + str(res) + 'm.tif'
            outpath = os.path.join(prod_loc,filename)
            mosaic_rasters(rasterlist,outpath)
        except:
            print(str(datetime.datetime.now()) + ': ' +'Scan angle rasters were not generated', file = log)
        
        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `scan` " + str(res) + " complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise

    try:
        print(str(datetime.datetime.now()) + ': ' +'Generating CHM', file = log)
        f = 'chm_' + str(res) + 'm'
        out = os.path.join(wdir,f)
        if not os.path.exists(out):
            os.mkdir(out)
        
        cmd = os.path.join(lastools,'lasgrid.exe') + ' -i ' + norm + '\\*.laz' + \
            ' -cores ' + opt['cores'] + ' -clamp_z_below 0 -elevation -highest' + \
            ' -step ' + opt['pixelsize'] + \
            ' -mem 1900 -cpu64 -temp_files "temp" -use_tile_bb -otif -utm 11N -nad83' + \
            ' -odir ' + out
        run_process(cmd)

        #remove any potentially empty files to avoid errors
        remove_empty(out)
        
        print(str(datetime.datetime.now()) + ': ' +'CHM mosaic', file = log)
        rasterlist = getfiles(out,'.tif')
        filename = studyarea + '_CHM_' + str(res) + 'm.tif'
        outpath = os.path.join(prod_loc,filename)
        mosaic_rasters(rasterlist,outpath)
        
        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `CHM` " + str(res) + " complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        exit 
    
    ###############################################################################
    t2 = datetime.datetime.now()
    print('#### ' + str(datetime.datetime.now()) + ': ' + 'END ' + str(res) + ' SURFACES PROCESSING - TOTAL TIME: ' + str(t2-t1) + ' ####', file = log)

    msgslack(MESSAGE = '#### ' + str(datetime.datetime.now()) + ': ' + 'END ' + str(res) + ' SURFACES PROCESSING - TOTAL TIME: ' + str(t2-t1) + ' ####')

    log.close()

### end of file 
###############################################################################

## How to run
# non_norm = r'C:\Data\Woodlot_0007\laz_reclass\non_norm'
# outdir = r'C:\Data\Woodlot_0007'
# studyarea = 'Woodlot0007'
# res = 1
# prod_loc = r'C:\Data\Woodlot_0007\products'
# surfaces(non_norm=non_norm,outdir=outdir,studyarea=studyarea,res=res,prod_loc=prod_loc)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    







