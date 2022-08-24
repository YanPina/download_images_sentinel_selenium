import os
from tabnanny import check
import ee
import shutil
from time import sleep
from pathlib import Path
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from functions_project.FunctionsProject import GisFunctions, CheckDownload

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

class Download_Cenas:
    def download_bandas(lista_cenas, pasta_download, download_folder_selenium):

        print('\n\n------ Iniciando Download e Processamento das Cenas... ------')

        lista_cenas_baixadas = []
        # r=root, d=directories, f = files
        for r, d, f in os.walk(pasta_download):
            for file in f:
                if file.endswith(".jp2"):
                    file = Path(os.path.join(r, file)).stem
                    filename_cena = file[17:77]
                    
                    lista_cenas_baixadas.append(filename_cena)

        #Exclui Duplicados
        lista_cenas = list(dict.fromkeys(lista_cenas))

        #Reverte a ordem pra baixar as cenas mais recentes
        lista_cenas.reverse()

        for cena in lista_cenas:
            
            #Aguarda a confirmação de download de todas as bandas da cena para prosseguir para a próxima cena
            CheckDownload.confirm_download(download_folder_selenium)

            if cena not in lista_cenas_baixadas:

                CheckDownload.verificar_quantos_valtam(lista_cenas_baixadas, lista_cenas)

                number = cena[39:41]
                letra_1 = cena[41:42]
                letras_2 = cena[42:44]

                band_link_part_1 = cena[38:44]
                band_link_part_2 = cena[11:26]

                base_url = (f'https://console.cloud.google.com/storage/browser/gcp-public-data-sentinel-2/L2/tiles/{number}/{letra_1}/{letras_2}/{cena}.SAFE/GRANULE')

                driver.get(base_url)


                try:
                    email = 'testeuserselenium@gmail.com'
                    password = 'P@sstest'

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

                folder_data = driver.find_element_by_xpath('//*[@id="_0rif_cfc-table-caption-0-row-0"]/td[2]')
                sleep(1)
                folder_data.click()

                sleep(2)

                img_data = driver.find_element_by_xpath('//*[@id="_0rif_cfc-table-caption-0-row-2"]/td[2]/div/span')
                sleep(1)
                img_data.click()

                sleep(2)

                r_10 = driver.find_element_by_xpath('//*[@id="_0rif_cfc-table-caption-0-row-0"]/td[2]/div/span')
                sleep(1)
                r_10.click()

                print(f'\nFazendo download das bandas da cena: "{cena}"')


                download_band_4 = driver.find_element_by_xpath(f'//*[@title="Fazer o download de {band_link_part_1}_{band_link_part_2}_B04_10m.jp2"]')
                sleep(2)
                download_band_4.click()

                sleep(3)

                download_band_8 = driver.find_element_by_xpath(f'//*[@title="Fazer o download de {band_link_part_1}_{band_link_part_2}_B08_10m.jp2"]')
                sleep(2)
                download_band_8.click()


                #Aguarda a confirmação de download de todas as bandas da cena para prosseguir para a próxima cena
                CheckDownload.confirm_download(download_folder_selenium)
    
                try:
                    #Move as bandas baixadas para o diretório escolhido
                    CheckDownload.move_bands_to_folder(download_folder_selenium, lista_cenas_baixadas, lista_cenas, pasta_download, cena)

                    lista_cenas_baixadas.append(cena)
                except:
                    print('\n\nErro ao mover banda baixada para a pasta de destino!!\nPor favor, configure o diretório de download padrão do selenium no arquivo sentinel_download_images.py(linha 36) e tente novamente!')
                    pass

        print('\n\n -------- Download das cenas finalizados!! --------')


class DetectarCenas:
    def cenas(gdf, date_range):
        lista_cenas = []

        # Trigger the authentication flow gee.
        #ee.Authenticate()

        # Initialize the library gee.
        ee.Initialize()
        
        gdf = GisFunctions.dissolve_geometry(gdf)

        gdf=gdf.convex_hull

        feature = GisFunctions.feature(gdf, ee)

        ee_object = ee.FeatureCollection(feature)

        s2 = ee.ImageCollection("COPERNICUS/S2_SR")

        
        print('\nCenas encontradas:\n')
        for data in date_range:

            td = timedelta(4)
            start = str(datetime.strptime(data, '%Y-%m-%d').date())
            end = str(datetime.strptime(data, '%Y-%m-%d').date() + td)

            s2_filter = s2.filterBounds(ee_object) \
                        .filterDate(start, end)

            for i in range(len((s2_filter.getInfo()['features']))):
                properties = s2_filter.getInfo()['features'][i]['properties']

                product_id = properties['PRODUCT_ID']
                print(product_id)

                lista_cenas.append(product_id)

            len_lista_cenas = len(lista_cenas)
        print(f'\n\nForam encontradas {len_lista_cenas} Cenas!!!!')
        
        return lista_cenas