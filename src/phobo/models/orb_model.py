import cv2
import pickle
import numpy as np

class ORBModel:

    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        pass
    
    def __init__(self):
        pass

    def dump(self, img:np.ndarray, file_name:str):
        orb = cv2.ORB_create()
        kp, des = orb.detectAndCompute(img, None)

        index = []
        for point in kp:
            temp = (point.pt, point.size, point.angle, point.response, point.octave, 
                    point.class_id) 
            index.append(temp)
            
        # Dump the keypoints
        with open(file_name, "wb") as f:
            f.write(pickle.dumps((index,des)))
            f.close()

        return kp, des

    def load(self, file_name:str):
        with open(file_name,'rb') as f:
            index, des = pickle.loads(f.read())
        kp = []
        for point in index:
           kp.append(cv2.KeyPoint(
                x=point[0][0],
                y=point[0][1],
                size=point[1],
                angle=point[2], 
                response=point[3],
                octave=point[4],
                class_id=point[5]
            ))
        return kp, des

    def compare(self, kp0, des0, kp1, des1):
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des0, des1, k=2)
        # Apply ratio test
        good = 0
        for m,n in matches:
            if m.distance < 0.75*n.distance:
                good += 1
        return good/len(kp0)

