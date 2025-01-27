import sys
import gi
import gatt
import configparser

gi.require_version("Gtk", "3.0")

from pathlib import Path
from gi.repository import Gtk, Gio, Gdk
from .window import SigloWindow
from .bluetooth import InfiniTimeManager


class Application(Gtk.Application):
    def __init__(self):
        self.manager = None
        config = self.configuration_setup()
        self.mode = config["settings"]["mode"]
        self.deploy_type = config["settings"]["deploy_type"]
        super().__init__(
            application_id="org.gnome.siglo", flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def configuration_setup(self):
        config = configparser.ConfigParser()
        home = str(Path.home())
        config_dir = home + "/.config/siglo"
        if not Path(config_dir).is_dir():
            Path.mkdir(Path(config_dir))
        config_file = config_dir + "/siglo.ini"
        if not self.config_file_is_valid(config, config_file):
            config["settings"] = {"mode": "singleton", "deploy_type": "quick"}
            with open(config_file, "w") as f:
                config.write(f)
        config.read(config_file)
        return config

    def config_file_is_valid(self, config, config_file):
        keys = ("mode", "deploy_type")
        if not Path(config_file).is_file():
            return False
        else:
            config.read(config_file)
            for key in keys:
                if not key in config["settings"]:
                    return False
            return True

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = SigloWindow(
                application=self, mode=self.mode, deploy_type=self.deploy_type
            )
        win.present()
        self.manager = InfiniTimeManager(self.mode)
        info_prefix = "[INFO ] Done Scanning"
        try:
            self.manager.scan_for_infinitime()
        except gatt.errors.NotReady:
            info_prefix = "[WARN ] Bluetooth is disabled"
        if self.mode == "singleton":
            win.done_scanning_singleton(self.manager, info_prefix)
        if self.mode == "multi":
            win.done_scanning_multi(self.manager, info_prefix)

    def do_window_removed(self, window):
        self.manager.stop()
        self.quit()


def main(version):
    def gtk_style():
        css = b"""
#multi_mac_label { font-size: 33px; }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    gtk_style()
    app = Application()
    return app.run(sys.argv)
