import ee
from datetime import datetime, timedelta

from functions_project.FunctionsProject import GisFunctions

class Cenas:
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

