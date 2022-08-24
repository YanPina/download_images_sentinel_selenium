import ee
from time import sleep
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from functions_project.FunctionsProject import GisFunctions, CheckDownload, WebDriver, Authentication



class Download_Cenas:
    def download_bandas(lista_cenas, pasta_download, download_folder_selenium):

        driver = WebDriver.SeleniumWebDriver(webdriver)

        print('\n\n------ Iniciando Download e Processamento das Cenas... ------')

        lista_cenas_baixadas = CheckDownload.list_downloaded_scenes(pasta_download)

        #Exclui Duplicados
        lista_cenas = list(dict.fromkeys(lista_cenas))

        #Reverte a ordem pra baixar as cenas mais recentes
        lista_cenas.reverse()

        for cena in lista_cenas:
            
            #Aguarda a confirmação de download de todas as bandas da cena para prosseguir para a próxima cena
            CheckDownload.__confirm_download(download_folder_selenium)

            if cena not in lista_cenas_baixadas:

                CheckDownload.verificar_quantos_valtam(lista_cenas_baixadas, lista_cenas)

                band_link_part_1 = cena[38:44]
                band_link_part_2 = cena[11:26]

                base_url = CheckDownload.base_url(cena)

                driver.get(base_url)

                #Verifica se há solicitação de autenticação e a faz caso houver.
                Authentication.__login_google(driver, Keys)

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
                    CheckDownload.__move_bands_to_folder(download_folder_selenium, lista_cenas_baixadas, lista_cenas, pasta_download, cena)

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