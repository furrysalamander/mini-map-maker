# mini-map-maker
A tool for automating the workflow of converting lidar data from the USGS website into a DEM format that DEMto3D can use

To use this script, go to the USGS LidarExplorer

https://prd-tnm.s3.amazonaws.com/LidarExplorer/index.html#/

Select an area, and then click the "Download list" button under "Lidar within AOI"

This should give you a file called `downloadlist.txt`.  Simply place this text file in the same directory as the script, and then run the script.

Do note, lastools is not completely free.  This script downloads lastools automatically.  If you are using lastools in a commercial environment, you will need to pay for a license.

https://rapidlasso.com/lastools/
