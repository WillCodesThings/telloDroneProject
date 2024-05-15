from flask import Flask, jsonify, request, render_template, Response
from djitellopy import Tello

app = Flask(__name__)
tello = Tello()

throwTakeoff = False

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/connect', methods=['GET'])
def connect():
    tello.connect()
    return jsonify({'message': 'Connected to Tello.'})

@app.route('/battery', methods=['GET'])
def battery():
    battery = tello.get_battery()
    return jsonify({'battery': battery})

@app.route('/streamon', methods=['GET'])
def streamon():
    tello.streamon()
    return jsonify({'message': 'Video stream on.'})

@app.route('/streamoff', methods=['GET'])
def streamoff():
    tello.streamoff()
    return jsonify({'message': 'Video stream off.'})

@app.route("/video_feed", methods=["GET"])
def video_feed():
    return Response(tello.get_frame_read(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route('/flightTime', methods=['GET'])
def flightTime():
    flightTime = tello.get_flight_time()
    return jsonify({'flightTime': flightTime})

@app.route('/curHeight', methods=['GET'])
def curHeight():
    curHeight = tello.get_height()
    return jsonify({'curHeight': curHeight})

@app.route('/curTemp', methods=['GET'])
def curTemp():
    curTemp = tello.get_temperature()
    return jsonify({'curTemp': curTemp})

@app.route('/throwTakeoff', methods=['GET'])
def throwTakeoff():
    throwTakeoff = not throwTakeoff

    if throwTakeoff:
        tello.throw_and_go()
        return jsonify({'message': 'Tello throw and go.'})
    else:
        tello.land()
        return jsonify({'message': 'Tello landing.'})

@app.route('/takeoff', methods=['GET'])
def takeoff():
    tello.takeoff()
    return jsonify({'message': 'Tello taking off.'})

@app.route('/land', methods=['GET'])
def land():
    tello.land()
    return jsonify({'message': 'Tello landing.'})

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    direction = data.get('direction')
    distance = data.get('distance')
    if direction == 'up':
        tello.move_up(distance)
    elif direction == 'down':
        tello.move_down(distance)
    elif direction == 'left':
        tello.move_left(distance)
    elif direction == 'right':
        tello.move_right(distance)
    elif direction == 'forward':
        tello.move_forward(distance)
    elif direction == 'back':
        tello.move_back(distance)
    return jsonify({'message': f'Moved {direction} by {distance} cm.'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
