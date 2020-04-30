from datetime import datetime
from util import carpeta_fotos, ObjectId, cambiarBandera
import pymongo
import os
from deepface.basemodels import FbDeepFace
from deepface.commons import functions

model = FbDeepFace.loadModel()
input_shape = model.layers[0].input_shape[1:3]

def getEncode(urlImg):
    img_representation = []
    try:
        img_face = functions.detectFace(urlImg, input_shape)
        img_representation = model.predict(img_face)[0, :]
    except:
        pass
    return img_representation

# Conexion Database MONGODB
cliente = pymongo.MongoClient("mongodb://localhost:27017/")
database = cliente["ibartiface"]
personas = database["persons"]

personas.delete_many({})

modelos = os.listdir(carpeta_fotos)
for modelo in modelos:
    print(modelo)
    fotos = os.listdir(carpeta_fotos+modelo+'/')
    inicial = True
    _persona = None
    for foto in fotos:
        encoding = getEncode(carpeta_fotos+modelo+'/'+foto)
        if len(encoding) > 0:
            if inicial:
                inicial = False
                person = {
                    "cod_person": "",
                    "doc_id": str(modelo),
                    "category": ObjectId("5ea9ba5cc9006359504ff64f"), #Verificar ID con Base de Datos
                    "status": ObjectId("5ea9baa9c9006359504ff650"),#Verificar ID con Base de Datos
                    "client": '001',
                    "template_recognition": [encoding.tolist()],
                    "created_date": datetime.now()
                }
                personas.insert_one(person)
                ruta_foto = carpeta_fotos+modelo+'/'+foto
                new_nombre = ruta_foto.replace('.jpg', '-0.jpg')
                os.rename(ruta_foto, new_nombre)
                print(new_nombre)
            else:
                if not _persona:
                    _persona = list(personas.find({'doc_id': str(modelo)}))
                _persona[0]['template_recognition'].append(encoding.tolist())
                myquery = {"_id":  _persona[0]['_id']}
                newvalues = {"$set": {'template_recognition': _persona[0]['template_recognition']}}
                personas.update_one(myquery, newvalues)
                ruta_foto = carpeta_fotos+modelo+'/'+foto
                new_nombre = ruta_foto.replace('.jpg', '-'+str(len(_persona[0]['template_recognition'])-1)+'.jpg')
                os.rename(ruta_foto, new_nombre)
                print(new_nombre)
        else:
            print('Sin Rostro: ', carpeta_fotos+modelo+'/'+foto)

cambiarBandera('T')