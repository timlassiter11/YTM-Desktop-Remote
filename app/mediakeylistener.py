from PySide6.QtCore import QObject, Signal, Qt
from pynput import keyboard

class MediaKeyListener(QObject):
    keyPressed = Signal(Qt.Key)

    def __init__(self):
        super().__init__()
        self._listener = keyboard.Listener(on_press=self._on_press)

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()
        self._listener.join()
    
    def _on_press(self, key: keyboard.Key):
        if key == keyboard.Key.media_play_pause:
            self.keyPressed.emit(Qt.Key.Key_MediaTogglePlayPause)
        elif key == keyboard.Key.media_next:
            self.keyPressed.emit(Qt.Key.Key_MediaNext)
        elif key == keyboard.Key.media_previous:
            self.keyPressed.emit(Qt.Key.Key_MediaPrevious)