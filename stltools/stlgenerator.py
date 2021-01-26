"""
A collection of functions to generate a 3D stl
model using various data sets.
https://github.com/r-barnes/DEMto3D
"""

import functools
import math
import numpy as np
from struct import pack
from . import writefacets
from multiprocessing import Pool

def CalculateRow(heightmap, y, h_scale):
    facets = bytearray()
    height = heightmap.shape[0] - 1
    width  = heightmap.shape[1] - 1
    facets += writefacets.writeEastFacet(x=0,     y=y, heightmap=heightmap, hs=h_scale)
    facets += writefacets.writeWestFacet(x=width, y=y, heightmap=heightmap, hs=h_scale)
    for x in range(width):
        if y == 0:
            facets += writefacets.writeNorthFacet(x=x, y=y,   heightmap=heightmap, hs=h_scale)
        elif y == height-1:
            facets += writefacets.writeSouthFacet(x=x, y=y+1, heightmap=heightmap, hs=h_scale)
        facets += writefacets.writeBottomFacet(x=x, y=y, z=0, hs=h_scale)
        facets += writefacets.writeTopFacet   (x=x, y=y, hs=h_scale, heightmap=heightmap)
    return facets

np.set_printoptions(threshold=np.inf)

def generate_from_heightmap_array(heightmap, destination, hsize=1, vsize=1, base=0, hsep=0.6, anchorsize=0.75, sep_dep=0.1, tab_dep=0.3, tab_size=0.5, objectname="DEM 3D Model", multiprocessing=True, hmin = None, hmax = None):
    #A binary STL file has an 80-character header (which is generally ignored,
    #but should never begin with "solid" because that may lead some software to
    #assume that this is an ASCII STL file). 
    if len(objectname)>80:
        raise Exception("STL object name must be 80 characters or less!")


    if not isinstance(heightmap,list):
        heightmap = [heightmap]

    hmin = hmin or min([hm.min() for hm in heightmap])
    hmax = hmax or max([hm.max() for hm in heightmap])
    vsize /= 750
    heightmap       -= hmin                                              #Set base elevation to 0
    heightmap       *= vsize#/hmax                                        #Convert heightmap from input units to output units
    heightmap       += base                                              #Add the indicated amount of base (in output units)
    h_scale = hsize/min((heightmap[0].shape[1], heightmap[0].shape[0]))  #Find the horizontal scale
    tab_size         = math.ceil(tab_size/h_scale)                       #Convert tab size from output units to cells
    separation_array = np.zeros(shape=(1,heightmap[0].shape[1]))+sep_dep #Separation array equal to width of piece set to sep_dep height
    separation_array[0,0:tab_size] = tab_dep                             #Add tabs
    separation_array[0,-tab_size:] = tab_dep                             #Add tabs
    separation_array = np.repeat(separation_array, repeats=math.ceil(hsep/h_scale), axis=0) #Make sure separation array is appropriately wide
    heightmap_new    = [heightmap[0]]
    for hm in heightmap[1:]:
        heightmap_new += [separation_array, hm]
    heightmap = np.concatenate(heightmap_new, axis=0)

    if anchorsize>0:
        pad_array = np.zeros((math.ceil(anchorsize/h_scale), heightmap.shape[1]))+heightmap.max()  #Should be ~0.75 inches
        heightmap = np.concatenate((pad_array, separation_array, heightmap, separation_array, pad_array), axis=0)


    percentComplete = 0
    height = heightmap.shape[0] - 1
    width  = heightmap.shape[1] - 1
    with open(destination, 'wb') as f:
        # Write the number of facets
        numTopBottomFacets  = 4 * width * height
        numNorthSouthFacets = 4 * width 
        numEastWestFacets   = 4 * height 

        if multiprocessing:
            pool   = Pool()
            facets = pool.starmap(CalculateRow, [(heightmap,y,h_scale) for y in range(height)])
            facets = b''.join(facets)
        else:
            facets = bytearray()
            # Generate the bottom plane.
            for y in range(height):
                if int(float(y) / height * 100) != percentComplete:
                    percentComplete = int(float(y) / height * 100)
                    print("Writing STL File... {0}% Complete".format(percentComplete))
                facets += CalculateRow(heightmap, y, h_scale)

        # Write the file header
        f.write(pack('80s', objectname.encode()))
        #Following the header is a 4-byte little-endian unsigned integer
        #indicating the number of triangular facets in the file. Following that
        #is data describing each triangle in turn. The file simply ends after
        #the last triangle.
        f.write(pack('<i', numTopBottomFacets + numNorthSouthFacets + numEastWestFacets))

        f.write(facets)

    # Finished writing to file
    print("File saved as: " + destination)
