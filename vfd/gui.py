# -*- coding: utf-8 -*-

"""Graphical user interface for vfd."""

import sys
import os

import shutil
from PIL import Image, ImageTk

try:
    import tkinter as tk
    import tkinter.filedialog as tkfiledialog

except ImportError:
    import Tkinter as tk
    import Tkinter.filedialog as tkfiledialog

from . import vfd
from . import __version__

img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


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


class VfdGui(tk.Frame, object):

    def __init__(self, master=None):
        super(VfdGui, self).__init__(master=master)

        self.master.title("".join(('VFD GUI v', __version__)))

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

        img_open = ImageTk.PhotoImage(Image.open(os.path.join(img_path, "document-open.png")))
        btn_open = tk.Button(self.toolbar, image=img_open, relief=tk.FLAT, command=self.open_choose)
        btn_open.image = img_open
        btn_open.pack(side=tk.LEFT, padx=2, pady=2)

        img_xlsx = ImageTk.PhotoImage(Image.open(os.path.join(img_path, "x-office-spreadsheet.png")))
        btn_xlsx = tk.Button(self.toolbar, image=img_xlsx, relief=tk.FLAT, command=self.export_xlsx_choose)
        btn_xlsx.image = img_xlsx
        btn_xlsx.pack(side=tk.LEFT, padx=2, pady=2)

        img_exit = ImageTk.PhotoImage(Image.open(os.path.join(img_path, "system-log-out.png")))
        btn_exit = tk.Button(self.toolbar, image=img_exit, relief=tk.FLAT, command=self.quit)
        btn_exit.image = img_exit
        btn_exit.pack(side=tk.LEFT, padx=2, pady=2)

        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Create the preview frame
        self.preview_frame = tk.Frame(self)

        self.preview_toolbar = tk.Frame(self.preview_frame, bd=1, relief=tk.RAISED)
        ## Variables
        self.var_style = tk.StringVar()
        self.var_style.set("")
        self.preview_style = ParBox(self.preview_toolbar, self.var_style, pre_text="Style", help_text="Matplotlib style(s) to use in the plot.")
        self.preview_style.pack(side=tk.LEFT)

        self.var_tight = tk.IntVar()
        self.var_tight.set(0)
        self.chk_tight = tk.Checkbutton(self.preview_toolbar, text="Tight", variable=self.var_tight)
        self.chk_tight.pack(side=tk.LEFT)

        self.preview_refresh = tk.Button(self.preview_toolbar, image=img_xlsx, relief=tk.FLAT,
                                         command=self.refresh)
        self.preview_refresh.pack(side=tk.RIGHT)

        self.preview_toolbar.pack(side=tk.TOP)

        self.preview = tk.Label(self.preview_frame, text="Preview will be shown here")
        self.preview.pack(side=tk.BOTTOM)

        self.preview_frame.pack(side=tk.RIGHT)

        # UI is ready, pack it
        self.pack()

        self.file_path = None

    def open_choose(self):
        file = tkfiledialog.askopenfile(parent=self, mode='r', filetypes=(("VFD file", "*.vfd"), ("all files", "*.*")),
                                        title='Open a VFD')
        if file:
            self.open(file.name)

    def open(self, path):
        self.file_path = path
        self.refresh()

    def refresh(self):
        if self.file_path:
            style = self.var_style.get()  # TODO: To list
            tight = self.var_tight.get()

            vfd.create_scripts(self.file_path, context=style, tight_layout=tight, run=True, blocking=True, export_format=["png"])
            self.update_preview()

    def update_preview(self):
        img = ImageTk.PhotoImage(Image.open(self.file_path[:-3] + "png"))
        self.preview.configure(image=img)
        self.preview.image = img
        pass

    def export_xlsx_choose(self):
        file = tkfiledialog.asksaveasfilename(parent=self, filetypes=(("Spreadsheet", "*.xlsx"),),
                                              title='Export as xlsx')
        if file:
            self.export_xlsx(file)

    def export_xlsx(self, path=None):
        vfd.create_xlsx(self.file_path)
        gen_path = self.file_path[:-3] + "xlsx"
        # TODO: Check if exists
        if path is not None and path != gen_path:
            shutil.move(gen_path, path)

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
