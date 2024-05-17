from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from djitellopy import Tello
import threading
import time
import cv2
import os

app = FastAPI()

tello = Tello()
tello_ready_event = threading.Event()

def initialize_tello():
    global tello
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
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(1 / 30)  # 30 FPS

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
    distance = data.get("distance", 60)  # Use 60 if distance is not provided

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

# Absolute path to the directory containing your static files
static_files_path = os.path.join(os.path.dirname(__file__), 'build', '_app')

# Serve static files from the 'build/_app' directory
app.mount("/_app", StaticFiles(directory=static_files_path), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
