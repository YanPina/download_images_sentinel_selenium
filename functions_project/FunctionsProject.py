import os
import geojson
import psycopg2
import shapely.wkt
from time import sleep
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon

class GisFunctions:
    
    def convert_3D_2D(geometry):
        #Converte a geoemetria 3D Multi/Polygons (has_z) em uma geometria 2D Multi/Polygons
        new_geo = []
        for p in geometry:
            if p.has_z:
                if p.geom_type == 'Polygon':
                    lines = [xy[:2] for xy in list(p.exterior.coords)]
                    new_p = Polygon(lines)
                    new_geo.append(new_p)
                elif p.geom_type == 'MultiPolygon':
                    new_multi_p = []
                    for ap in p:
                        lines = [xy[:2] for xy in list(ap.exterior.coords)]
                        new_p = Polygon(lines)
                        new_multi_p.append(new_p)
                    new_geo.append(MultiPolygon(new_multi_p))
        return new_geo


    def reproject_epsg(geodf):
        geodf = gpd.GeoDataFrame(geodf)
        try:
            geodf = geodf.to_crs(epsg=4326)
        except:
            geodf.crs = "EPSG:4326"

        geodf = gpd.GeoDataFrame(geodf)
        
        return geodf


    def dissolve_geometry(geodf):

        #print('\nDissolvendo geometrias...')
        geodf = geodf[~geodf.geometry.is_empty]
        geodf = gpd.GeoDataFrame(geodf)
        geodf['geometry'] = geodf.buffer(0)

        geodf = GisFunctions.reproject_epsg(geodf)
        
        geodf_dissolve = geodf.dissolve()

        geodf_dissolve = GisFunctions.reproject_epsg(geodf)
        
        #print('Geometrias dissolvidas!\n')
        return geodf_dissolve


    def feature(gdf, ee):
        g1 = shapely.wkt.loads(str(gdf.geometry[0]))                
        g2 = geojson.Feature(geometry=g1, properties={})

        feature=None

        if g2.geometry.type =='MultiPolygon':
            area = ee.Geometry.MultiPolygon(g2['geometry']['coordinates'])
            feature = ee.Feature(area)

        elif g2.geometry.type =='Polygon':
            area = ee.Geometry.Polygon(g2['geometry']['coordinates'])
            feature = ee.Feature(area)

        return feature


class DbFunctions:
    def _connection_db():
        DB_USER = os.getenv("DB_USER")
        DB_NAME = os.getenv("DB_NAME")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")

        return psycopg2.connect(f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}")


class VerifyDownload:

    def confirm_download(download_folder_selenium):
        fileends = "crdownload"
        while "crdownload" == fileends:
            sleep(3)
            newest_file = VerifyDownload.latest_download_file(download_folder_selenium)
            if "crdownload" in newest_file:
                fileends = "crdownload"
            else:
                fileends = "finalizado"
        
        return fileends

        
    def latest_download_file(download_folder_selenium):
        path = download_folder_selenium
        os.chdir(path)
        files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
        newest = files[-1]

        return newest

    
    