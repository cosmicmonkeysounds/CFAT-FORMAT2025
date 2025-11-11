/*
Test carpet_hotel_sound.scd with explicit device selection
to fix the premature server exit issue
*/

(
// ===== GLOBAL STATE =====
var audioPath, floors, players, volumes;
var numFloors = 10;
var masterVolume = 0.7;
var sampleRate = 44100;  // Changed from 48000

// ===== STARTUP MESSAGE =====
"=== CARPET HOTEL AUDIO ENGINE (TEST) ===".postln;

// ===== STEP 1: CONFIGURE SERVER =====
~configureServer = {
    "Configuring audio server...".postln;

    // Try explicit device instead of auto-detect
    s.options.device = "MacBook Pro Speakers";  // NEW: Explicit device
    s.options.sampleRate = sampleRate;
    s.options.numOutputBusChannels = 2;
    s.options.numInputBusChannels = 0;

    ("Device: " ++ s.options.device).postln;
    ("Sample rate: " ++ sampleRate ++ " Hz").postln;
    "✓ Server configured".postln;
};

// ===== STEP 2: LOAD AUDIO FILES =====
~loadAudioFiles = {
    "Loading audio files...".postln;

    // Initialize dictionaries
    floors = Dictionary.new;
    players = Dictionary.new;
    volumes = Dictionary.new;

    // Path to audio files
    audioPath = (thisProcess.nowExecutingPath.dirname +/+ "../../data/").standardizePath;
    ("Searching in: " ++ audioPath).postln;

    // Load all carpet audio files in a Routine
    Routine({
        (1..numFloors).do({ |i|
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
                    var amp = \amp.kr(0.0, 0.05);
                    // If mono, duplicate to stereo output
                    if(numChannels == 1, {
                        sig = sig ! 2;
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
    "✓ OSC handlers ready".postln;
};

// ===== STEP 4: CLEANUP =====
~setupCleanup = {
    CmdPeriod.doOnce({
        "Stopping audio engine...".postln;
        if(players.notNil, { players.do({ |player| player.free }); });
        if(floors.notNil, { floors.do({ |buffer| buffer.free }); });
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
