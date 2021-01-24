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
REDUCE_BY = 1

# Disable this option if you want to generate a seperate DEM for each LAS tile.
MERGE_LAS = False


# lastools isn't completely free/open source, so we can't distribute it with the program.
def install_lastools():
    file_name = wget.filename_from_url(LASTOOLS_URL)
    if not os.path.exists(BLAST2DEM_EXE):
        print('Installing lastools...')
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
        print(f"{file_name} downloaded, skipping...")
        return
    with closing(request.urlopen(url)) as r:
        with open(file_name, 'wb') as f:
            shutil.copyfileobj(r, f)
    print(f"Downloaded {url}")


def unzip_to_las(list_of_zip) -> list:
    list_of_las = []
    for name in list_of_zip:
        print(name)
        las_name = "LAS\\" + name.rstrip('.zip') + '.las'
        list_of_las.append(las_name)
        if os.path.exists(las_name):
            continue
        with zipfile.ZipFile(name, "r") as zip_ref:
            zip_ref.extractall("LAS")
    return list_of_las


def main():
    install_lastools()
    
    # For each tile in the USGS dataset, download the zip
    f = open(sys.argv[1])
    list_of_urls = []
    list_of_zip = []
    for line in f:
        if not line.rstrip('\n').endswith('.zip'):
            continue
        print(line := line.rstrip('\n'))
        file_name = wget.filename_from_url(line)
        list_of_zip.append(file_name)
        list_of_urls.append(line)
    
    with multiprocessing.Pool(16) as p:
        p.starmap(get_file_from_url, zip(list_of_urls, list_of_zip))

    # Unzip each zip file that was downloaded
    list_of_las = unzip_to_las(list_of_zip)
    # This is the definitive list of all file names for each phase of the pipeline from here out.
    list_of_files = [x.rstrip('.zip') for x in list_of_zip]

    # if MERGE_LAS:
    #     las2las_cmd = f'{LAS2LAS_EXE} -i LAS\\*.las -o LAS\\tmp_las.las -merged -keep_every_nth 4'
    #     # las2las_cmd = f'{LAS2LAS_EXE} -i LAS\\*.las -o LAS\\tmp_las.las -merged -drop_every_nth 2'
    #     print(las2las_cmd)
    #     os.system(las2las_cmd)
    #     shutil.move("LAS\\tmp_las.las", list_of_las[0])
    #     list_of_las = [list_of_las[0]]
    #     list_of_zip = [list_of_zip[0]]

    # Prep the list of DTM files
    list_of_dtm = []
    for z in list_of_zip:
        list_of_dtm.append(f'DTM\\{z.rstrip(".zip") + ".dtm"}')
    if not os.path.exists('DTM'):
        os.mkdir('DTM')

    # If necessary, make sure all las files get combined into one DTM
    print("\nGenerating .dtm files...\n")
    if MERGE_LAS:
        list_of_dtm = [list_of_dtm[0]]
        list_of_zip = [list_of_zip[0]]
    for l, d in zip(list_of_las, list_of_dtm):
        print(d)
        if os.path.exists(d):
            continue
        if MERGE_LAS:
            os.system(f'{GRID_EXE} {d} {REDUCE_BY} M M 0 0 0 0 LAS\\*.las')
        else:
            os.system(f'{GRID_EXE} {d} {REDUCE_BY} M M 0 0 0 0 {l}')

    if not os.path.exists('ASC'):
        os.mkdir('ASC')
    list_of_asc = []
    for z in list_of_zip:
        list_of_asc.append(f'ASC\\{z.rstrip(".zip") + ".asc"}')
    # Convert all the dtm files into asc files
    print("\nGenerating .asc files...\n")
    for d, a in zip(list_of_dtm, list_of_asc):
        print(a)
        if os.path.exists(a):
            pass
        os.system(f'{D2A_EXE} /raster {d} {a}')

    name_of_prj = list_of_las[0].rstrip(".las") + ".prj"
    # Use lastools to generate the prj file that QGIS will need
    os.system(f'{BLAST2DEM_EXE} -i {list_of_las[0]} -oasc')

    shutil.copy(name_of_prj, 'ASC')

    # Delete the directories used for the intermediate steps
    print("Cleaning up...")
    shutil.rmtree('LAS')
    shutil.rmtree('DTM')
    for a in list_of_asc:
        asc_parse.gen_stl_from_asc(a)

if __name__ == "__main__":
    # Just in case the user doesn't pass in the file name, assume it's what the USGS names it.
    sys.argv.append('downloadlist.txt')
    # sys.argv.append('downloadlist2.txt')
    main()
