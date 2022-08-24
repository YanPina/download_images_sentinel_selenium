import pandas as pd
import geopandas as gpd
from datetime import datetime

from download_bandas.download_bandas import Download_Cenas, DetectarCenas
from functions_project.FunctionsProject import GisFunctions, DbFunctions

#Pasta onde serão armazenadas as imagens
pasta_download = ''

#Verificar em qual diretório o Selenium está baixando os arquivos e setar esse diretório na variável abaixo
download_folder_selenium = ''


#Datas de interesse
initial_date = '06/10/2020'
final_date = '31/12/2020'

start_date = str(datetime.strptime(initial_date, '%d/%m/%Y').date())
end_date = str(datetime.strptime(final_date, '%d/%m/%Y').date())


#Cria uma lista com um range de datas com diferença de 5 dias
date_range_full = pd.date_range(start=start_date, end=end_date, freq='5D').strftime('%Y-%m-%d').tolist()

#criar engine
connect = DbFunctions.__connection_db()

#Lê tabela de talhoes
query_db = ''
gdf = gpd.read_postgis(query_db, geom_col="geometry",con=connect)

gdf = GisFunctions.reproject_epsg(gdf)

for data in date_range_full:
    date_range=[data]

    lista_cenas = DetectarCenas.cenas(gdf, date_range)

    download_images = Download_Cenas.download_bandas(lista_cenas, pasta_download, download_folder_selenium)
   