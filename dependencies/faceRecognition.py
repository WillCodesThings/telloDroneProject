import cv2
from dependencies.simple_facerec import SimpleFacerec

class FacialRecognition():
    def __init__(self, known_faces_path):
        self.sfr = SimpleFacerec()
        self.sfr.load_encoding_images(known_faces_path + "\\")
        self.face_locations = []
        self.face_names = []
    
    def detect_face(self, frame):
        self.face_locations, self.face_names = self.sfr.detect_known_faces(frame)
        return self.face_locations, self.face_names
    