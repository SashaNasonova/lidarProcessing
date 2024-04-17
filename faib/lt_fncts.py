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
            