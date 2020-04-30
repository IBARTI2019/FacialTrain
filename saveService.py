import time
from glob import glob
from deepface.basemodels import FbDeepFace
from deepface.commons import functions
import os
import os.path
from util import insertPerson,carpeta_agregar, moveToFotos,formatingSaveFile

print("Cargando")
ti = time.time()
model = FbDeepFace.loadModel()
input_shape = model.layers[0].input_shape[1:3]
tf = time.time()
print("Cargado: "+str(tf-ti))

# linkProcess = 'images/procesando'


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

def main():
    listImageSave()

if __name__ == "__main__":
    main()
