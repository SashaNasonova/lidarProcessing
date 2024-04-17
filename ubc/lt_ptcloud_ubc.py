# -*- coding: utf-8 -*-
"""
Created on Mon Jul 19 11:14:26 2021

@author: SNASONOV & TGOODBODY
"""
import os, subprocess, datetime
import geopandas as gpd
import pandas as pd
from osgeo import gdal
import shutil

#####
from msgslack import msgslack
from lt_surfaces_ubc import remove_empty
#####

def getfiles(d,ext):
    paths = []
    for file in os.listdir(d):
        if file.endswith(ext):
            paths.append(os.path.join(d, file))
    return(paths) 

def run_process(cmd):
    subprocess.run(cmd,shell=True)
    #print(str(datetime.datetime.now()) + ': ' +val)
        
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
            
def ptcloud_ubc(studyarea,tile_size,buffer_size,cores,height_cutoff,datloc=None,outfolder=None,clean=None,lastools = r"C:/LAStools/bin"):
    #### LiDAR Processing, adapted from Geoff Quinn's batch file ####
     #lastools location

    #### Define options
    opt = {}
    opt['clean'] = clean
    opt['tile_size'] = str(tile_size)
    opt['buffer_size'] = str(buffer_size)
    opt['cores'] = str(cores)
    opt['height_cutoff'] = str(height_cutoff)
    
    #### Create and set directories
    #datloc is the location of the input data, will be unaltered
    outdir = os.path.join (outfolder,studyarea) #outputs, deliver these 
    prod_loc = os.path.join(outdir,'products') #deliver these
    vectors = os.path.join(prod_loc,'vectors') #deliver these
    wdir = os.path.join(outdir,'intermediate') # modified point cloud location, can be deleted if space is an issue
        
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    
    if not os.path.exists(prod_loc):
        os.makedirs(prod_loc)
    
    if not os.path.exists(vectors):
        os.mkdir(vectors)

    if not os.path.exists(wdir):
        os.mkdir(wdir)

    # create logfile for processing
    logfile = os.path.join(outdir, studyarea + '_log' + '.txt')
    log = open(logfile, "a")

    t1 = datetime.datetime.now()
    
    print(str(datetime.datetime.now()) + ': ' +'Input Data: ' + datloc, file = log)
    print('#### ' + str(datetime.datetime.now()) + ': ' + 'START POINTCLOUD PROCESSING: ' + str(t1) + ' ####', file = log)

    msgslack(MESSAGE='#### ' + str(datetime.datetime.now()) + ': ' + 'START POINTCLOUD PROCESSING: ' + str(t1) + ' ####')
    
    # # ##############################################################################
    
    # Important!!! This script assumes that input data have been worked: projected,
    # compressed to laz, correct headers
    
    in_laz = getfiles(datloc,'.laz')
    print(str(datetime.datetime.now()) + ': ' +'Found ' + str(len(in_laz)) + ' laz files', file = log)
    
    if len(in_laz) == 0:
        return(print(str(datetime.datetime.now()) + ': ' +'No laz files were found, exiting', file = log))
    else:
        pass     

    in_lax = getfiles(datloc,'.lax')
    print(str(datetime.datetime.now()) + ': ' +'Found ' + str(len(in_laz)) + ' lax files', file = log)
    
    try:
        # check that the right number of lax files exist
        if len(in_lax) != len(in_laz):
            print(str(datetime.datetime.now()) + ': ' +'Indexing inputs', file = log)
            #lasindex
            print(str(datetime.datetime.now()) + ': ' +'Indexing to use multicore tiling', file = log)
            cmd = os.path.join(lastools,'lasindex.exe') + ' -i ' + datloc + '\\*.laz' + \
                ' -cpu64 -cores ' + opt['cores'] 
            run_process(cmd)
        else:
            print(str(datetime.datetime.now()) + ': ' +'Index files already exist', file = log)
            pass
        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  Raw `lasindex` complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise

    out = os.path.join(prod_loc,'lasinfo')
    
    if not os.path.exists(out):
        os.makedirs(out)
    
    in_lasinfo = getfiles(out,'.txt')
    print(str(datetime.datetime.now()) + ': ' + 'Found ' + str(len(in_lasinfo)) + ' lasinfo files', file = log)
    
    try:
        # check that the right number of lax files exist
        if len(in_lasinfo) != len(in_laz):
            print(str(datetime.datetime.now()) + ': ' +'Running lasinfo', file = log)
            # lasinfo
            cmd = os.path.join(lastools,'lasinfo.exe') + ' -i ' + datloc + '\\*.laz' + \
                ' -odir ' + out + ' -cores ' + opt['cores'] +\
                ' -cd -gw -cpu64 -repair -otxt'
            run_process(cmd)
        else:
            print(str(datetime.datetime.now()) + ': ' + 'lasinfo files already exist', file = log)
            pass
        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `lasinfo` complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise

    out = os.path.join(wdir,'tile_shp','pre_tile_shp')
    if not os.path.exists(out):
        os.makedirs(out)
    
    in_shp = getfiles(out,'.shp')
    print(str(datetime.datetime.now()) + ': ' +'Found ' + str(len(in_shp)) + ' tile shp files', file = log)

    try:
        # check that the right number of lax files exist
        if len(in_shp) != len(in_laz):
            print(str(datetime.datetime.now()) + ': Creating pretile shapefile')
            #lasboundary pretile
            cmd = os.path.join(lastools,'lasboundary.exe') + ' -i ' + datloc + '\\*.laz' + \
                ' -use_bb -labels -cpu64 -cores ' + opt['cores'] +\
                ' -odir ' + out
            run_process(cmd)

            print(str(datetime.datetime.now()) + ': ' + 'Merging pretiling shapefiles') 
            shplist = getfiles(out,'.shp')
            base = 'pretiling_merged'
            name = base + '.shp'
            outpath = os.path.join(vectors,name)
            merge_shapefiles(shplist,outpath)
        else:
            print(str(datetime.datetime.now()) + ': ' + 'pretile shapefiles already exist', file = log)
            pass
        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `lasboundary` pretile complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise

    print(str(datetime.datetime.now()) + ': ' +'Tiling data at ' + opt['tile_size'] + 'm with ' + opt['buffer_size'] + 'm buffer', file = log) 
    # #-tile_ll flag can be used for offset to match to an existing raster
    # Using relatively small tiles to make sure that we don't hit the maximum allowable limit by lastools
    # May want to increase the tile size to 500m or 1km
    # Drops class 6 and 7
    # More info of tiling and buffering: https://rapidlasso.com/2015/08/07/use-buffers-when-processing-lidar-in-tiles/
        
    rawtiles = out = os.path.join(wdir,'tiles','raw')
    
    if not os.path.exists(out):
        os.makedirs(out)

    in_tile = getfiles(out,'.laz')
    print(str(datetime.datetime.now()) + ': ' + 'Found ' + str(len(in_tile)) + ' laz tiles', file = log)
    
    try:
        # if any tiles exist dont tile again 
        if len(in_tile) == 0:
            #print(str(datetime.datetime.now()) + ': Tiling')
            #lastile & lasindex
            #cmd = os.path.join(lastools,'lastile.exe') + ' -i ' + datloc + '\\*.laz' + \
            #' -drop_class 6 7 -o ' + opt['tile_size'] + "m_tile" ' -tile_size ' + opt['tile_size'] + ' -buffer ' + opt['buffer_size'] + ' -flag_as_withheld -cores ' + opt['cores'] + \
            #' -odir ' + out + ' -olaz -cpu64'
            #run_process(cmd)

            #lasindex
            print(str(datetime.datetime.now()) + ': ' +'Indexing tiles', file = log)
            cmd = os.path.join(lastools,'lasindex.exe') + ' -i ' + out + '\\*.laz' + \
                ' -cpu64 -cores ' + opt['cores'] 
            run_process(cmd)
        else:
            print(str(datetime.datetime.now()) + ': ' + 'Tiles already exist', file = log)
            pass
        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `lastile` & `lasindex` complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise

    # get number of tiles created
    in_tile = getfiles(out,'.laz')
  
    out = os.path.join(wdir,'tile_shp','post_tile_shp')
    if not os.path.exists(out):
        os.makedirs(out)

    in_shp = getfiles(out,'.shp')
    print(str(datetime.datetime.now()) + ': ' +'Found ' + str(len(in_shp)) + ' posttile shp files', file = log)
    
    try:
    # check that the right number of posttile shp files exist
        if len(in_shp) != len(in_tile):

            print(str(datetime.datetime.now()) + ': ' + 'Creating post tiling shapefile', file = log) 

            #lasboundary posttile
            #cmd = os.path.join(lastools,'lasboundary.exe') + ' -i ' + rawtiles + '\\*.laz' + \
            #' -use_lax -cpu64 -labels -cores ' + opt['cores'] + ' -oshp' \
            #' -odir ' + out
            #run_process(cmd)

            #remove any potentially empty files to avoid errors
            remove_empty(out)

            print(str(datetime.datetime.now()) + ': ' + 'Merging posttiling shapefiles', file = log)
            shplist = getfiles(out,'.shp')
            base = 'post_tile_merged'
            name = base + '.shp'
            outpath = os.path.join(vectors,name)
            merge_shapefiles(shplist,outpath)
        else:
            print(str(datetime.datetime.now()) + ': ' + 'Posttile shapefiles already exist', file = log)
            pass

        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `lasboundary` posttile complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise
           
    out = os.path.join(wdir,'tile_shp','extent_tile_shp')
    if not os.path.exists(out):
        os.makedirs(out)

    in_shp = getfiles(out,'.shp')
    print(str(datetime.datetime.now()) + ': ' + 'Found ' + str(len(in_shp)) + ' detailed shp files', file = log)

    try:
        # check that the right number of detailed shp files exist
        if len(in_shp) != len(in_tile):
            print(str(datetime.datetime.now()) + ': ' + 'Creating a detailed extent shapefile', file = log)
            #lasboundary detailed extent
            cmd = os.path.join(lastools,'lasboundary.exe') + ' -i ' + rawtiles + '\\*.laz' + \
                ' -drop_withheld -cpu64 -cores ' + opt['cores'] + ' -concavity 10 -disjoint -labels' \
                ' -odir ' + out + ' -odix "_conc10" -oshp'
            run_process(cmd)

            #remove any potentially empty files to avoid errors
            remove_empty(out)
        
            print(str(datetime.datetime.now()) + ': ' + 'Merging extent shapefile', file = log)
            shplist = getfiles(out,'.shp')
            base = 'detailed_extent_post_tile_merged'
            name = base + '.shp'
            outpath = os.path.join(vectors,name)
            merge_shapefiles(shplist,outpath)
        else:
            print(str(datetime.datetime.now()) + ': ' + 'Extent shapefiles already exist', file = log)
            pass

        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `lasboundary` detailed complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise
    
    nonnorm = out = os.path.join(wdir,'tiles','non_norm')
    if not os.path.exists(out):
        os.makedirs(out)

    in_dup = getfiles(out,'.laz')
    print(str(datetime.datetime.now()) + ': ' + 'Found ' + str(len(in_dup)) + ' cleaned laz files')

    try:
        if len(in_dup) != len(in_tile):
            print(str(datetime.datetime.now()) + ': ' + 'Removing duplicate values')
            #lasduplicate
            cmd = os.path.join(lastools,'lasduplicate.exe') + ' -i ' + rawtiles + '\\*.laz' + \
                ' -cores ' + opt['cores'] + ' -unique_xyz' \
                ' -odir ' + out + ' -odix "_unique" -olaz -cpu64'
            run_process(cmd)

            #lasindex
            print(str(datetime.datetime.now()) + ': ' + 'Indexing non-duplicate data to use multicore tiling', file = log)
            #os.chdir(os.path.join(wdir,'non_norm'))
            cmd = os.path.join(lastools,'lasindex.exe') + ' -i ' + out + '\\*.laz' + \
                ' -cores ' + str(cores) 
            run_process(cmd)
        else:
            print(str(datetime.datetime.now()) + ': ' + 'Unique tiles already exist', file = log)
            pass

        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `lasduplicate` & `lasindex` complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise
        
    print(str(datetime.datetime.now()) + ': ' + 'Running Voxel density noise classification/removal')
    
    out = os.path.join(prod_loc,'pointclouds','non_norm')
    
    if not os.path.exists(out):
        os.makedirs(out)

    in_norm = getfiles(out,'.laz')
    print(str(datetime.datetime.now()) + ': ' + 'Found ' + str(len(in_norm)) + ' normalized product laz files', file = log)

    try:
        if len(in_norm) != len(in_tile):
            print(str(datetime.datetime.now()) + ': Filtering Noise')
            #lasnoise
            if opt['clean'] == 'standard':
                print(str(datetime.datetime.now()) + ': ' + 'Standard clean selected', file = log)
                cmd = os.path.join(lastools,'lasnoise.exe') + ' -i ' + nonnorm + '\\*.laz' + \
                ' -cores ' + opt['cores'] + ' -drop_class 7 -step 10 -isolated 25' \
                ' -odir ' + out + ' -odix "_denoise" -olaz'
                run_process(cmd)  
                in_ind = out
                
            elif opt['clean'] == 'aggressive':
                print(str(datetime.datetime.now()) + ': ' + 'Aggressive clean selected', file = log)
                
                cmd = os.path.join(lastools,'lasnoise.exe') + ' -i ' + nonnorm + '\\*.laz' + \
                ' -cores ' + opt['cores'] + ' -drop_class 7 -step 3 -isolated 5' \
                ' -odir ' + out + ' -odix "_denoise" -olaz -cpu64'
                run_process(cmd)
                in_ind = out
                
            else:
                print(str(datetime.datetime.now()) + ': ' + 'No cleaning selected, proceeding with non-duplicate data', file = log)
                in_ind = nonnorm
        else:
            print(str(datetime.datetime.now()) + ': ' + 'Denoised tiles already exist', file = log)
            pass

        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `lasnoise` complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise

    in_lax = getfiles(out,'.lax')
    print(str(datetime.datetime.now()) + ': ' + 'Found ' + str(len(in_lax)) + ' normalized product lax files')

    try:
        if len(in_lax) != len(in_tile):
            print(str(datetime.datetime.now()) + ': Indexing')
            #lasindex    
            print(str(datetime.datetime.now()) + ': ' + 'Indexing non-duplicate data to use multicore tiling')
            cmd = os.path.join(lastools,'lasindex.exe') + ' -i ' + in_ind + '\\*.laz' + \
                ' -cpu64 -cores ' + opt['cores'] 
            run_process(cmd)
        else:
            print(str(datetime.datetime.now()) + ': ' + 'Index files already exist', file = log)
            pass

        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `lasindex` non-normalized complete."
        msgslack(MESSAGE = msg)
    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error))
        raise

    #print(str(datetime.datetime.now()) + ': ' +'Output noise points for checking')
    #out = os.path.join(wdir,'tiles','lasnoise')
    
    #if not os.path.exists(out):
    #    os.mkdir(out)
    
    #lassplit
    #cmd = os.path.join(lastools,'lassplit.exe') + ' -i ' + in_ind + '\\*.laz' + \
    #    ' -drop_withheld -keep_class 7 -merged -by_classification' \
    #    '-odir ' + out + ' -o "noise.laz'
    #run_process(cmd)    
    
    print(str(datetime.datetime.now()) + ': ' + 'Generating normalized point cloud with ' + opt['height_cutoff'] + 'm height cutoff', file = log)
    #Drops heights above 80m, but this is forest type dependent
    #In coastal areas tree heights above 80m are possible
    
    out = os.path.join(prod_loc,'pointclouds','norm')
    if not os.path.exists(out):
        os.makedirs(out)

    in_norm = getfiles(out,'.laz')
    print(str(datetime.datetime.now()) + ': ' + 'Found ' + str(len(in_lax)) + ' normalized product lax files')

    try:
        if len(in_norm) != len(in_tile):
            print(str(datetime.datetime.now()) + ': Normalizing')
            #lasheight
            cmd = os.path.join(lastools,'lasheight.exe') + ' -i ' + in_ind + '\\*.laz' + \
                ' -cores ' + opt['cores'] + ' -replace_z -drop_class 7 -drop_above ' + opt['height_cutoff'] + \
                ' -cpu64 -odix "_norm" -olaz' + \
                ' -odir ' + out
            run_process(cmd)

            print(str(datetime.datetime.now()) + ': ' + 'Indexing') #getting a warning here to remove buffers
    
            #### Index to use multicore tiling
            cmd = os.path.join(lastools,'lasindex.exe') + ' -i ' + out + '\\*.laz' + \
                ' -cpu64 -cores ' + opt['cores']
            run_process(cmd)
        else:
            print(str(datetime.datetime.now()) + ': ' + 'Normalized product files already exist', file = log)
            pass

        msg = str(datetime.datetime.now() - t1) + " -- :white_check_mark:  :  `lasheight` & `lasindex` normalized complete."
        msgslack(MESSAGE = msg)

    except Exception as error:
        msgslack(MESSAGE = " :alert: `ERROR:`  " + str(error) + ' :alert:')
        raise

    t2 = datetime.datetime.now()
    print('#### ' + str(datetime.datetime.now()) + ': ' + 'END POINTCLOUD PROCESSING - TOTAL TIME: ' + str(t2-t1) + ' ####' , file = log)

    msgslack(MESSAGE = '#### ' + str(datetime.datetime.now()) + ': ' + 'END POINTCLOUD PROCESSING - TOTAL TIME: ' + str(t2-t1) + ' ####')

    #close log
    log.close()

##end of file 
###############################################################################
## How to run

# clean = 'standard' #'aggressive', 'standard', None
# datloc = r'C:\Data\Woodlot_0007\laz_reclass'
# outfolder = r'C:\Data\Woodlot_0007'
# prod_loc = r'C:\Data\Woodlot_0007\products'
# ptcloud(datloc=datloc,outfolder=outfolder,clean=clean,prod_loc=prod_loc)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    







