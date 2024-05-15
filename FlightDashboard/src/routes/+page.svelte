<script>
    import { onMount } from "svelte";
    import Bg from "../assets/images/mapBG-removebg.png"

    let droneImage = "";

    onMount(() => {
        console.log("Page mounted");

        droneImage = ""

        // setInterval(() => {
        //     droneImage = fetch("http://localhost:5000/droneImage")
        //         .then((response) => response.json())
        //         .then((data) => {
        //             console.log(data);
        //             droneImage = data;
        //         });
        // }, 5);

    });
</script>

<section class="bg-slate-700 w-full h-[100vh] relative">
    <!-- Drone Dashboard -->
    <div class="grid grid-cols-5 grid-rows-5 w-full h-full absolute z-front gap-4 p-2 z-10">
        <div class="bg-black col-span-3 row-span-3 rounded-2xl">
            <img src={droneImage} alt="">
        </div>
        <div class="bg-black">a</div>
        <div class="bg-black">a</div>
        <div class="bg-black">a</div>
        <div class="bg-black">a</div>
        <div class="bg-black">a</div>
        <div class="bg-black">a</div>
        <div class="bg-black">a</div>
        <div class="bg-black">a</div>
        <div class="bg-black">a</div>
    </div>
    <img class="absolute top-0 w-full h-full object-fill opacity-10 invert select-none cursor-default z-0" src={Bg} alt="mapBG">
</section>
