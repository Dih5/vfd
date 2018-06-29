# -*- coding: utf-8 -*-

"""Graphical user interface for vfd."""

import sys
import os

from . import vfd
from . import __version__

try:
    import tkinter as tk
    import tkinter.filedialog as tkfiledialog

except ImportError:
    import Tkinter as tk
    import Tkinter.filedialog as tkfiledialog

from PIL import Image, ImageTk

img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


class VfdGui(tk.Frame):

    def __init__(self, master=None):
        super().__init__(master=master)

        self.master.title("".join(('VFD GUI v', __version__)))

        menu = tk.Menu(self.master)
        self.file_menu = tk.Menu(self.master, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.open_choose)
        self.file_menu.add_command(label="Exit", command=self.leave)
        menu.add_cascade(label="File", menu=self.file_menu)

        toolbar = tk.Frame(self.master, bd=1, relief=tk.RAISED)

        img_open = ImageTk.PhotoImage(Image.open(os.path.join(img_path, "document-open.png")))
        btn_open = tk.Button(toolbar, image=img_open, relief=tk.FLAT, command=self.open_choose)
        btn_open.image = img_open
        btn_open.pack(side=tk.LEFT, padx=2, pady=2)

        img_xlsx = ImageTk.PhotoImage(Image.open(os.path.join(img_path, "x-office-spreadsheet.png")))
        btn_xlsx = tk.Button(toolbar, image=img_xlsx, relief=tk.FLAT, command=self.export_xlsx)
        btn_xlsx.image = img_xlsx
        btn_xlsx.pack(side=tk.LEFT, padx=2, pady=2)

        img_exit = ImageTk.PhotoImage(Image.open(os.path.join(img_path, "system-log-out.png")))
        btn_exit = tk.Button(toolbar, image=img_exit, relief=tk.FLAT, command=self.quit)
        btn_exit.image = img_exit
        btn_exit.pack(side=tk.LEFT, padx=2, pady=2)

        toolbar.pack(side=tk.TOP, fill=tk.X)
        self.master.config(menu=menu)

        self.preview = tk.Label(master, text="Preview will be shown here")
        self.preview.pack(side=tk.TOP)
        self.pack()

        self.file_path = None

    def open_choose(self):
        ifile = tkfiledialog.askopenfile(parent=self, mode='r', title='Open a VFD')
        path = ifile.name
        self.open(path)

    def open(self, path):
        self.file_path = path
        vfd.create_scripts(path, run=True, blocking=True, export_format=["png"])
        self.update_preview()

    def update_preview(self):
        img = ImageTk.PhotoImage(Image.open(self.file_path[:-3] + "png"))
        self.preview.configure(image=img)
        self.preview.image = img
        pass

    def export_xlsx(self):
        vfd.create_xlsx(self.file_path)

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
