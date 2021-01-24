"""
A collection of methods that will write a single polygonal facet
to a binary STL file.
https://github.com/r-barnes/DEMto3D
"""

from struct import pack

#foreach triangle
#REAL32[3] - Normal vector
#REAL32[3] - Vertex 1
#REAL32[3] - Vertex 2
#REAL32[3] - Vertex 3
#UINT16 - Attribute byte count


def writeTopFacet(x, y, hs, heightmap):
    ret = bytearray()
    # Normal - A
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, heightmap[y][x])
    # Vertex 2
    ret += pack('3f', (x+1)*hs, y*hs, heightmap[y][x+1])
    # Vertex 3
    ret += pack('3f', (x+1)*hs, (y+1)*hs, heightmap[y+1][x+1])
    # End Facet
    ret += pack('h', 0)
    # Normal - B
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', (x+1)*hs, (y+1)*hs, heightmap[y+1][x+1])
    # Vertex 2
    ret += pack('3f', x*hs, (y+1)*hs, heightmap[y+1][x])
    # Vertex 3
    ret += pack('3f', x*hs, y*hs, heightmap[y][x])
    # End Facet
    ret += pack('h', 0)

    return ret

def writeBottomFacet(x, y, z, hs):
    ret = bytearray()
    # Normal - A
    ret += pack('3f', 0, 0, -1)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, z)
    # Vertex 2
    ret += pack('3f', (x+1)*hs, (y+1)*hs, z)
    # Vertex 3
    ret += pack('3f', (x+1)*hs, y*hs, z)
    # End Facet
    ret += pack('h', 0)
    # Normal - B
    ret += pack('3f', 0, 0, -1)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, z)
    # Vertex 2
    ret += pack('3f', x*hs, (y+1)*hs, z)
    # Vertex 3
    ret += pack('3f', (x+1)*hs, (y+1)*hs, z)
    # End Facet
    ret += pack('h', 0) #"Attribute byte count": Should be zero since most software does not understand anything else

    return ret

def writeNorthFacet(x, y, heightmap, hs):
    ret = bytearray()
    # Normal - A
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, 0)
    # Vertex 2
    ret += pack('3f', (x+1)*hs, y*hs, heightmap[y][x+1])
    # Vertex 3
    ret += pack('3f', x*hs, y*hs, heightmap[y][x])
    # End Facet
    ret += pack('h', 0)
    # Normal - B
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, 0)
    # Vertex 2
    ret += pack('3f', (x+1)*hs, y*hs, 0)
    # Vertex 3
    ret += pack('3f', (x+1)*hs, y*hs, heightmap[y][x+1])
    # End Facet
    ret += pack('h', 0)

    return ret

def writeSouthFacet(x, y, heightmap, hs):
    ret = bytearray()
    # Normal - A
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, 0)
    # Vertex 2
    ret += pack('3f', x*hs, y*hs, heightmap[y][x])
    # Vertex 3
    ret += pack('3f', (x+1)*hs, y*hs, heightmap[y][x+1])
    # End Facet
    ret += pack('h', 0)
    # Normal - B
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, 0)
    # Vertex 2
    ret += pack('3f', (x+1)*hs, y*hs, heightmap[y][x+1])
    # Vertex 3
    ret += pack('3f', (x+1)*hs, y*hs, 0)
    # End Facet
    ret += pack('h', 0)

    return ret

def writeEastFacet(x, y, heightmap, hs):
    ret = bytearray()
    # Normal - A
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, 0)
    # Vertex 2
    ret += pack('3f', x*hs, y*hs, heightmap[y][x])
    # Vertex 3
    ret += pack('3f', x*hs, (y+1)*hs, heightmap[y+1][x])
    # End Facet
    ret += pack('h', 0)
    # Normal - B
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, 0)
    # Vertex 2
    ret += pack('3f', x*hs, (y+1)*hs, heightmap[y+1][x])
    # Vertex 3
    ret += pack('3f', x*hs, (y+1)*hs, 0)
    # End Facet
    ret += pack('h', 0)

    return ret

def writeWestFacet(x, y, heightmap, hs):
    ret = bytearray()
    # Normal - A
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, 0)
    # Vertex 2
    ret += pack('3f', x*hs, (y+1)*hs, heightmap[y+1][x])
    # Vertex 3
    ret += pack('3f', x*hs, y*hs, heightmap[y][x])
    # End Facet
    ret += pack('h', 0)
    # Normal - B
    ret += pack('3f', 0, -1, 0)
    # Vertex 1
    ret += pack('3f', x*hs, y*hs, 0)
    # Vertex 2
    ret += pack('3f', x*hs, (y+1)*hs, 0)
    # Vertex 3
    ret += pack('3f', x*hs, (y+1)*hs, heightmap[y+1][x])
    # End Facet
    ret += pack('h', 0)

    return ret