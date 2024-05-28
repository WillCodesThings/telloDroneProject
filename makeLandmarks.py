import cv2
import numpy as np


def capture_and_save_landmarks(output_path, num_frames=10):
    orb = cv2.ORB_create()
    descriptors_list = []

    cap = cv2.VideoCapture(0)  # Use the correct camera ID if not using the default one
    for _ in range(num_frames):
        ret, frame = cap.read()
        if not ret:
            break
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = orb.detectAndCompute(gray_frame, None)
        if descriptors is not None:
            descriptors_list.append(descriptors)

    cap.release()
    combined_descriptors = np.vstack(descriptors_list)
    np.save(output_path, combined_descriptors)


# Example usage
capture_and_save_landmarks("landmark_descriptors.npy")
