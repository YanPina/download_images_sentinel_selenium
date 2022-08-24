import os
import shutil
import psycopg2
from time import sleep
from pathlib import Path

import geojson
import geopandas as gpd
import shapely.wkt
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


class CheckDownload:

    def confirm_download(download_folder_selenium):
        fileends = "crdownload"
        while "crdownload" == fileends:
            sleep(3)
            newest_file = CheckDownload.latest_download_file(download_folder_selenium)
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

    def verificar_quantos_valtam(lista_cenas_baixadas, lista_cenas):
        lista_cenas_baixadas = list(dict.fromkeys(lista_cenas_baixadas))

        lista_cenas_que_faltam = len(list(set(lista_cenas_baixadas) ^ set(lista_cenas)))
        if lista_cenas_que_faltam == 1:
            print(f'\nAinda falta {lista_cenas_que_faltam} Cena...')
        else:
            print(f'\nAinda faltam {lista_cenas_que_faltam} Cenas...')



    def move_bands_to_folder(download_folder_selenium, lista_cenas_baixadas, lista_cenas, pasta_download, cena):
        for r, d, f in os.walk(download_folder_selenium):
            for file in f:
                if file.endswith(".jp2"):
                    file_path = Path(os.path.join(r, file))
                    
                    filename = Path(os.path.join(r, file)).stem
                    filename_cena = filename[17:77]

                    if (filename_cena in lista_cenas) & (filename not in lista_cenas_baixadas):
                        new_folder_cena = (f'{pasta_download}\\{filename}.jp2')
                        shutil.move(file_path, new_folder_cena)

        print(f'Download das Bandas da cena "{cena}" finalizado!\n')
    
    