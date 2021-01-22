import os
import sys
import zipfile
import wget
import shutil
import urllib.request as request
from contextlib import closing
import shutil

GRID_EXE = "GridSurfaceCreate64.exe"
D2A_EXE = "DTM2ASCII.exe"
LASTOOLS_URL = "http://lastools.github.io/download/LAStools.zip"
BLAST2DEM_EXE = "LAStools\\bin\\blast2dem.exe"

# Disable this option if you want to generate a seperate DEM for each LAS tile.
MERGE_LAS = True

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

def main():
    install_lastools()
    
    # For each tile in the USGS dataset, download the zip
    f = open(sys.argv[1])
    list_of_zip = []
    for line in f:
        print(line := line.rstrip('\n'))
        file_name = wget.filename_from_url(line)
        list_of_zip.append(file_name)
        # This is a pattern you'll see several times.  I don't want to have to
        # redo the whole process if it fails along the way.
        if os.path.exists(file_name):
            continue
        with closing(request.urlopen(line)) as r:
            with open(file_name, 'wb') as f:
                shutil.copyfileobj(r, f)
    
    # Unzip each zip file that was downloaded
    list_of_las = []
    for name in list_of_zip:
        print(name)
        las_name = "LAS\\" + name.rstrip('.zip') + '.las'
        list_of_las.append(las_name)
        if os.path.exists(las_name):
            continue
        with zipfile.ZipFile(name, "r") as zip_ref:
            zip_ref.extractall("LAS")

    # Prep the list of DTM files
    list_of_dtm = []
    for z in list_of_zip:
        list_of_dtm.append(f'DTM\\{z.rstrip(".zip") + ".dtm"}')
    if not os.path.exists('DTM'):
        os.mkdir('DTM')
    # If necessary, make sure all las files get combined into one DTM
    if MERGE_LAS:
        list_of_dtm = [list_of_dtm[0]]
        list_of_zip = [list_of_zip[0]]
    for l, d in zip(list_of_las, list_of_dtm):
        print(d)
        if os.path.exists(d):
            continue
        if MERGE_LAS:
            os.system(f'{GRID_EXE} {d} 1 M M 0 0 0 0 LAS\\*.las')
        else:
            os.system(f'{GRID_EXE} {d} 1 M M 0 0 0 0 {l}')

    if not os.path.exists('ASC'):
        os.mkdir('ASC')
    list_of_asc = []
    for z in list_of_zip:
        list_of_asc.append(f'ASC\\{z.rstrip(".zip") + ".asc"}')
    # Convert all the dtm files into asc files
    for d, a in zip(list_of_dtm, list_of_asc):
        print(a)
        if os.path.exists(a):
            continue
        os.system(f'{D2A_EXE} /raster {d} {a}')

    name_of_prj = list_of_las[0].rstrip(".las") + ".prj"
    # Use lastools to generate the prj file that QGIS will need
    os.system(f'{BLAST2DEM_EXE} -i {list_of_las[0]} -oasc')

    shutil.copy(name_of_prj, 'ASC')

    # Delete the directories used for the intermediate steps
    print("Cleaning up...")
    shutil.rmtree('LAS')
    shutil.rmtree('DTM')
    

if __name__ == "__main__":
    # Just in case the user doesn't pass in the file name, assume it's what the USGS names it.
    sys.argv.append('downloadlist.txt')
    main()