VERSION = "1.0.0"
APP_NAME = "YTM Desktop Remote"
APP_DESCRIPTION = "Remote control for Youtube Music Desktop Application"
APP_AUTHOR = "Timothy Lassiter"
DOMAIN_NAME = ""
ORGANIZATION_NAME = ""


def run():
    import locale
    import sys

    from PySide6.QtCore import Qt, Slot, QCommandLineParser, QCommandLineOption
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from app.apiworker import ApiWorker
    from app.keyboardlistener import MediaKeyListener
    from app.tray import SystemTrayApp
    from app.ui import rc_resources

    locale.setlocale(locale.LC_ALL, "")

    QApplication.setOrganizationName(ORGANIZATION_NAME)
    QApplication.setOrganizationDomain(DOMAIN_NAME)
    QApplication.setApplicationName(APP_NAME)
    QApplication.setApplicationVersion(VERSION)

    app = QApplication(sys.argv)

    parser = QCommandLineParser()
    parser.setApplicationDescription(APP_DESCRIPTION)
    parser.addHelpOption()
    parser.addVersionOption()

    server_option = QCommandLineOption(["s", "server"], "Server URL", "server", defaultValue="http://localhost:13091")
    parser.addOption(server_option)
    listener_option = QCommandLineOption(["l", "listen"], "Listen for hotkeys")
    parser.addOption(listener_option)
    parser.process(app)

    server = parser.value(server_option)
    listen = parser.isSet(listener_option)
    
    worker = ApiWorker(server=server)

    listener = None
    if listen:
        @Slot(Qt.Key)
        def handle_key_press(key: Qt.Key):
            if key == Qt.Key.Key_MediaTogglePlayPause:
                worker.toggle_play_pause()
            elif key == Qt.Key.Key_MediaPlay:
                worker.play()
            elif key == Qt.Key.Key_MediaPause:
                worker.pause()
            elif key == Qt.Key.Key_MediaNext:
                worker.next_track()
            elif key == Qt.Key.Key_MediaPrevious:
                worker.prev_track()

        listener = MediaKeyListener()
        listener.key_pressed.connect(handle_key_press, Qt.ConnectionType.QueuedConnection)
        listener.start()
    
    icon = QIcon(":/icons/icon.png")
    tray = SystemTrayApp(icon, worker=worker)
    tray.show()

    ret = app.exec()
    worker.stop()

    if listener:
        listener.stop()

    return sys.exit(ret)
