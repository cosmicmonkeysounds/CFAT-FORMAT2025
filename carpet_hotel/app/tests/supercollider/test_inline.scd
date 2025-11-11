/*
Test SuperCollider with inline code (no functions)
to isolate the server boot issue
*/

"=== INLINE TEST ===".postln;

// Configure server
s.options.sampleRate = 48000;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 0;

"Booting server...".postln;

s.waitForBoot({
    "Audio server ready!".postln;
    ("Sample rate: " ++ s.sampleRate).postln;

    // Keep sclang alive
    SystemClock.sched(1.0, { 1.0 });

    "Loading audio files...".postln;

    // Use a simple Routine instead of function call
    Routine({
        var audioPath = (thisProcess.nowExecutingPath.dirname +/+ "../../data/").standardizePath;
        ("Path: " ++ audioPath).postln;

        // Try to load just ONE file
        var path = audioPath ++ "carpet_1.wav";
        var file = PathName(path);

        if(file.isFile, {
            var buffer = Buffer.read(s, path);
            ("✓ Loaded: " ++ file.fileName).postln;
            s.sync;
        }, {
            "✗ File not found".postln;
        });

        "=== READY ===".postln;
    }).play;
});
