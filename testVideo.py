# Code adapted from Tensorflow Object Detection Framework
# https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb
# Tensorflow Object Detection Detector

import numpy as np
import tensorflow as tf
import cv2
import time
from playsound import playsound


class DetectorAPI:
    def __init__(self, path_to_ckpt):
        self.path_to_ckpt = path_to_ckpt

        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(self.path_to_ckpt, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        self.default_graph = self.detection_graph.as_default()
        self.sess = tf.Session(graph=self.detection_graph)

        # Definite input and output Tensors for detection_graph
        self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
        # Each box represents a part of the image where a particular object was detected.
        self.detection_boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        self.detection_scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
        self.detection_classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
        self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

    def processFrame(self, image):
        # Expand dimensions since the trained_model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image, axis=0)
        # Actual detection.
        start_time = time.time()
        (boxes, scores, classes, num) = self.sess.run(
            [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
            feed_dict={self.image_tensor: image_np_expanded})
        end_time = time.time()

        print("Elapsed Time:", end_time-start_time)

        im_height, im_width,_ = image.shape
        boxes_list = [None for i in range(boxes.shape[1])]
        for i in range(boxes.shape[1]):
            boxes_list[i] = (int(boxes[0,i,0] * im_height),
                        int(boxes[0,i,1]*im_width),
                        int(boxes[0,i,2] * im_height),
                        int(boxes[0,i,3]*im_width))

        return boxes_list, scores[0].tolist(), [int(x) for x in classes[0].tolist()], int(num[0])

    def close(self):
        self.sess.close()
        self.default_graph.close()

def dist(p1,p2):
    return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2

if __name__ == "__main__":
    #model_path = 'faster_rcnn_inception_v2_coco_2018_01_28/frozen_inference_graph.pb'
    model_path = 'ssd_mobilenet_v1_coco_2017_11_17/frozen_inference_graph.pb'
    odapi = DetectorAPI(path_to_ckpt=model_path)
    threshold = 0.3
    cap = cv2.VideoCapture('test-video3.mp4')

    while True:
        r, img = cap.read()
        img = cv2.resize(img, (1280, 720))

        boxes, scores, classes, num = odapi.processFrame(img)

        
        
        locations = []
        for i in range(len(boxes)):
            # Class 1 represents human

            if classes[i] == 1 and scores[i] > threshold:
                box = boxes[i]
                # Get middle points of humans and add to list
                x_middle = int((box[1]+box[3])/2)
                y_middle = int((box[0]+box[2])/2)
                locations.append([x_middle,y_middle])
                cv2.circle(img,(x_middle,y_middle),10,(0,255,0),thickness = -1)
                cv2.rectangle(img,(box[1],box[0]),(box[3],box[2]),(255,0,0),2)
        
        #For more than 2 people
        for i in range(len(locations)-1):
            for j in range(i+1,len(locations)):
                print("Dist:")
                print(i,j)
                print(dist(locations[i],locations[j]))
                
                #Number 300000 is a paramater that can be changed due to camera angles
                if (dist(locations[i],locations[j])) < 300000:
                    print("Too close")
                    
                    cv2.circle(img,tuple(locations[i]),10,(0,0,255),thickness = -1)
                    cv2.circle(img,tuple(locations[j]),10,(0,0,255),thickness = -1)
                    
                    playsound("siren.wav")
                else:
                    print("Ok")
        
        print("-----")
        cv2.imshow("preview", img)
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            break