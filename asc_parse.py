import sys
import cv2
import numpy as np
import os
import multiprocessing
from stltools import stlgenerator

NO_DATA = -9999

def load_asc(file_name: str):
    data = np.loadtxt(file_name, skiprows=7)

    # A bit of numpy black magic from stack overflow to remove rows/columns at the start without data
    column_index = np.argwhere(np.all(data[..., :] == NO_DATA, axis=0))
    data = np.delete(data, column_index, axis=1)
    row_index = np.argwhere(np.all(data[:, ...] == NO_DATA, axis=1))
    data = np.delete(data, row_index, axis=0)

    # If we don't do this, the data ends up mirrored.
    data = cv2.flip(data, 0)
    return data

def gen_stls_from_ascs(list_of_asc: list, list_of_files: list, scale_adjustment = 1.0, vscale = 1.0, base = 0.0):
    # This is a bit inefficient IMO, but it's important in order
    # to ensure that we generate all stl files with a uniform height
    list_of_depth_maps = [load_asc(x) for x in list_of_asc]
    print(list_of_asc)
    lowest_value = np.inf
    for d in list_of_depth_maps:
        for y in d:
            for x in y:
                if x < lowest_value and x != NO_DATA:
                    lowest_value = x
    if lowest_value != np.inf:
        print(f'Lowest elevation found: {lowest_value}, using for base for all STLs')
    else:
        lowest_value = 0
        print(f'DEM Missing data!  Needs further adjustment.  Setting lowest value to 0.')

    for index, depth_map in enumerate(list_of_depth_maps):
        list_of_depth_maps[index] = np.where(depth_map == NO_DATA, lowest_value, depth_map)
        list_of_depth_maps[index] *= vscale

    if not os.path.exists('STL'):
        os.mkdir('STL')

    list_of_stl = [f'STL\\{x}.stl' for x in list_of_files]

    for d, s in zip(list_of_depth_maps, list_of_stl):
        stlgenerator.generate_from_heightmap_array(
            d,
            destination=s,
            hsep=0,
            sep_dep=0,
            tab_size=0,
            tab_dep=0,
            anchorsize=0,
            hmin=lowest_value - base,
            vsize=1/np.sqrt(scale_adjustment+0.5),
        )


def main():
    return

if __name__ == "__main__":
    main()
