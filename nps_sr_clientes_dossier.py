############################################################################################
##################################### IMPORTACIONES ########################################
############################################################################################

import pandas as pd
import numpy as np
import snowflake.connector
import json
import os
from datetime import datetime
from snowflake.connector.pandas_tools import write_pandas
from datetime import timedelta
import glob
from itertools import chain
import sys
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from google.oauth2.service_account import Credentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
pd.options.mode.chained_assignment = None

############################################################################################
############################# VALIDA VIRTUAL O PC PERSONAL #################################
############################################################################################


f = open('credentials.json')
data_pass = json.load(f)

ctx = snowflake.connector.connect(
    user = data_pass['snow']['USER'],
    password = data_pass['snow']['PASS'],
    account = data_pass['snow']['ACCOUNT'],
    database = 'SANDBOX_PLUS',
    schema = 'DWH'
)

cursor = ctx.cursor()

# Conexion VM a Snowflake

#else:
 #   pass
    # ctx = snowflake.connector.connect(
    #     user="PLUS_VM1_NEW",
    #     password="aK09fWyh4i5oVcI9A31Ea4vXMcquhMMlIE9sXRoil3oSw9faD9",
    #     account="XZ23267-dp32414",
    #     database="SANDBOX_PLUS",
    #     schema="DWH"
    #     )

    # cursor = ctx.cursor()


############################################################################################
################################## CUENTA DE SERVICIO ######################################
############################################################################################

SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_file('data_marketing_gdn_cuentaservicio_keys.json', scopes=SCOPES)

service = build('gmail', 'v1', credentials = credentials)

gc = gspread.authorize(credentials)

gauth = GoogleAuth()
drive = GoogleDrive(gauth)

############################################################################################
############################### REGIONALES CONFIGURACION ###################################
############################################################################################

regionales_dict = {
    '01':'SEBASTIAN LOPEZ',
    '02':'SEBASTIAN LOPEZ',
    '03':'LILIAN HERNANDEZ',
    '04':'SEBASTIAN LOPEZ',
    '05':'SEBASTIAN LOPEZ',
    '06':'LILIAN HERNANDEZ',
    '08':'ANA PEREYRA',
    '09':'SEBASTIAN LOPEZ',
    '11':'LILIAN HERNANDEZ',
    '12':'LILIAN HERNANDEZ',
    '13':'SEBASTIAN LOPEZ',
    '14':'SEBASTIAN LOPEZ',
    '15':'SEBASTIAN LOPEZ',
    '16':'LILIAN HERNANDEZ',
    '17':'LILIAN HERNANDEZ',
    '18':'LILIAN HERNANDEZ',
    '19':'ANA PEREYRA',
    '21':'SEBASTIAN LOPEZ',
    '22':'SEBASTIAN LOPEZ',
    '23':'ANA PEREYRA',
    '24':'LILIAN HERNANDEZ',
    '25':'LILIAN HERNANDEZ',
    '28':'SEBASTIAN LOPEZ',
    '29':'LILIAN HERNANDEZ',
    '30':'SEBASTIAN LOPEZ',
    '31':'LILIAN HERNANDEZ',
    '32':'ANA PEREYRA',
    '33':'ANA PEREYRA',
    '34':'ANA PEREYRA',
    '35':'ANA PEREYRA',
    '36':'LILIAN HERNANDEZ',
    '37':'LILIAN HERNANDEZ',
    '38':'LILIAN HERNANDEZ',
    '40':'SEBASTIAN LOPEZ',
    '42':'LILIAN HERNANDEZ',
    '43':'LILIAN HERNANDEZ',
    '44':'LILIAN HERNANDEZ',
    '45':'LILIAN HERNANDEZ',
    '46':'ANA PEREYRA',
    '47':'ANA PEREYRA',
    '48':'ANA PEREYRA',
    '49':'ANA PEREYRA',
    '50':'SEBASTIAN LOPEZ',
    '51':'SEBASTIAN LOPEZ',
    '52':'SEBASTIAN LOPEZ',
    '53':'SEBASTIAN LOPEZ',
    '54':'SEBASTIAN LOPEZ',
    '56':'SEBASTIAN LOPEZ',
    '58':'SEBASTIAN LOPEZ',
    '61':'SEBASTIAN LOPEZ',
    '63':'LILIAN HERNANDEZ',
    '90':'SEBASTIAN LOPEZ'
}

regionales_dict_str = {str(key): value for key, value in regionales_dict.items()}

############################################################################################
############################### DRIVE INICIAL - CONSUMO ####################################
############################################################################################

url_sr = 'https://docs.google.com/spreadsheets/d/1iGjKfVEnFADr7FW58fxUkTEtL5vpmZTy7mRrlpG6CQs/export?format=csv'
fis = pd.read_csv(url_sr)

# La columna l trae tanto CLIE_CLIE_NDOC (primeras miles de filas) y luego empezo a traer SOCI_SOCI_ID
fis.rename(columns =
           {'Para comenzar ingresa tu documento': 'DOCUMENTO',
           'Selecciona el local donde compraste':'LOCAL',
           '¿Recomendarías comprar en San Roque a familiares y amigos?':'RECOMENDAR',
           '¿Querrías darnos 1 minuto mas y contarnos un poco de tu experiencia.':'CONTAR_EXPERIENCIA',
           '¿Cómo calificarías tu experiencia de compra en San Roque?':'EXPERIENCIA',
            '¿Cómo calificarías la atención recibida en San Roque?':'ATENCION',
            '¿Qué es lo que más te gusta de San Roque?':'GUSTA',
            '¿Qué podemos mejorar?':'MEJORAR',
            '¿Encontraste todos los artículos que buscabas?':'ENCONTRASTE',
            'Cuéntanos, ¿qué producto buscabas? ': 'BUSCABAS',
            'Si lo deseas puedes dejarnos algún comentario sobre tu experiencia de compra en San Roque.' : 'EXPERIENCIA2',
            'Submitted At': 'FECHA'}, inplace = True)

fis['day'] =  list(map(lambda x: str(x).split('/')[0], fis['FECHA']))
fis['month'] =  list(map(lambda x: str(x).split('/')[1], fis['FECHA']))
fis['year'] = list(map(lambda x: str(x).split('/')[2].split(' ')[0], fis['FECHA']))
fis['PERIODO'] = pd.to_datetime(fis['year'] + '-' + fis['month']).dt.to_period('M')
fis['DIA'] = pd.to_datetime(fis[['year', 'month', 'day']])
fis['CANAL'] = 'QR'
fis['REGIONAL'] = fis['LOCAL'].str[:2].map(regionales_dict_str)

fis.drop(columns = ['Querrías darnos 1 minuto mas y contarnos un poco de tu experiencia.', 'month', 'year', 'day'], inplace = True)

############################################################################################
########################################## NPS #############################################
############################################################################################

df = fis.copy()

df['NPS'] = np.nan
df['NPS'][df['RECOMENDAR'].isin([9, 10])] = 'Promotores'
df['NPS'][df['RECOMENDAR'].isin([7, 8])] = 'Neutros'
df['NPS'][df['RECOMENDAR'].isin([0, 1, 2, 3, 4, 5, 6])] = 'Detractores'
df = df[~df['NPS'].isna()]
df['PROMOTOR'] = np.nan
df['PROMOTOR'][df['NPS'] == 'Promotores'] = 1
df['DETRACTOR'] = np.nan
df['DETRACTOR'][df['NPS'] == 'Detractores'] = 1

df_final = df

# Elimino puntos '.'
df_final['GUSTA'] = list(map(lambda x: str(x).replace('.', ''), df_final['GUSTA']))
# Elimino tildes
df_final['GUSTA'] = list(map(lambda x : x.translate(x.maketrans("áéíóú","aeiou")), df_final['GUSTA'] ))
df_final['GUSTA'] = list(map(lambda x: str(x).replace(', ', ','), df_final['GUSTA']))

gusta_aux = df_final[~df_final['GUSTA'].isna()]
gusta_aux = gusta_aux[gusta_aux['GUSTA'] != 'nan']

def chainer(s):
    return list(chain.from_iterable(s.str.split(',')))

# calculate lengths of splits
lens = gusta_aux['GUSTA'].str.split(',').map(len)

# create new dataframe, repeating or chaining as appropriate
gusta = pd.DataFrame({'GUSTA': np.repeat(gusta_aux['GUSTA'], lens),
                    'NPS': np.repeat(gusta_aux['NPS'], lens),
                    'PERIODO': np.repeat(gusta_aux['PERIODO'], lens),
                    'LOCAL': np.repeat(gusta_aux['LOCAL'], lens),
                    'DIA': np.repeat(gusta_aux['DIA'], lens),
                    'REGIONAL': np.repeat(gusta_aux['REGIONAL'], lens),
                    'BIGRAMS_GUSTA': chainer(gusta_aux['GUSTA'])})
gusta['BIGRAMS_GUSTA'] = gusta['BIGRAMS_GUSTA'].str.strip()

gusta_final = gusta.groupby(['PERIODO', 'NPS', 'LOCAL', 'REGIONAL', 'DIA', 'BIGRAMS_GUSTA'])['GUSTA'].count().reset_index().sort_values(by = 'GUSTA', ascending = False)
gusta_final.rename(columns = {'BIGRAMS_GUSTA':'Qué es lo que más te gusta?', 'GUSTA':' N° Respuestas'}, inplace = True)
gusta_final = gusta_final[gusta_final['Qué es lo que más te gusta?'] != ' ']
gusta_final = gusta_final[gusta_final['Qué es lo que más te gusta?'] != 'Nada']
gusta_final = gusta_final[gusta_final['Qué es lo que más te gusta?'] != '']
gusta_final = gusta_final[gusta_final['Qué es lo que más te gusta?'] != 'nan']
gusta_final = gusta_final[gusta_final['Qué es lo que más te gusta?'] != '!']
gusta_final = gusta_final[~gusta_final['Qué es lo que más te gusta?'].isna()]


### MEJORAR
# Elimino puntos '.'
df_final['MEJORAR'] = list(map(lambda x: str(x).replace('.', ''), df_final['MEJORAR']))
# Elimino tildes
df_final['MEJORAR'] = list(map(lambda x : x.translate(x.maketrans("áéíóú","aeiou")), df_final['MEJORAR'] ))

mejorar_aux = df_final[~df_final['MEJORAR'].isna()]
mejorar_aux = mejorar_aux[mejorar_aux['MEJORAR'] != 'nan']

# calculate lengths of splits
lens = mejorar_aux['MEJORAR'].str.split(',').map(len)

# create new dataframe, repeating or chaining as appropriate
mejorar = pd.DataFrame({'MEJORAR': np.repeat(mejorar_aux['MEJORAR'], lens),
                    'NPS': np.repeat(mejorar_aux['NPS'], lens),
                    'PERIODO': np.repeat(mejorar_aux['PERIODO'], lens),
                    'LOCAL': np.repeat(mejorar_aux['LOCAL'], lens),
                    'DIA': np.repeat(mejorar_aux['DIA'], lens),
                    'REGIONAL': np.repeat(mejorar_aux['REGIONAL'], lens),
                    'BIGRAMS_MEJORAR': chainer(mejorar_aux['MEJORAR'])})
mejorar['BIGRAMS_MEJORAR'] = mejorar['BIGRAMS_MEJORAR'].str.strip()

mejorar_final = mejorar.groupby(['PERIODO', 'NPS', 'LOCAL', 'REGIONAL', 'DIA', 'BIGRAMS_MEJORAR'])['MEJORAR'].count().reset_index().sort_values(by = 'MEJORAR', ascending = False)
mejorar_final.rename(columns = {'BIGRAMS_MEJORAR':'Qué podemos mejorar?', 'MEJORAR':' N° Respuestas'}, inplace = True)

mejorar_final = mejorar_final[mejorar_final['Qué podemos mejorar?'] != '']
mejorar_final = mejorar_final[mejorar_final['Qué podemos mejorar?'] != 'nan']
mejorar_final = mejorar_final[~mejorar_final['Qué podemos mejorar?'].isna()]

df_final['REGIONAL'].fillna('Sin Info', inplace = True)
df_final['LOCAL'].fillna('Sin Info', inplace = True)

df_final = df_final.rename(columns={col: col.upper() for col in df_final.columns})

df_final.rename(columns = {'BUSCABAS':'CUÉNTANOS, QUE PRODUCTO BUSCABAS', 'ENCONTRASTE':'ENCONTRASTE TODO LO QUE BUSCABAS', 'EXPERIENCIA2':'SI LO DESEAS PUEDES DEJARNOS ALGÚN COMENTARIO SOBRE TU EXPERIENCIA DE COMPRA EN SAN ROQUE'}, inplace = True)

general = df_final[['DOCUMENTO' , 'RECOMENDAR', 'EXPERIENCIA', 'ATENCION', 'ENCONTRASTE TODO LO QUE BUSCABAS', 'CUÉNTANOS, QUE PRODUCTO BUSCABAS', 'SI LO DESEAS PUEDES DEJARNOS ALGÚN COMENTARIO SOBRE TU EXPERIENCIA DE COMPRA EN SAN ROQUE', 'PERIODO', 'LOCAL', 'NPS', 'PROMOTOR', 'DETRACTOR', 'REGIONAL', 'DIA', 'CANAL']].copy(deep = True)

general['DOCUMENTO'] = general['DOCUMENTO'].astype(str)
general['DOCUMENTO'][general['DOCUMENTO'] == np.nan] = 0
general["DOCUMENTO"] = general["DOCUMENTO"].str[:-2]
general['PERIODO'] = general['PERIODO'].astype(str)
general['EXPERIENCIA'][general['EXPERIENCIA'] == ''] = np.nan
general['ATENCION'][general['ATENCION'] == ''] = np.nan
general['LOCAL'][general['LOCAL'] == 'nan'] = np.nan
general['ENCONTRASTE TODO LO QUE BUSCABAS'][general['ENCONTRASTE TODO LO QUE BUSCABAS'] == ''] = np.nan

general['PROMOTOR'][general['PROMOTOR'] == ''] = 0
general['PROMOTOR'][general['PROMOTOR'].isna()] = 0
general['PROMOTOR'] = general['PROMOTOR'].astype(int)

general['DETRACTOR'][general['DETRACTOR'] == ''] = 0
general['DETRACTOR'][general['DETRACTOR'].isna()] = 0
general['DETRACTOR'] = general['DETRACTOR'].astype(int)

general['ENCONTRASTE TODO LO QUE BUSCABAS'][general['ENCONTRASTE TODO LO QUE BUSCABAS'] == True] = 'Si'
general['ENCONTRASTE TODO LO QUE BUSCABAS'][general['ENCONTRASTE TODO LO QUE BUSCABAS'] == False] = 'No'
general['ENCONTRASTE TODO LO QUE BUSCABAS'].fillna('Sin Info', inplace = True)

general["DIA"] = pd.to_datetime(general["DIA"], unit="us", origin="unix").dt.date

############################################################################################
############################### FORMATOS GUSTA Y MEJORAR ###################################
############################################################################################

gusta_final.columns = map(lambda x: str(x).strip(), gusta_final.columns)
gusta_final['PERIODO'] = gusta_final['PERIODO'].astype(str)
gusta_final['DIA'] = gusta_final['DIA'].astype(str)
gusta_final.rename(columns = {'Qué es lo que más te gusta?':'QUE ES LO QUE MAS TE GUSTA', 'N° Respuestas':'N° RESPUESTAS'}, inplace = True)

mejorar_final.columns = map(lambda x: str(x).strip(), mejorar_final.columns)
mejorar_final['PERIODO'] = mejorar_final['PERIODO'].astype(str)
mejorar_final['DIA'] = mejorar_final['DIA'].astype(str)
mejorar_final.rename(columns = {'Qué podemos mejorar?':'QUE PODEMOS MEJORAR', 'N° Respuestas':'N° RESPUESTAS'}, inplace = True)
mejorar_final['QUE PODEMOS MEJORAR'] = mejorar_final['QUE PODEMOS MEJORAR'].apply(lambda x: str(x)[:250] if x is not None else None)


############################################################################################
######################################## CARGA SNOW ########################################
############################################################################################

# Eliminamos la tabla general
query = '''
DELETE FROM SANDBOX_PLUS.DWH.DOSSIER_NPS_SR_CLIENTES_GENERAL
'''

cursor.execute(query)

# Cargamos la tabla general
success, nchunks, nrows, _ = write_pandas(ctx,
    general,
    table_name='DOSSIER_NPS_SR_CLIENTES_GENERAL', database= 'SANDBOX_PLUS', schema = 'DWH')

############################################################################################

# Eliminamos la tabla gusta
query = '''
DELETE FROM SANDBOX_PLUS.DWH.DOSSIER_NPS_SR_CLIENTES_GUSTA
'''

cursor.execute(query)

# Cargamos la tabla gusta
success, nchunks, nrows, _ = write_pandas(ctx,
    gusta_final,
    table_name='DOSSIER_NPS_SR_CLIENTES_GUSTA', database= 'SANDBOX_PLUS', schema = 'DWH')

############################################################################################

# Eliminamos la tabla mejorar
query = '''
DELETE FROM SANDBOX_PLUS.DWH.DOSSIER_NPS_SR_CLIENTES_MEJORAR
'''

cursor.execute(query)

# Cargamos la tabla mejorar
success, nchunks, nrows, _ = write_pandas(ctx,
    mejorar_final,
    table_name='DOSSIER_NPS_SR_CLIENTES_MEJORAR', database= 'SANDBOX_PLUS', schema = 'DWH')