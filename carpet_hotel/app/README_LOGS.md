# Logging System

## Location
All logs are stored in `/app/logs/`:
- `arduino.log` - Arduino and serial communication
- `core.log` - Core system and integration
- `video.log` - Processing video system
- `sound.log` - SuperCollider audio system

## Behavior
- **On startup**: All log files are cleared automatically
- **During runtime**: All events are logged with timestamps
- **On shutdown**: Logs are preserved for debugging

## Viewing Logs
```bash
# View real-time logs
tail -f app/logs/arduino.log
tail -f app/logs/core.log

# View all logs at once
tail -f app/logs/*.log

# Search logs
grep "ERROR" app/logs/*.log
grep "Animation" app/logs/arduino.log
```

## Format
```
[2025-11-11 21:04:33.289] [Component] Message
```
