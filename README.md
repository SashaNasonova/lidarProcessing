# lidarProcessing
Lidar processing routines using lastools. 

## 1.	Pre-processing
- Ensure correct projection (epsg:3005)
- Ensure correct point classification 
- Laz format

## 2.	Point cloud processing
- Run lasinfo to create per tile metadata (compute point density (-cd), repair headers (-repair) and compute the gps week (-gw)
- Create pre-tiling shapefile
- Index input data to use multicore processing
- Tile data (250m with 20m buffers) and drop class 6 and 7
- Create post-tiling shapefile
- Create a detailed extent shapefile
- Remove duplicates
- Denoise
- Index cleaned data to use multicore processing
- Generate a normalized point cloud (Current script drops heights above 80m, the intent is to remove air hits but tree heights above 80m are possible in coastal areas. This value may need to be changed.)
- Index normalized point cloud for processing

# 3.	Surface generation
- Digital elevation model (DEM) 
- Digital surface model (DSM)
- Canopy height model (CHM)
- Point density raster
- Scan angle raster

# 4.	Canopy metrics
- Height metrics (min, max, avg, std, ske, kur, qav)
- Height percentiles (2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98)
- Canopy cover metrics (inverse of cov and dns)
- Bincentiles (2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98)
- Intensity metrics (min, max, avg, std, ske, kur, qav)
- Intensity percentiles (2 5 10 15 20 25 30 40 50 60 70 75 80 85 90 95 98)
- Vertical complexity index (vertical bins 1, 5, 10, 15)

# Pre-processing
Getting the data ready is the most labour-intensive part of the process. ALS point cloud data is usually delivered in las or laz formats. The point cloud data needs to be checked for errors and pre-processed to the specifications below. 
Format: .laz
Classes: 1 (undefined), 2 (ground), 6 (buildings), 7 (noise), 9 (water) *6, 7, 9 are optional
Horizontal datum: epsg:3005 
Vertical datum:	cgvd2013

1.	Run lasinfo on each file (with repair headers flag), run las_tabulate to create a metadata table
2.	Check projection (horizontal and vertical datum), point density, scan angle, acquisition date and point classification
3.	May need to:
- Reproject or assign a projection
- Reclass points 

Sometimes the projection is not defined, request data acquisition report or check coordinate numbers in QT Reader/Cloud Compare, usually BC Albers (3005) or NAD 1983 UTM. The filename of the point files may also state the projection (bc_092g028_2_4_1_xyes_8_utm10_20170713, NAD 1983 UTM Zone 10N).

The lt_prep.py script has the necessary functions to reproject and reclass. Please evaluate your dataset to determine what needs to be done. 

# Executing with test data
- run lt_main.py with test data first
- change line 18 to the script location
- change line 27 to lastools bin directory location
- change line 37 to processing root directory

# Installation
Required packages: geopandas, pandas, osgeo, use provided .yml file to create an Anaconda virtual environment.
