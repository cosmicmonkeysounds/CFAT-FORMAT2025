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
var masterVolume = 0.7;

// ===== STARTUP MESSAGE =====
"=== CARPET HOTEL AUDIO ENGINE ===".postln;

// ===== STEP 1: CONFIGURE SERVER =====
~configureServer = {
    "Configuring audio server...".postln;

    // Use system defaults for device and sample rate
    // User sets audio device via macOS System Settings
    s.options.numOutputBusChannels = 2;  // Stereo output
    s.options.numInputBusChannels = 0;   // No input needed

    "✓ Server configured (using system defaults)".postln;
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

                // Create looping player for each floor (start silent)
                players[i] = {
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
                }.play(outbus: 0, addAction: \addToTail);

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
        var sceneNum, numWindows, isAnimating, volumePerFloor, floorNum;

        sceneNum = msg[1].asInteger;
        numWindows = msg[2].asInteger;
        isAnimating = msg[3].asInteger;
        volumePerFloor = masterVolume / sqrt(numWindows);

        // Set all floors to silent first
        floors.keys.do({ |floorNum|
            if(players[floorNum].notNil, {
                players[floorNum].set(\amp, 0.0);
            });
        });

        // Set volume for active floors in current scene
        numWindows.do({ |i|
            floorNum = sceneNum + i + 1; // +1 because scenes are 0-indexed but files start at 1
            if(players[floorNum].notNil, {
                players[floorNum].set(\amp, volumePerFloor);
            });
        });
    }, '/carpet/scene');

    // OSC Responder for transitions
    OSCdef(\carpetTransition, { |msg|
        var currentFloor, progress, direction, numWindows, nextFloor, audibleFloors, volumePerFloor;

        currentFloor = msg[1].asInteger;
        progress = msg[2].asFloat;
        direction = msg[3].asInteger;
        numWindows = msg[4].asInteger;
        nextFloor = currentFloor + direction;
        audibleFloors = Set.new;

        // Calculate which floors are audible (current + next)
        numWindows.do({ |i|
            audibleFloors.add(currentFloor + i + 1); // +1 because scenes are 0-indexed but files start at 1
            audibleFloors.add(nextFloor + i + 1);
        });

        // Equal power mixing
        volumePerFloor = masterVolume / sqrt(audibleFloors.size);

        // Set all floors to silent first
        floors.keys.do({ |floorNum|
            if(players[floorNum].notNil, {
                players[floorNum].set(\amp, 0.0);
            });
        });

        // Apply crossfade with smooth curves
        audibleFloors.do({ |floorNum|
            var isNext, crossfadeGain, finalVolume;

            if(players[floorNum].notNil, {
                isNext = (floorNum >= (nextFloor + 1)) && (floorNum < (nextFloor + numWindows + 1));

                if(isNext, {
                    // Fading in: sine curve (0 to 1)
                    crossfadeGain = sin(progress * 0.5pi);
                }, {
                    // Fading out: cosine curve (1 to 0)
                    crossfadeGain = cos(progress * 0.5pi);
                });

                finalVolume = volumePerFloor * crossfadeGain;
                players[floorNum].set(\amp, finalVolume);
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
        players.do({ |player| player.free });
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
