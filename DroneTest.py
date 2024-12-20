from djitellopy import Tello
import cv2
import pygame
import numpy as np
import time
from dependencies.faceRecognition import FacialRecognition as fr

# Speed of the drone
S = 60
# Frames per second of the pygame window display
FPS = 120

FaceRecognition = fr("faces")


class FrontEnd(object):

    def __init__(self):
        """Maintains the Tello display and moves it through the keyboard keys.
        Press escape key to quit.
        The controls are:
            - T: Takeoff
            - L: Land
            - Arrow keys: Forward, backward, left and right.
            - A and D: Counter clockwise and clockwise rotations (yaw)
            - W and S: Up and down.
        """
        pygame.init()
        pygame.display.set_caption("Tello video stream")
        self.screen = pygame.display.set_mode([960, 720])
        self.tello = Tello()
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10
        self.send_rc_control = False
        pygame.time.set_timer(pygame.USEREVENT + 1, 1000 // FPS)
        self.PERFRAMERECOGNITION = 1

    def run(self):
        self.tello.connect()
        self.tello.set_speed(self.speed)
        self.tello.streamoff()
        self.tello.streamon()

        frame_read = self.tello.get_frame_read()
        should_stop = False
        while not should_stop:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.update()
                elif event.type == pygame.QUIT:
                    should_stop = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        should_stop = True
                    else:
                        self.keydown(event.key)
                elif event.type == pygame.KEYUP:
                    self.keyup(event.key)

            if frame_read.stopped:
                break

            frame = frame_read.frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Find all the faces and face encodings in the current frame of video

            if self.PERFRAMERECOGNITION % 10 == 0:
                face_locations, face_names = FaceRecognition.detect_face(frame_rgb)
                for face_loc, name in zip(face_locations, face_names):
                    y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
                    cv2.putText(
                        frame,
                        name,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_DUPLEX,
                        1,
                        (0, 0, 200),
                        2,
                    )
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 200), 4)

            self.screen.fill([0, 0, 0])
            text = "Battery: {}%".format(self.tello.get_battery())
            cv2.putText(
                frame, text, (5, 720 - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
            )
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = np.flipud(frame)
            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))
            pygame.display.update()

            time.sleep(1 / FPS)
            self.PERFRAMERECOGNITION += 1

        self.tello.end()

    def keydown(self, key):
        """Update velocities based on key pressed
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP:  # set forward velocity
            self.for_back_velocity = S
        elif key == pygame.K_DOWN:  # set backward velocity
            self.for_back_velocity = -S
        elif key == pygame.K_LEFT:  # set left velocity
            self.left_right_velocity = -S
        elif key == pygame.K_RIGHT:  # set right velocity
            self.left_right_velocity = S
        elif key == pygame.K_w:  # set up velocity
            self.up_down_velocity = S
        elif key == pygame.K_s:  # set down velocity
            self.up_down_velocity = -S
        elif key == pygame.K_a:  # set yaw counter clockwise velocity
            self.yaw_velocity = -S
        elif key == pygame.K_d:  # set yaw clockwise velocity
            self.yaw_velocity = S

    def keyup(self, key):
        """Update velocities based on key released
        Arguments:
            key: pygame key
        """
        if (
            key == pygame.K_UP or key == pygame.K_DOWN
        ):  # set zero forward/backward velocity
            self.for_back_velocity = 0
        elif (
            key == pygame.K_LEFT or key == pygame.K_RIGHT
        ):  # set zero left/right velocity
            self.left_right_velocity = 0
        elif key == pygame.K_w or key == pygame.K_s:  # set zero up/down velocity
            self.up_down_velocity = 0
        elif key == pygame.K_a or key == pygame.K_d:  # set zero yaw velocity
            self.yaw_velocity = 0
        elif key == pygame.K_t:  # takeoff
            self.tello.takeoff()
            self.send_rc_control = True
        elif key == pygame.K_l:  # land
            not self.tello.land()
            self.send_rc_control = False

    def update(self):
        if self.send_rc_control:
            self.tello.send_rc_control(
                self.left_right_velocity,
                self.for_back_velocity,
                self.up_down_velocity,
                self.yaw_velocity,
            )


def main():
    frontend = FrontEnd()
    frontend.run()


if __name__ == "__main__":
    main()
