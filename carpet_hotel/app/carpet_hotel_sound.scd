/*
CARPET HOTEL - SuperCollider Audio Engine
==========================================

Modular audio engine with functions for each component.

OSC Messages:
- /carpet/scene [sceneNum, numWindows, isAnimating]
- /carpet/transition [currentFloor, progress, direction, numWindows]
- /carpet/volume [volume]
*/

(
// ===== GLOBAL STATE =====
var audioPath, floors, players, volumes;
var numFloors; // Will be set dynamically based on available files
var numScreens = 2; // Number of display screens
var masterVolume = 0.7;

// ===== STARTUP MESSAGE =====
"=== CARPET HOTEL AUDIO ENGINE ===".postln;

// ===== STEP 1: CONFIGURE SERVER =====
~configureServer = {
    "Configuring audio server...".postln;

    // Use system defaults for device and sample rate
    // User sets audio device via macOS System Settings
    s.options.numOutputBusChannels = 4;  // 4 channels: Screen1(0-1), Screen2(2-3)
    s.options.numInputBusChannels = 0;   // No input needed

    "✓ Server configured (4 channels: 2 screens × stereo)".postln;
};

// ===== STEP 2: LOAD AUDIO FILES =====
~loadAudioFiles = {
    var carpetFiles, floorNumbers;

    "Loading audio files...".postln;

    // Initialize dictionaries
    floors = Dictionary.new;
    players = Dictionary.new;
    volumes = Dictionary.new;

    // Path to audio files
    audioPath = (thisProcess.nowExecutingPath.dirname +/+ "../data/").standardizePath;
    ("Searching in: " ++ audioPath).postln;

    // Dynamically detect available carpet_*.wav files
    carpetFiles = PathName(audioPath).files.select({ |file|
        file.fileName.beginsWith("carpet_") && file.extension == "wav"
    });

    // Extract floor numbers from filenames
    floorNumbers = carpetFiles.collect({ |file|
        var numStr = file.fileNameWithoutExtension.replace("carpet_", "");
        numStr.asInteger;
    });

    // Set numFloors based on available files
    if(floorNumbers.size > 0, {
        numFloors = floorNumbers.maxItem;
        ("Found " ++ floorNumbers.size ++ " audio files (max floor: " ++ numFloors ++ ")").postln;
    }, {
        "ERROR: No carpet_*.wav files found!".postln;
        numFloors = 0;
    });

    // Load all carpet audio files in a Routine
    Routine({
        floorNumbers.do({ |i|
            var path = audioPath ++ "carpet_" ++ i ++ ".wav";
            var file = PathName(path);

            if(file.isFile, {
                var buffer = Buffer.read(s, path);
                floors[i] = buffer;
                ("  ✓ Loaded floor " ++ i ++ ": " ++ file.fileName).postln;

                // Wait for buffer to load
                s.sync;

                // Create looping players for each floor - one per screen
                // players[floorNum] will be an IdentityDictionary with keys 'screen0', 'screen1'
                players[i] = IdentityDictionary.new;

                numScreens.do({ |screenIdx|
                    var outbus = screenIdx * 2; // Screen 0 → bus 0-1, Screen 1 → bus 2-3
                    var screenKey = ("screen" ++ screenIdx).asSymbol;

                    players[i][screenKey] = {
                        var numChannels = buffer.numChannels;
                        var sig = PlayBuf.ar(
                            numChannels,
                            buffer,
                            BufRateScale.kr(buffer),
                            loop: 1
                        );
                        var amp = \amp.kr(0.0, 0.05); // 50ms lag for smooth changes
                        // If mono, duplicate to stereo output
                        if(numChannels == 1, {
                            sig = sig ! 2;  // Duplicate mono to stereo
                        });
                        sig * amp;
                    }.play(outbus: outbus, addAction: \addToTail);
                });

                volumes[i] = 0.0;
            }, {
                ("  WARNING: Floor " ++ i ++ " audio not found").postln;
            });
        });

        "\n✓ Audio engine ready!".postln;
        "✓ Listening for OSC on port 57120".postln;
    }).play;
};

// ===== STEP 3: SETUP OSC HANDLERS =====
~setupOSC = {
    "Setting up OSC handlers...".postln;

    // OSC Responder for static scenes
    OSCdef(\carpetScene, { |msg|
        var sceneNum, numWindows, isAnimating, volumePerFloor;

        sceneNum = msg[1].asInteger;
        numWindows = msg[2].asInteger;
        isAnimating = msg[3].asInteger;
        volumePerFloor = masterVolume; // Full volume per screen in stable mode

        // Set all floors on all screens to silent first
        floors.keys.do({ |floorNum|
            if(players[floorNum].notNil, {
                numScreens.do({ |screenIdx|
                    var screenKey = ("screen" ++ screenIdx).asSymbol;
                    var player = players[floorNum][screenKey];
                    if(player.notNil, {
                        player.set(\amp, 0.0);
                    });
                });
            });
        });

        // Set volume for active floors in current scene
        // Each screen shows one floor
        numWindows.do({ |screenIdx|
            var floorNum = sceneNum + screenIdx + 1; // +1 because scenes are 0-indexed but files start at 1
            var screenKey = ("screen" ++ screenIdx).asSymbol;
            var player;

            // Bounds check - only play if floor exists
            if((floorNum >= 1) && (floorNum <= numFloors), {
                if(players[floorNum].notNil, {
                    player = players[floorNum][screenKey];
                    if(player.notNil, {
                        player.set(\amp, volumePerFloor);
                    });
                });
            });
        });
    }, '/carpet/scene');

    // OSC Responder for transitions
    OSCdef(\carpetTransition, { |msg|
        var currentFloor, progress, direction, numWindows;
        var currentFloorNum, nextFloorNum, fadeOutGain, fadeInGain;

        currentFloor = msg[1].asInteger;
        progress = msg[2].asFloat;
        direction = msg[3].asInteger;
        numWindows = msg[4].asInteger;

        // Smooth crossfade using sine/cosine curves
        fadeOutGain = cos(progress * 0.5pi);  // 1.0 → 0.0
        fadeInGain = sin(progress * 0.5pi);   // 0.0 → 1.0

        // Set all floors to silent first
        floors.keys.do({ |floorNum|
            if(players[floorNum].notNil, {
                numScreens.do({ |screenIdx|
                    var screenKey = ("screen" ++ screenIdx).asSymbol;
                    var player = players[floorNum][screenKey];
                    if(player.notNil, {
                        player.set(\amp, 0.0);
                    });
                });
            });
        });

        // Crossfade between current and next floors for each screen
        numWindows.do({ |screenIdx|
            var screenKey = ("screen" ++ screenIdx).asSymbol;
            var currentFloorForScreen, nextFloorForScreen;

            // Calculate current and next floor numbers for this screen
            currentFloorForScreen = currentFloor + screenIdx + 1; // +1 for file numbering
            nextFloorForScreen = (currentFloor + direction) + screenIdx + 1;

            // Bounds check - only play if floor exists
            // Fade out current floor
            if((currentFloorForScreen >= 1) && (currentFloorForScreen <= numFloors), {
                if(players[currentFloorForScreen].notNil, {
                    var player = players[currentFloorForScreen][screenKey];
                    if(player.notNil, {
                        player.set(\amp, fadeOutGain * masterVolume);
                    });
                });
            });

            // Fade in next floor
            if((nextFloorForScreen >= 1) && (nextFloorForScreen <= numFloors), {
                if(players[nextFloorForScreen].notNil, {
                    var player = players[nextFloorForScreen][screenKey];
                    if(player.notNil, {
                        player.set(\amp, fadeInGain * masterVolume);
                    });
                });
            });
        });
    }, '/carpet/transition');

    // Master volume control via OSC
    OSCdef(\carpetVolume, { |msg|
        var newVolume;

        newVolume = msg[1].asFloat.clip(0.0, 1.0);
        masterVolume = newVolume;
    }, '/carpet/volume');

    "✓ OSC handlers ready".postln;
};

// ===== STEP 4: CLEANUP =====
~setupCleanup = {
    CmdPeriod.doOnce({
        "Stopping audio engine...".postln;
        // Free all players (now dictionaries of synths)
        players.do({ |playerDict|
            if(playerDict.isKindOf(Dictionary), {
                playerDict.do({ |synth| synth.free });
            });
        });
        floors.do({ |buffer| buffer.free });
        OSCdef(\carpetScene).free;
        OSCdef(\carpetTransition).free;
        OSCdef(\carpetVolume).free;
    });
};

// ===== MAIN EXECUTION =====
"Booting audio server...".postln;

// Configure server
~configureServer.value;

// Boot server and wait for it
s.waitForBoot({
    "Audio server ready!".postln;
    ("Sample rate: " ++ s.sampleRate ++ " Hz").postln;

    // Keep sclang alive (MUST be inside waitForBoot)
    SystemClock.sched(1.0, { 1.0 });

    // Setup everything else
    ~loadAudioFiles.value;
    ~setupOSC.value;
    ~setupCleanup.value;

    "\n=== READY ===".postln;
    "Press Cmd+. to stop\n".postln;
});

) // End of main block
