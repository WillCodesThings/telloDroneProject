import math
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dependencies.faceRecognition import FacialRecognition
from djitellopy import Tello
import threading
import time
import cv2
import os
import json
import asyncio

app = FastAPI()

faceRecognition = FacialRecognition("faces")

velocity_x, velocity_y, velocity_z = 0.0, 0.0, 0.0
previous_timestamp = None

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

clients = []

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


def get_video_stream():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")

    frame_read = tello.get_frame_read()
    while True:
        try:
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
            time.sleep(1 / 35)
        except Exception as e:
            print(f"Error in video stream: {e}")
            time.sleep(1)


@app.get("/video_feed")
def video_feed():
    run_in_thread(tello.set_video_direction, tello.CAMERA_FORWARD)
    return StreamingResponse(
        get_video_stream(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/video_feed_down")
def video_feed_down():
    run_in_thread(tello.set_video_direction, tello.CAMERA_DOWNWARD)
    return StreamingResponse(
        get_video_stream(), media_type="multipart/x-mixed-replace; boundary=frame"
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

    def takeoff_with_logging():
        try:
            response = tello.takeoff()
            print(f"Takeoff response: {response}")
        except Exception as e:
            print(f"Error during takeoff: {e}")

    run_in_thread(takeoff_with_logging)
    return {"message": "Tello taking off..."}


@app.get("/land")
def land():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")

    def land_with_logging():
        try:
            response = tello.land()
            print(f"Land response: {response}")
        except Exception as e:
            print(f"Error during landing: {e}")

    run_in_thread(land_with_logging)
    return {"message": "Tello landing..."}


@app.websocket("/ws/move")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            movement_data = json.loads(data)
            await handle_movement(movement_data)
    except WebSocketDisconnect:
        clients.remove(websocket)


async def handle_movement(data: dict):
    if not tello_ready_event.is_set():
        for client in clients:
            await client.send_text(json.dumps({"error": "Tello not initialized"}))
        return

    speed = data.get("speed", 60)

    # Access and update the global velocity state
    global velocity_state

    # Update velocities based on input data
    velocity_state["left_right_velocity"] = data.get("left_right_velocity", 0) * speed
    velocity_state["forward_backward_velocity"] = data.get("forward_backward_velocity", 0) * speed
    velocity_state["up_down_velocity"] = data.get("up_down_velocity", 0) * speed
    velocity_state["yaw_velocity"] = data.get("yaw_velocity", 0) * speed

    # Send the rc control command with the updated velocities
    tello.send_rc_control(
        velocity_state["left_right_velocity"],
        velocity_state["forward_backward_velocity"],
        velocity_state["up_down_velocity"],
        velocity_state["yaw_velocity"],
    )

    # Stop the drone if all velocities are zero
    if all(v == 0 for v in velocity_state.values()):
        tello.send_rc_control(0, 0, 0, 0)

    # Broadcast updated state to all clients
    for client in clients:
        await client.send_text(json.dumps(velocity_state))


@app.websocket("/ws/specs")
async def specs_websocket(websocket: WebSocket):
    global velocity_x, velocity_y, velocity_z, previous_timestamp
    await websocket.accept()
    try:
        while True:
            if tello_ready_event.is_set():
                timestamp = time.time()
                if previous_timestamp is not None:
                    # transform three accelerations to one velocity
                    dt = timestamp - previous_timestamp
                    # accels
                    ax = tello.get_acceleration_x()
                    ay = tello.get_acceleration_y()
                    az = tello.get_acceleration_z()
                    # update velocity
                    velocity_x += ax * dt
                    velocity_y += ay * dt
                    velocity_z += az * dt
                
                previous_timestamp = timestamp
                #pythagorean theorem yipee
                speed = math.sqrt(velocity_x**2 + velocity_y**2 + velocity_z**2)

                battery = tello.get_battery()
                height = -1 * tello.get_height()
                temperature = tello.get_temperature()
                barometer = tello.get_barometer()
                speed_x = tello.get_speed_x()
                speed_y = tello.get_speed_y()
                speed_z = tello.get_speed_z()
                roll = tello.get_roll()
                pitch = tello.get_pitch()
                yaw = tello.get_yaw()
                
                flight_time = tello.get_flight_time()

                specs = {
                    "battery": battery,
                    "height": height,
                    "temperature": temperature,
                    "barometer": barometer,
                    "speed": {"x": speed_x, "y": speed_y, "z": speed_z},
                    "speed_magnitude": speed, # calculated speed, id trust it
                    "acceleration": {"x": ax, "y": ay, "z": az},
                    "roll": roll,
                    "pitch": pitch,
                    "yaw": yaw,
                    "flight_time": flight_time,
                }
                await websocket.send_text(json.dumps(specs))
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        pass


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
def face_recognition(data: dict):
    global faceProccessing
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    person = data.get("person")
    faceProccessing = 1
    return {"face": "detecting " + person}


@app.get("/faceDetection")
def face_detection():
    global faceProccessing
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    faceProccessing = -1
    return {"face": "detecting all faces"}


@app.get("/faceRecognitionStop")
def face_recognition_stop():
    global faceProccessing
    faceProccessing = 0
    return {"face": "stop detecting"}


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
def emergency():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    run_in_thread(tello.emergency)
    return {"message": "Stopped all motors"}

@app.get("/throwTakeoff")
def emergency():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    run_in_thread(tello.initiate_throw_takeoff)
    return {"message": "Throw within 5 seconds"}

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
