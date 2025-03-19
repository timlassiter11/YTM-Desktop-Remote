from PySide6.QtCore import QObject, Signal, Qt
from pynput import keyboard

class MediaKeyListener(QObject):
    key_pressed = Signal(Qt.Key)

    def __init__(self):
        super().__init__()
        self._listener = keyboard.Listener(on_press=self.on_press)

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()
        self._listener.join()
    
    def on_press(self, key: keyboard.Key):
        if key == keyboard.Key.media_play_pause:
            self.key_pressed.emit(Qt.Key.Key_MediaTogglePlayPause)
        elif key == keyboard.Key.media_next:
            self.key_pressed.emit(Qt.Key.Key_MediaNext)
        elif key == keyboard.Key.media_previous:
            self.key_pressed.emit(Qt.Key.Key_MediaPrevious)