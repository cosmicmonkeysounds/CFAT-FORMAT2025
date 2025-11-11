/*
Simple SuperCollider Boot Test
Just boots the server and prints status.
*/

"=== SC BOOT TEST ===".postln;
"Starting test...".postln;

// Test 1: Print args
"Command line arguments:".postln;
thisProcess.argv.do({ |arg, i|
    ("  argv[" ++ i ++ "] = " ++ arg).postln;
});

// Test 2: Configure and boot server
"Configuring server...".postln;
s.options.sampleRate = 48000;
s.options.numOutputBusChannels = 2;
s.options.numInputBusChannels = 0;

s.waitForBoot({
    "✓ Server booted successfully!".postln;
    ("Sample rate: " ++ s.sampleRate).postln;
    ("Output channels: " ++ s.options.numOutputBusChannels).postln;

    // Test 3: Send OSC message
    {
        var client = NetAddr("127.0.0.1", 12001);
        client.sendMsg("/test", "hello");
        "✓ OSC message sent".postln;
    }.defer(0.5);

    // Keep alive for 5 seconds then exit
    {
        "Test complete, exiting...".postln;
        0.exit;
    }.defer(5);
});
