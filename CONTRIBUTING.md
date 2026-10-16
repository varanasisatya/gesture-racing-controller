# Contributing

Thanks for helping improve Gesture / Racing.

## Before opening a pull request

1. Keep changes focused and describe the user-visible behavior they affect.
2. Do not include camera footage, local `settings.json`, environment folders, build outputs, or downloaded game files.
3. Run the relevant checks:

   ```powershell
   cd gesture_racing_controller
   python -m unittest -v test_system.py
   cd ..\website
   npm ci
   npm run lint
   npm run build
   ```

4. For camera, gesture, or input changes, include manual verification details: Windows version, camera type, gesture tried, selected game, and whether all held keys release on stop.
5. Do not claim a game works unless its current key bindings were verified in that game.

## Pull request description

Explain the problem, the change, how it was checked, and any known limitations. Include screenshots for visual changes only when they contain no face, camera frame, personal information, or private browser content unless that data is intentionally approved for publication.
