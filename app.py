import cv2
import numpy as np
import os
from flask import Flask, render_template, Response

app = Flask(__name__)

thres = 0.45 
nms_threshold = 0.5

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
classFile = os.path.join(BASE_DIR, 'config_files', 'coco.names')
configPath = os.path.join(BASE_DIR, 'config_files', 'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt')
weightsPath = os.path.join(BASE_DIR, 'config_files', 'frozen_inference_graph.pb')

classNames = []
with open(classFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0/127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

def detect_doors(image):
    gray        = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred     = cv2.GaussianBlur(gray, (5, 5), 0)
    edges       = cv2.Canny(blurred, 50, 150)
    kernel      = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated     = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    door_boxes = []
    img_h, img_w = image.shape[:2]

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect      = h / float(w) if w != 0 else 0
        rel_area    = (w * h) / float(img_h * img_w)
        if 1.5 < aspect < 4.5 and 0.02 < rel_area < 0.40 and w > 40 and h > 80:
            door_boxes.append((x, y, w, h))
    return door_boxes

def gen_frames():
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    cap.set(10, 150)

    while True:
        success, image = cap.read()
        if not success:
            break
        
        classIds, confs, bbox = net.detect(image, confThreshold=thres)
        if len(classIds) != 0:
            bbox = list(bbox)
            confs = list(np.array(confs).reshape(1,-1)[0])
            confs = list(map(float, confs))
            classIds = np.array(classIds).flatten()

            indicies = cv2.dnn.NMSBoxes(bbox, confs, thres, nms_threshold)
            if len(indicies) > 0:
                for i in np.array(indicies).flatten():
                    box = bbox[i]
                    x, y, w, h = box[0], box[1], box[2], box[3]
                    cv2.rectangle(image, (x, y), (x+w, h+y), color=(0, 255, 0), thickness=2)
                    cv2.putText(image, classNames[classIds[i]-1], (box[0]+10, box[1]+30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                                
        door_boxes = detect_doors(image)
        for (dx, dy, dw, dh) in door_boxes:
            cv2.rectangle(image, (dx, dy), (dx + dw, dy + dh), color=(255, 0, 0), thickness=2)
            cv2.putText(image, "Door", (dx + 10, dy + 30), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 2)

        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
