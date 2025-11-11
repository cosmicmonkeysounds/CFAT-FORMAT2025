/*
CARPET HOTEL - SuperCollider Audio Engine
==========================================

Self-contained audio engine - just evaluate this file and you're ready!
Receives OSC messages from Processing and handles all audio mixing.

OSC is BUILT INTO SuperCollider - no library needed!

OSC Messages:
- /carpet/scene [sceneNum, numWindows, isAnimating]
    Static scene: mix N audio files with equal power
- /carpet/transition [currentFloor, progress, direction, numWindows]
    Transition: crossfade up to 4 floors with smooth curves

Audio files should be in: ~/Documents/CFAT2025/carpets/carpet_hotel/data/
Named as: carpet_1.wav, carpet_2.wav, etc.

USAGE: Run with sclang carpet_hotel_audio.scd
*/

// Global variables to store state
var audioPath, floors, players, volumes;
var numFloors = 10;
var masterVolume = 0.7;
var audioDevice;

// ===== SERVER CONFIGURATION =====
"=== CARPET HOTEL AUDIO ENGINE ===".postln;

// Get audio device from command line argument (if provided)
audioDevice = thisProcess.argv.at(0);
if(audioDevice.notNil, {
    ("Using audio device: " ++ audioDevice).postln;
}, {
    "Using default audio device".postln;
});

"Configuring audio server...".postln;

// Set server options BEFORE booting
s.options.sampleRate = 44100;        // Match audio file sample rate
s.options.numOutputBusChannels = 2;  // Stereo output
s.options.numInputBusChannels = 0;   // No input needed
s.options.blockSize = 512;           // Balance between latency and CPU
s.options.memSize = 65536;           // Increased memory for buffers

// IMPORTANT: Set input and output device separately to avoid microphone issues
if(audioDevice.notNil, {
    s.options.outDevice = audioDevice;   // Output only
    s.options.inDevice = nil;            // Explicitly no input
}, {
    // Even with default, explicitly disable input
    s.options.inDevice = nil;
});

// Boot server and wait
"Booting audio server...".postln;

// Keep sclang alive with a simple recurring task
SystemClock.sched(1.0, { 1.0 }); // Reschedule every second to keep alive

s.waitForBoot({
    "Audio server ready!".postln;
    ("Sample rate: " ++ s.sampleRate ++ " Hz").postln;

    // Initialize
    floors = Dictionary.new;
    players = Dictionary.new;
    volumes = Dictionary.new;

    "=== CARPET HOTEL AUDIO ENGINE ===".postln;
    "Loading audio files...".postln;

    // Path to audio files (relative to this script)
    audioPath = (thisProcess.nowExecutingPath.dirname +/+ "../data/").standardizePath;
    ("Searching in: " ++ audioPath).postln;

    // Load all carpet audio files
    (1..numFloors).do({ |i|
        var path = audioPath ++ "carpet_" ++ i ++ ".wav";
        var file = PathName(path);

        if(file.isFile, {
            var buffer = Buffer.read(s, path);
            floors[i] = buffer;
            ("  Loaded floor " ++ i ++ ": " ++ file.fileName).postln;

            // Wait for buffer to load
            s.sync;

            // Create looping player for each floor (start silent)
            players[i] = {
                var sig = PlayBuf.ar(
                    2, // stereo
                    buffer,
                    BufRateScale.kr(buffer),
                    loop: 1
                );
                var amp = \amp.kr(0.0, 0.05); // 50ms lag for smooth changes
                sig * amp;
            }.play(outbus: 0, addAction: \addToTail);

            volumes[i] = 0.0;
        }, {
            ("  WARNING: Floor " ++ i ++ " audio not found").postln;
        });
    });

    "\n✓ Audio engine ready!".postln;
    "✓ Listening for OSC on port 57120 (built-in, no library needed)".postln;
    "\nOSC Messages:".postln;
    "  /carpet/scene [sceneNum, numWindows, isAnimating]".postln;
    "  /carpet/transition [currentFloor, progress, direction, numWindows]".postln;
    "  /carpet/volume [volume]".postln;
    "\n▶ Now run the Processing sketch!".postln;
    "▶ Press Cmd+. (or Ctrl+C) to stop all audio\n".postln;

    // OSC Responder for static scenes
    OSCdef(\carpetScene, { |msg|
        var sceneNum, numWindows, isAnimating, volumePerFloor, floorNum;

        sceneNum = msg[1].asInteger;
        numWindows = msg[2].asInteger;
        isAnimating = msg[3].asInteger;
        volumePerFloor = masterVolume / sqrt(numWindows);

        ("[OSC-RECV] /carpet/scene " ++ sceneNum ++ " " ++ numWindows ++ " " ++ isAnimating).postln;

        // Set all floors to silent first
        floors.keys.do({ |floorNum|
            if(players[floorNum].notNil, {
                players[floorNum].set(\amp, 0.0);
            });
        });

        // Set volume for active floors in current scene
        numWindows.do({ |i|
            floorNum = sceneNum + i + 2; // +2 to match file numbering
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

        ("[OSC-RECV] /carpet/transition " ++ currentFloor ++ " " ++ progress ++ " " ++ direction ++ " " ++ numWindows).postln;

        // Calculate which floors are audible (current + next)
        numWindows.do({ |i|
            audibleFloors.add(currentFloor + i + 2); // +2 for file numbering
            audibleFloors.add(nextFloor + i + 2);
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
                isNext = (floorNum >= (nextFloor + 2)) && (floorNum < (nextFloor + numWindows + 2));

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
        ("[OSC-RECV] /carpet/volume " ++ newVolume).postln;
        ("Master volume: " ++ (masterVolume * 100).round(1) ++ "%").postln;
    }, '/carpet/volume');

    // Cleanup on Cmd+.
    CmdPeriod.doOnce({
        "Stopping audio engine...".postln;
        players.do({ |player| player.free });
        floors.do({ |buffer| buffer.free });
        OSCdef(\carpetScene).free;
        OSCdef(\carpetTransition).free;
        OSCdef(\carpetVolume).free;
    });
});

/*
USAGE:
------
1. Make sure SuperCollider is installed
2. Run with: sclang carpet_hotel_audio.scd
3. Run the Processing sketch
4. Audio will automatically follow the visual transitions

TESTING:
--------
// Test scene change
n = NetAddr("127.0.0.1", 57120);
n.sendMsg("/carpet/scene", 0, 2, 0); // Scene 0, 2 windows, not animating

// Test transition
n.sendMsg("/carpet/transition", 0, 0.5, 1, 2); // Floor 0, 50% progress, going up, 2 windows

// Adjust master volume
n.sendMsg("/carpet/volume", 0.5); // 50% volume
*/
