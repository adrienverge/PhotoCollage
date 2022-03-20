import gi
import gettext
from photocollage import APP_NAME

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

gettext.textdomain(APP_NAME)
_ = gettext.gettext


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(
            _("Settings"), parent, 0,
            (Gtk.STOCK_OK, Gtk.ResponseType.OK,
             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.set_border_width(10)

        self.selected_border_color = parent.left_opts.border_c

        box = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add(vbox)

        label = Gtk.Label(xalign=0)
        label.set_markup("<big><b>%s</b></big>" % _("Output image size"))
        vbox.pack_start(label, False, False, 0)

        box = Gtk.Box(spacing=6)
        vbox.pack_start(box, False, False, 0)
        self.etr_outw = Gtk.Entry(text=str(parent.left_opts.out_w))
        self.etr_outw.connect("changed", self.validate_int)
        self.etr_outw.last_valid_text = self.etr_outw.get_text()
        box.pack_start(self.etr_outw, False, False, 0)
        box.pack_start(Gtk.Label("×", xalign=0), False, False, 0)
        self.etr_outh = Gtk.Entry(text=str(parent.left_opts.out_h))
        self.etr_outh.connect("changed", self.validate_int)
        self.etr_outh.last_valid_text = self.etr_outh.get_text()
        box.pack_start(self.etr_outh, False, False, 0)

        box.pack_end(Gtk.Label(_("pixels"), xalign=0), False, False, 0)

        templates = (
            ("Custom Canvas (300ppi)", (2475, 3225)),
            ("US-Letter portrait (300ppi)", (2550, 3300)),
            ("A4 portrait (300ppi)", (2480, 3508)),
            ("800 × 600", (800, 600)),
            ("1600 × 1200", (1600, 1200)),
            ("A4 landscape (300ppi)", (3508, 2480)),
            ("A3 landscape (300ppi)", (4960, 3508)),
            ("A3 portrait (300ppi)", (3508, 4960)),
            ("US-Letter landscape (300ppi)", (3300, 2550)),

        )

        def apply_template(combo):
            t = combo.get_model()[combo.get_active_iter()][1]
            if t:
                dims = dict(templates)[t]
                self.etr_outw.set_text(str(dims[0]))
                self.etr_outh.set_text(str(dims[1]))
                self.cmb_template.set_active(0)

        box = Gtk.Box(spacing=6)
        vbox.pack_start(box, False, False, 0)
        box.pack_start(Gtk.Label(_("Apply a template:"), xalign=0),
                       True, True, 0)

        self.cmb_template = Gtk.ComboBoxText()
        for t, d in templates:
            self.cmb_template.append(t, t)
        self.cmb_template.set_active(0)
        self.cmb_template.connect("changed", apply_template)
        box.pack_start(self.cmb_template, False, False, 0)

        vbox.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        label = Gtk.Label(xalign=0)
        label.set_markup("<big><b>%s</b></big>" % _("Border"))
        vbox.pack_start(label, False, False, 0)

        box = Gtk.Box(spacing=6)
        vbox.pack_start(box, False, False, 0)
        label = Gtk.Label(_("Thickness:"), xalign=0)
        box.pack_start(label, False, False, 0)
        self.etr_border = Gtk.Entry(text=str(50.0 * parent.left_opts.border_w))
        self.etr_border.connect("changed", self.validate_float)
        self.etr_border.last_valid_text = self.etr_border.get_text()
        self.etr_border.set_width_chars(4)
        self.etr_border.set_alignment(1.0)
        box.pack_start(self.etr_border, False, False, 0)
        label = Gtk.Label("%", xalign=0)
        box.pack_start(label, False, False, 0)

        label = Gtk.Label(_("Color:"), xalign=1)
        box.pack_start(label, True, True, 0)
        self.colorbutton = Gtk.ColorButton()
        color = Gdk.RGBA()
        color.parse(parent.left_opts.border_c)
        self.colorbutton.set_rgba(color)
        box.pack_end(self.colorbutton, False, False, 0)

        vbox.pack_start(Gtk.SeparatorToolItem(), True, True, 0)

        self.show_all()

    def validate_int(self, entry):
        entry_text = entry.get_text() or '0'
        try:
            int(entry_text)
            entry.last_valid_text = entry_text
        except ValueError:
            entry.set_text(entry.last_valid_text)

    def validate_float(self, entry):
        entry_text = entry.get_text() or '0'
        try:
            float(entry_text)
            entry.last_valid_text = entry_text
        except ValueError:
            entry.set_text(entry.last_valid_text)

    def apply_opts(self, opts):
        opts.out_w = int(self.etr_outw.get_text() or '1')
        opts.out_h = int(self.etr_outh.get_text() or '1')
        opts.border_w = float(self.etr_border.get_text() or '0') / 100.0
        opts.border_c = self.colorbutton.get_rgba().to_string()
