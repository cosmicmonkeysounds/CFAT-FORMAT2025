/*
Audio device diagnostic - shows what SC sees
*/

"=== AUDIO DIAGNOSTIC ===".postln;

// Show all available devices
"Available audio devices:".postln;
ServerOptions.devices.do({ |device, i|
    ("  " ++ i ++ ": " ++ device).postln;
});

// Show what the server will try to use
"\nServer options:".postln;
("  inDevice: " ++ s.options.inDevice).postln;
("  outDevice: " ++ s.options.outDevice).postln;
("  device: " ++ s.options.device).postln;
("  numInputBusChannels: " ++ s.options.numInputBusChannels).postln;
("  numOutputBusChannels: " ++ s.options.numOutputBusChannels).postln;
("  sampleRate: " ++ s.options.sampleRate).postln;

"\nTrying to boot with NO input channels...".postln;
s.options.numInputBusChannels = 0;
s.options.numOutputBusChannels = 2;

s.waitForBoot({
    "\n✓✓✓ SUCCESS ✓✓✓".postln;
    ("Server device: " ++ s.options.device).postln;
    ("Actual sample rate: " ++ s.sampleRate).postln;
    SystemClock.sched(1.0, { 1.0 });
});
