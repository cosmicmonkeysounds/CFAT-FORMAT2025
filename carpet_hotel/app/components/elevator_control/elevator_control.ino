/*
 * Elevator Control Panel for Arduino Nano
 *
 * Hardware:
 * - Pin A0: DOWN button (momentary, normally-closed)
 * - Pin A1: UP button (momentary, normally-closed)
 * - Pin D6: RED LED (PWM capable - ~)
 * - Pin D5: YELLOW LED (PWM capable - ~)
 * - Pin D3: GREEN LED (PWM capable - ~)
 *
 * Serial Protocol:
 * - Sends: "UP" or "DOWN" when buttons are pressed
 * - Receives: "RED:255" / "RED:0", "YELLOW:128", "GREEN:255", etc.
 *   Values are 0-255 for PWM brightness control
 *
 * Note: LED animations are controlled by Python, not by Arduino
 * IMPORTANT: Only D3, D5, D6, D9, D10, D11 support PWM on Arduino Nano!
 */

#include <string.h>

// ============================================================================
// MOMENTARY SWITCH CLASS
// ============================================================================
/*
 * Usage examples:
 *
 * // Normally-open with pullup (default debounce 50ms)
 * MomentarySwitch btn1(2, true, PULLUP_UP);
 *
 * // Normally-open with pullup and custom debounce
 * MomentarySwitch btn2(3, true, PULLUP_UP, 100);
 *
 * // Normally-open without pullup (requires external pulldown)
 * MomentarySwitch btn3(4, true, PULLUP_NONE);
 *
 * // Normally-closed with pullup
 * MomentarySwitch btn4(5, false, PULLUP_UP);
 *
 * // In setup():
 * btn1.begin();
 *
 * // In loop():
 * btn1.update();
 * if (btn1.wasPressed()) {
 *   // Handle press event (fires once per press)
 * }
 * if (btn1.isPressed()) {
 *   // Check if currently held down
 * }
 */

enum PullupMode {
  PULLUP_NONE = 0,
  PULLUP_UP = 1
};

enum MomentaryNormal {
  OPEN,
  CLOSED
};

class MomentarySwitch {
public:
  // Constructor
  MomentarySwitch(int pin, bool normallyOpen = true, PullupMode pullup = PULLUP_NONE, unsigned long debounceMs = 50)
    : pin(pin),
      normallyOpen(normallyOpen),
      pullupMode(pullup),
      debounceDelay(debounceMs),
      lastState(HIGH),
      currentState(HIGH),
      lastDebounceTime(0),
      pressDetected(false) {
  }

  // Initialize the pin
  void begin() {
    if (pullupMode == PULLUP_UP) {
      pinMode(pin, INPUT_PULLUP);
      // For normally-open with pullup, unpressed = HIGH, pressed = LOW
      // For normally-closed with pullup, unpressed = LOW, pressed = HIGH
    } else {
      pinMode(pin, INPUT);
      // For normally-open without pullup, unpressed = LOW, pressed = HIGH
      // For normally-closed without pullup, unpressed = HIGH, pressed = LOW
    }
    currentState = digitalRead(pin);
    lastState = currentState;
  }

  // Update the switch state (call this in loop())
  void update() {
    bool reading = digitalRead(pin);

    // Reset debounce timer if state changed
    if (reading != lastState) {
      lastDebounceTime = millis();
    }

    // If enough time has passed, accept the new state
    if ((millis() - lastDebounceTime) > debounceDelay) {
      // If state changed from last accepted state
      if (reading != currentState) {
        bool wasPressed = isPressed();  // Check old state
        currentState = reading;
        bool nowPressed = isPressed();  // Check new state

        // Detect press event (transition from not-pressed to pressed)
        if (!wasPressed && nowPressed) {
          pressDetected = true;
        }
      }
    }

    lastState = reading;
  }

  // Returns true if switch is currently pressed
  bool isPressed() const {
    if (normallyOpen) {
      // Normally open: pressed when LOW (with pullup) or HIGH (without pullup)
      if (pullupMode == PULLUP_UP) {
        return currentState == LOW;
      } else {
        return currentState == HIGH;
      }
    } else {
      // Normally closed: pressed when HIGH (with pullup) or LOW (without pullup)
      if (pullupMode == PULLUP_UP) {
        return currentState == HIGH;
      } else {
        return currentState == LOW;
      }
    }
  }

  // Returns true once per press (call after update())
  bool wasPressed() {
    if (pressDetected) {
      pressDetected = false;
      return true;
    }
    return false;
  }

private:
  int pin;
  bool normallyOpen;
  PullupMode pullupMode;
  unsigned long debounceDelay;
  bool lastState;
  bool currentState;
  unsigned long lastDebounceTime;
  bool pressDetected;
};

// Pin definitions
const int PIN_BUTTON_DOWN = A0;
const int PIN_BUTTON_UP = A1;
const int PIN_LED_RED = 6;      // D6 - PWM capable (~)
const int PIN_LED_YELLOW = 5;   // D5 - PWM capable (~)
const int PIN_LED_GREEN = 3;    // D3 - PWM capable (~)

// Buttons using MomentarySwitch class (normally-closed switches)
MomentarySwitch buttonDown(PIN_BUTTON_DOWN, false, PULLUP_UP, 50);
MomentarySwitch buttonUp(PIN_BUTTON_UP, false, PULLUP_UP, 50);

// No animation logic - Python controls LEDs directly

// Serial buffer - fixed size, no dynamic allocation
const int CMD_BUFFER_SIZE = 32;
char serialBuffer[CMD_BUFFER_SIZE];
int serialBufferIndex = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect (needed for native USB)
  }

  // Initialize buttons
  buttonDown.begin();
  buttonUp.begin();

  // Configure LED pins as outputs
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);

  // Initialize LEDs to OFF (PWM value 0)
  analogWrite(PIN_LED_RED, 0);
  analogWrite(PIN_LED_YELLOW, 0);
  analogWrite(PIN_LED_GREEN, 0);

  // Send ready message
  Serial.println("READY");
}

void loop() {
  // Update button states
  buttonDown.update();
  buttonUp.update();

  // Check for button presses
  if (buttonDown.wasPressed()) {
    Serial.println("DOWN");
  }
  if (buttonUp.wasPressed()) {
    Serial.println("UP");
  }

  // Process serial commands
  processSerial();
}

void processSerial() {
  while (Serial.available() > 0) {
    char inChar = Serial.read();

    if (inChar == '\n' || inChar == '\r') {
      if (serialBufferIndex > 0) {
        serialBuffer[serialBufferIndex] = '\0';  // Null terminate
        parseCommand(serialBuffer);
        serialBufferIndex = 0;  // Reset buffer
      }
    } else if (serialBufferIndex < CMD_BUFFER_SIZE - 1) {
      // Add to buffer if there's room (leave space for null terminator)
      serialBuffer[serialBufferIndex++] = inChar;
    }
    // If buffer is full, ignore additional characters until newline
  }
}

void parseCommand(char* command) {
  // Convert to uppercase in place
  for (int i = 0; command[i] != '\0'; i++) {
    if (command[i] >= 'a' && command[i] <= 'z') {
      command[i] = command[i] - 'a' + 'A';
    }
  }

  // Find colon separator
  char* colon = strchr(command, ':');
  if (colon == NULL) {
    return;  // Invalid command format
  }

  // Split into LED name and value
  *colon = '\0';  // Null terminate the LED name
  char* ledName = command;
  char* valueStr = colon + 1;

  // Parse PWM value (0-255) or legacy ON/OFF
  int pwmValue = 0;
  if (strcmp(valueStr, "ON") == 0 || strcmp(valueStr, "1") == 0) {
    pwmValue = 255;  // Full brightness
  } else if (strcmp(valueStr, "OFF") == 0 || strcmp(valueStr, "0") == 0) {
    pwmValue = 0;    // OFF
  } else {
    // Parse as integer (0-255)
    pwmValue = atoi(valueStr);
    pwmValue = constrain(pwmValue, 0, 255);
  }

  // Set LED using PWM
  if (strcmp(ledName, "RED") == 0) {
    analogWrite(PIN_LED_RED, pwmValue);
  } else if (strcmp(ledName, "YELLOW") == 0) {
    analogWrite(PIN_LED_YELLOW, pwmValue);
  } else if (strcmp(ledName, "GREEN") == 0) {
    analogWrite(PIN_LED_GREEN, pwmValue);
  }
}
