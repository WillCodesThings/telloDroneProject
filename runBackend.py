from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from djitellopy import Tello
import threading
import time
import cv2
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

def get_video_stream():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")

    frame_read = tello.get_frame_read()
    while True:
        frame = frame_read.frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', frame_rgb)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(1 / 30)

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(get_video_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

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
    
    direction = data.get("direction")
    distance = data.get("distance", 60)

    if direction == "up":
        run_in_thread(tello.move_up, distance)
    elif direction == "down":
        run_in_thread(tello.move_down, distance)
    elif direction == "left":
        run_in_thread(tello.move_left, distance)
    elif direction == "right":
        run_in_thread(tello.move_right, distance)
    elif direction == "forward":
        run_in_thread(tello.move_forward, distance)
    elif direction == "back":
        run_in_thread(tello.move_back, distance)
    elif direction == "yaw_left":
        run_in_thread(tello.rotate_counter_clockwise, distance)
    elif direction == "yaw_right":
        run_in_thread(tello.rotate_clockwise, distance)
    return {"message": f"Moved {direction} by {distance} cm."}

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
    if direction == "left":
        run_in_thread(tello.flip_left)
    elif direction == "right":
        run_in_thread(tello.flip_right)
    elif direction == "forward":
        run_in_thread(tello.flip_forward)
    elif direction == "back":
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
        "distance_z": distance_z
    }

@app.get("/reboot")
def reboot():
    if not tello_ready_event.is_set():
        raise HTTPException(status_code=500, detail="Tello not initialized")
    run_in_thread(tello.reboot)
    return {"message": "Rebooting Tello"}

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
            "speed": {
                "x": speed_x,
                "y": speed_y,
                "z": speed_z
            },
            "acceleration": {
                "x": ax,
                "y": ay,
                "z": az
            },
            "roll": roll,
            "pitch": pitch,
            "yaw": yaw,
            "flight_time": flight_time,
            "wifi_signal_noise_ratio": wifi_signal_noise_ratio
        }

        return specs

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Absolute path to the directory containing your static files
static_files_path = os.path.join(os.path.dirname(__file__), 'build', '_app')

# Serve static files from the 'build/_app' directory
app.mount("/_app", StaticFiles(directory=static_files_path), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_files_path, 'index.html'))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
