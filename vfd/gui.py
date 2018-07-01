# -*- coding: utf-8 -*-

"""Graphical user interface for vfd."""

import sys
import os
import tempfile
import io

try:
    from tempfile import TemporaryDirectory
except ImportError:
    class TemporaryDirectory(object):
        """Py2-compatible tempfile.TemporaryDirectory"""

        def __enter__(self):
            self.dir_name = tempfile.mkdtemp()
            return self.dir_name

        def __exit__(self, exc_type, exc_value, traceback):
            shutil.rmtree(self.dir_name)

import shutil
from PIL import Image, ImageTk

try:
    import tkinter as tk
    import tkinter.filedialog as tkfiledialog

except ImportError:
    import Tkinter as tk
    import Tkinter.filedialog as tkfiledialog

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from . import vfd
from . import __version__

_ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def get_ico_path(name):
    return os.path.join(_ico_path, name)


class CreateToolTip(object):
    """
    A tooltip for a given widget.
    """

    # Based on the content from this post:
    # http://stackoverflow.com/questions/3221956/what-is-the-simplest-way-to-make-tooltips-in-tkinter

    def __init__(self, widget, text, color="#ffe14c"):
        """
        Create a tooltip for an existent widget.
        Args:
            widget: The widget the tooltip is applied to.
            text (str): The text of the tooltip.
            color: The color of the tooltip.
        """
        self.waittime = 500  # miliseconds
        self.wraplength = 180  # pixels
        self.widget = widget
        self.text = text
        self.color = color
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                         background=self.color, relief='solid', borderwidth=1,
                         wraplength=self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


class ParBox:
    """A parameter entry with labels preceding and succeeding it and an optional tooltip"""

    def __init__(self, master=None, text_variable=0, pre_text="", post_text="", help_text="", read_only=False):
        """
        Create the parameter box.
        Args:
            master: the master widget.
            text_variable (:obj:`tkinter.Variable`): The variable associated with the parameter.
            pre_text (str): The text preceding the text entry.
            post_text (str): The text succeeding the text entry, typically the units.
            help_text (str): The help text to show in the tooltip. If "", no tooltip is shown.
            read_only (bool): Whether the entry is read_only.
        """
        self.frame = tk.Frame(master=master)

        self.lbl = tk.Label(self.frame, text=pre_text)
        self.lbl.pack(side=tk.LEFT)

        self.txt = tk.Entry(self.frame, textvariable=text_variable)
        self.txt.pack(side=tk.LEFT)

        self.units = tk.Label(self.frame, text=post_text, anchor=tk.W)
        self.units.pack(side=tk.LEFT)

        if help_text != "":
            self.lblTT = CreateToolTip(self.lbl, help_text)
            self.txtTT = CreateToolTip(self.txt, help_text)
        if read_only:
            self.txt["state"] = "readonly"

    def pack(self, *args, **kwargs):
        return self.frame.pack(*args, **kwargs)


class StyleDialog(tk.Frame, object):
    def __init__(self, master=None):
        # BEWARE: master being None will result in adding the dialog to the main window and closing it when the dialog
        # does so.
        if master is not None:
            master = tk.Toplevel(master)
        self.master = master
        super(StyleDialog, self).__init__(master=master)

        self.master.title("Select style(s)")

        self.style_list = ['default', 'classic'] + sorted(style for style in plt.style.available if style != 'classic')

        self.frm_lst_styles = tk.Frame(master=self)
        self.lst_styles = tk.Listbox(master=self.frm_lst_styles, selectmode=tk.EXTENDED)
        for item in self.style_list:
            self.lst_styles.insert(tk.END, item)
        self.scr_lst_styles = tk.Scrollbar(master=self.frm_lst_styles, orient=tk.VERTICAL)
        self.lst_styles.config(yscrollcommand=self.scr_lst_styles.set)
        self.scr_lst_styles.config(command=self.lst_styles.yview)

        self.scr_lst_styles.pack(side=tk.RIGHT, fill=tk.Y)
        self.lst_styles.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.frm_lst_styles.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.btn_ok = tk.Button(self, text="OK", command=self.choose)
        self.btn_ok.pack(side=tk.BOTTOM, fill=tk.X)

        self.choice = None

        self.pack(fill=tk.BOTH, expand=1)

    def choose(self):
        pos = list(map(int, self.lst_styles.curselection()))  # int conversion needed for very old Tk
        self.choice = ", ".join([self.style_list[i] for i in pos])
        self.master.destroy()


class VfdGui(tk.Frame, object):

    def __init__(self, master=None):
        super(VfdGui, self).__init__(master=master)

        self.master.title("".join(('VFD v', __version__, ' GUI')))

        # Create the menu bar
        self.menu = tk.Menu(self.master)
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.file_menu.add_command(label="Open", underline=0, accelerator="Ctrl+O", command=self.open_choose)
        self.file_menu.add_command(label="Export as xlsx", command=self.export_xlsx_choose)
        self.file_menu.add_command(label="Quit", underline=0, accelerator="Ctrl+Q", command=self.leave)
        self.menu.add_cascade(label="File", underline=0, menu=self.file_menu)
        self.master.config(menu=self.menu)

        # Create the toolbar
        self.toolbar = tk.Frame(self, bd=1, relief=tk.RAISED)

        self.img_open = ImageTk.PhotoImage(Image.open(get_ico_path("document-open.png")))
        self.btn_open = tk.Button(self.toolbar, image=self.img_open, relief=tk.FLAT, command=self.open_choose)
        self.btn_open.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_open_tt = CreateToolTip(self.btn_open, "Open")

        self.img_xlsx = ImageTk.PhotoImage(Image.open(get_ico_path("x-office-spreadsheet.png")))
        self.btn_xlsx = tk.Button(self.toolbar, image=self.img_xlsx, relief=tk.FLAT, command=self.export_xlsx_choose)
        self.btn_xlsx.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_xlsx_tt = CreateToolTip(self.btn_xlsx, "Export as xlsx")

        self.img_exit = ImageTk.PhotoImage(Image.open(get_ico_path("system-log-out.png")))
        self.btn_exit = tk.Button(self.toolbar, image=self.img_exit, relief=tk.FLAT, command=self.quit)
        self.btn_exit.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_exit_tt = CreateToolTip(self.btn_exit, "Quit")

        self.toolbar.pack(side=tk.TOP, fill=tk.X, expand=0)

        self.frm_general = tk.Frame(master=self)

        # Create the editor frame
        self.editor_frame = tk.LabelFrame(self.frm_general, text="Edit VFD")
        self.txt_editor = tk.Text(master=self.editor_frame)
        self.scr_txt_editor = tk.Scrollbar(self.editor_frame, orient=tk.VERTICAL)
        self.txt_editor.config(yscrollcommand=self.scr_txt_editor.set)
        self.scr_txt_editor.config(command=self.txt_editor.yview)

        self.scr_txt_editor.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_editor.pack(fill=tk.BOTH, expand=1)

        self.editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Create the matplotlib frame
        self.mpl_frame = tk.LabelFrame(self.frm_general, text="Matplotlib render")

        self.mpl_toolbar = tk.Frame(self.mpl_frame, bd=1, relief=tk.RAISED)
        self.var_style = tk.StringVar()
        self.var_style.set("")
        self.mpl_style = ParBox(self.mpl_toolbar, self.var_style, pre_text="Style",
                                help_text="Matplotlib style(s) to use in the plot.")
        self.mpl_style.pack(side=tk.LEFT)
        self.btn_preview_style = tk.Button(self.mpl_toolbar, text="...", command=self.open_style_dialog)
        self.btn_preview_style.pack(side=tk.LEFT)

        self.var_tight = tk.IntVar()
        self.var_tight.set(0)
        self.chk_tight = tk.Checkbutton(self.mpl_toolbar, text="Tight", variable=self.var_tight)
        self.chk_tight_tt = CreateToolTip(self.chk_tight, "Use a tight layout?")
        self.chk_tight.pack(side=tk.LEFT)

        self.var_scale_multi = tk.IntVar()
        self.var_scale_multi.set(0)
        self.chk_scale_multi = tk.Checkbutton(self.mpl_toolbar, text="Scale multi", variable=self.var_scale_multi)
        self.chk_scale_multi_tt = CreateToolTip(self.chk_scale_multi, "Proportionally scale multiplots?")
        self.chk_scale_multi.pack(side=tk.LEFT)

        self.img_refresh = ImageTk.PhotoImage(Image.open(get_ico_path("go-jump.png")))
        self.btn_refresh = tk.Button(self.mpl_toolbar, image=self.img_refresh, relief=tk.FLAT, command=self.refresh)
        self.btn_refresh_tt = CreateToolTip(self.btn_refresh, "Refresh preview")
        self.btn_refresh.pack(side=tk.RIGHT)

        self.img_img = ImageTk.PhotoImage(Image.open(get_ico_path("image-x-generic.png")))
        self.btn_img_export = tk.Button(self.mpl_toolbar, image=self.img_img, relief=tk.FLAT,
                                        command=self.mpl_export_choose)
        self.btn_img_export_tt = CreateToolTip(self.btn_img_export, "Export plot")
        self.btn_img_export.pack(side=tk.RIGHT)

        self.mpl_toolbar.pack(side=tk.TOP, fill=tk.X, expand=0)

        self.preview = tk.Label(self.mpl_frame, text="Preview will be shown here")
        self.preview.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)

        self.mpl_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        self.frm_general.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)

        # UI is ready, pack it
        self.pack(fill=tk.BOTH, expand=1)

        # Path of the opened file
        self.file_path = None
        # StyleDialog instance opened
        self.style_dialog = None

        # Create and prepare a temporary directory
        self._temp_dir = TemporaryDirectory()
        self.temp_dir = str(self._temp_dir)
        try:
            os.makedirs(self.temp_dir)
        except OSError:
            # Either already existing or unable to create it
            pass

        self.temp_vfd = os.path.join(self.temp_dir, "vfdgui.vfd")

    def open_style_dialog(self):
        if self.style_dialog is None:
            self.style_dialog = StyleDialog(master=self)
            self.wait_window(self.style_dialog)
            if self.style_dialog.choice is not None:
                self.var_style.set(self.style_dialog.choice)
            self.style_dialog = None

    def open_choose(self):
        file = tkfiledialog.askopenfile(parent=self, mode='r', filetypes=(("VFD file", "*.vfd"), ("all files", "*.*")),
                                        title='Open a VFD')
        if file:
            self.open(file.name)

    def open(self, path):
        self.file_path = path
        with io.open(path, 'r', encoding='utf8') as file:
            text = file.read()

        self.txt_editor.delete(1.0, tk.END)
        self.txt_editor.insert(tk.END, text)
        self.refresh()

    def update_temp_file(self):
        with io.open(self.temp_vfd, 'w', encoding='utf8') as file:
            file.write(self.txt_editor.get(1.0, tk.END))

    def refresh(self):
        self.mpl_create_img("png")
        self.update_preview()

    def mpl_export_choose(self):
        file = tkfiledialog.asksaveasfilename(parent=self, filetypes=(
            ("Portable Network Graphics", "*.png"), ("Portable Document Format", "*.pdf"), ("PostScript", "*.ps"),
            ("Encapsulated PostScript", "*.eps"), ("Scalable Vector Graphics", "*.svg"), ("JPEG", "*.jpg"),
            ("Any supported format", "*")), title='Export using matplotlib')
        if file:
            self.mpl_export(file)

    def mpl_export(self, path):
        file_name = os.path.basename(path)
        if "." not in file_name:
            raise ValueError("No extension in path %s" % path)
        ext = file_name.split(".")[-1]
        self.mpl_create_img(ext)
        shutil.copyfile(os.path.join(self.temp_dir, "vfdgui." + ext), path)

    def mpl_create_img(self, format):
        self.update_temp_file()
        style = self.var_style.get()
        if "," in style:
            style = list(filter(None, (s.strip() for s in style.split(","))))
        tight = bool(self.var_tight.get())
        scale_multi = bool(self.var_tight.get())

        vfd.create_scripts(self.temp_vfd, context=style, tight_layout=tight, run=True, blocking=True,
                           export_format=[format], scale_multiplot=scale_multi)

    def update_preview(self):
        img = ImageTk.PhotoImage(Image.open(os.path.join(self.temp_dir, "vfdgui.png")))
        self.preview.configure(image=img)
        self.preview.image = img

    def export_xlsx_choose(self):
        file = tkfiledialog.asksaveasfilename(parent=self, filetypes=(("Spreadsheet", "*.xlsx"),),
                                              title='Export as xlsx')
        if file:
            self.export_xlsx(file)

    def export_xlsx(self, path):
        self.update_temp_file()
        vfd.create_xlsx(self.temp_vfd)
        shutil.move(self.temp_vfd[:-3] + "xlsx", path)

    def leave(self):
        self.quit()


def main():
    root = tk.Tk()
    app = VfdGui(root)
    if len(sys.argv) == 2:
        app.open(sys.argv[1])
    app.mainloop()


if __name__ == '__main__':
    main()
