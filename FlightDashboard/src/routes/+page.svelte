<script>
    import { onMount } from "svelte";
    import Bg from "../assets/images/mapBG-removebg.png"
    import { ArrowUpIcon, ArrowDownIcon, CornerUpLeftIcon, CornerUpRightIcon, RepeatIcon, AlertTriangleIcon, ChevronsDownIcon, ChevronsUpIcon, ChevronsLeftIcon, ChevronsRightIcon, AnchorIcon, CloudIcon, RadioIcon, FeatherIcon, EyeIcon, CrosshairIcon } from "svelte-feather-icons";

    import { writable } from "svelte/store";

    let droneImage = "";

    let speed = 0; // speed in percentage of max speed
    let flightTime = 0; // flight time in seconds
    let battery = 100; // battery percentage
    let emergency = false; // emergency status
    let moveSpeed = 10; // speed in cm/s
    let PersonToDetect = ""; // person to detect
    let throwableLaunch = false; // throwable launch status
    let curTemp = 0; // current temperature
    let launched = false; // launched status
    let directions = writable({
        forward: false,
        backward: false,
        left: false,
        right: false
    });

    function toggleLaunch() {
        launched = !launched;
        console.log(launched);
    }

    // Function to toggle direction
    function toggleDirection(key) {
        // set all directions to false
        directions.update(current => {
            for (const direction in current) {
                current[direction] = false;
            }
            return current;
        });
        directions.update(current => {
            current[key] = !current[key];
            console.log(key, current[key]);
            return current;
        });
        console.log($directions);
    }

    function toggleEmergency() {
        emergency = !emergency;
        console.log(emergency);
    }

    function toggleThrowableLaunch() {
        throwableLaunch = true;
        console.log(throwableLaunch);
        setInterval(() => {
            throwableLaunch = false;
        }, 5000);
    }
    
    // color pallete
    // https://coolors.co/171219-225560-edf060-f0803c-310d20

    onMount(() => {
        console.log("Page mounted");

        droneImage = fetch("http://localhost:5000/video")
            .then((response) => response.json())
            .then((data) => {
                console.log(data);
                droneImage = data;
            });

        // setInterval(() => {
        //     droneImage = fetch("http://localhost:5000/video_feed")
        //         .then((response) => response.json())
        //         .then((data) => {
        //             console.log(data);
        //             droneImage = data;
        //         });
        // }, 5);

        const needle = document.querySelector('.needle');
        const speedDisplay = document.getElementById('speedValue');

        function updateSpeed(speed) {
            speed = Math.max(0, Math.min(100, speed)); // Clamp speed to the 0-100 range
            const angle = (speed / 100) * 180; // Map speed to angle between 0 degrees (left) and 180 degrees (right)
            needle.style.transform = `rotate(${angle - 90}deg)`; // Subtract 90 to align with the semi-circle start from left
        }

        document.addEventListener('keydown', (event) => {
            switch (event.key) {
                case 'w':
                    speed += 10;
                    break;
                case 's':
                    speed -= 10;
                    break;
                case 'a':
                    speed = 0;
                    break;
                case 'd':
                    speed = 100;
                    break;
                case 'ArrowUp':
                    speed += 10;
                    break;
                case 'ArrowDown':
                    speed -= 10;
                    break;
                case 'q':
                    speed += 10;
                    break;
                case 'e':
                    speed -= 10;
                    break;
                default:
                    break;
            }
            updateSpeed(speed);
            speedDisplay.textContent = `${speed} cm/s`;
        });

        const wasdControls = document.querySelector('.wasd-controls');
        wasdControls.addEventListener('click', (event) => {
            // Ensure we get the button element, regardless of what inside the button was clicked
            let target = event.target;
            while (target !== wasdControls && !target.getAttribute('data-direction')) {
                target = target.parentNode;
            }
            if (target.getAttribute('data-direction')) {
                const direction = target.getAttribute('data-direction');
                console.log(`Moving ${direction}`);
                // Replace console.log with your drone control command
                // Example: drone.move(direction);
            }
        });

        updateSpeed(speed); // Initial speed update

    });
</script>

<section class="bg-[#225560] w-full h-[100vh] relative text-[#E6E1D3]">
    <!-- Drone Dashboard -->
    <div class="grid grid-cols-5 grid-rows-5 w-full h-full absolute z-front gap-4 p-2 z-10">
        <div class="bg-[#171219] col-span-3 row-span-3 rounded-2xl p-2 flex flex-row">
            <div class="w-[75%] h-full bg-[#171219] shadow-[#29202c] shadow-sm rounded-md overflow-hidden" id="Camera">
                <!-- Placeholder for drone image -->
                <img src="http://localhost:8000/video_feed" alt="Drone Live Feed" class="rounded-md">
            </div>
            
            <select class="mx-auto mt-20 w-48 h-16 bg-[#29202c] rounded-md text-[#E6E1D3] font-medium text-xl p-2" name="cameras" id="Cameras">
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
                <div class="text-xl font-sans">{speed} cm/s</div>
            </div>
            
        </div>
        <div class="bg-[#171219] col-span-1 row-span-1 rounded-xl p-3 flex flex-col justify-center items-center ease-in-out text-center text-xl">
            Flight Time: 
            <div class="text-5xl font-semibold text-lime-500"> {flightTime} </div>
        </div>
        <div class="bg-[#171219] col-span-1 row-span-1 rounded-xl p-3 flex flex-row gap-10 justify-center items-center ease-in-out text-center text-xl">
            <div class="flex flex-col justify-center items-center">
                Battery: 
                <div class="{battery > 80 ? "text-green-500" : battery > 40 ? "text-orange-500" : "text-red-500"} text-5xl font-semibold"> {battery} %</div>
            </div>
            <div class="flex flex-col justify-center items-center">
                Temp:
                <div class="{curTemp > 80 ? "text-red-500" : curTemp > 40 ? "text-orange-500" : "text-blue-500"} text-5xl font-semibold"> {curTemp}°</div>
            </div>
            

        </div>

        <div class="bg-[#171219] col-span-1 row-span-1 rounded-xl p-3 flex flex-col justify-center items-center ease-in-out text-center text-xl">
            Altitude:
            <div class="text-5xl font-semibold text-lime-500"> 0 cm</div>
        </div>

        <div class="bg-[#171219] col-span-2 row-span-1 rounded-xl p-3 flex flex-row justify-evenly items-center ease-in-out text-center text-xl">
            <div class="flex flex-col">
                Roll:
                <div class="text-5xl font-semibold text-lime-500"> 0°</div>
            </div>
            <div class="flex flex-col">
                Pitch:
                <div class="text-5xl font-semibold text-amber-500"> 0°</div>
            </div>
            <div class="flex flex-col">
                Yaw:
                <div class="text-5xl font-semibold text-yellow-500"> 0°</div>
            </div>
        </div>

        <div class="bg-[#171219] col-span-3 row-span-2 rounded-xl px-10 py-3 flex flex-row justify-center gap-10 items-center ease-in-out text-center text-xl">
            <!-- WASD Controller -->
            <div class="wasd-controls">
                <div class="flex flex-col items-center justify-center space-y-2 ">
                    <div class="font-medium py-2">Movement Control</div>
                    <div class="flex items-center justify-center space-x-2">
                        <button class="control-btn flex justify-center items-center bg-[#29202c]" data-direction="up"><CornerUpLeftIcon/></button>
                        <button class="control-btn bg-[#29202c]" data-direction="forward">W</button>
                        <button class="control-btn flex justify-center items-center bg-[#29202c]" data-direction="down"><CornerUpRightIcon/></button>
                    </div>
                    <div class="flex space-x-2">
                        <button class="control-btn bg-[#29202c]" data-direction="left">A</button>
                        <button class="control-btn bg-[#29202c]" data-direction="backward">S</button>
                        <button class="control-btn bg-[#29202c]" data-direction="right">D</button>
                    </div>
                </div>
            </div>

            <!-- Flip Controller -->
            <div class="flex flex-col items-center justify-center space-y-2">
                <div class="font-medium py-2">Flip/Emergency Control</div>
                <div class="flex flex-row gap-2">
                    <button class="control-btn flex flex-col items-center justify-center bg-[#29202c]" data-direction="flip"><RepeatIcon/></button>
                
                <button class="control-btn flex flex-col items-center justify-center {emergency ? "bg-red-600" : "bg-[#29202c]"}" on:click={() => toggleEmergency()} data-direction="emergency"><AlertTriangleIcon/></button>
                </div>
            </div>
            <div class="">
                <div class="font-medium py-2">Flip Direction</div>
                <div class="grid grid-cols-2 grid-rows-2 items-center justify-center gap-2">
                    
                        <button 
                            class:active={$directions.forward}
                            class="control-btn {$directions.forward ? 'bg-green-700' : 'bg-[#29202c]'} flex flex-col items-center justify-center"
                            on:click={() => toggleDirection('forward')}>
                            <ChevronsUpIcon/>
                        </button>
                        <button 
                            class:active={$directions.backward}
                            class="control-btn {$directions.backward ? 'bg-green-700' : 'bg-[#29202c]'} flex flex-col items-center justify-center"
                            on:click={() => toggleDirection('backward')}>
                            <ChevronsDownIcon/>
                        </button>
                        <button
                            class:active={$directions.left}
                            class="control-btn {$directions.left ? 'bg-green-700' : 'bg-[#29202c]'} flex flex-col items-center justify-center"
                            on:click={() => toggleDirection('left')}>
                            <ChevronsLeftIcon/>
                        </button>
                        <button 
                        class:active={$directions.right}
                            class="control-btn {$directions.right ? 'bg-green-700' : 'bg-[#29202c]'} flex flex-col items-center justify-center"
                            on:click={() => toggleDirection('right')}>
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
                    <button class="control-btn bg-[#29202c] flex flex-col justify-center items-center"><CloudIcon/></button>
                    <button class="control-btn bg-[#29202c] flex flex-col justify-center items-center"><AnchorIcon/></button>
                </div>
                
            </div>
            
        </div>

        <div class="bg-[#171219] col-span-2 row-span-1 rounded-xl p-3 flex flex-row justify-evenly items-center ease-in-out text-center text-xl">
            <div class="flex flex-col text-center">
                <div class="font-medium py-2">Face Detection</div>
                <div class="flex flex-row justify-evenly">
                    <button class="control-btn bg-[#29202c] flex flex-col justify-center items-center"><CrosshairIcon/></button>
                    <button class="control-btn bg-[#29202c] flex flex-col justify-center items-center"><EyeIcon/></button>
                </div>
                
                <select bind:value={PersonToDetect} class="bg-[#29202c] rounded-md text-[#E6E1D3] font-medium mt-2">
                    <option value="person">Will</option>
                    <option value="car">Objects</option>
                </select>
            </div>
            <div class="flex flex-row items-center">
                <div class="flex-col flex justify-center items-center">
                    <div class="font-medium py-2">Throwable Launch</div>
                    <div class="flex flex-row gap-2">
                        <button class="control-btn {throwableLaunch ? 'bg-green-500' : 'bg-[#29202c]'} flex flex-col justify-center items-center" on:click={() => {toggleThrowableLaunch()}}><FeatherIcon/></button>
                    <button class="control-btn {launched ? 'bg-green-500' : 'bg-[#29202c]'} flex flex-col justify-center items-center" on:click={() => {toggleLaunch()}}><RadioIcon/></button>
                    </div>
                    
                </div>
                
                <!-- add toggle switch here -->                
            </div>
            
        </div>
    </div>
    <img class="absolute top-0 w-full h-full object-fill opacity-10 invert select-none cursor-default z-0" src="{Bg}" alt="Map Background">
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