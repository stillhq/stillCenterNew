import os

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import constants


@Gtk.Template(filename=os.path.join(constants.UI_DIR, "AppGridView.ui"))
class AppGridView(Gtk.GridView):
    __gtype_name__ = "AppGridView"
    stillCenter = None
    factory: Gtk.BuilderListItemFactory = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.connect("activate", self.activate)

    def set_store(self, stillCenter, model: Gtk.ListStore):
        self.stillCenter = stillCenter
        self.set_model(Gtk.NoSelection.new(model))

    def activate(self, _app_grid_view, index):
        self.stillCenter.app_page.show_app(self.get_model().get_item(index).app_id)
