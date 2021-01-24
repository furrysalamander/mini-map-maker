import os
import sys
import zipfile
import asc_parse
import re
import wget
import shutil
import multiprocessing
import urllib.request as request
from contextlib import closing
import shutil

GRID_EXE = "GridSurfaceCreate64.exe"
D2A_EXE = "DTM2ASCII.exe"
LASTOOLS_URL = "http://lastools.github.io/download/LAStools.zip"
BLAST2DEM_EXE = "LAStools\\bin\\blast2dem.exe"
LAS2LAS_EXE = "LAStools\\bin\\las2las.exe"

# A decimal value that will decrease the output file size as it increases
REDUCE_BY = 1.0

# Disable this option if you want to generate a seperate DEM/STL for each LAS tile.
MERGE_LAS = False

# Generate 3D models
GENERATE_STLS = True

# Delete LAS Directory when finished
DELETE_LAS = False

# Enabling this option will generate .prj files for each generated .asc file.  This requires blast2dem,
# a closed source utility that is part of lastools.  If you enable this option, lastools will be automatically
# downloaded an unzipped, however, the output may not be used for commercial purposes unless you purchase
# a lastools license.  This option is only necessary if you plan on using the DEMto3D plugin that is part of
# QGIS.  More information about lastools licensing is available here:
# https://lastools.github.io/LICENSE.txt
QGIS_COMPATIBLE_DEM = False


# lastools isn't completely free/open source, so we can't distribute it with the program.
def install_lastools():
    file_name = wget.filename_from_url(LASTOOLS_URL)
    if not os.path.exists(BLAST2DEM_EXE):
        print('lastools missing, downloading...')
        with closing(request.urlopen(LASTOOLS_URL)) as r:
            with open(file_name, 'wb') as f:
                shutil.copyfileobj(r, f)
        with zipfile.ZipFile(file_name, "r") as zip_ref:
            zip_ref.extractall("")
        os.remove(file_name)


def get_file_from_url(url, file_name):
    # This is a pattern you'll see several times.  I don't want to have to
    # redo the whole process if it fails along the way.
    if os.path.exists(file_name):
        print(f"{file_name} already downloaded, skipping...")
        return
    with closing(request.urlopen(url)) as r:
        with open(file_name, 'wb') as f:
            shutil.copyfileobj(r, f)
    print(f"Downloaded {url}")


def unzip_to_las(file_name, las_name):
    print(f'Unzipping {file_name}')
    if os.path.exists(las_name):
        print(f'{las_name} already exists, skipping...')
        return
    with zipfile.ZipFile(file_name, "r") as zip_ref:
        zip_ref.extractall("LAS")


def main():
    # For each tile in the USGS dataset, download the zip
    f = open(sys.argv[1])
    list_of_urls = []
    list_of_zip = []

    # TODO check if first line is a URL or not

    for line in f:
        if not line.rstrip('\n').endswith('.zip'):
            continue
        print(line := line.rstrip('\n'))
        file_name = wget.filename_from_url(line)
        list_of_zip.append(file_name)
        list_of_urls.append(line)

    # This is the definitive list of all file names for each phase of the pipeline from here out.
    list_of_files = [x.removesuffix('.zip') for x in list_of_zip]

    list_of_las = [f'LAS\\{x}.las' for x in list_of_files]

    if not os.path.exists('LAS'):
        os.mkdir('LAS')

    with multiprocessing.Pool(16) as p:
        p.starmap(get_file_from_url, zip(list_of_urls, list_of_zip))
        # Unzip each zip file that was downloaded
        p.starmap(unzip_to_las, zip(list_of_zip, list_of_las))

    if MERGE_LAS:
        list_of_files = [list_of_files[0]]

    # Prep the list of DTM files
    list_of_dtm = [f'DTM\\{x}.dtm' for x in list_of_files]

    if not os.path.exists('DTM'):
        os.mkdir('DTM')

    print("\nGenerating .dtm files...\n")

    for l, d in zip(list_of_las, list_of_dtm):
        print(d)
        if os.path.exists(d):
            continue
        # If necessary, make sure all las files get combined into one DTM
        if MERGE_LAS:
            os.system(f'{GRID_EXE} {d} {REDUCE_BY} M M 0 0 0 0 LAS\\*.las')
        else:
            os.system(f'{GRID_EXE} {d} {REDUCE_BY} M M 0 0 0 0 {l}')

    if not os.path.exists('ASC'):
        os.mkdir('ASC')

    list_of_asc = [f'ASC\\{x}.asc' for x in list_of_files]

    # Convert all the dtm files into asc files
    print("\nGenerating .asc files...\n")
    for d, a in zip(list_of_dtm, list_of_asc):
        print(a)
        if os.path.exists(a):
            pass
        os.system(f'{D2A_EXE} /raster {d} {a}')

    if QGIS_COMPATIBLE_DEM:
        install_lastools()
        list_of_prj = [f'LAS\\{x}.prj' for x in list_of_files]
        # Use lastools to generate the prj file that QGIS will need
        for l, p in zip(list_of_las, list_of_prj):
            os.system(f'{BLAST2DEM_EXE} -i {l} -oasc')
            shutil.copy(p, 'ASC')

    # Delete the directories used for the intermediate steps
    print("Cleaning up...")
    if DELETE_LAS:
        shutil.rmtree('LAS')
    shutil.rmtree('DTM')

    if GENERATE_STLS:
        asc_parse.gen_stls_from_ascs(list_of_asc, list_of_files)

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        # On Windows calling this function is necessary.
        multiprocessing.freeze_support()
    # Just in case the user doesn't pass in the file name, assume it's what the USGS names it.
    sys.argv.append('downloadlist.txt')
    # sys.argv.append('downloadlist2.txt')
    main()
