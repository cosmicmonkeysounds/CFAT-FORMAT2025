# CARPET HOTEL - Transition Configuration Guide

## Overview
The transition_config.txt file lets you customize all the visual effects that occur during floor transitions (the "elevator" animation).

This file is located in the same folder as carpet_hotel.pde (NOT in the data/ folder).

## How to Use
1. Edit transition_config.txt (in the same folder as carpet_hotel.pde)
2. Save the file
3. Press 'R' while the program is running to reload the configuration
4. Press 'D' to see current config values in the debug panel

## Configuration Parameters

### ANIMATION_SPEED (default: 0.1)
- Controls how fast the elevator scrolls between floors
- Higher = faster transitions
- Range: 0.01 (very slow) to 1.0 (instant)
- Example: 0.05 = half speed, 0.2 = double speed

### CHROMATIC_INTENSITY (default: 8.0)
- RGB channel separation effect (retro/glitch look)
- Higher = more dramatic color separation
- Range: 0.0 (off) to 20.0 (extreme)
- Sweet spot: 5.0 to 15.0

### MOTION_BLUR_SAMPLES (default: 3)
- Number of blur copies drawn
- More samples = smoother blur but slower performance
- Range: 1 (minimal) to 10 (heavy)
- Note: Values above 5 may impact performance

### MOTION_BLUR_INTENSITY (default: 15.0)
- Distance of blur in opposite direction of movement
- Higher = more pronounced speed lines
- Range: 0.0 (off) to 50.0 (extreme)
- Sweet spot: 10.0 to 25.0

### BLOOM_INTENSITY (default: 80.0)
- Bright glow overlay effect
- Higher = brighter, dreamier look
- Range: 0.0 (off) to 150.0 (very bright)
- Note: Values above 100 may wash out the video

### MAX_EFFECT_INTENSITY (default: 0.8)
- Peak intensity at 50% of transition
- All effects scale to this maximum
- Range: 0.0 (no effects) to 1.0 (full intensity)
- 0.5 = subtle, 0.8 = moderate, 1.0 = extreme

### EFFECT_THRESHOLD (default: 0.05)
- When effects start appearing
- Lower = effects appear earlier in transition
- Range: 0.0 (immediate) to 0.2 (delayed)

### CHROMATIC_R/G/B_ALPHA (default: 200)
- Transparency of RGB channels in chromatic aberration
- Lower = more transparent, ethereal
- Range: 0 (invisible) to 255 (opaque)
- Try: All at 150 for ghost-like effect

### MOTION_BLUR_ALPHA_DIVISOR (default: 2)
- Controls fade of blur samples
- Higher = more transparent blur (lighter)
- Lower = more opaque blur (heavier)
- Range: 1 (opaque) to 5 (very faint)

## Preset Suggestions

### Subtle / Professional
animation_speed=0.08
chromatic_intensity=4.0
motion_blur_samples=2
motion_blur_intensity=10.0
bloom_intensity=40.0
max_effect_intensity=0.5

### Extreme / Psychedelic
animation_speed=0.15
chromatic_intensity=15.0
motion_blur_samples=5
motion_blur_intensity=30.0
bloom_intensity=120.0
max_effect_intensity=1.0

### Fast / Minimal
animation_speed=0.25
chromatic_intensity=3.0
motion_blur_samples=1
motion_blur_intensity=8.0
bloom_intensity=30.0
max_effect_intensity=0.4

### Slow / Dreamy
animation_speed=0.05
chromatic_intensity=6.0
motion_blur_samples=4
motion_blur_intensity=12.0
bloom_intensity=100.0
max_effect_intensity=0.7

## Troubleshooting

**Effects are too subtle**
- Increase max_effect_intensity to 0.9 or 1.0
- Increase individual effect intensities
- Lower effect_threshold to 0.02

**Effects are overwhelming**
- Decrease max_effect_intensity to 0.5 or lower
- Reduce individual effect intensities by 30-50%
- Increase effect_threshold to 0.1

**Performance issues / low FPS**
- Reduce motion_blur_samples to 2 or 1
- Lower animation_speed (counterintuitively, faster = more work)
- Reduce bloom_intensity

**Transitions too fast/slow**
- Adjust animation_speed
- Note: Distance affects duration (scene 1→8 takes longer than 1→2)

## Tips

1. Make small adjustments (10-20% at a time)
2. Test with both short (1 floor) and long (5+ floors) transitions
3. The effect intensity curve peaks at 50% - effects fade in and out
4. Watch the debug panel (press D) to see live config values
5. Keep backups of configs you like!

## Effect Timing
- 0% progress: No effects (effect_threshold)
- 25% progress: Effects ramping up
- 50% progress: PEAK intensity (max_effect_intensity)
- 75% progress: Effects fading out
- 100% progress: No effects
