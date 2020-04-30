import datetime
import json
import math
import shutil
import time
from mysql.connector import Error, MySQLConnection

import pymongo
from bson import ObjectId
import os
import os.path
import pickle

from python_mysql_dbconfig import read_db_config
from deepface.basemodels import FbDeepFace
from deepface.commons import functions

carpeta='./cloud/'
carpeta_standby='./standby/'
carpeta_reconocidos='./reconocidos/'
carpeta_sin_rostro='./sin_rostro/'
carpeta_fotos='./fotos/'
carpeta_agregar='./save/'
ALLOWED_EXTENSIONS = {'jpg'}

# Conexion Database MONGODB
cliente = pymongo.MongoClient("mongodb://localhost:27017/")
database = cliente["ibartiface"]
personas = database["persons"]
person_history = database["activity_history"]
categorias = database["category"]
estatus = database["conditions"]

def leerBandera():
    archivo = open('band.txt', 'r')
    band = archivo.read(1)
    archivo.close()
    return str(band) == 'T'

def cambiarBandera(val):
    archivo = open('band.txt', 'w')
    archivo.write(val)
    archivo.close()
    
def run_query_ibarti(query='', args=''):
    data = []
    if query:
        try:
            db_config = read_db_config()
            conn = MySQLConnection(**db_config)
            cursor = conn.cursor()         # Crear un cursor
            if args:
                cursor.execute(query, args)          # Ejecutar una consulta
            else:
                cursor.execute(query)          # Ejecutar una consulta con argumentos
            if query.upper().startswith('SELECT'):
                _data = cursor.fetchall()   # Traer los resultados de un select
                row_headers = [x[0] for x in cursor.description]  # Extraer las cabeceras de las filas
                for result in _data:
                    data.append(dict(zip(row_headers, result)))
                # data = json.dumps(data)
            else:
                conn.commit()              # Hacer efectiva la escritura de datos
        except Error as error:
            print(error)
        finally:
            cursor.close()                 # Cerrar el cursor
            conn.close()                   # Cerrar la conexión

    return data

def insertPerson(image, cedula, category, status, client):
    _persona = list(personas.find({'doc_id': cedula}))
    print(type(image))
    if _persona:
        persona = _persona[0]
        persona['template_recognition'].append(image.tolist())
        myquery = {"_id":  _persona[0]['_id']}
        newvalues = {"$set": {'template_recognition': persona['template_recognition']}}
        personas.update_one(myquery, newvalues)
    else:
        persona = {
            "cod_person": "",
            "doc_id": cedula,
            "category": ObjectId(category),
            "status": ObjectId(status),
            "client": client,
            "template_recognition": [image.tolist()],
            "created_date": datetime.datetime.now()
        }
        persona = personas.insert_one(persona)
    cambiarBandera('T')
    return persona, len(_persona[0]['template_recognition']) if _persona else 1

def setHistory(data, status):
    try:
        # print('setHistory', data, metodo)
        data["status"] = ObjectId(status)
        data["create_date"] = str(datetime.datetime.now())
        if(data["status"] and data["activity"]):
            if(estatus.find({"_id": data["status"]}).count() > 0):
                return person_history.insert(data)
            else:
                return False
        else:
            return False

    except pymongo.errors.PyMongoError as error:
        print(error)
        return error

def getEncode(urlImg):
    model = FbDeepFace.loadModel()
    input_shape = model.layers[0].input_shape[1:3]
    img_representation = []
    try:
        img_face = functions.detectFace(urlImg, input_shape)
        img_representation = model.predict(img_face)[0, :]
    except:
        pass
    return img_representation

def formatingFile(filename):
    partes = filename.split('/')[-1].split('\\')[-1].split('.')
    if len(partes) > 1:
        partes = partes[0].split('+')
        if len(partes) >= 4:
            propiedades = {}
            try:
                propiedades['fecha'] = str(
                    datetime.datetime.strptime(partes[2], '%Y-%m-%d').date())
            except:
                return False
            try:
                partes[3] = partes[3].replace('&', ':')
                partes[3] = partes[3].replace('_', ':')
                propiedades['hora'] = str(
                    datetime.datetime.strptime(partes[3], '%H:%M:%S:%f').time())
            except:
                return False
            propiedades['cliente'] = partes[0]
            propiedades['dispositivo'] = partes[1]
            # propiedades['nFoto'] = partes[2]
            propiedades['url'] = filename
            return propiedades
        else:
            return False
    else:
        return False


def formatingSaveFile(filename):
    partes = filename.split('/')[-1].split('\\')[-1].split('.')
    if len(partes) > 1:
        partes = partes[0].split('+')
        if len(partes) >= 4:
            propiedades = {}
            propiedades['cedula'] = partes[0]
            propiedades['category'] = partes[1]
            propiedades['status'] = partes[2]
            propiedades['cliente'] = partes[3]
            return propiedades
        else:
            return False
    else:
        return False


def moveToSaveFotos(filename, newName):
    ruta = carpeta_agregar+'/'+newName
    try:
        os.stat(carpeta_agregar)
    except:
        os.mkdir(carpeta_agregar)
    try:
        fileName = filename.split('/')[-1]
        shutil.move(filename, ruta)
    except:
        return False
    return ruta


def moveToFotos(filename, cedula):
    ruta = carpeta_fotos+cedula+'/'
    try:
        os.stat(carpeta_fotos)
    except:
        os.mkdir(carpeta_fotos)
    try:
        fileName = filename.split('/')[-1]
        try:
          os.stat(ruta)
        except:
          os.mkdir(ruta)
        shutil.move(filename, ruta)
    except:
        return False
    return ruta+fileName

def insertarasistencia(equipo, auxidentificador, datos):
    datos["hora"] = datos["hora"][:-7]
    auxequipo = equipo
    auxhora = datos["hora"]
    auxfecha = datos["fecha"] + ' ' + datos["hora"]
    auxfechaservidor=time.strftime("%Y/%m/%d %H:%M:%S")
    auxchecktipo="E"
    auxtrama="Trama"
    auxevento="IDENTIFY"
    auxeventodata="FACIAL"
    auxorigen=equipo
    auxchequeado="N"
    # activot=fichaactiva(auxidentificador)
    query = "INSERT INTO ch_inout(huella,cod_dispositivo,fechaserver,fecha,hora,checktipo,trama,evento,eventodata," \
            "origen,checks) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    args = (auxidentificador,auxequipo,auxfechaservidor,auxfecha,auxhora,auxchecktipo,auxtrama,auxevento,auxeventodata,
            auxorigen,auxchequeado)

    return run_query_ibarti(query, args)

def consultarasistencia(fecha_desde, fecha_hasta):
    query = "SELECT v_ch_identify.codigo, IFNULL(ficha.cedula, 'SIN CEDULA') cedula , " \
            "IFNULL(ficha.cod_ficha, 'SIN FICHA') cod_ficha, IFNULL(CONCAT(ficha.apellidos,' ',ficha.nombres), " \
            "v_ch_identify.huella) ap_nombre , v_ch_identify.cod_dispositivo,  clientes_ubicacion.codigo cod_ubicacion," \
            " clientes_ubicacion.descripcion ubicacion, clientes.codigo cod_cliente, clientes.nombre cliente, " \
            "DATE_FORMAT(v_ch_identify.fechaserver, '%Y-%m-%d %h:%i:%s') fechaserver, DATE_FORMAT(v_ch_identify.fecha, '%Y-%m-%d') fecha, " \
            "DATE_FORMAT(v_ch_identify.hora, '%h:%i:%s') hora, " \
            "'SI' vetado FROM v_ch_identify LEFT JOIN ficha ON v_ch_identify.cedula = ficha.cedula AND " \
            "ficha.cod_ficha_status = 'A', clientes_ub_ch, clientes, clientes_ubicacion " \
            "WHERE DATE_FORMAT(v_ch_identify.fecha, '%Y-%m-%d') BETWEEN '"+fecha_desde+"' AND '"+fecha_hasta+"' " \
            "AND v_ch_identify.cod_dispositivo = clientes_ub_ch.cod_capta_huella " \
            "AND clientes_ub_ch.cod_cl_ubicacion = clientes_ubicacion.codigo " \
            "AND clientes_ubicacion.cod_cliente = clientes.codigo " \
            "AND ficha.cod_ficha IN (SELECT clientes_vetados.cod_ficha FROM  clientes_vetados " \
            "WHERE clientes_vetados.cod_cliente = clientes_ubicacion.cod_cliente " \
            "AND clientes_vetados.cod_ubicacion = clientes_ubicacion.codigo " \
            "AND ficha.cod_ficha = clientes_vetados.cod_ficha) AND v_ch_identify.eventodata = 'FACIAL' " \
            "UNION ALL " \
            "SELECT v_ch_identify.codigo, IFNULL(ficha.cedula, 'SIN CEDULA') cedula , " \
            " IFNULL(ficha.cod_ficha, 'SIN FICHA') cod_ficha, IFNULL(CONCAT(ficha.apellidos,' ',ficha.nombres)," \
            " v_ch_identify.huella) ap_nombre , v_ch_identify.cod_dispositivo,  " \
            "clientes_ubicacion.codigo cod_ubicacion, clientes_ubicacion.descripcion ubicacion," \
            " clientes.codigo cod_cliente, clientes.nombre cliente, " \
            "DATE_FORMAT(v_ch_identify.fechaserver, '%Y-%m-%d %h:%i:%s') fechaserver, " \
            "DATE_FORMAT(v_ch_identify.fecha, '%Y-%m-%d') fecha, DATE_FORMAT(v_ch_identify.hora, '%h:%i:%s') hora, " \
            "'NO' vetado FROM v_ch_identify LEFT JOIN ficha ON v_ch_identify.cedula = ficha.cedula " \
            "AND ficha.cod_ficha_status = 'A', clientes_ub_ch, clientes, clientes_ubicacion " \
            "WHERE DATE_FORMAT(v_ch_identify.fecha, '%Y-%m-%d') BETWEEN '"+fecha_desde+"' AND '"+fecha_hasta+"' " \
            "AND v_ch_identify.cod_dispositivo = clientes_ub_ch.cod_capta_huella " \
            "AND clientes_ub_ch.cod_cl_ubicacion = clientes_ubicacion.codigo " \
            "AND clientes_ubicacion.cod_cliente = clientes.codigo " \
            "AND ficha.cod_ficha NOT IN (SELECT clientes_vetados.cod_ficha FROM  clientes_vetados " \
            "WHERE clientes_vetados.cod_cliente = clientes_ubicacion.cod_cliente " \
            "AND clientes_vetados.cod_ubicacion = clientes_ubicacion.codigo " \
            "AND ficha.cod_ficha = clientes_vetados.cod_ficha) AND v_ch_identify.eventodata = 'FACIAL' " \
            "GROUP BY cedula, DATE_FORMAT(fecha, '%Y-%m-%d') ORDER BY fecha ASC, cedula"

    return run_query_ibarti(query)