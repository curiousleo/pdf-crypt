import tkinter as tk
import tkinter.simpledialog as sd
import tkinter.filedialog as fd

import pikepdf

app = tk.Tk()
app.withdraw()

password_options = {"show": "\u2022"}
file_options = {"defaultextension": "pdf", "filetypes": [("PDF files", ".pdf")]}

input_file = fd.askopenfilename(title="Choose PDF file to decrypt or encrypt", **file_options)
try:
    with pikepdf.Pdf.open(input_file) as pdf:
        assert not pdf.is_encrypted
        password = sd.askstring("Encrypt PDF file", "Password", **password_options)
        output_file = fd.asksaveasfilename(title="Choose where to save encrypted PDF file", **file_options)
        encryption = pikepdf.Encryption(owner=password, user=password, R=6, aes=True, metadata=True)
        pdf.save(output_file, encryption=encryption)
except pikepdf.PasswordError:
    # input_file was encrypted
    while True:
        try:
            password = sd.askstring("Decrypt PDF file", "Password", **password_options)
            with pikepdf.Pdf.open(input_file, password=password) as pdf:
                output_file = fd.asksaveasfilename(title="Choose where to save decrypted PDF file", **file_options)
                pdf.save(output_file, encryption=False)
                break
        except pikepdf.PasswordError:
            continue
