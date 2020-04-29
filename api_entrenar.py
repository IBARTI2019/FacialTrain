from flask import Flask, jsonify, request, make_response
import os
from tqdm import tqdm
import numpy as np
import pandas as pd
import cv2
import time
import re
import json
import os
import ast
import uuid
import tensorflow as tf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from deepface.basemodels import FbDeepFace
from deepface.commons import functions, distance as dst

#import DeepFace
#from basemodels import VGGFace, OpenFace, Facenet, FbDeepFace

#------------------------------

app = Flask(__name__)

tic = time.time()

model = FbDeepFace.loadModel()
print("DeepFace model is built")

toc = time.time()

print("Face recognition models are built in ", toc-tic," seconds")

graph = tf.get_default_graph()

#------------------------------
#Service API Interface

@app.route('/')
def index():
	return '<h1>Hello, world!</h1>'


@app.route('/verify', methods=['POST'])
def verify():
	
	global graph
	
	
	
	tic = time.time()
	req = request.get_json()
	trx_id = uuid.uuid4()
	#Carga de archivo Json (modelo)
	files = open('archivo.json','r')
	data = json.load(files)
	#print("Model Json", data)
	#asignacion del modelo de evaluacion
	model_name = "VGG-Face"; distance_metric = "cosine"
	if "model_name" in list(req.keys()):
		model_name = req["model_name"]
	if "distance_metric" in list(req.keys()):
		distance_metric = req["distance_metric"]
	img = './eliezer1.jpg'
	# face recognition models have different size of inputs
	input_shape = model.layers[0].input_shape[1:3]
	# lumbral de reconocimiento segun cada modelo
	threshold = functions.findThreshold(model_name, distance_metric)
	# Deteccion de rostro en la imagen
	img_face = functions.detectFace(img, input_shape)
    # optener los puntos faciales
	#img_representation = model.predict(img_face)[0, :]

	resp_obj = {'success': False}
	with graph.as_default():
		img_representation = model.predict(img_face)[0, :]
		resp_obj['success'] = True
		resp_obj['model_name'] = model_name
		resp_obj['distance_metric'] = distance_metric
		resp_obj['threshold'] = threshold
        
	#--------------------------
	
	toc =  time.time()
	
	return resp_obj, 200

if __name__ == '__main__':
	
	app.run()