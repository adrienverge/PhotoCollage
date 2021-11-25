import gi
import gettext
from photocollage import APP_NAME

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

gettext.textdomain(APP_NAME)
_ = gettext.gettext

PROCESSED_CORPUS_FILE = "processed_corpus_file"
CORPUS_DIR = "corpus_dir"
CONFIG_FILE = "config_file"
OUTPUT_DIR = "output_dir"
SCHOOL_NAME = "school_name"
MAX_COUNT = "max_count"


class ConfigSelectorDialog(Gtk.Dialog):

    def __init__(self, parent):
        super().__init__(
            title="Settings", parent=parent, flags=0,
            buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK,
                     Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        super().resize(600, 100)
        self.config_parameters = {SCHOOL_NAME: "Vargas Elementary", MAX_COUNT: 12}
        self.etr_outw = None
        self.set_border_width(10)
        self.selected_border_color = parent.opts.border_c

        box = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add(vbox)

        self.btn_select_db = Gtk.Button(label=_("Select Database File..."))
        self.db_entry = Gtk.Entry()
        self.db_entry.set_activates_default(True)
        self.db_entry.set_text("/Users/ashah/GoogleDrive/Rilee4thGrade/VargasElementary.db")
        self.config_parameters[CONFIG_FILE] = self.db_entry.get_text()

        self.btn_select_corpus = Gtk.Button(label=_("Select Processed Corpus..."))
        self.corpus_entry = Gtk.Entry()
        self.corpus_entry.set_text("/Users/ashah/GoogleDrive/Rilee4thGrade/processedCorpus_rilee_recognizer.out")
        self.config_parameters[PROCESSED_CORPUS_FILE] = self.corpus_entry.get_text()

        import os.path
        self.config_parameters[CORPUS_DIR] = os.path.dirname(self.corpus_entry.get_text())

        self.btn_select_out_dir = Gtk.Button(label=_("Select Output Dir..."))
        self.out_dir_entry = Gtk.Entry()
        self.out_dir_entry.set_text("/Users/ashah/Downloads/VargasElementary")
        self.config_parameters[OUTPUT_DIR] = self.out_dir_entry.get_text()

        # Position the UI elements
        grid = Gtk.Grid()
        grid.add(self.btn_select_db)
        grid.attach(child=self.db_entry, left=1, top=0, width=8, height=1)
        grid.attach_next_to(self.btn_select_corpus, self.btn_select_db, Gtk.PositionType.BOTTOM, 1, 1)
        grid.attach_next_to(self.corpus_entry, self.btn_select_corpus, Gtk.PositionType.RIGHT, 2, 1)
        grid.attach_next_to(self.btn_select_out_dir, self.btn_select_corpus, Gtk.PositionType.BOTTOM, 1, 1)
        grid.attach_next_to(self.out_dir_entry, self.btn_select_out_dir, Gtk.PositionType.RIGHT, 4, 1)

        self.btn_select_db.connect("clicked", self.setup_config_file_selector)
        self.btn_select_corpus.connect("clicked", self.setup_processed_corpus_file_selector)
        self.btn_select_out_dir.connect("clicked", self.setup_output_folder_selector)

        vbox.add(grid)
        self.show_all()

    # TODO: This should be easy to generalize but for some reason if we try to do that, it gets clicked automatically.
    def setup_config_file_selector(self, button):
        # Add the actions to the buttons
        chooser = Gtk.FileChooserDialog(title="Select Config File",
                                        action=Gtk.FileChooserAction.OPEN,
                                        buttons=(Gtk.STOCK_CANCEL,
                                                 Gtk.ResponseType.CANCEL,
                                                 Gtk.STOCK_OPEN,
                                                 Gtk.ResponseType.OK))
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            print(button.get_label() + " :Config file selected...", chooser.get_filename())
            self.db_entry.set_text(chooser.get_filename())
            self.config_parameters[CONFIG_FILE] = chooser.get_filename()
            chooser.destroy()
        else:
            chooser.destroy()

    def setup_corpus_dir_selector(self, button):
        # Add the actions to the buttons
        chooser = Gtk.FileChooserDialog(title="Select Corpus Directory",
                                        action=Gtk.FileChooserAction.SELECT_FOLDER,
                                        buttons=(Gtk.STOCK_CANCEL,
                                                 Gtk.ResponseType.CANCEL,
                                                 Gtk.STOCK_OPEN,
                                                 Gtk.ResponseType.OK))
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            print("Corpus dir selected...", chooser.get_filename())
            self.corpus_dir_entry.set_text(chooser.get_filename())
            self.config_parameters[CORPUS_DIR] = chooser.get_filename()
            chooser.destroy()
        else:
            chooser.destroy()

    def setup_processed_corpus_file_selector(self, button):
        # Add the actions to the buttons
        chooser = Gtk.FileChooserDialog(title="Select Processed Corpus File",
                                        action=Gtk.FileChooserAction.OPEN,
                                        buttons=(Gtk.STOCK_CANCEL,
                                                 Gtk.ResponseType.CANCEL,
                                                 Gtk.STOCK_OPEN,
                                                 Gtk.ResponseType.OK))
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            print("Processed Corpus file selected...", chooser.get_filename())
            self.config_parameters[PROCESSED_CORPUS_FILE] = chooser.get_filename()
            self.corpus_entry.set_text(chooser.get_filename())
            chooser.destroy()
        else:
            chooser.destroy()

    def setup_output_folder_selector(self, button):
        # Add the actions to the buttons
        chooser = Gtk.FileChooserDialog(title="Select Output Dir",
                                        action=Gtk.FileChooserAction.SELECT_FOLDER,
                                        buttons=(Gtk.STOCK_CANCEL,
                                                 Gtk.ResponseType.CANCEL,
                                                 Gtk.STOCK_OPEN,
                                                 Gtk.ResponseType.OK))
        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            print("Output dir selected...", chooser.get_filename())
            self.config_parameters[OUTPUT_DIR] = chooser.get_filename()
            chooser.destroy()
        else:
            chooser.destroy()
