import tkinter as tk

from src.gui import InvoiceApp


def main() -> None:
    root = tk.Tk()
    InvoiceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
