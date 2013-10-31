#!/usr/bin/env python3

import sys
import json
import csv

gpx_header = """<?xml version="1.0" encoding="UTF-8"?>
<gpx
  version="1.0"
  creator="GPSBabel - http://www.gpsbabel.org"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns="http://www.topografix.com/GPX/1/0"
  xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">
"""

gpx_footer = """</gpx>
"""

gpx_bounds = """<bounds minlat="{min_lat}" minlon="{min_lon}" maxlat="{max_lat}" maxlon="{max_lon}"/>
"""

gpx_wpt = """<wpt lat="{lat}" lon="{lon}">
  <desc>{desc}</desc>
  <name>{name}</name>
  <ele>{alt}</ele>
  <speed>{speed}</speed>
  <course>{heading}</course>
</wpt>
"""

gpx_trk_header = """<trk>
"""

gpx_trk_footer = """</trk>
"""

gpx_trkseg_header = """<trkseg>
"""

gpx_trkseg_footer = """</trkseg>
"""

gpx_trkpt = """<trkpt lat="{lat}" lon="{lon}">
  <desc>{desc}</desc>
  <name>{name}</name>
  <ele>{alt}</ele>
  <speed>{speed}</speed>
  <course>{heading}</course>
</trkpt>
"""


if __name__ == '__main__':
    iname = sys.argv[1]
    oname = sys.argv[2]

    inlines = open(iname, 'r').readlines()
    outfile = open(oname, 'w')
    

    outfile.write(gpx_header)

    d = json.loads(inlines[0].strip())
    min_lat = d['lat']
    min_lon= d['lon']
    max_lat = min_lat
    max_lon = min_lon

    for line in inlines:
        d = json.loads(line.strip())
        lat = d['lat']
        lon = d['lon']

        if lat < min_lat:
            min_lat = lat
        elif lat > max_lat:
            max_lat = lat

        if lon < min_lon:
            min_lon = lon
        elif lon > max_lon:
            max_lon = lon

    outfile.write(gpx_bounds.format(min_lat=min_lat, min_lon=min_lon, max_lat=max_lat, max_lon=max_lon))

    outfile.write(gpx_trk_header)
    outfile.write(gpx_trkseg_header)

    n = 0
    for line in inlines:
        d = json.loads(line.strip())
        d['name'] = 'Waypoint %d' % (n)
        d['desc'] = 'GPS sample %d' % (n) 

        #if n%10 == 0:
        #    outfile.write(gpx_trkpt.format(**d))
        outfile.write(gpx_trkpt.format(**d))

        n += 1

    outfile.write(gpx_trkseg_footer)
    outfile.write(gpx_trk_footer)
    outfile.write(gpx_footer)
