<script>
    import { onMount } from "svelte";
    import Bg from "../assets/images/mapBG-removebg.png";
    import { CornerUpLeftIcon, CornerUpRightIcon, RepeatIcon, AlertTriangleIcon, ChevronsDownIcon, ChevronsUpIcon, ChevronsLeftIcon, ChevronsRightIcon, AnchorIcon, CloudIcon, RadioIcon, FeatherIcon, EyeIcon, CrosshairIcon } from "svelte-feather-icons";
    import { writable } from "svelte/store";

    let droneImage = "";
    let speed = 0; // speed in percentage of max speed
    let flightTime = 0; // flight time in seconds
    let battery = 100; // battery percentage
    let emergency = false; // emergency status
    let moveSpeed = 10; // speed in cm/s
    let PersonToDetect = ""; // person to detect
    let throwableLaunch = false; // throwable launch status
    let altitude = 0;
    let curTemp = 0; // current temperature
    let launched = false; // launched status
    let flipDir = "f";
    let roll = 0;
    let pitch = 0;
    let cameraDirection = "front";
    let yaw = 0;
    let directions = writable({
        forward: false,
        backward: false,
        left: false,
        right: false,
        yaw_left: false,
        yaw_right: false,
        up: false,
        down: false
    });

    // Function to send HTTP requests
    async function sendRequest(url, method = 'GET', body = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: body ? JSON.stringify(body) : null
        };
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            document.getElementById('console').innerHTML = document.getElementById('console').innerHTML + `<br/>` + JSON.stringify(data, null, 2);

            return data;
        } catch (error) {
            console.error('Error:', error);
        }
    }

    // Function to toggle launch
    function toggleLaunch() {
        launched = !launched;
        if (launched) {
            sendRequest('http://localhost:8000/takeoff');
        } else {
            sendRequest('http://localhost:8000/land');
        }
    }

    function faceRecognition() {
        sendRequest('http://localhost:8000/faceRecognition', 'POST', { person: PersonToDetect });
    }

    function faceDetection() {
        sendRequest('http://localhost:8000/faceDetection');
    }

    // Function to update direction and send control commands
    function updateDirection(direction, isActive) {
        directions.update(current => {
            current[direction] = isActive;
            return current;
        });

        const currentDirections = $directions;
        const velocities = {
            left_right_velocity: (currentDirections.right ? 1 : 0) - (currentDirections.left ? 1 : 0),
            forward_backward_velocity: (currentDirections.forward ? 1 : 0) - (currentDirections.backward ? 1 : 0),
            up_down_velocity: (currentDirections.up ? 1 : 0) - (currentDirections.down ? 1 : 0),
            yaw_velocity: (currentDirections.yaw_right ? 1 : 0) - (currentDirections.yaw_left ? 1 : 0),
            speed: moveSpeed
        };

        sendRequest('http://localhost:8000/move', 'POST', velocities);
    }

    function updateMovement() {

    }

    function handleKeydown(event) {
        switch (event.key) {
            case 'w':
                updateDirection('forward', true);
                break;
            case 's':
                updateDirection('backward', true);
                break;
            case 'a':
                updateDirection('left', true);
                break;
            case 'd':
                updateDirection('right', true);
                break;
            case 'ArrowUp':
                updateDirection('up', true);
                break;
            case 'ArrowDown':
                updateDirection('down', true);
                break;
            case 'q':
                updateDirection('yaw_left', true);
                break;
            case 'e':
                updateDirection('yaw_right', true);
                break;
            case 't':
                toggleLaunch();
                break;
            default:
                break;
        }
    }

    function handleKeyup(event) {
        console.log(event.key);
        switch (event.key) {
            case 'w':
                updateDirection('forward', false);
                break;
            case 's':
                updateDirection('backward', false);
                break;
            case 'a':
                updateDirection('left', false);
                break;
            case 'd':
                updateDirection('right', false);
                break;
            case 'ArrowUp':
                updateDirection('up', false);
                break;
            case 'ArrowDown':
                updateDirection('down', false);
                break;
            case 'q':
                updateDirection('yaw_left', false);
                break;
            case 'e':
                updateDirection('yaw_right', false);
                break;
            default:
                break;
        }
    }

    function toggleDirection(direction) {
        flipDir = direction;
    }

    function toggleEmergency() {
        emergency = !emergency;
        console.log(emergency);
        sendRequest('http://localhost:8000/emergency');
    }

    function toggleThrowableLaunch() {
        throwableLaunch = true;
        sendRequest('http://localhost:8000/throwTakeoff');
        console.log(throwableLaunch);
        setInterval(() => {
            throwableLaunch = false;
        }, 5000);
    }

    async function updateStats() {
        const specs = await sendRequest('http://localhost:8000/specs');

        try {
            if (specs.error || specs['detail'].includes("Tello not initialized")) {
                battery = 0;
                curTemp = 0;
                flightTime = 0;
                roll = 0;
                pitch = 0;
                yaw = 0;
                altitude = 0;
            }
            return;
        } catch (error) {
            console.error('Error:', error);
        }

        battery = specs.battery;
        curTemp = specs.temperature;
        flightTime = specs.flight_time;
        roll = specs.roll;
        pitch = specs.pitch;
        yaw = specs.yaw;
        altitude = specs.height;
    }

    onMount(() => {
        console.log("Page mounted");

        droneImage = fetch("http://localhost:8000/video_feed")
            .then((response) => response.json())
            .then((data) => {
                console.log(data);
                droneImage = data;
            });

        const needle = document.querySelector('.needle');
        const speedDisplay = document.getElementById('speedValue');

        function updateSpeed(speed) {
            speed = Math.max(0, Math.min(100, speed)); // Clamp speed to the 0-100 range
            const angle = (speed / 100) * 180; // Map speed to angle between 0 degrees (left) and 180 degrees (right)
            needle.style.transform = `rotate(${angle - 90}deg)`; // Subtract 90 to align with the semi-circle start from left
        }

        document.addEventListener('keydown', handleKeydown);
        document.addEventListener('keyup', handleKeyup);

        updateSpeed(speed); // Initial speed update
        updateStats();
        setInterval(updateStats, 1000); // Update stats every second
    });
</script>

<section class="bg-[#225560] w-full h-[100vh] relative text-[#E6E1D3]">
    <!-- Drone Dashboard -->
    <div class="grid grid-cols-5 grid-rows-5 w-full h-full absolute z-front gap-4 p-2 z-10">
        <div class="bg-[#171219] col-span-3 row-span-3 rounded-2xl p-2 flex flex-row">
            <div class="w-[75%] h-full bg-[#171219] shadow-[#29202c] shadow-sm rounded-md overflow-hidden" id="Camera">
                <!-- Placeholder for drone image -->
                <img src="{cameraDirection.includes("front") ? "http://localhost:8000/video_feed" : "http://localhost:8000/video_feed_down"}" alt="Drone Live Feed" class="rounded-md">
            </div>
            
            <select class="mx-auto mt-20 w-48 h-16 bg-[#29202c] rounded-md text-[#E6E1D3] font-medium text-xl p-2" name="cameras" id="Cameras" bind:value={cameraDirection}>
                <option value="front">Front Camera</option>
                <option value="bottom">Bottom Camera</option>
            </select>
        </div>
        <div class="bg-[#171219] col-span-1 row-span-1 rounded-xl p-3 flex justify-center items-center ease-in-out">
            <div class="speedometer justify-center items-center flex flex-col">
                <svg viewBox="0 0 200 100" width="300px" height="150px">
                    <path d="M 10,90 A 80,80 0 0,1 190,90" fill="transparent" stroke="#333" stroke-width="2"/>
                    <!-- Colored tick marks -->
                    <g fill="none" stroke-width="2" transform="translate(100,90)">
                        ${[...Array(21)].map((_, i) => {
                            const colors = ['#E6E1D3', '#E6E1D3', '#E6E1D3']; // Colors for ticks, adjust or add more as needed
                            return `<line x1="0" y1="-80" x2="0" y2="-70" stroke="${colors[Math.floor(i / 7)]}" 
                                  transform="rotate(${135 + i * 4.5})"/>`;
                        }).join('')}
                    </g>
                </svg>
                <div class="needle"></div>
                <div class="text-xl font-sans" id="speedValue">{speed} cm/s</div>
            </div>
        </div>
        <div class="bg-[#171219] col-span-1 row-span-1 rounded-xl p-3 flex flex-col justify-center items-center ease-in-out text-center text-xl">
            Flight Time: 
            <div class="text-5xl font-semibold text-lime-500"> {flightTime} </div>
        </div>
        <div class="bg-[#171219] col-span-1 row-span-1 rounded-xl p-3 flex flex-row gap-10 justify-center items-center ease-in-out text-center text-xl">
            <div class="flex flex-col justify-center items-center">
                Battery: 
                <div class="{battery > 80 ? 'text-green-500' : battery > 40 ? 'text-orange-500' : 'text-red-500'} text-5xl font-semibold"> {battery} %</div>
            </div>
            <div class="flex flex-col justify-center items-center">
                Temp:
                <div class="{curTemp > 80 ? 'text-red-500' : curTemp > 40 ? 'text-orange-500' : 'text-blue-500'} text-5xl font-semibold"> {curTemp}°</div>
            </div>
        </div>

        <div class="bg-[#171219] col-span-1 row-span-1 rounded-xl p-3 flex flex-col justify-center items-center ease-in-out text-center text-xl">
            Altitude:
            <div class="text-5xl font-semibold text-lime-500" id="altitude">{altitude} cm</div>
        </div>

        <div class="bg-[#171219] col-span-2 row-span-1 rounded-xl p-3 flex flex-row justify-evenly items-center ease-in-out text-center text-xl">
            <div class="flex flex-col">
                Roll:
                <div class="text-5xl font-semibold text-lime-500">{roll}°</div>
            </div>
            <div class="flex flex-col">
                Pitch:
                <div class="text-5xl font-semibold text-amber-500">{pitch}°</div>
            </div>
            <div class="flex flex-col">
                Yaw:
                <div class="text-5xl font-semibold text-yellow-500">{yaw}°</div>
            </div>
        </div>

        <div class="bg-[#171219] col-span-3 row-span-2 rounded-xl px-10 py-3 flex flex-row justify-center gap-10 items-center ease-in-out text-center text-xl">
            <!-- WASD Controller -->
            <div class="wasd-controls">
                <div class="flex flex-col items-center justify-center space-y-2 ">
                    <div class="font-medium py-2">Movement Control</div>
                    <div class="flex items-center justify-center space-x-2">
                        <button class="control-btn flex justify-center items-center {$directions.yaw_left ? 'bg-green-700' : 'bg-[#29202c]'}" data-direction="up"><CornerUpLeftIcon/></button>
                        <button class="control-btn {$directions.forward ? 'bg-green-700' : 'bg-[#29202c]'}" data-direction="forward">W</button>
                        <button class="control-btn flex justify-center items-center {$directions.yaw_right ? 'bg-green-700' : 'bg-[#29202c]'}" data-direction="down"><CornerUpRightIcon/></button>
                    </div>
                    <div class="flex space-x-2">
                        <button class="control-btn {$directions.left ? 'bg-green-700' : 'bg-[#29202c]'}" data-direction="left">A</button>
                        <button class="control-btn {$directions.backward ? 'bg-green-700' : 'bg-[#29202c]'}" data-direction="backward">S</button>
                        <button class="control-btn {$directions.right ? 'bg-green-700' : 'bg-[#29202c]'}" data-direction="right">D</button>
                    </div>
                </div>
            </div>

            <!-- Flip Controller -->
            <div class="flex flex-col items-center justify-center space-y-2">
                <div class="font-medium py-2">Flip/Emergency Control</div>
                <div class="flex flex-row gap-2">
                    <button class="control-btn flex flex-col items-center justify-center bg-[#29202c]" on:click={() => sendRequest('http://localhost:8000/flip', 'POST', { direction: flipDir })}><RepeatIcon/></button>
                    <button class="control-btn flex flex-col items-center justify-center {emergency ? 'bg-red-600' : 'bg-[#29202c]'}" on:click={toggleEmergency} data-direction="emergency"><AlertTriangleIcon/></button>
                </div>
            </div>
            <div class="">
                <div class="font-medium py-2">Flip Direction</div>
                <div class="grid grid-cols-2 grid-rows-2 items-center justify-center gap-2">
                    <button 
                        class:active={flipDir.includes("f")}
                        class="control-btn {flipDir.includes("f") ? 'bg-green-700' : 'bg-[#29202c]'} flex flex-col items-center justify-center"
                        on:click={() => toggleDirection('f')}>
                        <ChevronsUpIcon/>
                    </button>
                    <button 
                        class:active={flipDir.includes("b")}
                        class="control-btn {flipDir.includes("b") ? 'bg-green-700' : 'bg-[#29202c]'} flex flex-col items-center justify-center"
                        on:click={() => toggleDirection('b')}>
                        <ChevronsDownIcon/>
                    </button>
                    <button
                        class:active={flipDir.includes("l")}
                        class="control-btn {flipDir.includes("l") ? 'bg-green-700' : 'bg-[#29202c]'} flex flex-col items-center justify-center"
                        on:click={() => toggleDirection('l')}>
                        <ChevronsLeftIcon/>
                    </button>
                    <button 
                        class:active={flipDir.includes("r")}
                        class="control-btn {flipDir.includes("r") ? 'bg-green-700' : 'bg-[#29202c]'} flex flex-col items-center justify-center"
                        on:click={() => toggleDirection('r')}>
                        <ChevronsRightIcon/>
                    </button>
                </div>
            </div>
            
            <!-- speed control -->

            <div class="">
                <div class="font-medium py-2">Speed Control</div>
                <div class="flex flex-col items-center justify-center space-y-2">
                    <input type="range" min="10" max="50" class="bg-[#29202c] appearance-none w-full h-2 rounded-full outline-none slider-thumb:bg-green-500 slider-thumb:hover:bg-green-700" style="cursor:pointer;" bind:value={moveSpeed}>
                    {moveSpeed} cm/s
                </div>
            </div>

            <div class="">
                <div class="font-medium py-2">Launch Control</div>
                <div class="flex flex-row items-center justify-center gap-2">
                    <button class="{launched ? 'bg-green-700' : 'bg-[#29202c]'} control-btn bg-[#29202c] flex flex-col justify-center items-center" on:click={toggleLaunch}><CloudIcon/></button>
                    <button class="control-btn {throwableLaunch ? 'bg-green-500' : 'bg-[#29202c]'} flex flex-col justify-center items-center" on:click={toggleThrowableLaunch}><FeatherIcon/></button>
                </div>
            </div>
        </div>

        <div class="bg-[#171219] col-span-2 row-span-1 rounded-xl p-3 flex flex-row justify-evenly items-center ease-in-out text-center text-xl">
            <div class="flex flex-col text-center">
                <div class="font-medium py-2">Face Detection</div>
                <div class="flex flex-row justify-evenly">
                    <button class="control-btn bg-[#29202c] flex flex-col justify-center items-center" on:click={faceRecognition()}><CrosshairIcon/></button>
                    <button class="control-btn bg-[#29202c] flex flex-col justify-center items-center" on:clic={faceDetection()}><EyeIcon/></button>
                </div>
                
                <select bind:value={PersonToDetect} class="bg-[#29202c] rounded-md text-[#E6E1D3] font-medium mt-2">
                    <option value="person">Will</option>
                    <option value="car">Objects</option>
                </select>
            </div>
        </div>

        <!-- console -->
        <div class="bg-[#171219] col-span-2 row-span-1 rounded-xl p-3 flex flex-row justify-evenly items-center ease-in-out text-center text-xl">
            <div class="w-full h-full bg-[#0e0b0f] overflow-y-scroll overflow-x-hidden" id="console"></div>
        </div>
    </div>
    <img class="absolute top-0 w-full h-full object-fill opacity-10 invert select-none cursor-default z-0" src={Bg} alt="Map Background">
</section>

<style>
    .speedometer {
        position: relative;
        width: 300px; /* Adjust if necessary */
        height: 150px; /* Adjust if necessary */
    }
    .needle {
        width: 2px;
        height: 80px;  /* This should be long enough to reach or almost reach the top of the arc. */
        background-color: red;
        position: absolute;
        bottom: 40px;  /* Adjust this value to properly position the needle's pivot at the arc's base */
        left: 50%;
        transform-origin: bottom;  /* Ensures rotation around the bottom of the needle */
        transition: transform 0.3s ease-in-out;
    }

    /* Customizing the slider thumb for WebKit browsers */
    input[type="range"]::-webkit-slider-thumb {
        -webkit-appearance: none; /* Removes default system styling */
        appearance: none;
        background: #4CAF50; /* Green background */
        cursor: pointer;
        height: 20px; /* Set the height */
        width: 20px; /* Set the width */
        border-radius: 50%; /* Circular shape */
        border: 2px solid #29202c; /* Dark border */
    }

    /* Customizing the slider thumb for Firefox */
    input[type="range"]::-moz-range-thumb {
        background: #4CAF50;
        cursor: pointer;
        height: 20px;
        width: 20px;
        border-radius: 50%;
        border: 2px solid #29202c;
    }

    .control-btn {
    width: 50px;
    height: 50px;
    color: #E6E1D3;
    border: none;
    border-radius: 5px;
    font-size: 20px;
    font-weight: bold;
    cursor: pointer;
    outline: none;
    transition: background-color 0.3s ease;
    }

    .control-btn:hover {
        background-color: #3a3a3a;
    }

    .wasd-controls {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
</style>
