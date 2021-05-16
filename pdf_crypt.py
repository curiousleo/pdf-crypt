import pikepdf
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import namedtuple
from typing import Literal, NamedTuple, NewType, Union
from os import path
import logging

password_options = {"show": "\u2022"}
file_options = {"defaultextension": "pdf", "filetypes": [("PDF files", ".pdf")]}

TkState = Union[Literal["normal"], Literal["disabled"]]


class AwaitingInput(NamedTuple):
    def setInput(self, input_file: str):
        is_encrypted = False
        try:
            pikepdf.Pdf.open(input_file)
        except pikepdf.PasswordError:
            is_encrypted = True
        except Exception as e:
            logging.warning(f"Failed to open {input_file}", e)
            return self
        return AwaitingOutput(input_file, is_encrypted)


class AwaitingOutput(NamedTuple):
    input_file: str
    input_is_encrypted: bool

    def setInput(self, input_file: str):
        is_encrypted = False
        try:
            pikepdf.Pdf.open(input_file)
        except pikepdf.PasswordError:
            is_encrypted = True
        except Exception as e:
            logging.warning(f"Failed to open {input_file}", e)
            return self
        return AwaitingOutput(input_file, is_encrypted)

    def setOutput(self, output_file: str):
        return AwaitingPassword(self.input_file, self.input_is_encrypted, output_file)


class AwaitingPassword(NamedTuple):
    input_file: str
    input_is_encrypted: bool
    output_file: str

    def setInput(self, input_file: str):
        is_encrypted = False
        try:
            pikepdf.Pdf.open(input_file)
        except pikepdf.PasswordError:
            is_encrypted = True
        except Exception as e:
            logging.warning(f"Failed to open {input_file}", e)
            return self
        return AwaitingPassword(input_file, is_encrypted, self.output_file)

    def setOutput(self, output_file: str):
        return AwaitingPassword(self.input_file, self.input_is_encrypted, output_file)


AppState = Union[AwaitingInput, AwaitingOutput, AwaitingPassword]


class GuiState(NamedTuple):
    inputState: TkState
    outputState: TkState
    passwordState: TkState

    inputText: str
    outputText: str
    actionText: str


def toGuiState(app_state: AppState) -> GuiState:
    if isinstance(app_state, AwaitingInput):
        return GuiState(tk.NORMAL, tk.DISABLED, tk.DISABLED, "", "", "…")
    elif isinstance(app_state, AwaitingOutput):
        actionText = "Decrypt" if app_state.input_is_encrypted else "Encrypt"
        return GuiState(
            tk.NORMAL, tk.NORMAL, tk.DISABLED, app_state.input_file, "", actionText
        )
    elif isinstance(app_state, AwaitingPassword):
        actionText = "Decrypt" if app_state.input_is_encrypted else "Encrypt"
        return GuiState(
            tk.NORMAL,
            tk.NORMAL,
            tk.NORMAL,
            app_state.input_file,
            app_state.output_file,
            actionText,
        )
    raise AssertionError(app_state)


class PdfCryptGui(ttk.Frame):
    def __init__(self, root, app_state):
        super().__init__()

        self.root = root
        self.app_state = app_state

        self.initUi()
        self.updateState()

    def initUi(self):
        self.master.title("Encrypt/decrypt PDF")
        self.pack(fill=tk.BOTH, expand=True)

        frame_options = {"fill": tk.X}
        label_options = {"side": tk.LEFT, "padx": 2, "pady": 2}
        entry_options = {"fill": tk.X, "padx": 2, "expand": True}
        button_options = {"side": tk.RIGHT, "padx": 2, "pady": 2}

        inputFrame = ttk.Frame(self)
        inputFrame.pack(**frame_options)
        self._inputLabel = ttk.Label(inputFrame, text="① Input file", width=14)
        self._inputLabel.pack(**label_options)
        self._inputButton = ttk.Button(
            inputFrame, text="Choose \u2026", command=self.chooseInputFile
        )
        self._inputButton.pack(**button_options)
        self._inputString = tk.StringVar()
        self._inputEntry = ttk.Entry(
            inputFrame, state=tk.DISABLED, textvariable=self._inputString
        )
        self._inputEntry.pack(**entry_options)

        outputFrame = ttk.Frame(self)
        outputFrame.pack(**frame_options)
        self._outputLabel = ttk.Label(outputFrame, text="② Output file", width=14)
        self._outputLabel.pack(**label_options)
        self._outputButton = ttk.Button(
            outputFrame, text="Choose \u2026", command=self.chooseOutputFile
        )
        self._outputButton.pack(**button_options)
        self._outputString = tk.StringVar()
        self._outputEntry = ttk.Entry(
            outputFrame, state=tk.DISABLED, textvariable=self._outputString
        )
        self._outputEntry.pack(**entry_options)

        passwordFrame = ttk.Frame(self)
        passwordFrame.pack(**frame_options)
        self._passwordLabel = ttk.Label(passwordFrame, text="③ Password", width=14)
        self._passwordLabel.pack(**label_options)
        self._passwordButtonString = tk.StringVar()
        self._passwordButton = ttk.Button(
            passwordFrame,
            textvariable=self._passwordButtonString,
            command=self.encryptOrDecrypt,
        )
        self._passwordButton.pack(**button_options)
        self._passwordEntry = ttk.Entry(passwordFrame, show="\u2022")
        self._passwordEntry.pack(**entry_options)

    def chooseInputFile(self):
        fname = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if fname == "":
            return
        self.app_state = self.app_state.setInput(fname)
        self.updateState()

    def chooseOutputFile(self):
        fname = filedialog.asksaveasfilename(filetypes=[("PDF files", "*.pdf")])
        if fname == "":
            return
        self.app_state = self.app_state.setOutput(fname)
        self.updateState()

    def encryptOrDecrypt(self):
        if not isinstance(self.app_state, AwaitingPassword):
            raise AssertionError("wrong state!")

        try:
            if self.app_state.input_is_encrypted:
                self.decrypt(
                    self.app_state.input_file,
                    self.app_state.output_file,
                    self._passwordEntry.get(),
                )
            else:
                self.encrypt(
                    self.app_state.input_file,
                    self.app_state.output_file,
                    self._passwordEntry.get(),
                )
        except pikepdf.PasswordError:
            messagebox.showerror(
                "Wrong password", "That's not the correct password. Please try again."
            )
            return
        except Exception as e:
            messagebox.showerror("Error", f"There was a problem: \n\n{e}")

        self.root.destroy()

    def decrypt(self, input_file, output_file, password):
        with pikepdf.Pdf.open(input_file, password=password) as pdf:
            pdf.save(output_file, encryption=False)

    def encrypt(self, input_file, output_file, password):
        with pikepdf.Pdf.open(input_file) as pdf:
            encryption = pikepdf.Encryption(
                owner=password, user=password, R=6, aes=True, metadata=True
            )
            pdf.save(output_file, encryption=encryption)

    def updateState(self):
        gui_state = toGuiState(self.app_state)
        print(self.app_state)
        print(gui_state)

        self._inputLabel["state"] = gui_state.inputState
        self._inputButton["state"] = gui_state.inputState
        self._inputString.set(path.basename(gui_state.inputText))

        self._outputLabel["state"] = gui_state.outputState
        self._outputButton["state"] = gui_state.outputState
        self._outputString.set(path.basename(gui_state.outputText))

        self._passwordLabel["state"] = gui_state.passwordState
        self._passwordButton["state"] = gui_state.passwordState
        self._passwordEntry["state"] = gui_state.passwordState
        self._passwordButtonString.set(gui_state.actionText)


def main():
    app_state = AwaitingInput()
    if len(sys.argv) == 2:
        app_state = app_state.setInput(sys.argv[1])
    root = tk.Tk()
    PdfCryptGui(root, app_state)
    root.mainloop()


if __name__ == "__main__":
    main()
