import sadb.__main__ as sadb

import CategoryPage
import constants
import threading
import os
import gi
import sam.quick

from SamInterface import sam_interface
from LoadingPage import LoadingPage

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib
from CategoryButtonBig import CategoryButtonBig
import AppStore, AppPage, FlowApps, AppGridView, AppListView, CategoryPage


class StillCenter(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.stillhq.stillCenter")

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(constants.UI_DIR, "stillCenter.ui"))

        # Get objects from the builder
        self.window = self.builder.get_object("window")
        self.sidebar = self.builder.get_object("main_sidebar")
        self.sidebar_split = self.builder.get_object("sidebar_split_view")
        self.main_stack = self.builder.get_object("main_stack")
        self.main_view = self.builder.get_object("main_view")
        self.categories_flowbox = self.builder.get_object("categories_flowbox")
        self.search_stack = self.builder.get_object("search_stack")
        self.search_app_list = self.builder.get_object("search_app_list")
        self.search_entry = self.builder.get_object("search_entry")
        self.search_placeholder = self.builder.get_object("search_placeholder")
        self.update_box = self.builder.get_object("update_box")
        self.update_all_button = self.builder.get_object("update_all_button")
        self.available_updates = self.builder.get_object("available_updates")

        # Setting up the sidebar
        self.sidebar_index = []
        main_stack_pages = self.main_stack.get_pages()
        for i in range(main_stack_pages.get_n_items()):
            stack_page = main_stack_pages.get_item(i)
            sidebar_row = Gtk.ListBoxRow()
            label = Gtk.Label(label=stack_page.get_title(), xalign=0)
            sidebar_row.set_child(label)
            self.sidebar_index.append(stack_page.get_name())
            self.sidebar.append(sidebar_row)
        self.sidebar.connect("row-selected", self.sidebar_selected)

        # Set IDs of Flowboxes for Featured Apps
        FlowApps.set_stillcenter(self)

        # Populating Categories
        self.categories_flowbox.append(
            CategoryButtonBig(self, "Audio", "Audio", "audio-x-generic-symbolic")
        )
        self.categories_flowbox.append(
            CategoryButtonBig(self, "Development", "Development", "applications-engineering-symbolic")
        )
        self.categories_flowbox.append(
            CategoryButtonBig(self, "Education", "Education", "accessories-dictionary-symbolic")
        )
        self.categories_flowbox.append(
            CategoryButtonBig(self, "Game", "Games", "applications-games-symbolic")
        )
        self.categories_flowbox.append(
            CategoryButtonBig(self, "Graphics", "Graphics", "applications-graphics-symbolic")
        )
        self.categories_flowbox.append(
            CategoryButtonBig(self, "Network", "Network", "preferences-system-network-symbolic")
        )
        self.categories_flowbox.append(
            CategoryButtonBig(self, "Office", "Office", "x-office-document-symbolic")
        )
        self.categories_flowbox.append(
            CategoryButtonBig(self, "Utility", "Utilities", "applications-utilities-symbolic")
        )
        self.categories_flowbox.append(
            CategoryButtonBig(self, "Video", "Video", "applications-multimedia-symbolic")
        )
        self.categories_flowbox.append(
            CategoryButtonBig(self, "System", "System", "preferences-other-symbolic")
        )

        # Setup search
        self.search_entry.connect("changed", self.search_changed)

        # Loading base pages
        self.app_page = AppPage.AppPage(self)
        self.category_page = CategoryPage.CategoryPage(self)

        # Set update button
        sam_interface.connect_to_signal("queue_changed", self.run_update_installed_page)
        self.update_all_button.connect("clicked", self.update_all)

        # Loading screen
        self.loading_screen = LoadingPage(self)

        self.loading_screen.push()
        thread = threading.Thread(target=self.load_apps)
        thread.start()

    def update_all(self, button):
        thread = threading.Thread(target=lambda: sam_interface.update_all(False))
        thread.start()

    def run_update_installed_page(self):
        thread = threading.Thread(target=self.update_installed_page)
        thread.start()

    # Update installed page
    def update_installed_page(self):
        try:
            sadb.update_installed()
        except SystemExit:
            pass

        AppStore.refresh_installed_store()

        GLib.idle_add(self.update_installed_gui)

    def update_installed_gui(self):
        # Set models of ListViews
        self.builder.get_object("installed").set_store(self, AppStore.INSTALLED_STORE["no_update"])
        self.builder.get_object("available_updates").set_store(self, AppStore.INSTALLED_STORE["update"])

        if AppStore.INSTALLED_STORE["update"].get_n_items() == 0:
            self.available_updates.set_visible(False)
            self.update_box.set_visible(False)
        else:
            self.available_updates.set_visible(True)
            self.update_box.set_visible(True)

        queue = sam.quick.get_queue_dicts()
        if not queue:
            queue = {}  # Prevent function from breaking if queue is empty
        if len(queue) != 0:
            self.update_all_button.set_sensitive(False)
        else:
            self.update_all_button.set_sensitive(True)

    def load_apps(self):
        try:
            sadb.update_db()
        except SystemExit:  # needed because of the click command
            pass

        self.update_installed_page()

        GLib.idle_add(lambda: self.populate_apps())
        GLib.idle_add(self.loading_screen.pop)

    def populate_apps(self):
        self.search_placeholder.set_title(f"Search from {len(AppStore.STORE["all"])} Apps")
        FlowApps.populate_apps()

    def sidebar_selected(self, _listbox, row):
        self.main_stack.set_visible_child_name(self.sidebar_index[row.get_index()])
        if self.sidebar_split.get_collapsed() and not self.sidebar_split.get_show_content():
            self.sidebar_split.set_show_content(True)

    def search_changed(self, entry):
        if len(entry.get_text().strip()) > 0:
            store = AppStore.search_algorithm(entry.get_text())

            if store.get_n_items() == 0:
                self.search_stack.set_visible_child_name("no_results")
                return

            self.search_app_list.set_store(self, store)
            self.search_stack.set_visible_child_name("results")
        else:
            self.search_stack.set_visible_child_name("search_placeholder")

    def do_activate(self):
        self.window.set_application(self)
        self.window.present()
