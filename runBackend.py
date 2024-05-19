from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dependencies.faceRecognition import FacialRecognition
from djitellopy import Tello
import threading
import time
import cv2
import os

app = FastAPI()

faceRecognition = FacialRecognition("faces")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

faceProccessing = 0

# Initialize velocity state
velocity_state = {
    "left_right_velocity": 0,
    "forward_backward_velocity": 0,
    "up_down_velocity": 0,
    "yaw_velocity": 0,
}

tello = None
tello_ready_event = threading.Event()


def initialize_tello():
    global tello
    tello = Tello()
    try:
        tello.connect()
        tello.streamon()
        print("Connected to Tello.")
        tello_ready_event.set()
    except Exception as e:
        print(f"Error initializing Tello: {e}")
        tello = None


@app.on_event("startup")
def on_startup():
    threading.Thread(target=initialize_tello).start()


def run_in_thread(target, *args, **kwargs):
    thread = threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.start()
    return thread


def get_video_stream(direction):
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")

    if direction == 1:
        tello.set_video_direction(tello.CAMERA_FORWARD)
    elif direction == 0:
        tello.set_video_direction(tello.CAMERA_DOWNWARD)
    else:
        raise HTTPException(status_code=400, detail="Invalid video direction")

    frame_read = tello.get_frame_read()
    while True:
        frame = frame_read.frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if faceProccessing == 1:
            face_locations, face_names = faceRecognition.detect_face(frame_rgb)
            for face_loc, name in zip(face_locations, face_names):
                y1, x2, y2, x1 = face_loc[0], face_loc[1], face_loc[2], face_loc[3]
                cv2.putText(
                    frame_rgb,
                    name,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_DUPLEX,
                    1,
                    (0, 0, 200),
                    2,
                )
                cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (0, 0, 200), 4)
        elif faceProccessing == -1:
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

            # Convert the image to grayscale
            gray_image = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2GRAY)

            # Look for faces in the image using the loaded cascade file
            faces = face_cascade.detectMultiScale(gray_image, 1.1, 5)

            # Draw a rectangle around the faces
            for x, y, w, h in faces:
                cv2.rectangle(frame_rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)

        _, buffer = cv2.imencode(".jpg", frame_rgb)
        frame = buffer.tobytes()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(1 / 30)


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        get_video_stream(1), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/video_feed_down")
def video_feed():
    return StreamingResponse(
        get_video_stream(0), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/connect")
def connect():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    run_in_thread(tello.connect)
    return {"message": "Connecting to Tello..."}


@app.get("/battery")
def battery():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    battery = tello.get_battery()
    return {"battery": battery}


@app.get("/takeoff")
def takeoff():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    run_in_thread(tello.takeoff)
    return {"message": "Tello taking off..."}


@app.get("/land")
def land():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    run_in_thread(tello.land)
    return {"message": "Tello landing..."}


@app.post("/move")
def move(data: dict):
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    speed = data.get(
        "speed", 60
    )  # Use speed instead of distance to match send_rc_control

    # Access and update the global velocity state
    global velocity_state

    # Map directions to velocities
    if data.get("up_down_velocity") >= 1:
        velocity_state["up_down_velocity"] += speed
    elif data.get("up_down_velocity") <= -1:
        velocity_state["up_down_velocity"] -= speed
    elif data.get("left_right_velocity") <= 1:
        velocity_state["left_right_velocity"] -= speed
    elif data.get("left_right_velocity") >= 1:
        velocity_state["left_right_velocity"] += speed
    elif data.get("forward_backward_velocity") >= 1:
        velocity_state["forward_backward_velocity"] += speed
    elif data.get("forward_backward_velocity") <= 1:
        velocity_state["forward_backward_velocity"] -= speed
    elif data.get("yaw_velocity") <= -1:
        velocity_state["yaw_velocity"] -= speed
    elif data.get("yaw_velocity") >= 1:
        velocity_state["yaw_velocity"] += speed

    # Determine the direction based on the velocity state
    direction = []
    if velocity_state["up_down_velocity"] > 0:
        direction.append("up")
    elif velocity_state["up_down_velocity"] < 0:
        direction.append("down")

    if velocity_state["left_right_velocity"] > 0:
        direction.append("right")
    elif velocity_state["left_right_velocity"] < 0:
        direction.append("left")

    if velocity_state["forward_backward_velocity"] > 0:
        direction.append("forward")
    elif velocity_state["forward_backward_velocity"] < 0:
        direction.append("backward")

    if velocity_state["yaw_velocity"] > 0:
        direction.append("yaw_right")
    elif velocity_state["yaw_velocity"] < 0:
        direction.append("yaw_left")

    # Send the rc control command with the updated velocities
    run_in_thread(
        tello.send_rc_control,
        velocity_state["left_right_velocity"],
        velocity_state["forward_backward_velocity"],
        velocity_state["up_down_velocity"],
        velocity_state["yaw_velocity"],
    )

    return {"message": f"Moving {direction} with speed {speed}"}


@app.post("/stop")
def stop():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    tello.send_rc_control(0, 0, 0, 0)
    return {"message": "Stopping all movements"}


@app.get("/acceleration")
def get_acceleration():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    ax = tello.get_acceleration_x()
    ay = tello.get_acceleration_y()
    az = tello.get_acceleration_z()
    return {"acceleration_x": ax, "acceleration_y": ay, "acceleration_z": az}


@app.get("/barometer")
def get_barometer():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    barometer = tello.get_barometer()
    return {"barometer": barometer}


@app.get("/faceRecognition")
def faceRecognition(data: dict):
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    person = data.get("person")
    faceProccessing = 1
    return {"face": "detecting" + person}


@app.get("/faceDetection")
def faceRecognition():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    faceProccessing = -1
    return {"face": "detecting all faces"}


@app.get("/height")
def get_height():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    height = tello.get_height()
    return {"height": height}


@app.get("/temperature")
def get_temperature():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    temperature = tello.get_temperature()
    return {"temperature": temperature}


@app.get("/speed")
def get_speed():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    speed_x = tello.get_speed_x()
    speed_y = tello.get_speed_y()
    speed_z = tello.get_speed_z()
    return {"speed_x": speed_x, "speed_y": speed_y, "speed_z": speed_z}


@app.post("/flip")
def flip(data: dict):
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")

    direction = data.get("direction")
    if direction == "l":
        run_in_thread(tello.flip_left)
    elif direction == "r":
        run_in_thread(tello.flip_right)
    elif direction == "f":
        run_in_thread(tello.flip_forward)
    elif direction == "b":
        run_in_thread(tello.flip_back)
    else:
        raise HTTPException(status_code=400, detail="Invalid flip direction")
    return {"message": f"Flipping {direction}"}


@app.get("/mission_pad")
def mission_pad():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    pad_id = tello.get_mission_pad_id()
    distance_x = tello.get_mission_pad_distance_x()
    distance_y = tello.get_mission_pad_distance_y()
    distance_z = tello.get_mission_pad_distance_z()
    return {
        "pad_id": pad_id,
        "distance_x": distance_x,
        "distance_y": distance_y,
        "distance_z": distance_z,
    }


@app.get("/reboot")
def reboot():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    run_in_thread(tello.reboot)
    return {"message": "Rebooting Tello"}


@app.get("/emergency")
def reboot():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    run_in_thread(tello.emergency)
    return {"message": "Stopped all motors"}


@app.get("/rotate")
def rotate(degrees: int):
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    run_in_thread(tello.rotate_clockwise, degrees)
    return {"message": f"Rotating {degrees} degrees"}


@app.get("/get_state_field")
def get_state_field(field: str):
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    value = tello.get_state_field(field)
    return {field: value}


@app.get("/query_sdk_version")
def query_sdk_version():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    version = tello.query_sdk_version()
    return {"sdk_version": version}


@app.get("/specs")
def get_specs():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    try:
        battery = tello.get_battery()
        height = tello.get_height()
        temperature = tello.get_temperature()
        barometer = tello.get_barometer()
        speed_x = tello.get_speed_x()
        speed_y = tello.get_speed_y()
        speed_z = tello.get_speed_z()
        roll = tello.get_roll()
        pitch = tello.get_pitch()
        yaw = tello.get_yaw()
        ax = tello.get_acceleration_x()
        ay = tello.get_acceleration_y()
        az = tello.get_acceleration_z()
        flight_time = tello.get_flight_time()
        wifi_signal_noise_ratio = tello.query_wifi_signal_noise_ratio()

        specs = {
            "battery": battery,
            "height": height,
            "temperature": temperature,
            "barometer": barometer,
            "speed": {"x": speed_x, "y": speed_y, "z": speed_z},
            "acceleration": {"x": ax, "y": ay, "z": az},
            "roll": roll,
            "pitch": pitch,
            "yaw": yaw,
            "flight_time": flight_time,
            "wifi_signal_noise_ratio": wifi_signal_noise_ratio,
        }

        return specs

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Absolute path to the directory containing your static files
static_files_path = os.path.join(os.path.dirname(__file__), "build", "_app")

# Serve static files from the 'build/_app' directory
app.mount("/_app", StaticFiles(directory=static_files_path), name="static")


@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_files_path, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
