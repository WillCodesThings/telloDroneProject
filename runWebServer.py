from flask import Flask, jsonify, request, Response, send_from_directory
from djitellopy import Tello
import threading

app = Flask(__name__, static_folder='build/_app', static_url_path='/_app')

tello = None
throwTakeoff = False

def run_in_thread(target, *args, **kwargs):
    thread = threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.start()
    return thread

def initialize_tello():
    global tello
    tello = Tello()
    try:
        tello.connect()
        print("Connected to Tello.")
    except Exception as e:
        print(f"Error initializing Tello: {e}")

@app.route("/", methods=["GET"])
def index():
    return send_from_directory('build/_app', 'index.html')

@app.route("/connect", methods=["GET"])
def connect():
    run_in_thread(tello.connect)
    return jsonify({"message": "Connecting to Tello..."})

@app.route("/battery", methods=["GET"])
def battery():
    battery = tello.get_battery()
    return jsonify({"battery": battery})

@app.route("/streamon", methods=["GET"])
def streamon():
    run_in_thread(tello.streamon)
    return jsonify({"message": "Turning video stream on..."})

@app.route("/streamoff", methods=["GET"])
def streamoff():
    run_in_thread(tello.streamoff)
    return jsonify({"message": "Turning video stream off..."})

@app.route("/video_feed", methods=["GET"])
def video_feed():
    return Response(
        tello.get_frame_read(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/video", methods=["GET"])
def video():
    return tello.get_udp_video_address()

@app.route("/speed", methods=["GET"])
def speed():
    speed = tello.get_speed()
    return jsonify({"speed": speed})

@app.route("/flightTime", methods=["GET"])
def flightTime():
    flightTime = tello.get_flight_time()
    return jsonify({"flightTime": flightTime})

@app.route("/curHeight", methods=["GET"])
def curHeight():
    curHeight = tello.get_height()
    return jsonify({"curHeight": curHeight})

@app.route("/curTemp", methods=["GET"])
def curTemp():
    curTemp = tello.get_temperature()
    return jsonify({"curTemp": curTemp})

@app.route("/throwTakeoff", methods=["GET"])
def throw_takeoff():
    global throwTakeoff
    throwTakeoff = not throwTakeoff

    if throwTakeoff:
        run_in_thread(tello.throw_and_go)
        return jsonify({"message": True})
    else:
        run_in_thread(tello.land)
        return jsonify({"message": False})

@app.route("/takeoff", methods=["GET"])
def takeoff():
    run_in_thread(tello.takeoff)
    return jsonify({"message": "Tello taking off..."})

@app.route("/land", methods=["GET"])
def land():
    run_in_thread(tello.land)
    return jsonify({"message": "Tello landing..."})

@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()
    direction = data.get("direction")
    distance = data.get("distance")
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
    return jsonify({"message": f"Moved {direction} by {distance} cm."})

# Serve static files from the 'build/_app' directory
@app.route('/_app/<path:filename>')
def custom_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    run_in_thread(initialize_tello)
    app.run(debug=True, host="0.0.0.0", port=5000)
