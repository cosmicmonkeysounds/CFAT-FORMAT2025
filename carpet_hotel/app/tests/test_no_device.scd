/*
Test without explicit device - use system default
*/

(
// ===== STARTUP MESSAGE =====
"=== TEST: System Default Device ===".postln;

// Configure server - NO explicit device
s.options.sampleRate = 44100;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 0;

"✓ Server configured (using system default device)".postln;

// Boot server and wait for it
s.waitForBoot({
    "✓ Audio server ready!".postln;
    ("Sample rate: " ++ s.sampleRate ++ " Hz").postln;

    // Keep sclang alive
    SystemClock.sched(1.0, { 1.0 });

    "\n=== SUCCESS ===".postln;
});

) // End
