/*
Minimal SuperCollider Boot Test
Just boots the server and prints status.
*/

"=== MINIMAL BOOT TEST ===".postln;
"Script is executing!".postln;

s.options.sampleRate = 48000;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 0;

"Booting server...".postln;

s.waitForBoot({
    "✓ Server booted!".postln;
    ("Sample rate: " ++ s.sampleRate).postln;
    "Audio server ready!".postln;  // This is what carpet_hotel_scd.py looks for

    // Keep alive
    SystemClock.sched(1.0, { 1.0 });
});
