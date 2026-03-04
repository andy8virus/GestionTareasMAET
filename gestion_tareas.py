#!/usr/bin/env python3
"""
Gestión de Tareas MAET - Arquitectura por Roles
Dashboard Usuario + Panel de Administración
"""

import sys
import os
import shutil
from tkinter import messagebox, filedialog, Frame as TkFrame, Button as TkButton
# DPI en Windows: intentar alta resolución; fallback si falla (ej. ARM64)
if sys.platform == "win32":
    try:
        from ctypes import windll
        try:
            windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import customtkinter as ctk
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

try:
    import winsound
except ImportError:
    winsound = None

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from tkcalendar import DateEntry
    TKCALENDAR_OK = True
except ImportError:
    TKCALENDAR_OK = False

# Configuración
APP_TITLE = "Gestión de Tareas MAET"
DB_FILE = "tareas.db"
CLAVE_ADMIN = "MAET2026"
USUARIO_ADMIN = "admin"
ASSETS_DIR = Path(__file__).parent / "assets"
FONDO_DEFAULT = ASSETS_DIR / "fondo_dashboard.jpg"

# Estados de tarea
ESTADO_PENDIENTE = "Pendiente"
ESTADO_FUERA_PLAZO = "Fuera de Plazo"
ESTADO_TERMINADA = "Terminada"
ESTADO_NO_REALIZADA = "No Realizada"

ESTADOS_TODOS = [ESTADO_PENDIENTE, ESTADO_FUERA_PLAZO, ESTADO_TERMINADA, ESTADO_NO_REALIZADA]

# Colores por estado
COLOR_ESTADO = {
    ESTADO_PENDIENTE: "#CA8A04",
    ESTADO_FUERA_PLAZO: "#DC2626",
    ESTADO_TERMINADA: "#16A34A",
    ESTADO_NO_REALIZADA: "#EA580C",
}

COLORES = {
    "fondo": "#F8FAFC",
    "card": "#FFFFFF",
    "texto": "#334155",
    "texto_secundario": "#64748B",
    "acento": "#0EA5E9",
    "verde": "#16A34A",
    "amarillo": "#CA8A04",
    "rojo": "#DC2626",
    "naranja": "#EA580C",
    "borde": "#E2E8F0",
}

FORMATO_DATETIME = "%d/%m/%Y %H:%M"
FORMATO_DATETIME_DISPLAY = "DD/MM/AAAA HH:MM"
FORMATO_RELOJ = "%H:%M:%S  %d/%m/%Y"


def crear_reloj(parent, font=("Segoe UI", 11), **kwargs):
    """Crea un label de reloj sincronizado con el PC."""
    lbl = ctk.CTkLabel(parent, text="", font=font, text_color=COLORES.get("texto_secundario", "#64748B"), **kwargs)

    def _actualizar():
        if lbl.winfo_exists():
            lbl.configure(text=datetime_pc().strftime(FORMATO_RELOJ))
            lbl.after(1000, _actualizar)

    _actualizar()
    return lbl


# Botones visibles en modales (tk.Button garantiza texto legible en todas las plataformas)
def _crear_btns_modal(contenedor, on_aceptar, on_cancelar, texto_aceptar="✓ Confirmar cambio"):
    f = TkFrame(contenedor, bg=COLORES["card"])
    b1 = TkButton(f, text=texto_aceptar, command=on_aceptar, font=("Segoe UI", 12, "bold"),
                  bg="#15803D", fg="white", activebackground="#166534", activeforeground="white",
                  relief="raised", bd=2, padx=24, pady=10, cursor="hand2")
    b2 = TkButton(f, text="✗ Cancelar", command=on_cancelar, font=("Segoe UI", 12, "bold"),
                  bg="#64748B", fg="white", activebackground="#475569", activeforeground="white",
                  relief="raised", bd=2, padx=24, pady=10, cursor="hand2")
    b1.pack(side="left", padx=(0, 12))
    b2.pack(side="left")
    return f


def datetime_pc():
    return datetime.now()


def parsear_datetime(texto):
    texto = texto.strip()
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(texto, fmt)
            if fmt == "%d/%m/%Y":
                dt = dt.replace(hour=23, minute=59, second=0)
            return dt
        except ValueError:
            continue
    return None


def _tarea_coincide_fecha(tarea, fecha_dia):
    """True si la tarea toca el día dado (inicio o término)."""
    f_i = parsear_datetime(tarea.get("fecha_hora_inicio", ""))
    f_t = parsear_datetime(tarea.get("fecha_hora_termino", ""))
    d = fecha_dia.date()
    if f_i and f_i.date() == d:
        return True
    if f_t and f_t.date() == d:
        return True
    return False


def calcular_color_tarea(tarea):
    """Pendiente=Amarillo, Fuera de Plazo=Rojo, Terminada=Verde, No Realizada=Naranja."""
    estado = tarea.get("estado", ESTADO_PENDIENTE)
    if estado in COLOR_ESTADO:
        return COLOR_ESTADO[estado]
    if estado == "Lista":
        return COLORES["verde"]
    dt_termino = parsear_datetime(tarea.get("fecha_hora_termino", ""))
    if dt_termino and datetime_pc() > dt_termino and estado == ESTADO_PENDIENTE:
        return COLOR_ESTADO[ESTADO_FUERA_PLAZO]
    return COLOR_ESTADO.get(estado, COLORES["amarillo"])


class BaseDatos:
    def __init__(self):
        self.ruta_db = Path(__file__).parent / DB_FILE
        ASSETS_DIR.mkdir(exist_ok=True)
        self._inicializar_db()

    def _conectar(self):
        return sqlite3.connect(str(self.ruta_db))

    def _inicializar_db(self):
        with self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    codigo TEXT UNIQUE,
                    clave TEXT NOT NULL,
                    es_admin INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tareas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    responsable_id INTEGER,
                    responsable_nombre TEXT,
                    fecha_hora_inicio TEXT,
                    fecha_hora_termino TEXT,
                    detalles TEXT,
                    estado TEXT DEFAULT 'Pendiente',
                    archivada INTEGER DEFAULT 0,
                    modificado_por INTEGER,
                    fecha_modificacion TEXT,
                    fecha_creacion TEXT,
                    nota_cierre TEXT,
                    FOREIGN KEY (responsable_id) REFERENCES usuarios(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config_dashboard (
                    clave TEXT PRIMARY KEY,
                    valor TEXT
                )
            """)
            self._migrar_columnas(conn)
            conn.commit()
            self._crear_admin_si_no_existe(conn)
            self._insertar_config_default(conn)

    def _migrar_columnas(self, conn):
        for tbl, cols in [
            ("usuarios", [("codigo", "TEXT")]),
            ("tareas", [("archivada", "INTEGER DEFAULT 0"), ("responsable_id", "INTEGER"), ("responsable_nombre", "TEXT")]),
        ]:
            try:
                cur = conn.execute(f"PRAGMA table_info({tbl})")
                existing = [r[1] for r in cur.fetchall()]
                for col, def_ in cols:
                    if col not in existing:
                        conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {def_}")
            except sqlite3.OperationalError:
                pass

    def _crear_admin_si_no_existe(self, conn):
        cur = conn.execute("SELECT id FROM usuarios WHERE es_admin=1").fetchone()
        if cur:
            conn.execute("UPDATE usuarios SET codigo=?, clave=? WHERE id=?", ("ADMIN", CLAVE_ADMIN, cur[0]))
        else:
            conn.execute(
                "INSERT INTO usuarios (nombre, codigo, clave, es_admin) VALUES (?, ?, ?, 1)",
                (USUARIO_ADMIN, "ADMIN", CLAVE_ADMIN),
            )
        conn.commit()

    def _insertar_config_default(self, conn):
        conn.execute(
            "INSERT OR IGNORE INTO config_dashboard (clave, valor) VALUES ('tarjeta', 'Bienvenido al Dashboard MAET')"
        )
        conn.execute(
            "INSERT OR IGNORE INTO config_dashboard (clave, valor) VALUES ('fondo', '')"
        )
        self._migrar_responsable_id(conn)
        conn.commit()

    def _migrar_responsable_id(self, conn):
        try:
            cur = conn.execute("PRAGMA table_info(tareas)")
            cols = [r[1] for r in cur.fetchall()]
            if "responsable_nombre" not in cols:
                conn.execute("ALTER TABLE tareas ADD COLUMN responsable_nombre TEXT")
            if "responsable" in cols:
                conn.execute("UPDATE tareas SET responsable_nombre = COALESCE(responsable_nombre, responsable) WHERE responsable IS NOT NULL")
            for row in conn.execute("SELECT id, responsable_nombre FROM tareas WHERE responsable_id IS NULL AND responsable_nombre IS NOT NULL").fetchall():
                uid = conn.execute("SELECT id FROM usuarios WHERE nombre=?", (row[1],)).fetchone()
                if uid:
                    conn.execute("UPDATE tareas SET responsable_id=? WHERE id=?", (uid[0], row[0]))
            cur = conn.execute("PRAGMA table_info(usuarios)")
            ucols = [r[1] for r in cur.fetchall()]
            if "codigo" in ucols:
                for row in conn.execute("SELECT id, nombre FROM usuarios WHERE codigo IS NULL OR codigo=''").fetchall():
                    cod = ((row[1] or "U")[:8].upper()).replace(" ", "_")
                    conn.execute("UPDATE usuarios SET codigo=? WHERE id=?", (cod, row[0]))
        except sqlite3.OperationalError:
            pass

    def login_usuario(self, codigo, clave):
        with self._conectar() as conn:
            row = conn.execute(
                "SELECT id, nombre FROM usuarios WHERE codigo=? AND clave=? AND es_admin=0",
                (codigo.strip(), clave.strip())
            ).fetchone()
            return (row[0], row[1]) if row else None

    def login_admin(self, usuario, clave):
        with self._conectar() as conn:
            row = conn.execute(
                "SELECT id FROM usuarios WHERE (nombre=? OR codigo=?) AND clave=? AND es_admin=1",
                (usuario.strip(), usuario.strip(), clave.strip())
            ).fetchone()
            return row[0] if row else None

    def listar_usuarios(self):
        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(
                "SELECT id, nombre, codigo, es_admin FROM usuarios ORDER BY nombre"
            ).fetchall()]

    def crear_usuario(self, nombre, codigo, clave):
        cod = (codigo or "").strip() or (nombre or "U").upper()[:8].replace(" ", "_")
        with self._conectar() as conn:
            conn.execute(
                "INSERT INTO usuarios (nombre, codigo, clave, es_admin) VALUES (?, ?, ?, 0)",
                (nombre, cod, clave)
            )
            conn.commit()

    def actualizar_usuario(self, id_u, nombre, codigo, clave):
        with self._conectar() as conn:
            if clave:
                conn.execute(
                    "UPDATE usuarios SET nombre=?, codigo=?, clave=? WHERE id=?",
                    (nombre, codigo or nombre.upper()[:8], clave, id_u)
                )
            else:
                conn.execute(
                    "UPDATE usuarios SET nombre=?, codigo=? WHERE id=?",
                    (nombre, codigo or nombre.upper()[:8], id_u)
                )
            conn.commit()

    def eliminar_usuario(self, id_u):
        with self._conectar() as conn:
            conn.execute("DELETE FROM usuarios WHERE id=? AND es_admin=0", (id_u,))
            conn.commit()

    def obtener_usuario(self, id_u):
        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            r = conn.execute("SELECT * FROM usuarios WHERE id=?", (id_u,)).fetchone()
            return dict(r) if r else None

    def get_config(self, clave):
        with self._conectar() as conn:
            r = conn.execute("SELECT valor FROM config_dashboard WHERE clave=?", (clave,)).fetchone()
            return r[0] if r else ""

    def set_config(self, clave, valor):
        with self._conectar() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO config_dashboard (clave, valor) VALUES (?, ?)",
                (clave, str(valor))
            )
            conn.commit()

    def tareas_por_usuario(self, usuario_id, incluir_archivadas=False):
        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            arch = "" if incluir_archivadas else " AND (archivada IS NULL OR archivada=0)"
            rows = conn.execute(
                f"SELECT * FROM tareas WHERE responsable_id=?{arch} ORDER BY fecha_hora_termino",
                (usuario_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def listar_tareas_admin(self, incluir_archivadas=False):
        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            if incluir_archivadas:
                rows = conn.execute("SELECT * FROM tareas ORDER BY fecha_hora_termino").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tareas WHERE (archivada IS NULL OR archivada=0) ORDER BY fecha_hora_termino"
                ).fetchall()
            return [dict(r) for r in rows]

    def insertar_tarea(self, nombre, resp_id, resp_nombre, fecha_i, fecha_t, detalles, id_admin):
        ahora = datetime_pc().strftime("%Y-%m-%d %H:%M")
        with self._conectar() as conn:
            conn.execute(
                """INSERT INTO tareas (nombre, responsable_id, responsable_nombre, fecha_hora_inicio,
                   fecha_hora_termino, detalles, estado, archivada, modificado_por, fecha_modificacion, fecha_creacion)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)""",
                (nombre, resp_id, resp_nombre, fecha_i, fecha_t, detalles, ESTADO_PENDIENTE,
                 id_admin, ahora, ahora)
            )
            conn.commit()

    def actualizar_tarea(self, id_t, nombre, resp_id, resp_nombre, fecha_i, fecha_t, detalles, estado, id_user, nota=""):
        ahora = datetime_pc().strftime("%Y-%m-%d %H:%M")
        with self._conectar() as conn:
            conn.execute(
                """UPDATE tareas SET nombre=?, responsable_id=?, responsable_nombre=?, fecha_hora_inicio=?,
                   fecha_hora_termino=?, detalles=?, estado=?, modificado_por=?, fecha_modificacion=?, nota_cierre=? WHERE id=?""",
                (nombre, resp_id, resp_nombre, fecha_i, fecha_t, detalles, estado, id_user, ahora, nota or "", id_t)
            )
            conn.commit()

    def actualizar_estado_tarea(self, id_tarea, estado, id_usuario, nota=""):
        ahora = datetime_pc().strftime("%Y-%m-%d %H:%M")
        with self._conectar() as conn:
            conn.execute(
                "UPDATE tareas SET estado=?, modificado_por=?, fecha_modificacion=?, nota_cierre=? WHERE id=?",
                (estado, id_usuario, ahora, nota or "", id_tarea)
            )
            conn.commit()

    def archivar_tarea(self, id_tarea, archivada=True):
        with self._conectar() as conn:
            conn.execute("UPDATE tareas SET archivada=? WHERE id=?", (1 if archivada else 0, id_tarea))
            conn.commit()

    def eliminar_tarea(self, id_tarea):
        with self._conectar() as conn:
            conn.execute("DELETE FROM tareas WHERE id=?", (id_tarea,))
            conn.commit()

    def obtener_tarea(self, id_tarea):
        with self._conectar() as conn:
            conn.row_factory = sqlite3.Row
            r = conn.execute("SELECT * FROM tareas WHERE id=?", (id_tarea,)).fetchone()
            return dict(r) if r else None

    def estadisticas_por_estado(self, fecha_ini=None, fecha_fin=None, usuario_id=None):
        with self._conectar() as conn:
            where, params = [], []
            if fecha_ini:
                where.append("fecha_hora_termino >= ?")
                params.append(fecha_ini)
            if fecha_fin:
                where.append("fecha_hora_termino <= ?")
                params.append(fecha_fin)
            if usuario_id:
                where.append("responsable_id = ?")
                params.append(usuario_id)
            w = " AND " + " AND ".join(where) if where else ""
            rows = conn.execute(
                f"SELECT estado, COUNT(*) as c FROM tareas WHERE (archivada IS NULL OR archivada=0){w} GROUP BY estado",
                params
            ).fetchall()
            return dict(rows)

    def estadisticas_por_usuario(self):
        with self._conectar() as conn:
            rows = conn.execute(
                """SELECT responsable_nombre, COUNT(*) as c FROM tareas
                   WHERE (archivada IS NULL OR archivada=0) AND responsable_nombre IS NOT NULL
                   GROUP BY responsable_nombre"""
            ).fetchall()
            return dict(rows)

    def estadisticas_por_fecha(self, agrupar="mes"):
        with self._conectar() as conn:
            rows = conn.execute(
                "SELECT fecha_hora_termino, COUNT(*) as c FROM tareas WHERE (archivada IS NULL OR archivada=0)"
            ).fetchall()
            from collections import defaultdict
            grupos = defaultdict(int)
            for fstr, c in rows:
                if not fstr:
                    continue
                dt = parsear_datetime(fstr)
                if not dt:
                    continue
                if agrupar == "dia":
                    k = dt.strftime("%d/%m/%Y")
                elif agrupar == "mes":
                    k = dt.strftime("%m/%Y")
                else:
                    k = str(dt.year)
                grupos[k] += c
            return dict(grupos)


class SemáforoCircular(ctk.CTkFrame):
    def __init__(self, parent, color, size=28, **kwargs):
        super().__init__(parent, width=size, height=size, fg_color=color,
                         corner_radius=size // 2, **kwargs)
        self.pack_propagate(False)


class ModalEstadoTarea(ctk.CTkToplevel):
    """Modal para que el usuario seleccione estado y agregue notas (sin pedir contraseña)."""

    def __init__(self, parent, nombre_tarea, **kwargs):
        super().__init__(parent, **kwargs)
        self.title("Actualizar Estado")
        self.resultado = None  # (estado, nota)
        self._configurar(nombre_tarea)

    def _configurar(self, nombre_tarea):
        self.geometry("420x400")
        self.resizable(True, True)
        self.minsize(400, 380)
        self.transient(self.master)
        self.grab_set()
        self.configure(fg_color=COLORES["card"])
        crear_reloj(self, font=("Segoe UI", 9)).pack(anchor="e", padx=24, pady=(12, 0))
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=24, pady=20)
        ctk.CTkLabel(f, text=f"Tarea: {nombre_tarea}", font=("Segoe UI Semibold", 14),
                     text_color=COLORES["texto"]).pack(anchor="w")
        ctk.CTkLabel(f, text="Nuevo estado:", font=("Segoe UI", 11),
                     text_color=COLORES["texto_secundario"]).pack(anchor="w", pady=(16, 4))
        self.combo_estado = ctk.CTkOptionMenu(f, values=[ESTADO_TERMINADA, ESTADO_NO_REALIZADA],
                                             width=220, height=40, font=("Segoe UI", 12), corner_radius=8)
        self.combo_estado.pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(f, text="Notas (opcional):", font=("Segoe UI", 11),
                     text_color=COLORES["texto_secundario"]).pack(anchor="w", pady=(12, 4))
        self.txt_notas = ctk.CTkTextbox(f, height=70, font=("Segoe UI", 11), corner_radius=8)
        self.txt_notas.pack(fill="x", pady=(0, 24))
        # Botones visibles con texto legible (tk.Button)
        btn_f = _crear_btns_modal(self, self._aceptar, self._cancelar, "✓ Confirmar cambio")
        btn_f.pack(fill="x", padx=24, pady=(0, 20))

    def _aceptar(self):
        self.resultado = (self.combo_estado.get(), self.txt_notas.get("1.0", "end").strip())
        self.destroy()

    def _cancelar(self):
        self.resultado = None
        self.destroy()


# --- PANTALLA INICIAL: Login por pestañas ---
class PantallaLogin(ctk.CTkFrame):
    def __init__(self, parent, on_usuario, on_admin, **kwargs):
        super().__init__(parent, fg_color=COLORES["fondo"], **kwargs)
        self.on_usuario = on_usuario
        self.on_admin = on_admin
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._crear_ui()

    def _crear_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Gestión de Tareas MAET", font=("Segoe UI Semibold", 22),
                     text_color=COLORES["texto"]).grid(row=0, column=0, pady=(24, 16))
        crear_reloj(self, font=("Segoe UI", 10)).grid(row=0, column=1, padx=20, pady=(24, 16), sticky="e")
        self.tabview = ctk.CTkTabview(self, width=400, height=320, fg_color=COLORES["card"])
        self.tabview.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 24))
        self.tabview.add("Usuario")
        self.tabview.add("Administrador")
        self.tabview.set("Usuario")
        self._tab_usuario()
        self._tab_admin()

    def _tab_usuario(self):
        tab = self.tabview.tab("Usuario")
        tab.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tab, text="Ingrese código y contraseña:", font=("Segoe UI", 11),
                     text_color=COLORES["texto_secundario"]).grid(row=0, column=0, padx=20, pady=(20, 8), sticky="w")
        self.ent_codigo = ctk.CTkEntry(tab, height=40, font=("Segoe UI", 12), corner_radius=8, placeholder_text="Código")
        self.ent_codigo.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")
        self.ent_codigo.bind("<Return>", lambda e: self.ent_clave_usuario.focus())
        self.ent_clave_usuario = ctk.CTkEntry(tab, height=40, show="•", font=("Segoe UI", 12), corner_radius=8,
                                              placeholder_text="Contraseña")
        self.ent_clave_usuario.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.ent_clave_usuario.bind("<Return>", lambda e: self._login_usuario())
        ctk.CTkButton(tab, text="Entrar", command=self._login_usuario,
                      height=44, fg_color=COLORES["acento"], corner_radius=10
                      ).grid(row=3, column=0, padx=20, pady=(0, 24), sticky="ew")

    def _tab_admin(self):
        tab = self.tabview.tab("Administrador")
        tab.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tab, text="Ingrese usuario y clave:", font=("Segoe UI", 11),
                     text_color=COLORES["texto_secundario"]).grid(row=0, column=0, padx=20, pady=(20, 8), sticky="w")
        self.ent_admin_user = ctk.CTkEntry(tab, height=40, font=("Segoe UI", 12), corner_radius=8,
                                           placeholder_text="Usuario")
        self.ent_admin_user.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")
        self.ent_admin_user.bind("<Return>", lambda e: self.ent_admin_clave.focus())
        self.ent_admin_clave = ctk.CTkEntry(tab, height=40, show="•", font=("Segoe UI", 12), corner_radius=8,
                                            placeholder_text="Clave")
        self.ent_admin_clave.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.ent_admin_clave.bind("<Return>", lambda e: self._login_admin())
        ctk.CTkButton(tab, text="Entrar", command=self._login_admin,
                      height=44, fg_color=COLORES["rojo"], corner_radius=10
                      ).grid(row=3, column=0, padx=20, pady=(0, 24), sticky="ew")

    def _limpiar_campos(self):
        """Vacía los campos de login para no guardar credenciales entre sesiones."""
        if hasattr(self, "ent_codigo"):
            self.ent_codigo.delete(0, "end")
        if hasattr(self, "ent_clave_usuario"):
            self.ent_clave_usuario.delete(0, "end")
        if hasattr(self, "ent_admin_user"):
            self.ent_admin_user.delete(0, "end")
        if hasattr(self, "ent_admin_clave"):
            self.ent_admin_clave.delete(0, "end")

    def _login_usuario(self):
        codigo = self.ent_codigo.get().strip()
        clave = self.ent_clave_usuario.get().strip()
        if not codigo or not clave:
            messagebox.showerror("Error", "Ingrese código y contraseña.", parent=self.winfo_toplevel())
            return
        self.on_usuario(codigo, clave)

    def _login_admin(self):
        user = self.ent_admin_user.get().strip()
        clave = self.ent_admin_clave.get().strip()
        if not user or not clave:
            messagebox.showerror("Error", "Ingrese usuario y clave.", parent=self.winfo_toplevel())
            return
        self.on_admin(user, clave)


# --- DASHBOARD USUARIO ---
class DashboardUsuario(TkFrame):
    def __init__(self, parent, db, usuario_id, usuario_nombre, volver, **kwargs):
        super().__init__(parent, bg=COLORES["fondo"], **kwargs)
        self.db = db
        self.usuario_id = usuario_id
        self.usuario_nombre = usuario_nombre
        self.volver = volver
        self._img_fondo = None
        self._ultimo_tam_fondo = (0, 0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._crear_ui()
        self.bind("<Configure>", self._actualizar_fondo)

    def _actualizar_fondo(self, ev=None):
        ruta = self.db.get_config("fondo") or ""
        if not ruta or not Path(ruta).exists() or not PIL_OK:
            return
        if not hasattr(self, "lbl_fondo") or not self.lbl_fondo or not self.lbl_fondo.winfo_exists():
            return
        w, h = max(self.winfo_width(), 100), max(self.winfo_height(), 100)
        if abs(w - self._ultimo_tam_fondo[0]) < 20 and abs(h - self._ultimo_tam_fondo[1]) < 20:
            return
        self._ultimo_tam_fondo = (w, h)
        try:
            from PIL import Image as PilImage
            img = PilImage.open(ruta).convert("RGB")
            img = img.resize((w, h), PilImage.LANCZOS)
            new_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
            self.lbl_fondo.configure(image=new_img)
            self.lbl_fondo.image = new_img
        except Exception:
            pass

    def _crear_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        h.grid_columnconfigure(1, weight=1)
        tarjeta_texto = self.db.get_config("tarjeta") or "Bienvenido"
        self.card_info = ctk.CTkFrame(h, fg_color=COLORES["acento"], corner_radius=12,
                                       width=260, height=90)
        self.card_info.grid(row=0, column=0, padx=(0, 12))
        self.card_info.grid_propagate(False)
        self.lbl_tarjeta = ctk.CTkLabel(self.card_info, text=tarjeta_texto[:120], font=("Segoe UI", 13),
                     text_color="white", wraplength=250, justify="left")
        self.lbl_tarjeta.pack(anchor="w", padx=16, pady=16, fill="both", expand=True)
        crear_reloj(h, font=("Segoe UI", 10)).grid(row=0, column=2, padx=(0, 12))
        ctk.CTkButton(h, text="Salir", command=self.volver, width=100, height=40,
                      fg_color=COLORES["rojo"], corner_radius=8).grid(row=0, column=3)
        f_filtros = ctk.CTkFrame(self, fg_color="transparent")
        f_filtros.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        f_filtros.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(f_filtros, text="Día:", font=("Segoe UI", 10)).grid(row=0, column=0, padx=(0, 6))
        hoy = datetime_pc().strftime("%d/%m/%Y")
        self.ent_filtro_fecha = ctk.CTkEntry(f_filtros, width=100, height=32, placeholder_text="DD/MM/AAAA")
        self.ent_filtro_fecha.insert(0, hoy)
        self.ent_filtro_fecha.grid(row=0, column=1, padx=(0, 10))
        self.ent_filtro_fecha.bind("<KeyRelease>", lambda e: self._cargar_tareas())
        ctk.CTkLabel(f_filtros, text="Estado:", font=("Segoe UI", 10)).grid(row=0, column=2, padx=(0, 6))
        self.combo_filtro_estado = ctk.CTkOptionMenu(f_filtros, values=["Todos"] + ESTADOS_TODOS, width=120,
                                                    command=lambda x: self._cargar_tareas())
        self.combo_filtro_estado.grid(row=0, column=3, padx=(0, 6))
        ctk.CTkButton(f_filtros, text="Limpiar", width=80, command=self._limpiar_filtros).grid(row=0, column=4)
        self.contenedor = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.contenedor.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.contenedor.grid_columnconfigure(0, weight=1)
        self._cargar_tareas()
        self._crear_fondo()

    def _crear_fondo(self):
        self.lbl_fondo = getattr(self, "lbl_fondo", None)
        if self.lbl_fondo and self.lbl_fondo.winfo_exists():
            self.lbl_fondo.destroy()
        self.lbl_fondo = None
        self._ultimo_tam_fondo = (0, 0)
        ruta_fondo = self.db.get_config("fondo") or ""
        if ruta_fondo and Path(ruta_fondo).exists() and PIL_OK:
            try:
                from PIL import Image as PilImage
                img = PilImage.open(ruta_fondo).convert("RGB")
                w, h = max(400, self.winfo_width() or 400), max(300, self.winfo_height() or 300)
                img = img.resize((w, h), PilImage.LANCZOS)
                self._img_fondo = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
                self.lbl_fondo = ctk.CTkLabel(self, text="", image=self._img_fondo)
                self.lbl_fondo.place(x=0, y=0, relwidth=1, relheight=1)
                self.lbl_fondo.lower()
            except Exception:
                self.lbl_fondo = None

    def _refrescar_config(self):
        """Recarga tarjeta y fondo desde la BD para ver cambios de Tarjetas y fondo."""
        tarjeta_texto = self.db.get_config("tarjeta") or "Bienvenido"
        if hasattr(self, "lbl_tarjeta") and self.lbl_tarjeta and self.lbl_tarjeta.winfo_exists():
            self.lbl_tarjeta.configure(text=tarjeta_texto[:120])
        self._crear_fondo()

    def _limpiar_filtros(self):
        self.ent_filtro_fecha.delete(0, "end")
        self.combo_filtro_estado.set("Todos")
        self._cargar_tareas()

    def _cargar_tareas(self):
        for w in self.contenedor.winfo_children():
            w.destroy()
        tareas = self.db.tareas_por_usuario(self.usuario_id)
        filtro_fecha = self.ent_filtro_fecha.get().strip()
        filtro_estado = self.combo_filtro_estado.get()
        if filtro_fecha:
            fecha_obj = parsear_datetime(filtro_fecha + " 00:00")
            if fecha_obj:
                tareas = [t for t in tareas if _tarea_coincide_fecha(t, fecha_obj)]
        if filtro_estado and filtro_estado != "Todos":
            tareas = [t for t in tareas if t.get("estado") == filtro_estado]
        if not tareas:
            msg = "No hay tareas que coincidan con los filtros." if (filtro_fecha or (filtro_estado and filtro_estado != "Todos")) else "No tiene tareas asignadas."
            ctk.CTkLabel(self.contenedor, text=msg,
                         font=("Segoe UI", 14), text_color=COLORES["texto_secundario"]).grid(row=0, column=0, pady=40)
        else:
            for t in tareas:
                self._crear_card(t)

    def _crear_card(self, tarea):
        color = calcular_color_tarea(tarea)
        tid = tarea["id"]
        f = ctk.CTkFrame(self.contenedor, fg_color=COLORES["card"], corner_radius=10,
                         border_width=2, border_color=color, cursor="hand2")
        f.grid_columnconfigure(1, weight=1)
        f.bind("<Button-1>", lambda e: self._abrir_modal(tid))
        detalles_txt = (tarea.get("detalles") or "").strip()
        n_filas = 3 if detalles_txt else 2
        s = SemáforoCircular(f, color, 32)
        s.grid(row=0, column=0, rowspan=n_filas, padx=(16, 12), pady=14, sticky="ns")
        s.bind("<Button-1>", lambda e: self._abrir_modal(tid))
        ctk.CTkLabel(f, text=tarea["nombre"], font=("Segoe UI Semibold", 14),
                     text_color=COLORES["texto"], anchor="w"
                     ).grid(row=0, column=1, padx=(0, 16), pady=(14, 2), sticky="ew")
        info = f"{tarea.get('fecha_hora_inicio','')} → {tarea.get('fecha_hora_termino','')} • {tarea.get('estado','')}"
        ctk.CTkLabel(f, text=info, font=("Segoe UI", 11), text_color=COLORES["texto_secundario"],
                     anchor="w").grid(row=1, column=1, padx=(0, 16), pady=(0, 2), sticky="ew")
        if detalles_txt:
            txt_mostrar = detalles_txt[:200] + ("..." if len(detalles_txt) > 200 else "")
            ctk.CTkLabel(f, text=txt_mostrar, font=("Segoe UI", 10),
                         text_color=COLORES["texto_secundario"], anchor="w",
                         wraplength=420, justify="left").grid(row=2, column=1, padx=(0, 16), pady=(0, 14), sticky="ew")
        f.grid(row=len(self.contenedor.winfo_children()), column=0, sticky="ew", pady=(0, 10))

    def _abrir_modal(self, id_tarea):
        t = self.db.obtener_tarea(id_tarea)
        if not t:
            return
        if t.get("responsable_id") != self.usuario_id:
            messagebox.showerror("Error", "No tiene acceso a esta tarea.", parent=self.winfo_toplevel())
            return
        modal = ModalEstadoTarea(self.winfo_toplevel(), t["nombre"])
        self.winfo_toplevel().wait_window(modal)
        if not modal.resultado:
            return
        estado, nota = modal.resultado
        self.db.actualizar_estado_tarea(id_tarea, estado, self.usuario_id, nota)
        messagebox.showinfo("OK", "Estado actualizado.", parent=self.winfo_toplevel())
        self._cargar_tareas()


def _horas_disponibles():
    return [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]


class DialogoCalendario(ctk.CTkToplevel):
    """Diálogo de fecha y hora. Usa tkcalendar si está disponible, sino fallback custom."""

    def __init__(self, parent, titulo="Fecha", valor_inicial=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(titulo)
        self.resultado = None
        dt = parsear_datetime(valor_inicial) if valor_inicial else datetime_pc()
        fecha_inicial = dt.date() if dt else datetime_pc().date()
        hora_inicial = dt.strftime("%H:%M") if dt else "08:00"
        self.geometry("360x280")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=COLORES["card"])

        crear_reloj(self, font=("Segoe UI", 9)).pack(anchor="e", padx=20, pady=(8, 0))
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(f, text="Fecha:", font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 4))
        # Contenedor para DateEntry (usa tk.Frame porque DateEntry es ttk)
        self.frame_fecha = TkFrame(f, bg=COLORES["fondo"])
        self.frame_fecha.pack(fill="x", pady=(0, 12))

        if TKCALENDAR_OK:
            try:
                self.date_entry = DateEntry(
                    self.frame_fecha, width=18, font=("Segoe UI", 11),
                    date_pattern="dd/mm/yyyy",
                    year=fecha_inicial.year, month=fecha_inicial.month, day=fecha_inicial.day
                )
            except Exception:
                self.date_entry = DateEntry(
                    self.frame_fecha, width=18, font=("Segoe UI", 11),
                    year=fecha_inicial.year, month=fecha_inicial.month, day=fecha_inicial.day
                )
            self.date_entry.pack(fill="x", padx=4, pady=4)
        else:
            # Fallback: Entry manual con placeholder
            self.date_entry = None
            self.ent_fecha = ctk.CTkEntry(self.frame_fecha, height=36, placeholder_text="DD/MM/AAAA",
                                           font=("Segoe UI", 11))
            self.ent_fecha.pack(fill="x", padx=4, pady=4)
            self.ent_fecha.insert(0, fecha_inicial.strftime("%d/%m/%Y"))

        ctk.CTkLabel(f, text="Hora:", font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 4))
        horas = _horas_disponibles()
        self.combo_h = ctk.CTkOptionMenu(f, values=horas, width=120, height=36, font=("Segoe UI", 11))
        self.combo_h.pack(anchor="w", pady=(0, 20))
        if hora_inicial in horas:
            self.combo_h.set(hora_inicial)
        else:
            self.combo_h.set(horas[0] if horas else "08:00")

        btn_f = _crear_btns_modal(self, self._ok, self._cancelar, "✓ Aceptar")
        btn_f.pack(fill="x", padx=20, pady=(0, 16))

    def _ok(self):
        try:
            if TKCALENDAR_OK and self.date_entry:
                d = self.date_entry.get_date()
            else:
                texto = self.ent_fecha.get().strip()
                parsed = parsear_datetime(texto + " 00:00")
                d = parsed.date() if parsed else None
            if d:
                hora = self.combo_h.get() or "08:00"
                self.resultado = f"{d.strftime('%d/%m/%Y')} {hora}"
        except Exception:
            pass
        self.destroy()

    def _cancelar(self):
        self.resultado = None
        self.destroy()


# --- PANEL ADMINISTRACIÓN ---
class PanelAdmin(TkFrame):
    def __init__(self, parent, db, admin_id, volver, **kwargs):
        super().__init__(parent, bg=COLORES["fondo"], **kwargs)
        self.db = db
        self.admin_id = admin_id
        self.volver = volver
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._crear_ui()

    def _crear_ui(self):
        h = ctk.CTkFrame(self, fg_color=COLORES["card"], corner_radius=12, border_width=1, border_color=COLORES["borde"])
        h.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        h.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(h, text="Panel de Administración", font=("Segoe UI Semibold", 20),
                     text_color=COLORES["texto"]).grid(row=0, column=0, padx=24, pady=16, sticky="w")
        crear_reloj(h, font=("Segoe UI", 10)).grid(row=0, column=1, padx=(0, 12))
        ctk.CTkButton(h, text="Cerrar Sesión", command=self.volver, width=140, height=40,
                      fg_color=COLORES["rojo"], corner_radius=10).grid(row=0, column=2, padx=24, pady=16)
        self.tabview = ctk.CTkTabview(self, fg_color=COLORES["card"], width=800, height=450)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.tabview.grid_columnconfigure(0, weight=1)
        self.tabview.grid_rowconfigure(0, weight=1)
        self.tabview.add("Tarjetas y Fondo")
        self.tabview.add("Gestión de Usuarios")
        self.tabview.add("Gestión de Tareas")
        self.tabview.add("Estadísticas")
        self._tab_tarjetas()
        self._tab_usuarios()
        self._tab_tareas()
        self._tab_estadisticas()

    def _tab_tarjetas(self):
        tab = self.tabview.tab("Tarjetas y Fondo")
        tab.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tab, text="Texto de la tarjeta (Dashboard usuario):", font=("Segoe UI", 12)).grid(row=0, column=0, padx=20, pady=(20,8), sticky="w")
        self.ent_tarjeta = ctk.CTkTextbox(tab, height=80, font=("Segoe UI", 11))
        self.ent_tarjeta.grid(row=1, column=0, padx=20, pady=(0,16), sticky="ew")
        self.ent_tarjeta.insert("1.0", self.db.get_config("tarjeta") or "")
        ctk.CTkLabel(tab, text="Imagen de fondo del Dashboard:", font=("Segoe UI", 12)).grid(row=2, column=0, padx=20, pady=(8,8), sticky="w")
        f_img = ctk.CTkFrame(tab, fg_color="transparent")
        f_img.grid(row=3, column=0, padx=20, pady=(0,20), sticky="ew")
        f_img.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(f_img, text="Cargar imagen", command=self._cargar_imagen, width=140).grid(row=0, column=0, padx=(0,8))
        self.lbl_ruta = ctk.CTkLabel(f_img, text=self.db.get_config("fondo") or "Ninguna", font=("Segoe UI", 10),
                                     text_color=COLORES["texto_secundario"])
        self.lbl_ruta.grid(row=0, column=1, sticky="w")
        ctk.CTkButton(tab, text="Guardar", command=self._guardar_config, width=120, height=40,
                      fg_color=COLORES["verde"]).grid(row=4, column=0, padx=20, pady=20)

    def _cargar_imagen(self):
        path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if path:
            dest = ASSETS_DIR / "fondo_dashboard.jpg"
            try:
                shutil.copy(path, dest)
                self.db.set_config("fondo", str(dest))
                self.lbl_ruta.configure(text=str(dest))
                messagebox.showinfo("OK", "Imagen guardada.", parent=self.winfo_toplevel())
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self.winfo_toplevel())

    def _guardar_config(self):
        self.db.set_config("tarjeta", self.ent_tarjeta.get("1.0", "end").strip())
        messagebox.showinfo("OK", "Configuración guardada.", parent=self.winfo_toplevel())

    def _tab_usuarios(self):
        tab = self.tabview.tab("Gestión de Usuarios")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        f_add = ctk.CTkFrame(tab, fg_color="transparent")
        f_add.grid(row=0, column=0, padx=20, pady=(20,12), sticky="ew")
        f_add.grid_columnconfigure(1, weight=1)
        self.ent_u_nombre = ctk.CTkEntry(f_add, placeholder_text="Nombre completo", width=240, height=36)
        self.ent_u_nombre.grid(row=0, column=0, padx=(0,8))
        self.ent_u_codigo = ctk.CTkEntry(f_add, placeholder_text="Código", width=140, height=36)
        self.ent_u_codigo.grid(row=0, column=1, padx=(0,8))
        self.ent_u_clave = ctk.CTkEntry(f_add, placeholder_text="Clave", show="•", width=140, height=36)
        self.ent_u_clave.grid(row=0, column=2, padx=(0,8))
        ctk.CTkButton(f_add, text="Crear", command=self._crear_usuario, width=80).grid(row=0, column=3, padx=(0,8))
        self.contenedor_u = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.contenedor_u.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0,20))
        self._cargar_usuarios()

    def _actualizar_combo_responsable(self):
        us = [u["nombre"] for u in self.db.listar_usuarios() if not u["es_admin"]]
        vals = us if us else ["(Crear usuarios primero)"]
        self.ent_resp.configure(values=vals)
        if us:
            self.ent_resp.set(us[0])
        elif vals:
            self.ent_resp.set(vals[0])

    def _abrir_calendario(self, campo):
        ent = self.ent_inicio if campo == "inicio" else self.ent_termino
        val = ent.get().strip()
        dlg = DialogoCalendario(self.winfo_toplevel(), titulo=f"Fecha {campo.title()}", valor_inicial=val)
        self.winfo_toplevel().wait_window(dlg)
        if dlg.resultado:
            ent.delete(0, "end")
            ent.insert(0, dlg.resultado)

    def _crear_usuario(self):
        n, c, cl = self.ent_u_nombre.get().strip(), self.ent_u_codigo.get().strip(), self.ent_u_clave.get().strip()
        if not n or not cl:
            messagebox.showerror("Error", "Nombre y clave requeridos.", parent=self.winfo_toplevel())
            return
        try:
            self.db.crear_usuario(n, c or n.upper()[:8], cl)
            self.ent_u_nombre.delete(0,"end")
            self.ent_u_codigo.delete(0,"end")
            self.ent_u_clave.delete(0,"end")
            self._cargar_usuarios()
            self._actualizar_combo_responsable()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Código o nombre ya existe.", parent=self.winfo_toplevel())

    def _cargar_usuarios(self):
        for w in self.contenedor_u.winfo_children():
            w.destroy()
        for u in self.db.listar_usuarios():
            if u["es_admin"]:
                continue
            f = ctk.CTkFrame(self.contenedor_u, fg_color=COLORES["fondo"], corner_radius=8)
            f.grid_columnconfigure(0, weight=1)
            f.grid(row=len(self.contenedor_u.winfo_children()), column=0, sticky="ew", pady=(0,8))
            ctk.CTkLabel(f, text=f"{u['nombre']} — Cód: {u.get('codigo','')}", font=("Segoe UI", 12),
                        wraplength=450, anchor="w").grid(row=0, column=0, padx=12, pady=8, sticky="w")
            ctk.CTkButton(f, text="Editar", command=lambda i=u["id"]: self._editar_usuario(i), width=70).grid(row=0, column=1, padx=8, pady=8)
            ctk.CTkButton(f, text="Eliminar", command=lambda i=u["id"]: self._eliminar_usuario(i),
                         width=70, fg_color=COLORES["rojo"]).grid(row=0, column=2, padx=8, pady=8)

    def _editar_usuario(self, id_u):
        u = self.db.obtener_usuario(id_u)
        if not u:
            return
        dlg = ctk.CTkToplevel(self)
        dlg.title("Editar Usuario")
        dlg.geometry("360x200")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        ctk.CTkLabel(dlg, text="Nombre:").pack(anchor="w", padx=20, pady=(20,4))
        ent_n = ctk.CTkEntry(dlg, width=300)
        ent_n.pack(padx=20, pady=(0,12))
        ent_n.insert(0, u["nombre"])
        ctk.CTkLabel(dlg, text="Código:").pack(anchor="w", padx=20, pady=(4,4))
        ent_c = ctk.CTkEntry(dlg, width=300)
        ent_c.pack(padx=20, pady=(0,12))
        ent_c.insert(0, u.get("codigo") or "")
        ctk.CTkLabel(dlg, text="Nueva clave (vacío=mantener):").pack(anchor="w", padx=20, pady=(4,4))
        ent_cl = ctk.CTkEntry(dlg, width=300, show="•")
        ent_cl.pack(padx=20, pady=(0,12))
        def guardar():
            self.db.actualizar_usuario(id_u, ent_n.get().strip(), ent_c.get().strip(), ent_cl.get().strip())
            dlg.destroy()
            self._cargar_usuarios()
        ctk.CTkButton(dlg, text="Guardar", command=guardar).pack(pady=20)

    def _eliminar_usuario(self, id_u):
        if messagebox.askyesno("Confirmar", "¿Eliminar usuario?"):
            self.db.eliminar_usuario(id_u)
            self._cargar_usuarios()
            self._actualizar_combo_responsable()

    def _tab_tareas(self):
        tab = self.tabview.tab("Gestión de Tareas")
        tab.grid_columnconfigure(0, weight=0)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        form = ctk.CTkFrame(tab, width=380, fg_color=COLORES["card"], corner_radius=12, border_width=1)
        form.grid(row=0, column=0, padx=(0,10), pady=0, sticky="nsew")
        form.grid_propagate(False)
        r=0
        ctk.CTkLabel(form, text="Nueva/Editar Tarea", font=("Segoe UI Semibold", 14)).grid(row=r, column=0, columnspan=2, padx=20, pady=(20,12), sticky="w")
        r+=1
        ctk.CTkLabel(form, text="Nombre", font=("Segoe UI", 10)).grid(row=r, column=0, padx=20, pady=(8,2), sticky="w")
        self.ent_nombre = ctk.CTkEntry(form, height=34)
        self.ent_nombre.grid(row=r+1, column=0, columnspan=2, padx=20, pady=(0,8), sticky="ew")
        r+=2
        ctk.CTkLabel(form, text="Responsable", font=("Segoe UI", 10)).grid(row=r, column=0, padx=20, pady=(8,2), sticky="w")
        us = [u["nombre"] for u in self.db.listar_usuarios() if not u["es_admin"]]
        self.ent_resp = ctk.CTkOptionMenu(form, values=us if us else ["(Crear usuarios primero)"], width=200)
        self.ent_resp.grid(row=r+1, column=0, columnspan=2, padx=20, pady=(0,8), sticky="ew")
        r+=2
        ctk.CTkLabel(form, text="Inicio", font=("Segoe UI", 10)).grid(row=r, column=0, padx=20, pady=(8,2), sticky="w")
        f_inicio = ctk.CTkFrame(form, fg_color="transparent")
        f_inicio.grid(row=r+1, column=0, columnspan=2, padx=20, pady=(0,8), sticky="ew")
        f_inicio.grid_columnconfigure(0, weight=1)
        self.ent_inicio = ctk.CTkEntry(f_inicio, height=34, placeholder_text="DD/MM/AAAA HH:MM")
        self.ent_inicio.grid(row=0, column=0, padx=(0,8), sticky="ew")
        ctk.CTkButton(f_inicio, text="📅", width=44, height=34, command=lambda: self._abrir_calendario("inicio")).grid(row=0, column=1)
        r+=2
        ctk.CTkLabel(form, text="Término", font=("Segoe UI", 10)).grid(row=r, column=0, padx=20, pady=(8,2), sticky="w")
        f_termino = ctk.CTkFrame(form, fg_color="transparent")
        f_termino.grid(row=r+1, column=0, columnspan=2, padx=20, pady=(0,8), sticky="ew")
        f_termino.grid_columnconfigure(0, weight=1)
        self.ent_termino = ctk.CTkEntry(f_termino, height=34, placeholder_text="DD/MM/AAAA HH:MM")
        self.ent_termino.grid(row=0, column=0, padx=(0,8), sticky="ew")
        ctk.CTkButton(f_termino, text="📅", width=44, height=34, command=lambda: self._abrir_calendario("termino")).grid(row=0, column=1)
        r+=2
        ctk.CTkLabel(form, text="Detalles:").grid(row=r, column=0, padx=20, pady=(8,2), sticky="w")
        self.txt_det = ctk.CTkTextbox(form, height=60)
        self.txt_det.grid(row=r+1, column=0, columnspan=2, padx=20, pady=(0,8), sticky="ew")
        r+=2
        ctk.CTkLabel(form, text="Estado:").grid(row=r, column=0, padx=20, pady=(8,2), sticky="w")
        self.combo_est = ctk.CTkOptionMenu(form, values=ESTADOS_TODOS, width=200)
        self.combo_est.grid(row=r+1, column=0, columnspan=2, padx=20, pady=(0,12), sticky="ew")
        r+=2
        self.tarea_edit_id = None
        ctk.CTkButton(form, text="Guardar", command=self._guardar_tarea, fg_color=COLORES["verde"]).grid(row=r, column=0, padx=20, pady=12)
        ctk.CTkButton(form, text="Limpiar", command=lambda: self._limpiar_form_tarea()).grid(row=r, column=1, padx=20, pady=12)
        self.contenedor_t = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self._actualizar_combo_responsable()
        self.contenedor_t.grid(row=0, column=1, sticky="nsew", padx=(10,0), pady=0)
        self.contenedor_t.grid_columnconfigure(0, weight=1)
        self._cargar_tareas_admin()

    def _guardar_tarea(self):
        nombre = self.ent_nombre.get().strip()
        resp_nom = self.ent_resp.get() if hasattr(self.ent_resp, "get") else self.ent_resp.get().strip()
        inicio = self.ent_inicio.get().strip()
        termino = self.ent_termino.get().strip()
        if resp_nom == "(Crear usuarios primero)" or not resp_nom:
            messagebox.showerror("Error", "Cree al menos un usuario en Gestión de Usuarios.", parent=self.winfo_toplevel())
            return
        if not nombre or not inicio or not termino:
            messagebox.showerror("Error", "Complete todos los campos.", parent=self.winfo_toplevel())
            return
        dt_i, dt_t = parsear_datetime(inicio), parsear_datetime(termino)
        if not dt_i or not dt_t:
            messagebox.showerror("Error", "Formato fecha: DD/MM/AAAA HH:MM", parent=self.winfo_toplevel())
            return
        resp_id = next((u["id"] for u in self.db.listar_usuarios() if u["nombre"] == resp_nom), None)
        inicio_f = dt_i.strftime(FORMATO_DATETIME)
        termino_f = dt_t.strftime(FORMATO_DATETIME)
        detalles = self.txt_det.get("1.0", "end").strip()
        estado = self.combo_est.get()
        if self.tarea_edit_id:
            self.db.actualizar_tarea(self.tarea_edit_id, nombre, resp_id, resp_nom, inicio_f, termino_f, detalles, estado, self.admin_id)
            messagebox.showinfo("OK", "Tarea actualizada.", parent=self.winfo_toplevel())
        else:
            self.db.insertar_tarea(nombre, resp_id, resp_nom, inicio_f, termino_f, detalles, self.admin_id)
            messagebox.showinfo("OK", "Tarea creada.", parent=self.winfo_toplevel())
        self._limpiar_form_tarea()
        self._cargar_tareas_admin()

    def _limpiar_form_tarea(self):
        self.tarea_edit_id = None
        self.ent_nombre.delete(0,"end")
        self.ent_inicio.delete(0,"end")
        self.ent_termino.delete(0,"end")
        self.txt_det.delete("1.0","end")
        self.combo_est.set(ESTADO_PENDIENTE)
        self._actualizar_combo_responsable()

    def _cargar_tareas_admin(self):
        for w in self.contenedor_t.winfo_children():
            w.destroy()
        for t in self.db.listar_tareas_admin(incluir_archivadas=True):
            color = calcular_color_tarea(t)
            tid = t["id"]
            f = ctk.CTkFrame(self.contenedor_t, fg_color=COLORES["card"], corner_radius=8, border_width=2, border_color=color)
            f.grid_columnconfigure(1, weight=1)
            f.grid(row=len(self.contenedor_t.winfo_children()), column=0, sticky="ew", pady=(0,8))
            SemáforoCircular(f, color, 24).grid(row=0, column=0, rowspan=2, padx=(12,8), pady=10, sticky="ns")
            ctk.CTkLabel(f, text=t["nombre"], font=("Segoe UI", 12)).grid(row=0, column=1, padx=(0,8), pady=(10,2), sticky="ew")
            ctk.CTkLabel(f, text=f"{t.get('responsable_nombre','')} • {t.get('estado','')}", font=("Segoe UI", 10),
                        text_color=COLORES["texto_secundario"]).grid(row=1, column=1, padx=(0,8), pady=(0,10), sticky="ew")
            ctk.CTkButton(f, text="Editar", width=60, command=lambda i=tid: self._editar_tarea(i)).grid(row=0, column=2, rowspan=2, padx=8, pady=10)
            ctk.CTkButton(f, text="Archivar" if not t.get("archivada") else "Desarchivar", width=70,
                         command=lambda i=tid, a=not t.get("archivada"): self._archivar(i,a)).grid(row=0, column=3, rowspan=2, padx=4, pady=10)
            ctk.CTkButton(f, text="Eliminar", width=60, fg_color=COLORES["rojo"],
                         command=lambda i=tid: self._eliminar_tarea(i)).grid(row=0, column=4, rowspan=2, padx=8, pady=10)

    def _editar_tarea(self, id_t):
        t = self.db.obtener_tarea(id_t)
        if not t:
            return
        self.tarea_edit_id = id_t
        self._actualizar_combo_responsable()
        resp_nom = t.get("responsable_nombre", "")
        us = [u["nombre"] for u in self.db.listar_usuarios() if not u["es_admin"]]
        if resp_nom and resp_nom not in us:
            self.ent_resp.configure(values=us + [resp_nom])
        self.ent_nombre.delete(0,"end")
        self.ent_nombre.insert(0, t["nombre"])
        if resp_nom:
            self.ent_resp.set(resp_nom)
        self.ent_inicio.delete(0,"end")
        self.ent_inicio.insert(0, t.get("fecha_hora_inicio",""))
        self.ent_termino.delete(0,"end")
        self.ent_termino.insert(0, t.get("fecha_hora_termino",""))
        self.txt_det.delete("1.0","end")
        self.txt_det.insert("1.0", t.get("detalles") or "")
        self.combo_est.set(t.get("estado", ESTADO_PENDIENTE))

    def _archivar(self, id_t, arch):
        self.db.archivar_tarea(id_t, arch)
        self._cargar_tareas_admin()

    def _eliminar_tarea(self, id_t):
        if messagebox.askyesno("Confirmar", "¿Eliminar tarea?"):
            self.db.eliminar_tarea(id_t)
            self._cargar_tareas_admin()

    def _tab_estadisticas(self):
        tab = self.tabview.tab("Estadísticas")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        f_filtros = ctk.CTkFrame(tab, fg_color="transparent")
        f_filtros.grid(row=0, column=0, padx=20, pady=(20,12), sticky="ew")
        f_filtros.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(f_filtros, text="Usuario:").grid(row=0, column=0, padx=(0,8))
        usuarios_opts = ["Todos"] + [u["nombre"] for u in self.db.listar_usuarios() if not u["es_admin"]]
        self.combo_stat_user = ctk.CTkOptionMenu(f_filtros, values=usuarios_opts, width=120)
        self.combo_stat_user.grid(row=0, column=1, padx=(0,16))
        ctk.CTkLabel(f_filtros, text="Fecha:").grid(row=0, column=2, padx=(0,8))
        self.combo_stat_periodo = ctk.CTkOptionMenu(f_filtros, values=["Día", "Mes", "Año"], width=80)
        self.combo_stat_periodo.grid(row=0, column=3, padx=(0,16))
        ctk.CTkButton(f_filtros, text="Actualizar", command=self._dibujar_estadisticas).grid(row=0, column=4)
        self.frame_charts = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.frame_charts.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0,20))
        self.frame_charts.grid_columnconfigure(0, weight=1)
        self._dibujar_estadisticas()

    def _dibujar_estadisticas(self):
        for w in self.frame_charts.winfo_children():
            w.destroy()
        if not MATPLOTLIB_OK:
            ctk.CTkLabel(self.frame_charts, text="Instale matplotlib: pip install matplotlib",
                         font=("Segoe UI", 14)).grid(row=0, column=0, pady=40)
            return
        try:
            user = self.combo_stat_user.get()
            uid = None if user == "Todos" else next((u["id"] for u in self.db.listar_usuarios() if u["nombre"] == user), None)
            per = self.combo_stat_periodo.get().lower()[:3]
            fig = Figure(figsize=(8, 9), dpi=100)
            stats_est = self.db.estadisticas_por_estado(None, None, uid)
            lbs = list(stats_est.keys())
            vls = list(stats_est.values())
            if not lbs or not vls or sum(vls) == 0:
                lbs, vls = ["Sin datos"], [1]
            cols = [COLOR_ESTADO.get(l, COLORES["acento"]) for l in lbs]
            ax1 = fig.add_subplot(311)
            ax1.pie(vls, labels=lbs, autopct="%1.0f%%", colors=cols)
            ax1.set_title("Por estado de tarea")
            stats_usr = self.db.estadisticas_por_usuario()
            u_lbs = list(stats_usr.keys())
            u_vls = list(stats_usr.values())
            if not u_lbs or not u_vls:
                u_lbs, u_vls = ["Sin datos"], [1]
            ax2 = fig.add_subplot(312)
            ax2.bar(u_lbs, u_vls, color=COLORES["acento"])
            ax2.set_title("Por usuario responsable")
            ax2.tick_params(axis="x", rotation=30)
            stats_fec = self.db.estadisticas_por_fecha(agrupar=per)
            f_lbs = list(stats_fec.keys())
            f_vls = list(stats_fec.values())
            if not f_lbs or not f_vls:
                f_lbs, f_vls = ["Sin datos"], [1]
            f_lbs, f_vls = f_lbs[-10:], f_vls[-10:]
            ax3 = fig.add_subplot(313)
            ax3.bar(f_lbs, f_vls, color=COLORES["verde"])
            ax3.set_title(f"Por fecha ({self.combo_stat_periodo.get()})")
            ax3.tick_params(axis="x", rotation=30)
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.frame_charts)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        except Exception as ex:
            ctk.CTkLabel(self.frame_charts, text=f"No se pudieron cargar las estadísticas.\n{ex}",
                         font=("Segoe UI", 12), text_color=COLORES["texto_secundario"]).grid(row=0, column=0, pady=40)


# --- APP PRINCIPAL ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = BaseDatos()
        self._configurar()
        self._content = ctk.CTkFrame(self, fg_color=COLORES["fondo"])
        self._content.pack(fill="both", expand=True)
        self._login = None
        self._dash = None
        self._panel = None
        self._mostrar_login()

    def _ocultar_todos(self):
        for w in self._content.winfo_children():
            try:
                w.pack_forget()
            except Exception:
                pass

    def _mostrar_login(self):
        self._ocultar_todos()
        if self._login is None:
            self._login = PantallaLogin(self._content, self._on_usuario, self._on_admin)
        self._login._limpiar_campos()
        self._login.pack(fill="both", expand=True)

    def _on_usuario(self, codigo, clave):
        res = self.db.login_usuario(codigo, clave)
        if res:
            self._ocultar_todos()
            if self._dash is None:
                self._dash = DashboardUsuario(self._content, self.db, res[0], res[1], self._mostrar_login)
            else:
                self._dash.usuario_id, self._dash.usuario_nombre = res[0], res[1]
                self._dash._cargar_tareas()
                self._dash._refrescar_config()
            self._dash.pack(fill="both", expand=True)
            return
        aid = self.db.login_admin(codigo, clave)
        if aid:
            self._ocultar_todos()
            if self._panel is None:
                self._panel = PanelAdmin(self._content, self.db, aid, self._mostrar_login)
            self._panel.pack(fill="both", expand=True)
            return
        messagebox.showerror("Error", "Código o contraseña incorrectos.", parent=self)

    def _on_admin(self, usuario, clave):
        aid = self.db.login_admin(usuario, clave)
        if not aid:
            messagebox.showerror("Error", "Credenciales incorrectas.", parent=self)
            return
        self._ocultar_todos()
        if self._panel is None:
            self._panel = PanelAdmin(self._content, self.db, aid, self._mostrar_login)
        else:
            self._panel.admin_id = aid
        self._panel.pack(fill="both", expand=True)

    def _configurar(self):
        self.geometry("900x650")
        self.minsize(420, 520)
        self.resizable(True, True)
        ctk.set_appearance_mode("light")
        self.configure(fg_color=COLORES["fondo"])
        self._actualizar_titulo_reloj()

    def _actualizar_titulo_reloj(self):
        if self.winfo_exists():
            self.title(f"{APP_TITLE} — {datetime_pc().strftime(FORMATO_RELOJ)}")
            self.after(1000, self._actualizar_titulo_reloj)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
