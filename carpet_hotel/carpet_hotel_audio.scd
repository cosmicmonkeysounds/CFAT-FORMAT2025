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

USAGE: Select all code and press Cmd+Enter
*/

(
// ===== SERVER CONFIGURATION =====
"=== CARPET HOTEL AUDIO ENGINE ===".postln;
"Configuring audio server...".postln;

// Set server options BEFORE booting
s.options.sampleRate = 44100;        // Match audio file sample rate
s.options.numOutputBusChannels = 2;  // Stereo output
s.options.numInputBusChannels = 0;   // No input needed
s.options.blockSize = 512;           // Balance between latency and CPU
s.options.memSize = 65536;           // Increased memory for buffers

// Boot server if not already booted
if(s.serverRunning.not, {
    "Booting audio server...".postln;
    s.boot;
});

// ===== WAIT FOR BOOT, THEN INITIALIZE =====
s.waitForBoot({
    var audioPath, floors, players, volumes;
    var numFloors = 10;
    var masterVolume = 0.7;

    "Audio server ready!".postln;
    ("Sample rate: " ++ s.sampleRate ++ " Hz").postln;

    // Path to audio files
    audioPath = "~/Documents/CFAT2025/carpets/carpet_hotel/data/".standardizePath;

    // Initialize
    floors = Dictionary.new;
    players = Dictionary.new;
    volumes = Dictionary.new;

    "=== CARPET HOTEL AUDIO ENGINE ===".postln;
    "Loading audio files...".postln;

    // Load all carpet audio files
    (1..numFloors).do({ |i|
        var path = audioPath ++ "carpet_" ++ i ++ ".wav";
        var file = PathName(path);

        if(file.isFile, {
            var buffer = Buffer.read(s, path);
            floors[i] = buffer;
            ("  Loaded floor " ++ i ++ ": " ++ file.fileName).postln;

            // Create looping player for each floor (start silent)
            s.sync;
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
    "▶ Press Cmd+. to stop all audio\n".postln;

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
            floorNum = sceneNum + i + 2; // +2 to match file numbering
            if(players[floorNum].notNil, {
                players[floorNum].set(\amp, volumePerFloor);
            });
        });

        // Debug output
        // ("Scene: " ++ sceneNum ++ " | Active floors: " ++ numWindows).postln;
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

        // Debug output
        // ("Transition: floor " ++ currentFloor ++ " -> " ++ nextFloor ++ " | progress: " ++ progress).postln;
    }, '/carpet/transition');

    // Master volume control via OSC
    OSCdef(\carpetVolume, { |msg|
        var newVolume;

        newVolume = msg[1].asFloat.clip(0.0, 1.0);
        masterVolume = newVolume;
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
)

/*
USAGE:
------
1. Make sure SuperCollider is running
2. Evaluate this file (Cmd+Enter with cursor in the parentheses)
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
