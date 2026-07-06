"""
Mesin Kasir - Source Version
File: mesin_kasir_source.py
Tujuan: versi sumber (readable) dari aplikasi Mesin Kasir untuk pengembangan lebih lanjut.

Fitur utama:
- Manajemen Produk (Tambah/Edit/Hapus)
- Transaksi Penjualan (keranjang, checkout, cetak/simpan struk)
- Laporan Stok & Penjualan
- Penyimpanan data per-user: ~/.local/share/mesin-kasir/{produk.csv,transaksi.csv}
- Pembacaan/penulisan CSV aman (atomic)
- Validasi input & penanganan error lebih baik
- UI: dialog yang lebih ramah (Enter simpan, Escape tutup), tombol selalu terlihat

Catatan pengembang:
- Untuk distribusi pakai .deb yang disediakan.
- Untuk pengembangan, edit file ini di lokasi sumber Anda dan jalankan python3 mesin_kasir_source.py
"""

import os
import tempfile
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd

# -------- Configuration --------
APP_NAME = "Mesin Kasir"
STORE_NAME = "TOKO MAWAR"
ADDRESS = "Ds. Sumberdadi Kec, Sumbergempol"
PHONE = "08123413074"

# User data directory (per-user)
USER_DATA_DIR = os.path.expanduser("~/.local/share/mesin-kasir")
try:
    os.makedirs(USER_DATA_DIR, exist_ok=True)
except Exception:
    # fallback to current dir if cannot create
    USER_DATA_DIR = os.getcwd()

FILE_PRODUK = os.path.join(USER_DATA_DIR, "produk.csv")
FILE_TRANSAKSI = os.path.join(USER_DATA_DIR, "transaksi.csv")

# -------- Helpers: safe IO --------

def read_csv_safe(path, expected_columns=None):
    """Read CSV safely. Return empty DataFrame with expected columns on error."""
    try:
        df = pd.read_csv(path)
        if expected_columns:
            for col in expected_columns:
                if col not in df.columns:
                    return pd.DataFrame(columns=expected_columns)
        return df
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return pd.DataFrame(columns=expected_columns if expected_columns else [])
    except Exception as e:
        try:
            messagebox.showerror("Error", f"Error reading {path}: {e}")
        except Exception:
            print(f"Error reading {path}: {e}")
        return pd.DataFrame(columns=expected_columns if expected_columns else [])


def safe_to_csv(df, path):
    """Write CSV atomically: write to temp file and replace."""
    dirn = os.path.dirname(path) or "."
    try:
        fd, tmp = tempfile.mkstemp(dir=dirn, suffix='.tmp')
        os.close(fd)
        df.to_csv(tmp, index=False)
        os.replace(tmp, path)
    except Exception as e:
        try:
            messagebox.showerror("Error", f"Error saving {path}: {e}")
        except Exception:
            print(f"Error saving {path}: {e}")


# Initialize CSV files if not present
def inisialisasi_file():
    try:
        if not os.path.exists(FILE_PRODUK):
            pd.DataFrame(columns=["Kode", "Nama", "Harga", "Stok"]).to_csv(FILE_PRODUK, index=False)
        if not os.path.exists(FILE_TRANSAKSI):
            pd.DataFrame(columns=["Tanggal", "Kode_Produk", "Nama", "Jumlah", "Subtotal"]).to_csv(FILE_TRANSAKSI, index=False)
    except Exception as e:
        try:
            messagebox.showerror("Error", f"Error initializing files: {e}")
        except Exception:
            print(f"Error initializing files: {e}")


# -------- Application GUI --------
class AplikasiKasir:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Aplikasi Mesin Kasir - Toko Kecil")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        self.keranjang = []
        self.status_var = tk.StringVar(value="Siap")

        # Style
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        # Build UI
        self.create_menu()
        self.create_ui()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        # File
        menu_file = tk.Menu(menu_bar, tearoff=0)
        menu_file.add_command(label="Refresh Semua Data", command=self.refresh_semua)
        menu_file.add_separator()
        menu_file.add_command(label="Keluar Aplikasi", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=menu_file)
        # Navigasi
        menu_nav = tk.Menu(menu_bar, tearoff=0)
        menu_nav.add_command(label="Manajemen Produk", command=lambda: self.notebook.select(0))
        menu_nav.add_command(label="Transaksi Penjualan", command=lambda: self.notebook.select(1))
        menu_nav.add_command(label="Laporan", command=lambda: self.notebook.select(2))
        menu_bar.add_cascade(label="Navigasi", menu=menu_nav)
        # Bantuan
        menu_help = tk.Menu(menu_bar, tearoff=0)
        menu_help.add_command(label="Tentang Aplikasi", command=self.tampilkan_tentang)
        menu_bar.add_cascade(label="Bantuan", menu=menu_help)
        self.root.config(menu=menu_bar)

    def refresh_semua(self):
        self.refresh_produk()
        self.load_combo_produk()
        self.tampilkan_laporan()
        self.status_var.set("Semua data berhasil diperbarui.")
        messagebox.showinfo("Refresh", "Semua data berhasil diperbarui!")

    def tampilkan_tentang(self):
        info = f"{STORE_NAME}\nAlamat: {ADDRESS}\nTelp: {PHONE}\n\nSistem Kasir Desktop"
        messagebox.showinfo("Tentang Aplikasi", info)

    def create_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text=f"🏪 {STORE_NAME} - APLIKASI MESIN KASIR", font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(pady=10)

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab Produk
        self.tab_produk = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_produk, text="Manajemen Produk")
        self.create_tab_produk()

        # Tab Transaksi
        self.tab_transaksi = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_transaksi, text="Transaksi Penjualan")
        self.create_tab_transaksi()

        # Tab Laporan
        self.tab_laporan = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_laporan, text="Laporan")
        self.create_tab_laporan()

        # Status
        status_bar = tk.Label(self.root, textvariable=self.status_var, bg="#34495e", fg="white", relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # ---------------- Tab Produk ----------------
    def create_tab_produk(self):
        frame_button = tk.Frame(self.tab_produk, bg="#ecf0f1")
        frame_button.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(frame_button, text="➕ Tambah Produk", command=self.dialog_tambah_produk, bg="#27ae60", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_button, text="✏️ Edit Produk", command=self.dialog_edit_produk, bg="#3498db", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_button, text="🗑️ Hapus Produk", command=self.hapus_produk, bg="#e74c3c", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_button, text="🔄 Refresh", command=self.refresh_produk, bg="#95a5a6", fg="white", width=15).pack(side=tk.LEFT, padx=5)

        frame_tabel = tk.Frame(self.tab_produk)
        frame_tabel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar = tk.Scrollbar(frame_tabel)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_produk = ttk.Treeview(frame_tabel, columns=("Kode", "Nama", "Harga", "Stok"), height=20, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree_produk.yview)
        self.tree_produk.column("#0", width=0, stretch=tk.NO)
        self.tree_produk.column("Kode", anchor=tk.W, width=100)
        self.tree_produk.column("Nama", anchor=tk.W, width=300)
        self.tree_produk.column("Harga", anchor=tk.CENTER, width=150)
        self.tree_produk.column("Stok", anchor=tk.CENTER, width=100)
        self.tree_produk.heading("Kode", text="Kode Produk", anchor=tk.W)
        self.tree_produk.heading("Nama", text="Nama Produk", anchor=tk.W)
        self.tree_produk.heading("Harga", text="Harga (Rp)", anchor=tk.CENTER)
        self.tree_produk.heading("Stok", text="Stok", anchor=tk.CENTER)
        self.tree_produk.pack(fill=tk.BOTH, expand=True)

        self.refresh_produk()

    def refresh_produk(self):
        for item in self.tree_produk.get_children():
            self.tree_produk.delete(item)
        df = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
        for _, row in df.iterrows():
            try:
                harga = float(row.get("Harga", 0) if hasattr(row, 'get') else row["Harga"])
            except Exception:
                harga = 0.0
            try:
                stok = int(row.get("Stok", 0) if hasattr(row, 'get') else row["Stok"])
            except Exception:
                stok = 0
            kode = row.get("Kode", "") if hasattr(row, 'get') else row["Kode"]
            nama = row.get("Nama", "") if hasattr(row, 'get') else row["Nama"]
            values = (kode, nama, f"Rp {harga:,.0f}", stok)
            self.tree_produk.insert("", "end", values=values)
        self.status_var.set(f"Total produk: {len(df)}")

    def dialog_tambah_produk(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Tambah Produk")
        dialog.geometry("420x340")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus_force()

        tk.Label(dialog, text="Kode Produk:", font=("Arial", 10)).pack(pady=5)
        entry_kode = tk.Entry(dialog, width=30)
        entry_kode.pack(pady=5)

        tk.Label(dialog, text="Nama Produk:", font=("Arial", 10)).pack(pady=5)
        entry_nama = tk.Entry(dialog, width=30)
        entry_nama.pack(pady=5)

        tk.Label(dialog, text="Harga (Rp):", font=("Arial", 10)).pack(pady=5)
        entry_harga = tk.Entry(dialog, width=30)
        entry_harga.pack(pady=5)

        tk.Label(dialog, text="Stok:", font=("Arial", 10)).pack(pady=5)
        entry_stok = tk.Entry(dialog, width=30)
        entry_stok.pack(pady=5)

        # Fokus awal dan shortcut
        entry_kode.focus_set()
        dialog.bind('<Return>', lambda e: simpan())
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        def simpan():
            kode = entry_kode.get().strip()
            nama = entry_nama.get().strip()
            if not kode or not nama:
                messagebox.showerror("Error", "Kode dan nama tidak boleh kosong!")
                return
            try:
                harga = float(entry_harga.get())
                stok = int(entry_stok.get())
            except ValueError:
                messagebox.showerror("Error", "Harga dan stok harus berupa angka!")
                return
            if harga < 0 or stok < 0:
                messagebox.showerror("Error", "Harga dan stok tidak boleh negatif!")
                return
            df = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
            if kode in df["Kode"].values:
                messagebox.showerror("Error", "Kode produk sudah ada!")
                return
            df = pd.concat([df, pd.DataFrame([[kode, nama, harga, stok]], columns=df.columns)], ignore_index=True)
            safe_to_csv(df, FILE_PRODUK)
            messagebox.showinfo("Sukses", "Produk berhasil ditambahkan!")
            dialog.destroy()
            self.refresh_produk()

        btn_simpan = tk.Button(dialog, text="Simpan", command=simpan, bg="#27ae60", fg="white")
        btn_simpan.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

    def dialog_edit_produk(self):
        selected = self.tree_produk.selection()
        if not selected:
            messagebox.showerror("Error", "Pilih produk terlebih dahulu!")
            return
        item = self.tree_produk.item(selected[0])
        kode = item["values"][0]
        df = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
        filtered = df[df["Kode"] == kode]
        if filtered.empty:
            messagebox.showerror("Error", f"Produk dengan kode {kode} tidak ditemukan!")
            return
        produk = filtered.iloc[0]

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Produk")
        dialog.geometry("420x340")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus_force()

        tk.Label(dialog, text="Kode Produk:", font=("Arial", 10)).pack(pady=5)
        entry_kode = tk.Entry(dialog, width=30)
        entry_kode.insert(0, kode)
        entry_kode.config(state="readonly")
        entry_kode.pack(pady=5)

        tk.Label(dialog, text="Nama Produk:", font=("Arial", 10)).pack(pady=5)
        entry_nama = tk.Entry(dialog, width=30)
        entry_nama.insert(0, produk["Nama"])
        entry_nama.pack(pady=5)

        tk.Label(dialog, text="Harga (Rp):", font=("Arial", 10)).pack(pady=5)
        entry_harga = tk.Entry(dialog, width=30)
        entry_harga.insert(0, str(produk["Harga"]))
        entry_harga.pack(pady=5)

        tk.Label(dialog, text="Stok:", font=("Arial", 10)).pack(pady=5)
        entry_stok = tk.Entry(dialog, width=30)
        entry_stok.insert(0, str(int(produk["Stok"])))
        entry_stok.pack(pady=5)

        # Fokus dan shortcut
        entry_nama.focus_set()
        dialog.bind('<Return>', lambda e: simpan())
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        def simpan():
            nama = entry_nama.get().strip()
            if not nama:
                messagebox.showerror("Error", "Nama tidak boleh kosong!")
                return
            try:
                harga = float(entry_harga.get())
                stok = int(entry_stok.get())
            except ValueError:
                messagebox.showerror("Error", "Harga dan stok harus berupa angka!")
                return
            df = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
            matches = df[df["Kode"] == kode].index
            if matches.empty:
                messagebox.showerror("Error", f"Produk dengan kode {kode} tidak ditemukan saat menyimpan!")
                dialog.destroy()
                return
            idx = matches[0]
            df.loc[idx] = [kode, nama, harga, stok]
            safe_to_csv(df, FILE_PRODUK)
            messagebox.showinfo("Sukses", "Produk berhasil diedit!")
            dialog.destroy()
            self.refresh_produk()

        btn_simpan = tk.Button(dialog, text="Simpan", command=simpan, bg="#3498db", fg="white")
        btn_simpan.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

    def hapus_produk(self):
        selected = self.tree_produk.selection()
        if not selected:
            messagebox.showerror("Error", "Pilih produk terlebih dahulu!")
            return
        item = self.tree_produk.item(selected[0])
        kode = item["values"][0]
        if messagebox.askyesno("Konfirmasi", f"Hapus produk {kode}?"):
            df = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
            df = df[df["Kode"] != kode]
            safe_to_csv(df, FILE_PRODUK)
            messagebox.showinfo("Sukses", "Produk berhasil dihapus!")
            self.refresh_produk()

    # ---------------- Tab Transaksi ----------------
    def create_tab_transaksi(self):
        frame_utama = tk.Frame(self.tab_transaksi)
        frame_utama.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        frame_atas = tk.LabelFrame(frame_utama, text="Pilih Produk", font=("Arial", 10, "bold"))
        frame_atas.pack(fill=tk.X, pady=(0, 10))

        tk.Label(frame_atas, text="Produk:", font=("Arial", 10)).pack(side=tk.LEFT, padx=10, pady=10)
        self.combo_produk = ttk.Combobox(frame_atas, state="readonly", width=40)
        self.combo_produk.pack(side=tk.LEFT, padx=5, pady=10)

        tk.Label(frame_atas, text="Jumlah:", font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        self.spin_jumlah = tk.Spinbox(frame_atas, from_=1, to=999, width=10)
        self.spin_jumlah.delete(0, tk.END)
        self.spin_jumlah.insert(0, "1")
        self.spin_jumlah.pack(side=tk.LEFT, padx=5, pady=10)

        tk.Button(frame_atas, text="➕ Tambah ke Keranjang", command=self.tambah_ke_keranjang, bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=10, pady=10)
        self.load_combo_produk()

        frame_keranjang = tk.LabelFrame(frame_utama, text="Keranjang Belanja", font=("Arial", 10, "bold"))
        frame_keranjang.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = tk.Scrollbar(frame_keranjang)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_keranjang = ttk.Treeview(frame_keranjang, columns=("Kode", "Nama", "Jumlah", "Harga", "Subtotal"), height=10, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree_keranjang.yview)
        self.tree_keranjang.column("#0", width=0, stretch=tk.NO)
        self.tree_keranjang.column("Kode", anchor=tk.W, width=80)
        self.tree_keranjang.column("Nama", anchor=tk.W, width=200)
        self.tree_keranjang.column("Jumlah", anchor=tk.CENTER, width=80)
        self.tree_keranjang.column("Harga", anchor="e", width=120)
        self.tree_keranjang.column("Subtotal", anchor="e", width=150)
        self.tree_keranjang.heading("Kode", text="Kode")
        self.tree_keranjang.heading("Nama", text="Nama")
        self.tree_keranjang.heading("Jumlah", text="Jumlah")
        self.tree_keranjang.heading("Harga", text="Harga")
        self.tree_keranjang.heading("Subtotal", text="Subtotal")
        self.tree_keranjang.pack(fill=tk.BOTH, expand=True)

        frame_bawah = tk.Frame(frame_utama)
        frame_bawah.pack(fill=tk.X, pady=10)
        tk.Label(frame_bawah, text="Total:", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)
        self.label_total = tk.Label(frame_bawah, text="Rp 0,-", font=("Arial", 14, "bold"), fg="#e74c3c")
        self.label_total.pack(side=tk.LEFT, padx=10)

        frame_tombol = tk.Frame(frame_utama)
        frame_tombol.pack(fill=tk.X, pady=10)
        tk.Button(frame_tombol, text="🗑️ Hapus Item", command=self.hapus_dari_keranjang, bg="#e67e22", fg="white", width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_tombol, text="✅ Selesaikan Transaksi", command=self.selesaikan_transaksi, bg="#27ae60", fg="white", width=20).pack(side=tk.LEFT, padx=5)

    def load_combo_produk(self):
        df = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
        produk_list = [f"{row['Kode']} - {row['Nama']}" for _, row in df.iterrows()]
        self.combo_produk.config(values=produk_list)

    def tambah_ke_keranjang(self):
        df = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
        if df.empty:
            messagebox.showerror("Error", "Tidak ada produk!")
            return
        if not self.combo_produk.get():
            messagebox.showerror("Error", "Pilih produk!")
            return
        kode = self.combo_produk.get().split(" - ")[0]
        try:
            jumlah = int(self.spin_jumlah.get())
        except ValueError:
            messagebox.showerror("Error", "Jumlah harus berupa angka!")
            return
        if jumlah <= 0:
            messagebox.showerror("Error", "Jumlah harus lebih dari 0!")
            return
        filtered = df[df["Kode"] == kode]
        if filtered.empty:
            messagebox.showerror("Error", f"Produk dengan kode {kode} tidak ditemukan!")
            return
        produk = filtered.iloc[0]
        try:
            stok_tersedia = int(produk.get("Stok", 0) if hasattr(produk, 'get') else produk["Stok"])
        except Exception:
            stok_tersedia = 0
        if stok_tersedia < jumlah:
            messagebox.showerror("Error", f"Stok tidak mencukupi! Tersedia: {stok_tersedia}")
            return
        try:
            harga_produk = float(produk.get("Harga", 0) if hasattr(produk, 'get') else produk["Harga"])
        except Exception:
            harga_produk = 0.0
        self.keranjang.append({
            "Kode": kode,
            "Nama": produk.get("Nama", "") if hasattr(produk, 'get') else produk["Nama"],
            "Jumlah": jumlah,
            "Harga": harga_produk,
            "Subtotal": harga_produk * jumlah
        })
        self.update_keranjang()
        messagebox.showinfo("Sukses", f"{produk.get('Nama', produk['Nama']) if hasattr(produk, 'get') else produk['Nama']} ditambahkan ke keranjang!")

    def update_keranjang(self):
        for item in self.tree_keranjang.get_children():
            self.tree_keranjang.delete(item)
        total = 0
        for item in self.keranjang:
            values = (item["Kode"], item["Nama"], item["Jumlah"], f"Rp {item['Harga']:,.0f}", f"Rp {item['Subtotal']:,.2f}")
            self.tree_keranjang.insert("", "end", values=values)
            total += item["Subtotal"]
        self.label_total.config(text=f"Rp {total:,.2f}")

    def hapus_dari_keranjang(self):
        selected = self.tree_keranjang.selection()
        if not selected:
            messagebox.showerror("Error", "Pilih item keranjang!")
            return
        idx = self.tree_keranjang.index(selected[0])
        self.keranjang.pop(idx)
        self.update_keranjang()

    def buat_struk(self, tanggal):
        total = sum(item["Subtotal"] for item in self.keranjang)
        struk = ""
        struk += "=" * 50 + "\n"
        struk += f"{STORE_NAME:^50}\n"
        struk += f"{ADDRESS:^50}\n"
        struk += f"{PHONE:^50}\n"
        struk += "=" * 50 + "\n\n"
        struk += f"Tanggal: {tanggal}\n"
        struk += "-" * 50 + "\n"
        struk += f"{'Nama':<25} {'Jumlah':>8} {'Harga':>15}\n"
        struk += "-" * 50 + "\n"
        for item in self.keranjang:
            struk += f"{item['Nama']:<25} {item['Jumlah']:>8} Rp {item['Subtotal']:>12,.2f}\n"
        struk += "-" * 50 + "\n"
        struk += f"{'TOTAL':<25} {'':>8} Rp {total:>12,.2f}\n"
        struk += "=" * 50 + "\n"
        struk += "        Terima kasih atas pembelian Anda!\n"
        struk += "=" * 50 + "\n"
        return struk

    def cetak_bukti(self, struk, tanggal):
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(struk)
                temp_file = f.name
            try:
                subprocess.run(['lp', temp_file], check=True, capture_output=True)
                messagebox.showinfo("Cetak", "Bukti transaksi berhasil dicetak!")
            except FileNotFoundError:
                save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], initialfile=f"bukti_{tanggal.replace(':', '-').replace(' ', '_')}.txt")
                if save_path:
                    with open(save_path, 'w') as f:
                        f.write(struk)
                    messagebox.showinfo("Simpan", f"Bukti disimpan di: {save_path}")
            except subprocess.CalledProcessError as e:
                try:
                    stderr = e.stderr.decode() if e.stderr else str(e)
                except Exception:
                    stderr = str(e)
                save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], initialfile=f"bukti_{tanggal.replace(':', '-').replace(' ', '_')}.txt")
                if save_path:
                    with open(save_path, 'w') as f:
                        f.write(struk)
                    messagebox.showwarning("Cetak Gagal", f"Perintah cetak gagal. Pesan: {stderr}\nBukti disimpan di: {save_path}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            messagebox.showerror("Error", f"Error saat cetak: {e}")

    def selesaikan_transaksi(self):
        if not self.keranjang:
            messagebox.showerror("Error", "Keranjang kosong!")
            return
        df_produk = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
        df_transaksi = read_csv_safe(FILE_TRANSAKSI, expected_columns=["Tanggal", "Kode_Produk", "Nama", "Jumlah", "Subtotal"])
        tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in self.keranjang:
            if df_produk[df_produk["Kode"] == item["Kode"]].empty:
                messagebox.showerror("Error", f"Produk {item['Kode']} tidak ditemukan. Transaksi dibatalkan.")
                return
        for item in self.keranjang:
            df_transaksi = pd.concat([df_transaksi, pd.DataFrame([[tanggal, item["Kode"], item["Nama"], item["Jumlah"], item["Subtotal"]]], columns=df_transaksi.columns)], ignore_index=True)
            matches = df_produk[df_produk["Kode"] == item["Kode"]].index
            if matches.empty:
                messagebox.showerror("Error", f"Produk {item['Kode']} tidak ditemukan saat update stok. Transaksi dibatalkan.")
                return
            idx = matches[0]
            try:
                current_stok = int(df_produk.loc[idx, "Stok"])
            except Exception:
                current_stok = 0
            df_produk.loc[idx, "Stok"] = current_stok - int(item["Jumlah"])
        safe_to_csv(df_transaksi, FILE_TRANSAKSI)
        safe_to_csv(df_produk, FILE_PRODUK)

        # Buat struk
        struk = self.buat_struk(tanggal)
        # Kosongkan keranjang agar siap transaksi baru
        self.keranjang = []
        self.update_keranjang()
        self.refresh_produk()
        self.load_combo_produk()

        # Tampilkan struk dan opsi cetak/simpan
        dialog = tk.Toplevel(self.root)
        dialog.title("Transaksi Berhasil")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        text_struk = tk.Text(dialog, font=("Courier", 9), bg="white")
        text_struk.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_struk.insert("1.0", struk)
        text_struk.config(state="disabled")
        frame_btn = tk.Frame(dialog)
        frame_btn.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(frame_btn, text="🖨️ Cetak Bukti", bg="#27ae60", fg="white", command=lambda: self.cetak_bukti(struk, tanggal)).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_btn, text="💾 Simpan", bg="#3498db", fg="white", command=lambda: self.simpan_struk(struk, tanggal)).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_btn, text="Tutup", bg="#95a5a6", fg="white", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def simpan_struk(self, struk, tanggal):
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], initialfile=f"bukti_{tanggal.replace(':', '-').replace(' ', '_')}.txt")
        if save_path:
            with open(save_path, 'w') as f:
                f.write(struk)
            messagebox.showinfo("Sukses", f"Bukti berhasil disimpan!\n{save_path}")

    # ---------------- Laporan ----------------
    def create_tab_laporan(self):
        frame_pilih = tk.Frame(self.tab_laporan, bg="#ecf0f1")
        frame_pilih.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(frame_pilih, text="Pilih Laporan:", font=("Arial", 10), bg="#ecf0f1").pack(side=tk.LEFT, padx=10)
        self.combo_laporan = ttk.Combobox(frame_pilih, values=["Laporan Stok", "Laporan Penjualan"], state="readonly", width=30)
        self.combo_laporan.set("Laporan Stok")
        self.combo_laporan.pack(side=tk.LEFT, padx=5)
        self.combo_laporan.bind("<<ComboboxSelected>>", lambda e: self.tampilkan_laporan())
        tk.Button(frame_pilih, text="💾 Export CSV", command=self.export_csv, bg="#3498db", fg="white").pack(side=tk.LEFT, padx=5)
        frame_tabel = tk.Frame(self.tab_laporan)
        frame_tabel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar = tk.Scrollbar(frame_tabel)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_laporan = ttk.Treeview(frame_tabel, height=20, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree_laporan.yview)
        self.tree_laporan.pack(fill=tk.BOTH, expand=True)
        self.tampilkan_laporan()

    def tampilkan_laporan(self):
        for item in self.tree_laporan.get_children():
            self.tree_laporan.delete(item)
        pilihan = self.combo_laporan.get()
        if pilihan == "Laporan Stok":
            self.tampilkan_laporan_stok()
        else:
            self.tampilkan_laporan_penjualan()

    def tampilkan_laporan_stok(self):
        df = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
        self.tree_laporan["columns"] = ("Kode", "Nama", "Harga", "Stok")
        for col in self.tree_laporan["columns"]:
            self.tree_laporan.column(col, width=100)
            self.tree_laporan.heading(col, text=col)
        for _, row in df.iterrows():
            values = (row["Kode"], row["Nama"], f"Rp {row['Harga']:,.0f}", int(row["Stok"]))
            self.tree_laporan.insert("", "end", values=values)
        self.status_var.set(f"Total produk: {len(df)}")

    def tampilkan_laporan_penjualan(self):
        df = read_csv_safe(FILE_TRANSAKSI, expected_columns=["Tanggal", "Kode_Produk", "Nama", "Jumlah", "Subtotal"])
        self.tree_laporan["columns"] = ("Tanggal", "Kode", "Nama", "Jumlah", "Subtotal")
        for col in self.tree_laporan["columns"]:
            self.tree_laporan.column(col, width=150)
            self.tree_laporan.heading(col, text=col)
        for _, row in df.iterrows():
            values = (row["Tanggal"], row["Kode_Produk"], row["Nama"], int(row["Jumlah"]), f"Rp {row['Subtotal']:,.2f}")
            self.tree_laporan.insert("", "end", values=values)
        self.status_var.set(f"Total transaksi: {len(df)}")

    def export_csv(self):
        pilihan = self.combo_laporan.get()
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        if pilihan == "Laporan Stok":
            df = read_csv_safe(FILE_PRODUK, expected_columns=["Kode", "Nama", "Harga", "Stok"])
            df.to_csv(file_path, index=False)
        else:
            df = read_csv_safe(FILE_TRANSAKSI, expected_columns=["Tanggal", "Kode_Produk", "Nama", "Jumlah", "Subtotal"])
            df.to_csv(file_path, index=False)
        messagebox.showinfo("Sukses", f"File berhasil disimpan: {file_path}")


if __name__ == "__main__":
    inisialisasi_file()
    root = tk.Tk()
    app = AplikasiKasir(root)
    root.mainloop()
