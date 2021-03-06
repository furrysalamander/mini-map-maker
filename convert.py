import os
import sys
import zipfile
import asc_parse
import wget
import multiprocessing
import urllib.request as request
from contextlib import closing
import argparse
import shutil
import glob

# A decimal value that will decrease the output file size as it increases
REDUCE_BY = 1.0

# A decimal value that will make artificially make things taller as it increases
VERTICAL_SCALE = 1.0

# A decimal value that sets the base height of the model
BASE_HEIGHT = 0.0

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

if getattr(sys, 'frozen', False):
    APPLICATION_PATH = os.path.dirname(sys.executable)
elif __file__:
    APPLICATION_PATH = os.path.dirname(__file__)

GRID_EXE = os.path.join(APPLICATION_PATH, "GridSurfaceCreate64.exe")
D2A_EXE = os.path.join(APPLICATION_PATH, "DTM2ASCII.exe")
LASZIP_EXE = os.path.join(APPLICATION_PATH, "laszip-cli.exe")
LASTOOLS_URL = "http://lastools.github.io/download/LAStools.zip"
BLAST2DEM_EXE = os.path.join(APPLICATION_PATH, "LAStools\\bin\\blast2dem.exe")
LAS2LAS_EXE = os.path.join(APPLICATION_PATH, "LAStools\\bin\\las2las.exe")

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


def generate_dem_from_las(las_name, dem_name, filter: float = None, reduce_by: float = 1.0):
    global GRID_EXE
    if filter:
        GRID_EXE += f' /spike:{filter}'
    if os.path.exists(dem_name):
        print(f'{dem_name} already exists, skipping...')
        return
    print(f'Generating {dem_name}')
    os.system(f'{GRID_EXE} {dem_name} {reduce_by} M M 0 0 0 0 {las_name}')


def unzip_laz_file(laz_name, las_name):
    if os.path.exists(las_name):
        print(f'{las_name} already exists, skipping...')
        return
    print(f'Unzipping {laz_name} to {las_name}')
    os.system(f'{LASZIP_EXE} -i {laz_name} -o {las_name}')


def main():
    global VERTICAL_SCALE
    global BASE_HEIGHT
    global REDUCE_BY
    global MERGE_LAS
    global GENERATE_STLS
    global DELETE_LAS
    global QGIS_COMPATIBLE_DEM
    global GRID_EXE

    parser = argparse.ArgumentParser(description='A utility for automatically generating 3D printable STLs from USGS lidar scans.')
    # Just in case the user doesn't pass in the file name, assume it's what the USGS names it.
    parser.add_argument('--input', '-i', type=str, default='downloadlist.txt', help='The name of the file containing the URLs of all of the lidar scan data.')
    parser.add_argument('--reduce', '-r', type=float, default=REDUCE_BY, help='A decimal value that will decrease the output file size as it increases.  The default value is 1.0')
    parser.add_argument('--vscale', '-v', type=float, default=VERTICAL_SCALE, help='A decimal value that will make artificially make things taller as it increases.  The default value is 1.0')
    parser.add_argument('--base', '-b', type=float, default=BASE_HEIGHT, help='A decimal value that sets the base height of the model.  The default value is 0.0')
    parser.add_argument('--merge', '-m', action='store_true', help='Using this flag will merge all of the point clouds into one file before converting into a DEM.')
    parser.add_argument('--no_stl', '-s', action='store_false', help='Using this flag will disable STL generation.')
    parser.add_argument('--cleanup', '-c', action='store_true', help='Using this flag will cause the program to automatically delete the unzipped point cloud files after running.')
    parser.add_argument('--filter', '-f', type=float, default=False, help='A percent value (0-100, for the slope of the points being smoothed) that will enable the spike smoothing option.  This is good if you have points that are floating way up above the model and causing spikes in your final model.')
    parser.add_argument('--prj', '-p', action='store_true', help='Using this flag will cause the program to automatically download and use lastools to generate projection files for the elevation models.  This is important if you want to generate the STLs yourself in QGIS, but it means you\'ll have to be mindful of lastool\'s license limitations.  More info on lastool\'s website.')
    parser.add_argument('--external_files', '-e', action='store_true', default=False, help='Using this flag will grab las/laz files from the LAS directory instead of downloading them from an input list.')
    #parser.add_argument('--help', '-h', action='help')

    args = parser.parse_args()

    VERTICAL_SCALE = args.vscale
    BASE_HEIGHT = args.base
    REDUCE_BY = args.reduce
    MERGE_LAS = args.merge
    GENERATE_STLS = args.no_stl
    DELETE_LAS = args.cleanup
    QGIS_COMPATIBLE_DEM=args.prj

    if args.filter:
        GRID_EXE += f' /spike:{args.filter}'

    if not args.external_files:
        # For each tile in the USGS dataset, download the zip
        f = open(args.input)
        list_of_urls = []
        list_of_zip = []

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

    list_of_laz = list(glob.glob('LAS\\*.laz'))

    if list_of_laz:
        print("LAZ files detected, unzipping...")
        with multiprocessing.Pool() as p:
            p.starmap(unzip_laz_file, zip(list_of_laz, [x.removesuffix('.laz') + '.las' for x in list_of_laz]))

    list_of_las = list(glob.glob('LAS\\*.las'))
    list_of_files = [os.path.basename(x).removesuffix('.las') for x in list_of_las]

    if MERGE_LAS:
        list_of_files = [list_of_files[0]]

    # Prep the list of DTM files
    list_of_dtm = [f'DTM\\{x}.dtm' for x in list_of_files]

    if not os.path.exists('DTM'):
        os.mkdir('DTM')

    print("\nGenerating .dtm files...\n")

    # If necessary, make sure all las files get combined into one DTM
    if MERGE_LAS:
        os.system(f'{GRID_EXE} {list_of_dtm[0]} {REDUCE_BY} M M 0 0 0 0 LAS\\*.las')
    else:
        with multiprocessing.Pool() as p:
            p.starmap(generate_dem_from_las, zip(list_of_las, list_of_dtm, [args.filter] * len(list_of_las), [REDUCE_BY] * len(list_of_las)))

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

    if GENERATE_STLS:
        asc_parse.gen_stls_from_ascs(
            list_of_asc=list_of_asc,
            list_of_files=list_of_files,
            scale_adjustment=REDUCE_BY,
            vscale=VERTICAL_SCALE,
            base=BASE_HEIGHT,
        )

    # Delete the directories used for the intermediate steps
    print("Cleaning up...")
    if DELETE_LAS:
        shutil.rmtree('LAS')
    shutil.rmtree('DTM')

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        # On Windows calling this function is necessary.
        multiprocessing.freeze_support()
    main()
