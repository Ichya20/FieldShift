"""Rank actual MODIS grid footprints wholly inside the contextual Klaten bbox."""
from __future__ import annotations
import json,math
from prepare_soil_terrain import ROOT,RAW,OUT,dump,ACCESSED,BBOX
from prepare_landcover import stats
import numpy as np
import rasterio

def main():
    raw=ROOT/'data/prepared/vegetation/raw/klaten_cropland_candidate-A2021001-A2021145.json'
    d=json.loads(raw.read_text(encoding='utf-8'))
    x0=float(d['xllcorner']);y0=float(d['yllcorner']);s=float(d['cellsize']);R=6371007.181
    with rasterio.open(RAW/'worldcover-2021-klaten.tif') as ds:
        a=ds.read(1)
        rows,cols=np.indices(a.shape)
        lon=ds.transform.c+ds.transform.a*(cols+.5)
        lat=ds.transform.f+ds.transform.e*(rows+.5)
        x=R*np.radians(lon)*np.cos(np.radians(lat));y=R*np.radians(lat)
        ix=np.floor((x-x0)/s).astype(int);iy=np.floor((y-y0)/s).astype(int)
        found=[]
        for px,py in set(zip(ix.ravel().tolist(),iy.ravel().tolist())):
            xl=x0+px*s;yl=y0+py*s
            ys=np.array([yl,yl+s]);lats=np.degrees(ys/R)
            lons=np.degrees(np.array([[xl,xl+s],[xl,xl+s]])/(R*np.cos(np.radians(lats[:,None]))))
            if lons.min()<BBOX[0] or lons.max()>BBOX[2] or lats.min()<BBOX[1] or lats.max()>BBOX[3]:continue
            clat=math.degrees((yl+s/2)/R);clon=math.degrees((xl+s/2)/(R*math.cos(math.radians(clat))))
            values=a[(ix==px)&(iy==py)]
            found.append({'latitude':clat,'longitude':clon,'sinusoidal_bounds_m':[xl,yl,xl+s,yl+s],
                'landcover_stats':stats(values)})
    found.sort(key=lambda z:(-z['landcover_stats']['cropland_fraction_valid_cells'],
        (z['longitude']-110.55)**2+(z['latitude']+7.72)**2))
    report={'prepared_utc':ACCESSED,'role':'Potential demonstration pixels, not user farms',
        'method':'Assign native WorldCover2021 cell centers to the reported MODIS sinusoidal grid; rank cells whose complete pixel footprint lies inside Klaten bbox by crop-class fraction.',
        'evaluated_interior_pixels':len(found),'ranked_pixels':found,
        'limitations':'2021 classification uncertainty and possible land-use changes; never a claim of current crop species, crop-specific rotation, ownership, or plot extent.'}
    dump(OUT/'modis-cropland-pixel-candidates.json',report)
    print(json.dumps({'evaluated':len(found),'top3':found[:3]},indent=2),flush=True)

if __name__=='__main__':main()
