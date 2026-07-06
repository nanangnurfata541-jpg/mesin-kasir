# Mesin Kasir

A simple desktop point-of-sale (POS) application for small shops written in Python/Tkinter.

Features:
- Product management (add/edit/delete)
- Sales transactions with receipt printing/saving
- Stock and sales reports
- Per-user data stored in `~/.local/share/mesin-kasir/`

Installation (Debian/Ubuntu/Mint):

1. Install dependencies:

```bash
sudo apt update
sudo apt install -y python3 python3-pandas python3-tk
```

2. Install package (.deb):

```bash
sudo dpkg -i mesin-kasir_1.0.4_all.deb
sudo apt-get -f install -y
```

Run:

- From menu: "Mesin Kasir"
- From terminal: `mesin-kasir`
- Or directly: `python3 ~/.local/share/mesin-kasir/mesin_kasir.py`

Data location:
- `~/.local/share/mesin-kasir/produk.csv`
- `~/.local/share/mesin-kasir/transaksi.csv`

License: MIT
