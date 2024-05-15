import face_recognition
import cv2
import pygame
import sys

# Initialize pygame
pygame.init()

# Set up the display
screen_width, screen_height = 640, 480
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Face Recognition")

# Start the webcam
cam = cv2.VideoCapture(0)

# Load a sample picture and learn how to recognize it.
face_image = face_recognition.load_image_file("faces\Will.jpg")
face_encoding = face_recognition.face_encodings(face_image)[0]

# Create arrays of known face encodings and their names
known_face_encodings = [face_encoding]
known_face_names = ["Will"]

try:
    while True:
        # Capture frame-by-frame
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_frame = frame[:, :, ::-1]

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(
            face_locations, face_encodings
        ):
            matches = face_recognition.compare_faces(
                known_face_encodings, face_encoding
            )
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            # Draw a label with a name below the face
            cv2.rectangle(
                frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED
            )
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(
                frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1
            )

        # Convert the resulting image back to BGR to display using Pygame
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = pygame.surfarray.make_surface(frame)
        frame = pygame.transform.rotate(frame, -90)
        frame = pygame.transform.flip(frame, True, False)

        # Blit this frame to the screen
        screen.blit(frame, (0, 0))

        # Update the display
        pygame.display.flip()

        # Check for Pygame events, especially the quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cam.release()
                pygame.quit()
                sys.exit()

except KeyboardInterrupt:
    # Handle the Ctrl-C to quit
    cam.release()
    pygame.quit()
    sys.exit()
