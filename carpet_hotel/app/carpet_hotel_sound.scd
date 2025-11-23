/*
CARPET HOTEL - SuperCollider Audio Engine
==========================================

Multi-floor audio system matching Processing video architecture.

Architecture:
- Loads WAV files that loop independently (like videos)
- Two audio busses representing "floors" (like displays in Processing)
- Scene changes move which WAV files are active on each bus
- Crossfading during transitions (like video movement)

Routing Modes:
- Quad:   Bus 1 → channels 0+1, Bus 2 → channels 2+3
- Stereo: Bus 1 → channel 0,    Bus 2 → channel 1

OSC Messages:
- /carpet/scene [sceneNum, numBusses, isAnimating]
- /carpet/transition [currentFloor, progress, direction, numBusses]
- /carpet/volume [volume]
*/

(
// ===== GLOBAL STATE =====
var audioPath, floors, busPlayers;
var numFloors = 0;  // Detected dynamically
var numBusses = 2;  // Two audio busses (like two displays)
var masterVolume = 0.7;
var routingMode = \quad;  // \quad or \stereo (passed via command-line)

// ===== STARTUP MESSAGE =====
"=== CARPET HOTEL AUDIO ENGINE ===".postln;

// Parse command-line arguments
// argv[0] = routing mode ("quad" or "stereo")
if(thisProcess.argv.size > 0, {
    var modeStr = thisProcess.argv[0].asString;
    routingMode = modeStr.asSymbol;
    ("Routing mode: " ++ routingMode).postln;
}, {
    "No routing mode specified, using default: quad".postln;
});

// ===== STEP 1: CONFIGURE SERVER =====
~configureServer = {
    "Configuring audio server...".postln;

    // Configure output channels based on routing mode
    if(routingMode == \quad, {
        s.options.numOutputBusChannels = 4;  // Quad: 4 channels
        "✓ Server configured for QUAD output (4 channels)".postln;
        "  Bus 1 → outputs 0+1".postln;
        "  Bus 2 → outputs 2+3".postln;
    }, {
        s.options.numOutputBusChannels = 2;  // Stereo: 2 channels
        "✓ Server configured for STEREO output (2 channels)".postln;
        "  Bus 1 → output 0".postln;
        "  Bus 2 → output 1".postln;
    });

    s.options.numInputBusChannels = 0;   // No input needed
};

// ===== STEP 2: LOAD AUDIO FILES =====
~loadAudioFiles = {
    var carpetFiles, floorNumbers;

    "Loading audio files...".postln;

    // Initialize dictionaries
    // floors: floor number → Buffer
    // busPlayers: [busIndex][floorNum] → Synth
    floors = Dictionary.new;
    busPlayers = Array.fill(numBusses, { Dictionary.new });

    // Path to audio files
    audioPath = (thisProcess.nowExecutingPath.dirname +/+ "../data/").standardizePath;
    ("Searching in: " ++ audioPath).postln;

    // Dynamically detect available carpet_*.wav files
    carpetFiles = PathName(audioPath).files.select({ |file|
        (file.fileName.toLower.beginsWith("carpet_") ||
         file.fileName.toLower.beginsWith("carpet")) &&
        file.extension.toLower == "wav"
    });

    if(carpetFiles.size == 0, {
        "ERROR: No carpet WAV files found!".postln;
        numFloors = 0;
    }, {
        // Extract floor numbers from filenames
        floorNumbers = carpetFiles.collect({ |file|
            var filename = file.fileNameWithoutExtension;
            var numStr = filename.findRegexp("[0-9]+");
            if(numStr.size > 0, {
                numStr[0][1].asInteger;
            }, {
                0;
            });
        }).sort;

        numFloors = floorNumbers.size;
        ("Found " ++ numFloors ++ " audio files").postln;

        // Load all carpet audio files
        Routine({
            floorNumbers.do({ |floorNum, idx|
                var matchingFile = carpetFiles.detect({ |file|
                    var filename = file.fileNameWithoutExtension;
                    var numStr = filename.findRegexp("[0-9]+");
                    if(numStr.size > 0, {
                        numStr[0][1].asInteger == floorNum;
                    }, {
                        false;
                    });
                });

                if(matchingFile.notNil, {
                    var buffer = Buffer.read(s, matchingFile.fullPath);
                    s.sync;

                    floors[idx] = buffer;  // Store by index (0-based)
                    ("  ✓ Loaded floor " ++ idx ++ ": " ++ matchingFile.fileName).postln;

                    // Create looping players for each floor - one per bus
                    numBusses.do({ |busIdx|
                        var outChannels, synth;

                        // Determine output channels based on routing mode
                        if(routingMode == \quad, {
                            // Quad mode: each bus gets 2 channels
                            outChannels = busIdx * 2;  // Bus 0→ch0+1, Bus 1→ch2+3
                        }, {
                            // Stereo mode: each bus gets 1 channel
                            outChannels = busIdx;  // Bus 0→ch0, Bus 1→ch1
                        });

                        // Create synth for this floor on this bus
                        synth = {
                            var numChannels = buffer.numChannels;
                            var sig = PlayBuf.ar(
                                numChannels,
                                buffer,
                                BufRateScale.kr(buffer),
                                loop: 1
                            );
                            var amp = \amp.kr(0.0, 0.1);  // 100ms lag for smooth crossfades

                            // Handle mono/stereo conversion based on routing mode
                            if(routingMode == \quad, {
                                // Quad mode: output stereo to two channels
                                if(numChannels == 1, {
                                    sig = sig ! 2;  // Duplicate mono to stereo
                                });
                                sig * amp;
                            }, {
                                // Stereo mode: output mono to one channel
                                if(numChannels == 2, {
                                    sig = Mix(sig);  // Mix stereo to mono
                                });
                                sig * amp;
                            });
                        }.play(outbus: outChannels, addAction: \addToTail);

                        // Store synth
                        busPlayers[busIdx][idx] = synth;
                    });
                });
            });

            "\n✓ Audio engine ready!".postln;
            ("✓ " ++ numFloors ++ " floors loaded").postln;
            "✓ Listening for OSC on port 57120".postln;
        }).play;
    });
};

// ===== STEP 3: SETUP OSC HANDLERS =====
~setupOSC = {
    "Setting up OSC handlers...".postln;

    // OSC Responder for static scenes
    OSCdef(\carpetScene, { |msg|
        var sceneNum, numWindows, isAnimating;

        sceneNum = msg[1].asInteger;
        numWindows = msg[2].asInteger;
        isAnimating = msg[3].asInteger;

        // Silent all floors on all busses first
        numBusses.do({ |busIdx|
            busPlayers[busIdx].keysValuesDo({ |floorIdx, synth|
                if(synth.notNil, {
                    synth.set(\amp, 0.0);
                });
            });
        });

        // Set volume for active floors in current scene
        // Each bus shows one floor (like each display shows one video)
        numBusses.do({ |busIdx|
            var floorIdx = sceneNum + busIdx;  // Scene 0: floors 0+1, Scene 1: floors 1+2, etc.
            var synth;

            // Bounds check
            if((floorIdx >= 0) && (floorIdx < numFloors), {
                synth = busPlayers[busIdx][floorIdx];
                if(synth.notNil, {
                    synth.set(\amp, masterVolume);
                });
            });
        });
    }, '/carpet/scene');

    // OSC Responder for transitions
    OSCdef(\carpetTransition, { |msg|
        var currentFloor, progress, direction, numWindows;
        var currentFloorIdx, nextFloorIdx, fadeOutGain, fadeInGain;

        currentFloor = msg[1].asInteger;
        progress = msg[2].asFloat;
        direction = msg[3].asInteger;  // +1 ascending, -1 descending
        numWindows = msg[4].asInteger;

        // Smooth crossfade using sine/cosine curves
        fadeOutGain = cos(progress * 0.5pi);  // 1.0 → 0.0
        fadeInGain = sin(progress * 0.5pi);   // 0.0 → 1.0

        // Silent all floors on all busses first
        numBusses.do({ |busIdx|
            busPlayers[busIdx].keysValuesDo({ |floorIdx, synth|
                if(synth.notNil, {
                    synth.set(\amp, 0.0);
                });
            });
        });

        // Crossfade between current and next floors for each bus
        numBusses.do({ |busIdx|
            var currentFloorForBus, nextFloorForBus;
            var currentSynth, nextSynth;

            // Calculate current and next floor indices for this bus
            currentFloorForBus = currentFloor + busIdx;
            nextFloorForBus = (currentFloor + direction) + busIdx;

            // Fade out current floor
            if((currentFloorForBus >= 0) && (currentFloorForBus < numFloors), {
                currentSynth = busPlayers[busIdx][currentFloorForBus];
                if(currentSynth.notNil, {
                    currentSynth.set(\amp, fadeOutGain * masterVolume);
                });
            });

            // Fade in next floor
            if((nextFloorForBus >= 0) && (nextFloorForBus < numFloors), {
                nextSynth = busPlayers[busIdx][nextFloorForBus];
                if(nextSynth.notNil, {
                    nextSynth.set(\amp, fadeInGain * masterVolume);
                });
            });
        });
    }, '/carpet/transition');

    // Master volume control via OSC
    OSCdef(\carpetVolume, { |msg|
        var newVolume;

        newVolume = msg[1].asFloat.clip(0.0, 1.0);
        masterVolume = newVolume;
        ("Volume: " ++ (masterVolume * 100).round(1) ++ "%").postln;
    }, '/carpet/volume');

    "✓ OSC handlers ready".postln;
};

// ===== STEP 4: CLEANUP =====
~setupCleanup = {
    CmdPeriod.doOnce({
        "Stopping audio engine...".postln;

        // Free all synths on all busses
        numBusses.do({ |busIdx|
            busPlayers[busIdx].do({ |synth|
                if(synth.notNil, { synth.free });
            });
        });

        // Free all buffers
        floors.do({ |buffer|
            if(buffer.notNil, { buffer.free });
        });

        // Free OSC responders
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
