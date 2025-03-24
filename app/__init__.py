VERSION = "1.0.0"
APP_NAME = "YTM Desktop Remote"
APP_DESCRIPTION = "Remote control for Youtube Music Desktop Application"
APP_AUTHOR = "Timothy Lassiter"
DOMAIN_NAME = ""
ORGANIZATION_NAME = ""


def run():
    import locale

    from PySide6.QtWidgets import QApplication

    locale.setlocale(locale.LC_ALL, "")

    QApplication.setOrganizationName(ORGANIZATION_NAME)
    QApplication.setOrganizationDomain(DOMAIN_NAME)
    QApplication.setApplicationName(APP_NAME)
    QApplication.setApplicationVersion(VERSION)

    app = Application()
    return app.exec()


from .application import Application
