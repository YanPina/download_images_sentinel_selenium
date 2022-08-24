import os
import shutil
import psycopg2
from time import sleep
from pathlib import Path

import geojson
import geopandas as gpd
import shapely.wkt
from shapely.geometry import Polygon, MultiPolygon



class WebDriver:
    def SeleniumWebDriver(webdriver):

        #Configuração Selenium
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.56'

        options = webdriver.ChromeOptions()
        #options.add_argument('--headless') #Roda o webdriver em background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        #options.add_argument("--start-maximized")
        options.add_argument('--disable-extensions')
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        #User
        options.add_argument(f'user-agent={user_agent}')

        #Remove Logs desnecessários
        driver = webdriver.Chrome(executable_path=r"webdriver\\chromedriver.exe", options=options)
        driver.implicitly_wait(30)

        return driver


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
    def __connection_db():
        DB_USER = os.getenv("DB_USER")
        DB_NAME = os.getenv("DB_NAME")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")

        return psycopg2.connect(f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}")


class CheckDownload:

    def __confirm_download(download_folder_selenium):
        fileends = "crdownload"
        while "crdownload" == fileends:
            sleep(3)
            newest_file = CheckDownload.__latest_download_file(download_folder_selenium)
            if "crdownload" in newest_file:
                fileends = "crdownload"
            else:
                fileends = "finalizado"
        
        return fileends


    def __latest_download_file(download_folder_selenium):
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


    def __move_bands_to_folder(download_folder_selenium, lista_cenas_baixadas, lista_cenas, pasta_download, cena):
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
    

    def list_downloaded_scenes(pasta_download):
        lista_cenas_baixadas = []
        # r=root, d=directories, f = files
        for r, d, f in os.walk(pasta_download):
            for file in f:
                if file.endswith(".jp2"):
                    file = Path(os.path.join(r, file)).stem
                    filename_cena = file[17:77]
                    
                    lista_cenas_baixadas.append(filename_cena)

        return lista_cenas_baixadas


    
    def base_url(cena):
        number = cena[39:41]
        letra_1 = cena[41:42]
        letras_2 = cena[42:44]

        base_url = (f'https://console.cloud.google.com/storage/browser/gcp-public-data-sentinel-2/L2/tiles/{number}/{letra_1}/{letras_2}/{cena}.SAFE/GRANULE')

        return base_url


class Authentication:
    def __login_google(driver, Keys):
        try:

            email = os.getenv("EMAIL_GOOGLE")
            password = os.getenv("PASSWORD_GOOGLE")

            input_email = driver.find_element_by_xpath('/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/form/span/section/div/div/div[1]/div/div[1]/div/div[1]/input')
            sleep(2)
            input_email.send_keys(email)
            input_email.send_keys(Keys.ENTER)

            input_pass = driver.find_element_by_xpath('/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/form/span/section/div/div/div[1]/div[1]/div/div/div/div/div[1]/div/div[1]/input')
            sleep(2)
            input_pass.send_keys(password)
            input_pass.send_keys(Keys.ENTER)

            sleep(2)
        except:
            pass