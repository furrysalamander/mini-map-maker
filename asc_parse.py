import sys
import cv2
import numpy as np
from stltools import stlgenerator

def load_asc(file_name: str):
    data = np.loadtxt(file_name, skiprows=7)
    return data


def gen_stl_from_asc(file_name: str):
    data = load_asc(file_name)
    # dsize = tuple([int(x * 0.6) for x in reversed(data.shape)])
    # data = cv2.flip(cv2.resize(data, dsize, interpolation=cv2.INTER_CUBIC), 0)
    data = cv2.flip(data, 0)

    # A bit of numpy black magic from stack overflow to remove rows/columns at the start without data
    column_index = np.argwhere(np.all(data[..., :] == -9999, axis=0))
    data = np.delete(data, column_index, axis=1)
    row_index = np.argwhere(np.all(data[:, ...] == -9999, axis=1))
    data = np.delete(data, row_index, axis=0)

    stlgenerator.generate_from_heightmap_array(
        data,
        destination=file_name.rstrip('.asc')+'.stl',
        hsep=0,
        sep_dep=0,
        tab_size=0,
        tab_dep=0,
        anchorsize=0,
    )


def main():
    gen_stl_from_asc(sys.argv[1])
    return


if __name__ == "__main__":
    #sys.argv.append("test2.asc")
    sys.argv.append("ASC\\USGS_LPC_UT_WasatchFault_L3_2013_12TVK4400055000_LAS_2016.asc")
    main()
