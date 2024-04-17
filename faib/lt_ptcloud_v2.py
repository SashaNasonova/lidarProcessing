# -*- coding: utf-8 -*-
"""
Created on Mon Jul 19 11:14:26 2021

@author: SNASONOV
"""
import os, subprocess, datetime
import geopandas as gpd
import pandas as pd
from osgeo import gdal
import shutil

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
    
def copy_merged(inputfolder,basename,outputfolder):
    extlist = ['.shx','.shp','.prj','.dbf','.cpg']
    
    for ext in extlist:
        infile = os.path.join(inputfolder,basename + ext)
        try:
            shutil.copy(infile,outputfolder)
        except:
            pass 
            
def ptcloud(datloc=None,outfolder=None,clean=None,prod_loc=None,opt=None):
    #### Lidar processing, adapted from Geoff Quinn's batch file ####
    
    lastools = opt['lastools']
    
    t1 = datetime.datetime.now()    
    
    #### Create and set directories
    #datloc is the location of the input data, will be unaltered
    wdir = os.path.join(outfolder,'working') # modified point cloud location, can be deleted if space is an issue
    outdir = os.path.join (outfolder,'outdir') #outputs, deliver these 
    vectors = os.path.join(prod_loc,'vectors') #deliver these
    
    if not os.path.exists(wdir):
        os.mkdir(wdir)
        
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    
    if not os.path.exists(prod_loc):
        os.mkdir(prod_loc)
    
    if not os.path.exists(vectors):
        os.mkdir(vectors)
    
    print('Input Data: ' + datloc)
    print('Processing Start: ' + str(t1))
    
    # # ##############################################################################
    
    # Important!!! This script assumes that input data have been worked: projected,
    # compressed to laz, correct headers
    
    in_laz = getfiles(datloc,'.laz')
    print('Found ' + str(len(in_laz)) + ' laz files')
    
    if len(in_laz) == 0:
        return(print('No laz files were found, exiting'))
    else:
        pass     

    print('Running lasinfo')
    # out = os.path.join(outdir,'lasinfo') 
    # if not os.path.exists(out):
    #     os.mkdir(out)
    
    cmd = os.path.join(lastools,'lasinfo.exe') + ' -i ' + datloc + '\\*.laz' + \
            ' -odir ' + datloc + \
            ' -cd -gw -repair -otxt'
    run_process(cmd)
    
    print('Creating tile folder')
    out = os.path.join(outdir,'tile_shp')
    if not os.path.exists(out):
        os.mkdir(out)
    
    print('Creating a pre-tiling shapefile')
    out = os.path.join(outdir,'tile_shp','pre_tile_shp')
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lasboundary.exe') + ' -i ' + datloc + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -use_bb -labels' + \
        ' -odir ' + out
    run_process(cmd)
    
    print('Merging pre-tiling shapefiles') 
    shplist = getfiles(out,'.shp')
    base = 'pretiling_merged'
    name = base + '.shp'
    outpath = os.path.join(outdir,'tile_shp','pre_tile_shp',name)
    merge_shapefiles(shplist,outpath)
    
    copy_merged(os.path.join(outdir,'tile_shp','pre_tile_shp'),base,vectors) #copying to products 
    
    print('Indexing to use multicore tiling')
    cmd = os.path.join(lastools,'lasindex.exe') + ' -i ' + datloc + '\\*.laz' + \
        ' -cores ' + opt['cores']  
    run_process(cmd)
    
    # print('Tiling data, 250m and 20m overlap buffer') 
    # #-tile_ll flag can be used for offset to match to an existing raster
    # Using relatively small tiles to make sure that we don't hit the maximum allowable limit by lastools
    # May want to increase the tile size to 500m or 1km
    # Drops class 6 and 7
    # More info of tiling and buffering: https://rapidlasso.com/2015/08/07/use-buffers-when-processing-lidar-in-tiles/
    # Dec 20, 2023: changed tile_size and buffer_size to be provided in the main function.
    
    out = os.path.join(wdir,'tile')
    if not os.path.exists(out):
        os.mkdir(out)
    
    # cmd = os.path.join(lastools,'lastile.exe') + ' -i ' + datloc + '\\*.laz' + \
    #     ' -drop_class 6 7 -o "1km_tile" -tile_size 1000 -buffer 20 -flag_as_withheld -cores 7' + \
    #     ' -odir ' + out + ' -olaz'
        

    cmd = os.path.join(lastools,'lastile.exe') + ' -i ' + datloc + '\\*.laz' + \
        ' -drop_class 6 7 -o ' + opt['tile_size'] + "m_tile" \
        ' -tile_size ' + opt['tile_size'] + ' -buffer ' + opt['buffer_size'] + ' -flag_as_withheld' \
        ' -cores ' + opt['cores'] + \
        ' -odir ' + out + ' -olaz'
            
    run_process(cmd)
    
    print('Creating post tiling shapefile') 
   
    out = os.path.join(outdir,'tile_shp/post_tile_shp')
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lasboundary.exe') + ' -i ' + os.path.join(wdir,'tile') + '\\*.laz' + \
        ' -use_bb -labels -cores ' + opt['cores'] + \
        ' -oshp' + \
        ' -odir ' + out
    run_process(cmd)
    
    print('Merging post-tiling shapefiles')
    shplist = getfiles(out,'.shp')
    base = 'post_tile_merged'
    name = base + '.shp'
    outpath = os.path.join(outdir,'tile_shp','post_tile_shp',name)
    merge_shapefiles(shplist,outpath)
    
    copy_merged(os.path.join(outdir,'tile_shp','post_tile_shp'),base,vectors)
    
    print('Creating a detailed extent shapefile')
    out = os.path.join(outdir,'tile_shp/extent_tile_shp')
    if not os.path.exists(out):
        os.mkdir(out)
        
    cmd = os.path.join(lastools,'lasboundary.exe') + ' -i ' + os.path.join(wdir,'tile') + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -drop_withheld -concavity 10 -disjoint -labels' \
        ' -odir ' + out + ' -odix "_conc10" -oshp'
    run_process(cmd)
    
    print('Merging extent shapefile')
    shplist = getfiles(out,'.shp')
    base = 'detailed_extent_post_tile_merged'
    name = base + '.shp'
    outpath = os.path.join(outdir,'tile_shp','extent_tile_shp',name)
    merge_shapefiles(shplist,outpath)
    
    copy_merged(os.path.join(outdir,'tile_shp','extent_tile_shp'),base,vectors)
    
    print('Removing duplicate values')
    out = os.path.join(outdir,'non_dup')
    
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lasduplicate.exe') + ' -i ' + os.path.join(wdir,'tile') + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -unique_xyz' \
        ' -odir ' + out + ' -odix "_unique" -olaz'
    run_process(cmd)
    
    print('Indexing non-duplicate data to use multicore tiling')
    #os.chdir(os.path.join(wdir,'non_dup'))
    cmd = os.path.join(lastools,'lasindex.exe') + ' -i ' + os.path.join(outdir,'non_dup') + '\\*.laz' + \
        ' -cores ' + opt['cores'] 
    run_process(cmd)
    
    print('Running Voxel density noise classification/removal')
    
    if opt['clean'] == 'standard':
        print('Standard clean selected')
        out = os.path.join(outdir,'non_dup_clean')
        
        if not os.path.exists(out):
            os.mkdir(out)
        
        cmd = os.path.join(lastools,'lasnoise.exe') + ' -i ' + os.path.join(outdir,'non_dup') + '\\*.laz' + \
        ' -drop_class 7 -step 10 -isolated 25' \
        ' -cores ' + opt['cores'] + \
        ' -odir ' + out + ' -odix "_denoise" -olaz'
        run_process(cmd)  
        in_ind = os.path.join(outdir,'non_dup_clean')
        
    elif opt['clean'] == 'aggressive':
        print('Aggressive clean selected')
        out = os.path.join(outdir,'non_dup_clean')
        
        if not os.path.exists(out):
            os.mkdir(out)
        
        cmd = os.path.join(lastools,'lasnoise.exe') + ' -i ' + os.path.join(outdir,'non_dup') + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -drop_class 7 -step 3 -isolated 5' \
        ' -odir ' + out + ' -odix "_denoise" -olaz'
        run_process(cmd)
        in_ind = os.path.join(outdir,'non_dup_clean')
        
    else:
        print('No cleaning selected, proceeding with non-duplicate data')
        in_ind = os.path.join(outdir,'non_dup')
        
        
    print('Indexing non-duplicate data to use multicore tiling')
    cmd = os.path.join(lastools,'lasindex.exe') + ' -i ' + in_ind + '\\*.laz' + \
        ' -cores ' + opt['cores']
    run_process(cmd)
    
    print('Output noise points for checking')
    out = os.path.join(outdir,'laz_noise')
    
    if not os.path.exists(out):
        os.mkdir(out)
    
    cmd = os.path.join(lastools,'lassplit.exe') + ' -i ' + in_ind + '\\*.laz' + \
        ' -drop_withheld -keep_class 7 -merged -by_classification' \
        ' -odir ' + out + ' -o "noise.laz'
    run_process(cmd)    
    
    print('Generating normalized point cloud')
    
    if not os.path.exists(os.path.join(outdir,'chm')):
        os.mkdir(os.path.join(outdir,'chm'))
    if not os.path.exists(os.path.join(outdir,'chm','laz')):
        os.mkdir(os.path.join(outdir,'chm','laz'))
    
    out = os.path.join(outdir,'chm','laz')
    
    ## Need buffers because lasheight creates a TIN on the fly, after this point no longer need buffers
    ## Drop above some height later, want to see where the errors are first, can drop later -drop_above 80
    ## Slopes greater than 70deg and CHM greater than 4m
    cmd = os.path.join(lastools,'lasheight.exe') + ' -i ' + in_ind + '\\*.laz' + \
        ' -cores ' + opt['cores'] + \
        ' -replace_z -drop_class 7' + \
        ' -odix "_chm" -olaz' + \
        ' -odir ' + out
    run_process(cmd)
    
    print('Indexing to use multicore tiling') #getting a warning here to remove buffers
   
    #### Index to use multicore tiling
    cmd = os.path.join(lastools,'lasindex.exe') + ' -i ' + os.path.join(outdir,'chm','laz') + '\\*.laz' + \
        ' -cores ' + opt['cores'] 
    run_process(cmd)
    
    #TODO: drop buffers here
    
    #TODO: add lasinfo (check for slope violations)
    
    t2 = datetime.datetime.now()
    print('Processing time: ' + str(t2-t1))
    
    #returns non_dup or non_dup_clean and normalized laz
    return(in_ind,out)

##end of file 
###############################################################################
## How to run

# clean = 'standard' #'aggressive', 'standard', None
# datloc = r'C:\Data\Woodlot_0007\laz_reclass'
# outfolder = r'C:\Data\Woodlot_0007'
# prod_loc = r'C:\Data\Woodlot_0007\products'
# ptcloud(datloc=datloc,outfolder=outfolder,clean=clean,prod_loc=prod_loc)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    







