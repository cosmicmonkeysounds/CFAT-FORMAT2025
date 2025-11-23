/*
CARPET HOTEL - SuperCollider Audio Engine
==========================================

Multi-floor audio system matching Processing video architecture.

Architecture:
- Loads WAV files that loop independently (like videos)
- Two audio busses representing "floors" (like displays in Processing)
- Scene changes move which WAV files are active on each bus
- Crossfading during transitions (like video movement)

Signal Chain (per bus):
  SOURCE GROUP:  Floors → Doppler → Processing Bus
  ROUTING GROUP: Processing Bus → Dry Route → Master Bus
                 Processing Bus → Reverb Send → Reverb Send Bus
  REVERB GROUP:  Reverb Send Bus → Reverb → Freq Shift → Master Bus
  MASTER GROUP:  Master Bus (dry+wet mix) → Dynamic EQ → EQ Bus → Limiter → Output

Node groups ensure proper execution order for clean signal flow.

Transition Effects:
- Reverb Send: 0.0 → 1.0 (equal gain) → 0.0 (sine curve)
- Reverb: FreeVerb (room=0.9, mix=0.5)
- Frequency Shift: ±5 Hz, direction-based
- Doppler: ±15% pitch shift on dry signal
- Dry and wet signals mix at master bus, then processed together through EQ→Limiter

Routing Modes:
- Quad:   Bus 1 (dry+wet) → channels 0+1, Bus 2 (dry+wet) → channels 2+3
- Stereo: Bus 1 (dry+wet) → channel 0,    Bus 2 (dry+wet) → channel 1

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
var processingBusses, masterBusses, eqBusses, eqSynths, limiterSynths;  // Audio processing
var reverbSendBusses, reverbProcessedBusses;  // Reverb busses
var reverbSendSynths, reverbProcessSynths;  // Array of reverb synths (one per bus)
var dryRouteSynths;  // Dry signal routing synths
var sourceGroup, routingGroup, reverbGroup, masterGroup;  // Node groups for ordering

// Doppler effect settings
var dopplerEnabled = true;
var dopplerIntensity = 1.0;  // Max pitch shift: ±15% (1.15x / 0.85x)

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
    s.options.numAudioBusChannels = 2048;  // Plenty of busses for processing
};

// ===== STEP 1B: DEFINE SYNTHDEFS =====
~defineSynthDefs = {
    "Defining SynthDefs...".postln;

    // 3-band Dynamic EQ
    SynthDef(\dynamicEQ, {
        arg inBus, outBus,
        // Band 1 (Low)
        freq1=120, q1=1.0, gain1=0.0, thresh1=(-20), attack1=0.01, release1=0.1,
        // Band 2 (Mid)
        freq2=1000, q2=1.0, gain2=0.0, thresh2=(-20), attack2=0.01, release2=0.1,
        // Band 3 (High)
        freq3=8000, q3=1.0, gain3=0.0, thresh3=(-20), release3=0.1, attack3=0.01;

        var in, sig, band1, band2, band3, env1, env2, env3;
        var comp1, comp2, comp3, mixed;
        var numChannels = 2;  // Stereo processing

        in = In.ar(inBus, numChannels);

        // Band 1: Low frequencies
        band1 = BPF.ar(in, freq1, 1.0/q1);
        env1 = Amplitude.ar(band1, attack1, release1);
        comp1 = (env1.ampdb - thresh1).max(0) / thresh1.abs;
        comp1 = comp1 * gain1;  // Apply gain based on threshold excess

        // Band 2: Mid frequencies
        band2 = BPF.ar(in, freq2, 1.0/q2);
        env2 = Amplitude.ar(band2, attack2, release2);
        comp2 = (env2.ampdb - thresh2).max(0) / thresh2.abs;
        comp2 = comp2 * gain2;

        // Band 3: High frequencies
        band3 = BPF.ar(in, freq3, 1.0/q3);
        env3 = Amplitude.ar(band3, attack3, release3);
        comp3 = (env3.ampdb - thresh3).max(0) / thresh3.abs;
        comp3 = comp3 * gain3;

        // Apply dynamic gain to each band
        band1 = band1 * comp1.dbamp;
        band2 = band2 * comp2.dbamp;
        band3 = band3 * comp3.dbamp;

        // Mix processed bands back with original
        sig = in + band1 + band2 + band3;

        Out.ar(outBus, sig);
    }).add;

    // Limiter - Stereo
    SynthDef(\limiterStereo, {
        arg inBus, outBus,
        threshold=(-0.5), releaseTime=0.01;

        var in, limited;

        in = In.ar(inBus, 2);  // Stereo input
        limited = Limiter.ar(in, threshold.dbamp, releaseTime);

        Out.ar(outBus, limited);  // Stereo output
    }).add;

    // Limiter - Mono
    SynthDef(\limiterMono, {
        arg inBus, outBus,
        threshold=(-0.5), releaseTime=0.01;

        var in, limited;

        in = In.ar(inBus, 2);  // Stereo input
        in = Mix(in);  // Mix to mono
        limited = Limiter.ar(in, threshold.dbamp, releaseTime);

        Out.ar(outBus, limited);  // Mono output
    }).add;

    // Reverb - Stereo
    SynthDef(\stereoReverb, {
        arg inBus, outBus,
        mix=0.33, room=0.5, damp=0.5;

        var in, reverb;

        in = In.ar(inBus, 2);  // Stereo input
        reverb = FreeVerb2.ar(in[0], in[1], mix, room, damp);

        Out.ar(outBus, reverb);  // Stereo output
    }).add;

    // Frequency Shifter - Stereo
    SynthDef(\freqShifter, {
        arg inBus, outBus,
        shift=0.0;  // Frequency shift in Hz

        var in, shifted;

        in = In.ar(inBus, 2);  // Stereo input
        // Apply frequency shifting to both channels
        shifted = FreqShift.ar(in, shift);

        Out.ar(outBus, shifted);  // Stereo output
    }).add;

    // Reverb router - Routes stereo reverb to quad or stereo output
    SynthDef(\reverbRouter, {
        arg inBus, outBus, mode=0;  // mode: 0=stereo, 1=quad

        var in;

        in = In.ar(inBus, 2);  // Stereo input

        // mode == 0: Stereo (2 channels)
        // mode == 1: Quad (duplicate stereo to 4 channels)
        if(mode == 0, {
            Out.ar(outBus, in);  // Stereo output
        }, {
            Out.ar(outBus, [in[0], in[1], in[0], in[1]]);  // Quad: duplicate L/R
        });
    }).add;

    // Reverb send - Sends signal from processing bus to reverb
    SynthDef(\reverbSend, {
        arg inBus, outBus, sendLevel=0.0;

        var in;

        in = In.ar(inBus, 2);  // Stereo input
        Out.ar(outBus, in * sendLevel);  // Send to reverb with variable level
    }).add;

    // Amp control - Controls amplitude with lag for crossfading
    SynthDef(\ampControl, {
        arg inBus, outBus, amp=1.0, lagTime=0.1;

        var in, sig, ampLag;

        in = In.ar(inBus, 2);  // Stereo input
        ampLag = Lag.kr(amp, lagTime);  // Apply lag to amp parameter
        sig = in * ampLag;

        ReplaceOut.ar(outBus, sig);  // Replace on same bus
    }).add;

    s.sync;
    "✓ SynthDefs compiled".postln;
};

// ===== STEP 2: CREATE PROCESSING CHAIN =====
~createProcessingChain = {
    "Creating audio processing chain...".postln;

    // Create node groups for proper execution order
    sourceGroup = Group.new(s);  // Audio file players
    routingGroup = Group.after(sourceGroup);  // Dry routing + reverb sends
    reverbGroup = Group.after(routingGroup);  // Reverb processors
    masterGroup = Group.after(reverbGroup);  // EQ + Limiters

    "  ✓ Created execution groups".postln;

    // Create internal busses for processing
    processingBusses = Array.fill(numBusses, { Bus.audio(s, 2) });  // Where audio files play
    masterBusses = Array.fill(numBusses, { Bus.audio(s, 2) });  // Dry + wet mix here
    eqBusses = Array.fill(numBusses, { Bus.audio(s, 2) });  // After EQ, before limiter

    // Create reverb busses (one per audio bus)
    reverbSendBusses = Array.fill(numBusses, { Bus.audio(s, 2) });  // Send busses
    reverbProcessedBusses = Array.fill(numBusses, { Bus.audio(s, 2) });  // After reverb+freqshift

    // Initialize arrays for processing synths
    eqSynths = Array.newClear(numBusses);
    limiterSynths = Array.newClear(numBusses);
    reverbSendSynths = Array.newClear(numBusses);
    reverbProcessSynths = Array.newClear(numBusses);
    dryRouteSynths = Array.newClear(numBusses);

    numBusses.do({ |busIdx|
        var finalOut, limiterDef;

        // Determine final output channels and limiter type
        if(routingMode == \quad, {
            // Quad mode: stereo outputs
            finalOut = busIdx * 2;  // Bus 0→ch0+1, Bus 1→ch2+3
            limiterDef = \limiterStereo;
        }, {
            // Stereo mode: mono outputs
            finalOut = busIdx;  // Bus 0→ch0 (left), Bus 1→ch1 (right)
            limiterDef = \limiterMono;
        });

        // 1. Route dry signal directly to master bus (in routing group)
        dryRouteSynths[busIdx] = {
            var in = In.ar(processingBusses[busIdx].index, 2);
            Out.ar(masterBusses[busIdx].index, in);
        }.play(target: routingGroup);

        // 2. Create reverb send for this bus (in routing group)
        reverbSendSynths[busIdx] = Synth(\reverbSend, [
            \inBus, processingBusses[busIdx].index,
            \outBus, reverbSendBusses[busIdx].index,
            \sendLevel, 0.0  // Start with no send
        ], target: routingGroup);

        // 3. Master chain: masterBus → EQ → eqBus → Limiter → output
        eqSynths[busIdx] = Synth(\dynamicEQ, [
            \inBus, masterBusses[busIdx].index,
            \outBus, eqBusses[busIdx].index,  // Output to separate EQ bus
            // Default EQ settings
            \freq1, 100, \q1, 0.45, \gain1, 10.0, \thresh1, -35, \attack1, 0.01, \release1, 0.1,
            \freq2, 1500, \q2, 0.57, \gain2, -2.0, \thresh2, -40, \attack2, 0.005, \release2, 0.15,
            \freq3, 12000, \q3, 0.5, \gain3, 6.0, \thresh3, -45, \attack3, 0.001, \release3, 0.1
        ], target: masterGroup);

        limiterSynths[busIdx] = Synth.after(eqSynths[busIdx], limiterDef, [
            \inBus, eqBusses[busIdx].index,  // Read from EQ bus
            \outBus, finalOut,
            \threshold, -10.0,
            \releaseTime, 0.01
        ]);

        if(routingMode == \quad, {
            ("  ✓ Bus " ++ (busIdx + 1) ++ " (STEREO) → outputs " ++ finalOut ++ "+" ++ (finalOut + 1)).postln;
        }, {
            ("  ✓ Bus " ++ (busIdx + 1) ++ " (MONO) → output " ++ finalOut).postln;
        });
    });

    // Create reverb processing: sends → reverb → freq shift → master busses
    // Each bus has its own reverb path that routes back to its master bus

    numBusses.do({ |busIdx|
        // Process each bus's reverb send (in reverb group)
        reverbProcessSynths[busIdx] = {
            arg shift=0.0;
            var in, reverb, shifted;

            // 1. Read from reverb send bus
            in = In.ar(reverbSendBusses[busIdx].index, 2);

            // 2. Apply reverb
            reverb = FreeVerb2.ar(in[0], in[1], mix: 0.5, room: 0.9, damp: 0.5);

            // 3. Apply frequency shift (will be modulated during transitions)
            shifted = FreqShift.ar(reverb, shift);

            // 4. Output to this bus's master (mixes with dry signal)
            Out.ar(masterBusses[busIdx].index, shifted);
        }.play(target: reverbGroup);
    });

    "  ✓ Reverb chain: Sends → Reverb → FreqShift → Master Busses".postln;

    "✓ Processing chain ready".postln;
};

// ===== STEP 3: LOAD AUDIO FILES =====
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
                        var synth;

                        // Create synth for this floor on this bus
                        // Output to processing bus (in source group)
                        synth = {
                            var numChannels = buffer.numChannels;
                            var rate = \rate.kr(1.0, 0.05);  // Playback rate for doppler (50ms lag)
                            var sig = PlayBuf.ar(
                                numChannels,
                                buffer,
                                BufRateScale.kr(buffer) * rate,  // Modulate rate for doppler
                                loop: 1
                            );
                            var amp = \amp.kr(0.0, 0.1);  // 100ms lag for smooth crossfades

                            // Always output stereo to processing bus
                            if(numChannels == 1, {
                                sig = sig ! 2;  // Duplicate mono to stereo
                            });

                            sig * amp;
                        }.play(outbus: processingBusses[busIdx].index, target: sourceGroup);

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

// ===== STEP 4: SETUP OSC HANDLERS =====
~setupOSC = {
    "Setting up OSC handlers...".postln;

    // OSC Responder for static scenes
    OSCdef(\carpetScene, { |msg|
        var sceneNum, numWindows, isAnimating;

        sceneNum = msg[1].asInteger;
        numWindows = msg[2].asInteger;
        isAnimating = msg[3].asInteger;

        // Reset to dry signal only (no reverb in static scenes)
        numBusses.do({ |busIdx|
            // No reverb sends
            if(reverbSendSynths[busIdx].notNil, {
                reverbSendSynths[busIdx].set(\sendLevel, 0.0);
            });
            // Reset freq shift
            if(reverbProcessSynths[busIdx].notNil, {
                reverbProcessSynths[busIdx].set(\shift, 0.0);
            });
        });

        // Silent all floors on all busses first and reset pitch
        numBusses.do({ |busIdx|
            busPlayers[busIdx].keysValuesDo({ |floorIdx, synth|
                if(synth.notNil, {
                    synth.set(\amp, 0.0, \rate, 1.0);  // Reset pitch when silent
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
                    synth.set(\amp, masterVolume, \rate, 1.0);  // Normal pitch in stable scene
                });
            });
        });
    }, '/carpet/scene');

    // OSC Responder for transitions
    OSCdef(\carpetTransition, { |msg|
        var currentFloor, progress, direction, numWindows;
        var currentFloorIdx, nextFloorIdx, fadeOutGain, fadeInGain;
        var dopplerCurve, dopplerShift, currentRate, nextRate;
        var reverbSend, freqShiftAmount;

        currentFloor = msg[1].asInteger;
        progress = msg[2].asFloat;
        direction = msg[3].asInteger;  // +1 ascending, -1 descending
        numWindows = msg[4].asInteger;

        // Smooth crossfade using sine/cosine curves
        fadeOutGain = cos(progress * 0.5pi);  // 1.0 → 0.0
        fadeInGain = sin(progress * 0.5pi);   // 0.0 → 1.0

        // Calculate reverb send level (peaks in the middle of transition)
        // Goes from silence (0.0) to equal gain (1.0)
        reverbSend = sin(progress * pi);  // Max 1.0 send level (equal to dry)

        // Frequency shift amount (subtle, peaks in middle)
        // ±5 Hz max shift
        freqShiftAmount = sin(progress * pi) * 5.0 * direction;

        // Calculate doppler shift (peaks at 50% progress)
        if(dopplerEnabled, {
            // Sine curve that peaks at 0.5: 0.0 → 1.0 → 0.0
            dopplerCurve = sin(progress * pi);

            // Direction-based shift:
            // Ascending (+1): pitch shifts UP (feels like approaching)
            // Descending (-1): pitch shifts DOWN (feels like receding)
            dopplerShift = dopplerCurve * dopplerIntensity * direction;

            // Current floor: moving away (opposite shift)
            currentRate = 1.0 - dopplerShift;
            // Next floor: moving toward (same shift)
            nextRate = 1.0 + dopplerShift;
        }, {
            currentRate = 1.0;
            nextRate = 1.0;
        });

        // Set reverb send levels and freq shift for all busses
        numBusses.do({ |busIdx|
            if(reverbSendSynths[busIdx].notNil, {
                reverbSendSynths[busIdx].set(\sendLevel, reverbSend);
            });
            if(reverbProcessSynths[busIdx].notNil, {
                reverbProcessSynths[busIdx].set(\shift, freqShiftAmount);
            });
        });

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

            // Fade out current floor with doppler
            if((currentFloorForBus >= 0) && (currentFloorForBus < numFloors), {
                currentSynth = busPlayers[busIdx][currentFloorForBus];
                if(currentSynth.notNil, {
                    currentSynth.set(\amp, fadeOutGain * masterVolume, \rate, currentRate);
                });
            });

            // Fade in next floor with doppler
            if((nextFloorForBus >= 0) && (nextFloorForBus < numFloors), {
                nextSynth = busPlayers[busIdx][nextFloorForBus];
                if(nextSynth.notNil, {
                    nextSynth.set(\amp, fadeInGain * masterVolume, \rate, nextRate);
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

// ===== STEP 5: CLEANUP =====
~setupCleanup = {
    CmdPeriod.doOnce({
        "Stopping audio engine...".postln;

        // Free groups (which frees all synths inside them)
        if(sourceGroup.notNil, { sourceGroup.free });
        if(routingGroup.notNil, { routingGroup.free });
        if(reverbGroup.notNil, { reverbGroup.free });
        if(masterGroup.notNil, { masterGroup.free });

        // Free busses
        processingBusses.do({ |bus| if(bus.notNil, { bus.free }); });
        masterBusses.do({ |bus| if(bus.notNil, { bus.free }); });
        eqBusses.do({ |bus| if(bus.notNil, { bus.free }); });
        reverbSendBusses.do({ |bus| if(bus.notNil, { bus.free }); });
        reverbProcessedBusses.do({ |bus| if(bus.notNil, { bus.free }); });

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
    ~defineSynthDefs.value;
    ~createProcessingChain.value;
    ~loadAudioFiles.value;
    ~setupOSC.value;
    ~setupCleanup.value;

    "\n=== READY ===".postln;
    "Execution Groups:".postln;
    "  SOURCE → ROUTING → REVERB → MASTER".postln;
    "Signal Flow (per bus):".postln;
    "  Floors → [dry→Master, send→Reverb→Master] → DynEQ → Limiter → Out".postln;
    "Transitions: Reverb 0→1→0, FreqShift ±5Hz, Doppler ±15%".postln;
    if(dopplerEnabled, {
        ("Doppler effect: ENABLED (±" ++ (dopplerIntensity * 100) ++ "% pitch shift)").postln;
    }, {
        "Doppler effect: DISABLED".postln;
    });
    "Press Cmd+. to stop\n".postln;
});

) // End of main block
