import gi

from gi.repository import Gtk, GdkPixbuf, Gdk


class PictureView(Gtk.DrawingArea):
    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path
        self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.path)
        self.img_surface = Gdk.cairo_surface_create_from_pixbuf(
            self.pixbuf, 1, None
        )

    def get_useful_height(self):
        aw = self.get_allocated_width()
        pw = self.pixbuf.get_width()
        ph = self.pixbuf.get_height()
        return aw/pw * ph

    def get_scale_factor(self):
        return self.get_allocated_width() / self.pixbuf.get_width()

    def do_draw(self, context):
        sf = self.get_scale_factor()
        context.scale(sf, sf)
        context.set_source_surface(self.img_surface, 0, 0)
        context.paint()
        height = self.get_useful_height(self.get_allocated_width())
        self.set_size_request(-1, height)