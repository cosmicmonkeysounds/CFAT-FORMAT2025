/*
 * Elevator Control Panel for Arduino Nano
 *
 * Hardware:
 * - Pin A0: DOWN button (momentary, normally-closed)
 * - Pin A1: UP button (momentary, normally-closed)
 * - Pin D3: GREEN LED (PWM capable)
 * - Pin D5: YELLOW LED (PWM capable)
 * - Pin D6: RED LED (PWM capable)
 *
 * Serial Protocol:
 * - Sends: "up" or "down" when buttons are pressed
 * - Receives:
 *   - "ANIM:STABLE" - Green LED pulses gently (50-100% PWM)
 *   - "ANIM:TRANSITION" - Cycle RED->YELLOW->GREEN
 *   - "ANIM:OFF" - All LEDs off
 *   - "PERIOD:xxx" - Set transition animation period in ms
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
const int PIN_LED_GREEN = 3;   // PWM
const int PIN_LED_YELLOW = 5;  // PWM
const int PIN_LED_RED = 6;     // PWM

// Buttons using MomentarySwitch class
MomentarySwitch buttonDown(PIN_BUTTON_DOWN, false, PULLUP_UP, 50);
MomentarySwitch buttonUp(PIN_BUTTON_UP, false, PULLUP_UP, 50);

// Animation modes
enum AnimMode {
  ANIM_OFF,
  ANIM_STABLE,      // Green pulses
  ANIM_TRANSITION   // Cycle RED->YELLOW->GREEN
};

AnimMode currentMode = ANIM_OFF;
unsigned long transitionPeriod = 500;  // ms per LED in transition
unsigned long lastAnimUpdate = 0;
int transitionState = 0;  // 0=RED, 1=YELLOW, 2=GREEN
float pulsePhase = 0.0;   // 0.0 to 2*PI for stable pulse

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

  // Initialize LEDs to OFF
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_LED_YELLOW, LOW);
  digitalWrite(PIN_LED_GREEN, LOW);

  // Send ready message
  Serial.println("READY");
}

void loop() {
  // Update button states
  buttonDown.update();
  buttonUp.update();

  // Check for button presses
  if (buttonDown.wasPressed()) {
    Serial.println("down");
  }
  if (buttonUp.wasPressed()) {
    Serial.println("up");
  }

  // Process serial commands
  processSerial();

  // Update LED animations
  updateAnimations();
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

  // Split into command name and value
  *colon = '\0';  // Null terminate the command name
  char* cmdName = command;
  char* valueStr = colon + 1;

  // Handle animation commands
  if (strcmp(cmdName, "ANIM") == 0) {
    if (strcmp(valueStr, "STABLE") == 0) {
      currentMode = ANIM_STABLE;
      pulsePhase = 0.0;
    } else if (strcmp(valueStr, "TRANSITION") == 0) {
      currentMode = ANIM_TRANSITION;
      transitionState = 0;
      lastAnimUpdate = millis();
    } else if (strcmp(valueStr, "OFF") == 0) {
      currentMode = ANIM_OFF;
      // Turn all LEDs off
      analogWrite(PIN_LED_RED, 0);
      analogWrite(PIN_LED_YELLOW, 0);
      analogWrite(PIN_LED_GREEN, 0);
    }
  }
  // Handle period setting
  else if (strcmp(cmdName, "PERIOD") == 0) {
    // Parse period value
    unsigned long period = 0;
    for (int i = 0; valueStr[i] != '\0'; i++) {
      if (valueStr[i] >= '0' && valueStr[i] <= '9') {
        period = period * 10 + (valueStr[i] - '0');
      }
    }
    if (period > 0) {
      transitionPeriod = period;
    }
  }
}

void updateAnimations() {
  unsigned long now = millis();

  switch (currentMode) {
    case ANIM_OFF:
      // Nothing to do - LEDs are already off
      break;

    case ANIM_STABLE: {
      // Green LED pulses between 50% and 100% brightness
      // Use a sine wave for smooth pulsing
      pulsePhase += 0.05;  // Adjust speed here (lower = slower)
      if (pulsePhase > 6.283185) {  // 2*PI
        pulsePhase = 0.0;
      }

      // Calculate brightness: 50% + 50% * (sin + 1) / 2
      // sin ranges from -1 to 1, so (sin+1)/2 ranges from 0 to 1
      float sinVal = sin(pulsePhase);
      float brightness = 0.5 + 0.5 * ((sinVal + 1.0) / 2.0);
      int pwmValue = (int)(brightness * 255);

      analogWrite(PIN_LED_GREEN, pwmValue);
      analogWrite(PIN_LED_YELLOW, 0);
      analogWrite(PIN_LED_RED, 0);
      break;
    }

    case ANIM_TRANSITION:
      // Cycle through RED -> YELLOW -> GREEN
      if (now - lastAnimUpdate >= transitionPeriod) {
        lastAnimUpdate = now;
        transitionState = (transitionState + 1) % 3;

        // Turn on current LED, turn off others
        analogWrite(PIN_LED_RED, (transitionState == 0) ? 255 : 0);
        analogWrite(PIN_LED_YELLOW, (transitionState == 1) ? 255 : 0);
        analogWrite(PIN_LED_GREEN, (transitionState == 2) ? 255 : 0);
      }
      break;
  }
}
