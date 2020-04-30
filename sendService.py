import time
from glob import glob
import json
import subprocess,shutil,os,threading
from deepface.basemodels import FbDeepFace
from deepface.commons import functions, distance as dst
from itertools import groupby
import requests
import numpy as np
from PIL import Image
import math
import os
import os.path
from util import insertPerson, ALLOWED_EXTENSIONS, carpeta,carpeta_agregar, carpeta_standby, carpeta_fotos, personas, formatingFile, moveToFotos, insertarasistencia, carpeta_reconocidos, carpeta_sin_rostro,formatingSaveFile,setHistory

def searchPersons():
    retornar = {
        "templates": [],
        "doc_ids": []
    }
    templates = list(personas.find(
        {}, {'doc_id', 'template_recognition'}))
    for elementos in templates:
        for (index, elemento) in enumerate(elementos['template_recognition']):
            templete = [float(i) for i in elemento]
            templete = np.asarray(templete)
            retornar["templates"].append(templete)
            retornar["doc_ids"].append(elementos['doc_id'])
    return (retornar)

print("Cargando")
personas = searchPersons()
ti = time.time()
model = FbDeepFace.loadModel()
input_shape = model.layers[0].input_shape[1:3]
tf = time.time()
print("Cargado: "+str(tf-ti))

# linkProcess = 'images/procesando'

def imagenRecognition(imgD):
    new_nombre = imgD.replace('.jpg', '+P.jpg')
    os.rename(imgD, new_nombre)
    imgD = new_nombre
    datos = formatingFile(imgD)
    result = None
    if datos:
        datos['url'] = imgD
        template = getImageEncode(imgD)
        if len(personas['doc_ids']) > 0:
            result = reconocimiento(personas, template, datos)
        else:
            datos['url'] = moveStandBy(datos['url'], datos['cliente'])
            print('movido a standby No Ids', datos['url'], datos['cliente'])
            result = {'descripcion': 'movido a standby No Ids', 'url': datos['url'], 'cliente': datos['cliente']}
    return result

def getKeyDistance(obj):
    return obj['distance']

def reconocimiento(search, templete, datos):
    if (len(templete) > 0):
        predictions = verify(templete)
        if len(predictions) > 0:
            predictions.sort(key=getKeyDistance)
            doc_id = predictions[0]["doc"]
            distance = predictions[0]["distance"]
            datos['url'] = moveToReconocidos(datos['url'], datos['cliente'])
            datos['activity'] = "Reconocido"
            datos['json'] = {
                'descripcion': 'reconocido', 'url': datos['url'], 'cliente': datos['cliente'],
                'distance': distance, 'doc_id': doc_id
            }
            setHistory(datos,'5ea9e6663258742a999dda02')
            print('Reconocido', datos['url'], doc_id, distance)
            return {
                'descripcion': 'reconocido', 'url': datos['url'], 'cliente': datos['cliente'],
                'distance': distance, 'doc_id': doc_id
            }
        else:
            datos['url'] = moveStandBy(datos['url'], datos['cliente'])
            datos['json'] = {
                'descripcion': 'movido a standby', 'url': datos['url'], 'cliente': datos['cliente']
            }
            datos['activity'] = "Movido a Standby"
            setHistory(datos,'5ea9e6663258742a999dda02')
            print('Standby', datos['url'], datos['cliente'])
            return {
                'descripcion': 'movido a standby', 'url': datos['url'], 'cliente': datos['cliente']
            }
    else:
        datos['url'] = moveToSinRostro(datos['url'], datos['cliente'])
        print('movido a Sin Rostro', datos['url'], datos['cliente'])
        return {'descripcion': 'movido a sin Rostro', 'url': datos['url'], 'cliente': datos['cliente']}

def eliminarImagen(imagen):
    os.remove(imagen)

def moveStandBy(filename, cod_cliente):
    ruta = carpeta_standby+cod_cliente+'/'
    try:
        os.stat(carpeta_standby)
    except:
        os.mkdir(carpeta_standby)
    try:
        fileName = filename.split('/')[-1]
        try:
          os.stat(ruta)
        except:
          os.mkdir(ruta)

        shutil.move(filename, ruta)
    except:
        return False
    return ruta, fileName

def moveToReconocidos(filename, cod_cliente):
    ruta = carpeta_reconocidos+cod_cliente+'/'
    try:
        os.stat(carpeta_reconocidos)
    except:
        os.mkdir(carpeta_reconocidos)
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

def copyToReconocidos(filename, cod_cliente):
    ruta = carpeta_reconocidos+cod_cliente+'/'
    try:
        os.stat(carpeta_reconocidos)
    except:
        os.mkdir(carpeta_reconocidos)
    try:
        fileName = filename.split('/')[-1]
        try:
          os.stat(ruta)
        except:
          os.mkdir(ruta)

        shutil.copy(filename, ruta)
    except:
        return False
    return ruta+fileName

def moveToSinRostro(filename, cod_cliente):
    ruta = carpeta_sin_rostro+cod_cliente+'/'
    try:
        os.stat(carpeta_sin_rostro)
    except:
        os.mkdir(carpeta_sin_rostro)
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

def getEncodeImage(urlImg):
    img_representation = []
    try:
        img_face = functions.detectFace(urlImg, input_shape)
        img_representation = model.predict(img_face)[0, :]
        print(img_representation)
    except:
        pass
    return img_representation

def listImageSave():
     while(True):
        # print("Service Agregar Activo")
        try:
            os.stat(carpeta_agregar)
        except:
            os.mkdir(carpeta_agregar)
        new = glob(carpeta_agregar+"/*.jpg")
        if(len(new)>0):
            for saveF in new:
                datos = formatingSaveFile(saveF)
                if(datos):
                    encoding = getEncodeImage(saveF)
                    resp, template_recognition_lentgh = insertPerson(
                    encoding,
                    datos['cedula'],
                    datos['category'],
                    datos['status'],
                    datos['cliente']
                    )
                    new_nombre = saveF.replace('.jpg', '-'+str(template_recognition_lentgh-1)+'.jpg')
                    os.rename(saveF, new_nombre)
                    moveToFotos(new_nombre, datos['cedula'])
                    print("Guardada correctamente")

def listImage():
    while(True):
        # print("Service Reconocer Activo")
        new = glob(carpeta+"/*.jpg")
        if(len(new)>0):
            print("Empieza Lote")
            lEI = time.time()
            for images in new:
                tEI = time.time()
                datos = formatingFile(images)
                print('DATOS: ', datos)
                if datos:
                    imageName = images.split('/')[-1]
                    print("Comienza Reconocimiento")
                    encode = getEncodeImage(images)
                    print(encode)
                    reconocimiento(personas, encode, datos)
                    tEF = time.time()
                    print("Tiempo Reconocimiento"+str(tEF-tEI))
                lEF = time.time()
            print("Termina Lote"+str(lEF-lEI))

def verify(encode):
    model_name = "DeepFace"; distance_metric = "euclidean_l2"
    threshold = functions.findThreshold(model_name, distance_metric)
    prueba = []
    try:
        for i, template in enumerate(personas['templates']):
            distance = dst.findEuclideanDistance(dst.l2_normalize(template), dst.l2_normalize(encode))
            if distance <= threshold:
                prueba.append({"doc": personas['doc_ids'][i], "distance": distance})
    except e:
        print(e)
        pass
    return prueba

def main():
    listImage()
    # serviceRecog=threading.Thread(target=listImage)
    # serviceSave=threading.Thread(target=listImageSave)
    # serviceRecog.start()
    # serviceSave.start()

if __name__ == "__main__":
    main()
