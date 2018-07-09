# -*- coding: utf-8 -*-

"""Graphical user interface for vfd."""

from __future__ import division

import sys
import os
import tempfile
import io
import traceback

import shutil
from PIL import Image, ImageTk

try:
    import tkinter as tk
    import tkinter.filedialog as tkfiledialog

except ImportError:
    import Tkinter as tk
    import tkFileDialog as tkfiledialog

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
    def __init__(self, main_window=None):
        if main_window is None:
            raise ValueError("StyleDialog needs a master to serve")
        self.main_window = main_window
        self.top = tk.Toplevel(main_window)

        super(StyleDialog, self).__init__(master=self.top)

        self.top.title("Select style(s)")

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
        self.exit()

    def exit(self):
        self.main_window.focus_set()
        self.top.destroy()


class TraceDialog(tk.Frame, object):
    def __init__(self, main_window=None, msg=""):
        if main_window is None:
            raise ValueError("TraceDialog needs a master to serve")
        self.main_window = main_window
        self.top = tk.Toplevel(main_window)

        super(TraceDialog, self).__init__(master=self.top)

        self.top.title("Error")

        self.txt_trace = tk.Text(master=self)
        self.txt_trace.insert(tk.END, msg)
        self.txt_trace.config(state=tk.DISABLED)
        self.scr_txt_trace = tk.Scrollbar(master=self, orient=tk.VERTICAL)
        self.txt_trace.config(yscrollcommand=self.scr_txt_trace.set)
        self.scr_txt_trace.config(command=self.txt_trace.yview)
        self.scr_txt_trace.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_trace.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.btn_ok = tk.Button(self, text="OK", command=self.exit)
        self.btn_ok.bind('<Return>', lambda event: self.exit())
        self.btn_ok.bind('<Escape>', lambda event: self.exit())
        self.btn_ok.pack(side=tk.BOTTOM, fill=tk.X)

        self.choice = None

        self.pack(fill=tk.BOTH, expand=1)

        self.btn_ok.focus_set()

    def add_message(self, msg):
        self.txt_trace.config(state=tk.NORMAL)
        self.txt_trace.insert(tk.END, "\n" + msg)
        self.txt_trace.config(state=tk.DISABLED)
        self.txt_trace.see(tk.END)

    def exit(self):
        self.main_window.focus_set()
        self.top.destroy()


class VfdGui(tk.Frame, object):

    def __init__(self, master=None):
        super(VfdGui, self).__init__(master=master)

        master.report_callback_exception = self.report_callback_exception

        self.master.title("".join(('VFD v', __version__, ' GUI')))
        self.ico = ImageTk.PhotoImage(file=get_ico_path("vfdlogo.png"))
        self.master.tk.call('wm', 'iconphoto', self.master._w, self.ico)

        # Create the menu bar
        self.menu = tk.Menu(self.master)
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.file_menu.add_command(label="Open", underline=0, accelerator="Ctrl+O", command=self.open_choose)
        self.file_menu.add_command(label="Save as...", underline=0, accelerator="Ctrl+S", command=self.save_choose)
        self.file_menu.add_command(label="Export as xlsx...", command=self.export_xlsx_choose)
        self.file_menu.add_command(label="Quit", underline=0, accelerator="Ctrl+Q", command=self.leave)
        self.menu.add_cascade(label="File", underline=0, menu=self.file_menu)
        self.mpl_menu = tk.Menu(self.menu, tearoff=0)
        self.mpl_menu.add_command(label="Export script...", command=self.mpl_python_choose)
        self.mpl_menu.add_command(label="Export image...", command=self.mpl_export_choose)
        self.mpl_menu.add_command(label="Refresh preview", accelerator="Ctrl+R", command=self.refresh)
        self.menu.add_cascade(label="Matplotlib", menu=self.mpl_menu)
        self.master.config(menu=self.menu)

        self.master.bind('<Control-o>', lambda event: self.open_choose())
        self.master.bind('<Control-s>', lambda event: self.save_choose())
        self.master.bind('<Control-q>', lambda event: self.leave())
        self.master.bind('<Control-r>', lambda event: self.refresh())

        # Create the toolbar
        self.toolbar = tk.Frame(self, bd=1, relief=tk.RAISED)

        self.img_open = ImageTk.PhotoImage(file=get_ico_path("document-open.png"))
        self.btn_open = tk.Button(self.toolbar, image=self.img_open, relief=tk.FLAT, command=self.open_choose)
        self.btn_open.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_open_tt = CreateToolTip(self.btn_open, "Open")

        self.img_save = ImageTk.PhotoImage(file=get_ico_path("document-save-as.png"))
        self.btn_save = tk.Button(self.toolbar, image=self.img_save, relief=tk.FLAT, command=self.save_choose)
        self.btn_save.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_save_tt = CreateToolTip(self.btn_save, "Save VFD")

        self.img_xlsx = ImageTk.PhotoImage(file=get_ico_path("x-office-spreadsheet.png"))
        self.btn_xlsx = tk.Button(self.toolbar, image=self.img_xlsx, relief=tk.FLAT, command=self.export_xlsx_choose)
        self.btn_xlsx.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_xlsx_tt = CreateToolTip(self.btn_xlsx, "Export as xlsx")

        self.img_exit = ImageTk.PhotoImage(file=get_ico_path("system-log-out.png"))
        self.btn_exit = tk.Button(self.toolbar, image=self.img_exit, relief=tk.FLAT, command=self.leave)
        self.btn_exit.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_exit_tt = CreateToolTip(self.btn_exit, "Quit")

        self.toolbar.pack(side=tk.TOP, fill=tk.X, expand=0)

        self.frm_general = tk.PanedWindow(master=self)

        # Create the editor frame
        self.editor_frame = tk.LabelFrame(self.frm_general, text="Edit VFD")
        self.txt_editor = tk.Text(master=self.editor_frame, wrap=tk.NONE)
        self.scr_y_txt_editor = tk.Scrollbar(self.editor_frame, orient=tk.VERTICAL)
        self.txt_editor.config(yscrollcommand=self.scr_y_txt_editor.set)
        self.scr_y_txt_editor.config(command=self.txt_editor.yview)
        self.scr_x_txt_editor = tk.Scrollbar(self.editor_frame, orient=tk.HORIZONTAL)
        self.txt_editor.config(xscrollcommand=self.scr_x_txt_editor.set)
        self.scr_x_txt_editor.config(command=self.txt_editor.xview)

        self.scr_y_txt_editor.pack(side=tk.RIGHT, fill=tk.Y)
        self.scr_x_txt_editor.pack(side=tk.BOTTOM, fill=tk.X)
        self.txt_editor.pack(fill=tk.BOTH, expand=1)

        self.frm_general.add(self.editor_frame)

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

        self.img_refresh = ImageTk.PhotoImage(file=get_ico_path("go-jump.png"))
        self.btn_refresh = tk.Button(self.mpl_toolbar, image=self.img_refresh, relief=tk.FLAT, command=self.refresh)
        self.btn_refresh_tt = CreateToolTip(self.btn_refresh, "Refresh preview")
        self.btn_refresh.pack(side=tk.RIGHT)

        self.img_img = ImageTk.PhotoImage(file=get_ico_path("image-x-generic.png"))
        self.btn_img_export = tk.Button(self.mpl_toolbar, image=self.img_img, relief=tk.FLAT,
                                        command=self.mpl_export_choose)
        self.btn_img_export_tt = CreateToolTip(self.btn_img_export, "Export plot")
        self.btn_img_export.pack(side=tk.RIGHT)

        self.img_python = ImageTk.PhotoImage(file=get_ico_path("python.png"))
        self.btn_python = tk.Button(self.mpl_toolbar, image=self.img_python, relief=tk.FLAT,
                                    command=self.mpl_python_choose)
        self.btn_python_tt = CreateToolTip(self.btn_python, "Export python script")
        self.btn_python.pack(side=tk.RIGHT)

        self.mpl_toolbar.pack(side=tk.TOP, fill=tk.X, expand=0)

        self.preview = tk.Label(self.mpl_frame, text="Preview will be shown here")
        self.preview.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)

        self.frm_general.add(self.mpl_frame)

        self.frm_general.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)

        # UI is ready, pack it
        self.pack(fill=tk.BOTH, expand=1)

        # Path of the opened file
        self.file_path = None
        # StyleDialog instance opened
        self.style_dialog = None
        # TraceDialog instance opened
        self.trace_dialog = None
        # Preview image
        self.image = None

        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()

        self.temp_vfd = os.path.join(self.temp_dir, "vfdgui.vfd")

        self.master.protocol("WM_DELETE_WINDOW", self.leave)

    def report_callback_exception(self, exc_type, exc_value, exc_traceback):
        message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        if self.trace_dialog is None:
            self.trace_dialog = TraceDialog(main_window=self, msg=message)
            self.wait_window(self.trace_dialog)
            self.trace_dialog = None
        else:
            self.trace_dialog.add_message(message)

    def open_style_dialog(self):
        """Open the mpl style selection dialog"""
        if self.style_dialog is None:
            self.style_dialog = StyleDialog(main_window=self)
            self.wait_window(self.style_dialog)
            if self.style_dialog.choice is not None:
                self.var_style.set(self.style_dialog.choice)
            self.style_dialog = None

    def open_choose(self):
        """Show a dialog to choose which VFD to open"""
        file = tkfiledialog.askopenfile(parent=self, mode='r', filetypes=(("VFD file", "*.vfd"), ("all files", "*.*")),
                                        title='Open a VFD')
        if file:
            self.open(file.name)

    def open(self, path):
        """Open the VFD in the given path"""
        self.file_path = path
        with io.open(path, 'r', encoding='utf8') as file:
            text = file.read()

        self.txt_editor.delete(1.0, tk.END)
        self.txt_editor.insert(tk.END, text)
        self.refresh()

    def update_temp_file(self):
        """Update the vfd in temp dir"""
        self.save(self.temp_vfd)

    def refresh(self):
        """Recreate the image and update the preview"""
        self.mpl_create_img("png")
        self.update_preview()

    def mpl_export_choose(self):
        """Show a dialog to choose where to export a mpl-generated plot"""
        file = tkfiledialog.asksaveasfilename(parent=self, filetypes=(
            ("Portable Network Graphics", "*.png"), ("Portable Document Format", "*.pdf"), ("PostScript", "*.ps"),
            ("Encapsulated PostScript", "*.eps"), ("Scalable Vector Graphics", "*.svg"), ("JPEG", "*.jpg"),
            ("Any supported format", "*")), title='Export using matplotlib')
        if file:
            # TODO: if an extension was not added to the filename (as I see in Windows), mpl_export will fail
            self.mpl_export(file)

    def mpl_export(self, path):
        """Export using mpl to the given path"""
        file_name = os.path.basename(path)
        if "." not in file_name:
            raise ValueError("No extension in path %s" % path)
        ext = file_name.split(".")[-1]
        self.mpl_create_img(ext)
        shutil.copyfile(os.path.join(self.temp_dir, "vfdgui." + ext), path)

    def get_mpl_parameters(self):
        style = self.var_style.get()
        if "," in style:
            style = list(filter(None, (s.strip() for s in style.split(","))))
        tight = bool(self.var_tight.get())
        scale_multi = bool(self.var_tight.get())
        return {"context": style, "tight_layout": tight, "scale_multiplot": scale_multi}

    def mpl_python_choose(self):
        """Show a dialog to choose where to export a mpl-generating python script"""
        file = tkfiledialog.asksaveasfilename(parent=self, filetypes=(
            ("Python script", "*.py"),), title='Export matplotlib script')
        if file:
            # If an extension was not added to the filename (I see this in Windows)
            if file[-3:] != ".py":
                file += ".py"
            self.mpl_python(file)

    def mpl_python(self, path):
        """Export using mpl to the given path"""
        vfd.create_scripts(self.temp_vfd, run=False, **self.get_mpl_parameters())
        shutil.copyfile(os.path.join(self.temp_dir, "vfdgui.py"), path)

    def mpl_create_img(self, format):
        """Use the temp dir to create an image with the given format"""
        self.update_temp_file()
        vfd.create_scripts(self.temp_vfd, run=True, blocking=True, export_format=[format], **self.get_mpl_parameters())

    def update_preview(self):
        """Update the preview image using the one in the temp dir"""
        image = Image.open(os.path.join(self.temp_dir, "vfdgui.png"))
        # Image will be reduced if it's bigger than the available space
        self.master.update()  # Ensure measure is updated
        max_width = self.preview.winfo_width()
        max_height = self.preview.winfo_height()
        width, height = image.size
        scale = min(max_width / width, max_height / height)

        new_width, new_height = int(scale * width), int(scale * height)
        image = image.resize((new_width, new_height), Image.ANTIALIAS)

        self.image = ImageTk.PhotoImage(image)
        self.preview.configure(image=self.image)

    def save_choose(self):
        """Show a dialog to choose where to save the edited VFD file"""
        # TODO: Check if well formed
        file = tkfiledialog.asksaveasfilename(parent=self, filetypes=(("Vernacular Figure Description", "*.vfd"),),
                                              title='Save VFD', initialfile=self.file_path if self.file_path else None)
        if file:
            # If an extension was not added to the filename (I see this in Windows)
            if file[-4:] != ".vfd":
                file += ".vfd"
            self.save(file)

    def save(self, path):
        """Save the edited VFD to the given path"""
        with io.open(path, 'w', encoding='utf8') as file:
            file.write(self.txt_editor.get(1.0, tk.END))

    def export_xlsx_choose(self):
        """Show a dialog to choose where to export in xlsx format"""
        file = tkfiledialog.asksaveasfilename(parent=self, filetypes=(("Spreadsheet", "*.xlsx"),),
                                              title='Export as xlsx')
        if file:
            # If an extension was not added to the filename (I see this in Windows)
            if file[-5:] != ".xlsx":
                file += ".xlsx"
            self.export_xlsx(file)

    def export_xlsx(self, path):
        """Export as xlsx to the given path"""
        self.update_temp_file()
        vfd.create_xlsx(self.temp_vfd)
        shutil.move(self.temp_vfd[:-3] + "xlsx", path)

    def leave(self):
        """Exit the application"""
        for d in [self.trace_dialog, self.style_dialog]:
            if d is not None:
                d.exit()
        # Delete the temp folder unless running from pyinstaller
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.quit()


def main():
    root = tk.Tk()
    app = VfdGui(root)
    if len(sys.argv) == 2:
        app.open(sys.argv[1])
    app.mainloop()


if __name__ == '__main__':
    main()
