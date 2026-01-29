import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
import time
import os
import sys

class BlocNotes:
    def __init__(self, root):
        self.root = root
        self.root.title("Sans titre - Bloc-notes")

        # Fenêtre maximisée (Windows)
        try:
            self.root.state("zoomed")
        except Exception:
            self.root.attributes("-zoomed", True)

        self.filepath = None
        self.filename = "Sans titre"
        self.is_dirty = False
        self.wrap_enabled = True
        self.status_visible = True

        self._create_widgets()
        self._create_menu()
        self._bind_shortcuts()
        self._update_title()

    def _create_widgets(self):
        # Zone de texte + scrollbar
        self.text = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,  # retour à la ligne automatique par défaut
            undo=True,
            font=("Consolas", 11)
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        # Barre d’état
        self.status_bar = tk.Label(
            self.root,
            text="Ln 1, Col 1",
            anchor=tk.W,
            relief=tk.SUNKEN,
            bd=1
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Suivi des modifications
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._update_cursor_position)
        self.text.bind("<ButtonRelease-1>", self._update_cursor_position)

    def _create_menu(self):
        menubar = tk.Menu(self.root)

        # Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Nouveau", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Ouvrir...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Enregistrer", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Enregistrer sous...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.exit_app)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        # Édition
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Annuler", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_separator()
        edit_menu.add_command(label="Couper", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copier", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Coller", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_command(label="Supprimer", command=self.delete)
        edit_menu.add_separator()
        edit_menu.add_command(label="Tout sélectionner", command=self.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="Heure/Date", command=self.insert_datetime, accelerator="F5")
        menubar.add_cascade(label="Édition", menu=edit_menu)

        # Format
        format_menu = tk.Menu(menubar, tearoff=0)
        format_menu.add_checkbutton(
            label="Retour à la ligne automatique",
            command=self.toggle_wrap,
            onvalue=True,
            offvalue=False
        )
        menubar.add_cascade(label="Format", menu=format_menu)

        # Affichage
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(
            label="Barre d’état",
            command=self.toggle_status_bar,
            onvalue=True,
            offvalue=False
        )
        menubar.add_cascade(label="Affichage", menu=view_menu)

        # Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="À propos de Bloc-notes", command=self.about)
        menubar.add_cascade(label="Aide", menu=help_menu)

        self.root.config(menu=menubar)

    def _bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        self.root.bind("<F5>", lambda e: self.insert_datetime())

    # --- Gestion titre / état ---

    def _update_title(self):
        star = "*" if self.is_dirty else ""
        self.root.title(f"{star}{self.filename} - Bloc-notes")

    def _set_dirty(self, dirty=True):
        self.is_dirty = dirty
        self._update_title()

    def _on_modified(self, event=None):
        if self.text.edit_modified():
            self._set_dirty(True)
            self._update_cursor_position()
            self.text.edit_modified(False)

    def _update_cursor_position(self, event=None):
        try:
            index = self.text.index(tk.INSERT)
            line, col = index.split(".")
            self.status_bar.config(text=f"Ln {int(line)}, Col {int(col)+1}")
        except Exception:
            pass

    # --- Fichier ---

    def confirm_lose_changes(self):
        if not self.is_dirty:
            return True
        res = messagebox.askyesnocancel(
            "Bloc-notes",
            "Le texte a été modifié.\nVoulez-vous enregistrer les modifications ?"
        )
        if res is None:
            return False  # Annuler
        if res:
            return self.save_file()
        return True  # Ne pas enregistrer

    def new_file(self):
        if not self.confirm_lose_changes():
            return
        self.text.delete(1.0, tk.END)
        self.filepath = None
        self.filename = "Sans titre"
        self._set_dirty(False)

    def open_file(self):
        if not self.confirm_lose_changes():
            return
        path = filedialog.askopenfilename(
            filetypes=[
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()

        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, content)
        self.filepath = path
        self.filename = os.path.basename(path)
        self._set_dirty(False)

    def save_file(self):
        if self.filepath is None:
            return self.save_file_as()
        try:
            content = self.text.get(1.0, tk.END)
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(content.rstrip("\n"))
            self._set_dirty(False)
            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer le fichier.\n{e}")
            return False

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if not path:
            return False
        self.filepath = path
        self.filename = os.path.basename(path)
        return self.save_file()

    def exit_app(self):
        if self.confirm_lose_changes():
            self.root.destroy()

    # --- Édition ---

    def undo(self):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass

    def cut(self):
        self.copy()
        self.delete()

    def copy(self):
        try:
            selection = self.text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selection)
        except tk.TclError:
            pass

    def paste(self):
        try:
            content = self.root.clipboard_get()
            self.text.insert(tk.INSERT, content)
        except tk.TclError:
            pass

    def delete(self):
        try:
            self.text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

    def select_all(self):
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        self.text.see(tk.INSERT)

    def insert_datetime(self):
        now = time.strftime("%H:%M %d/%m/%Y")
        self.text.insert(tk.INSERT, now)

    # --- Format / Affichage ---

    def toggle_wrap(self):
        self.wrap_enabled = not self.wrap_enabled
        self.text.config(wrap=tk.WORD if self.wrap_enabled else tk.NONE)

    def toggle_status_bar(self):
        self.status_visible = not self.status_visible
        if self.status_visible:
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        else:
            self.status_bar.pack_forget()

    # --- Aide ---

    def about(self):
        messagebox.showinfo(
            "À propos de Bloc-notes",
            "Clone de Bloc-notes écrit en Python/Tkinter."
        )


def main():
    root = tk.Tk()
    app = BlocNotes(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()

if __name__ == "__main__":
    main()