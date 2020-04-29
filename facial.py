import threading
import shutil
from itertools import groupby

import numpy as np
import face_recognition
import subprocess
from flask import Flask, request, redirect, jsonify
from PIL import Image
from flask_cors import CORS, cross_origin
import math
import os
import os.path
from util import train, predict, insertPerson, ALLOWED_EXTENSIONS, carpeta, carpeta_standby, carpeta_fotos, personas, \
    getEncode, formatingFile, moveToFotos, insertarasistencia, carpeta_reconocidos, carpeta_sin_rostro

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
cors = CORS(app, resources={r"/": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
servidor='192.168.33.74'
servidorlocal=servidor
codigoequipo=6666
lineacomando='curl -F "file=@1.jpg" http://192.168.33.74:5001'

app = Flask(__name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def upload_image():
    # Chequea la imagen que llego

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file'] #file almacena la imagen

        if file.filename == '':
            return redirect(request.url)

        if allowed_file(file.filename):
            # valida la imagen y la envia a reconocimiento facial y la devuelve en result
            file.filename = str(file.filename).replace('&', ':')
            try:
                image = Image.open(file)
            except IOError:
                print("ERROR processing image", file.filename)
                return 'F'

            if not os.path.exists(carpeta+str(file.filename)) and \
                    not os.path.exists(carpeta+str(file.filename).replace('.jpg', '+P.jpg')):
                image.save(carpeta + str(file.filename))
    return 'T'

if __name__ == "__main__":
    print("Scaneando Puerto....")
    print("******Cargando Datos de Servidor y Puerto***************")

    configuracion=[]
    with open("ibartir.txt") as f:
        for linea in f:
            configuracion.append(linea)
    f.close()

    mi_puerto = int(configuracion[0])
    mi_server = configuracion[1]
    codigoimagenl = configuracion[2]

    app.run(host='192.168.33.77', port=mi_puerto, debug=False)
