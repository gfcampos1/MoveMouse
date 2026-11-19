"""
MoveMouse - Aplicativo para mover o mouse automaticamente e evitar bloqueio de tela
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import ctypes.wintypes
import time
import threading
import sys
import os

# Para o system tray
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


def get_resource_path(filename):
    """Obtém o caminho do recurso (funciona com PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


class MouseMover:
    """Classe para detectar inatividade e mover o mouse"""
    
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [
            ('cbSize', ctypes.c_uint),
            ('dwTime', ctypes.c_uint),
        ]
    
    def __init__(self):
        self.running = False
        self.interval_minutes = 5
        self.thread = None
        self.last_cycle_start = None
        self.last_user_input_time = 0
        
        # Constantes
        self.VK_SHIFT = 0x10
        self.VK_F15 = 0x7E
    
    def get_idle_time(self):
        """Retorna o tempo de inatividade em segundos"""
        lii = self.LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(self.LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        # GetTickCount retorna DWORD (32 bits sem sinal); força a leitura como
        # unsigned e aplica máscara de 32 bits para tratar o overflow/wraparound
        # que ocorre quando o sistema fica ligado por muitos dias.
        ctypes.windll.kernel32.GetTickCount.restype = ctypes.c_uint32
        tick = ctypes.windll.kernel32.GetTickCount()
        millis = (tick - lii.dwTime) & 0xFFFFFFFF
        return millis / 1000.0
    
    def press_key(self, key_code):
        """Pressiona e solta uma tecla usando keybd_event"""
        ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)  # Key down
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(key_code, 0, 2, 0)  # Key up
    
    def move_mouse(self):
        """Move o mouse de forma que o Windows detecte como atividade real"""
        # Método 1: Movimento grande com SetCursorPos
        point = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        
        # Movimento maior (50 pixels) em padrão quadrado
        movements = [
            (point.x + 50, point.y),       # direita
            (point.x + 50, point.y + 50),  # baixo
            (point.x, point.y + 50),       # esquerda
            (point.x, point.y),            # volta ao original
        ]
        
        for x, y in movements:
            ctypes.windll.user32.SetCursorPos(x, y)
            time.sleep(0.1)
        
        # Método 2: mouse_event (mais confiável para detectar atividade)
        ctypes.windll.user32.mouse_event(0x0001, 10, 0, 0, 0)  # Move 10px direita
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(0x0001, -10, 0, 0, 0)  # Volta 10px esquerda
        time.sleep(0.1)
        
        # Método 3: Pressionar tecla F15 (não faz nada visível)
        self.press_key(self.VK_F15)
        time.sleep(0.1)
        
        # Método 4: Pressionar Shift (não digita nada)
        self.press_key(self.VK_SHIFT)
    
    def monitor_loop(self):
        """Loop principal de monitoramento baseado em inatividade REAL do Windows"""
        while self.running:
            idle_seconds = self.get_idle_time()
            target_seconds = self.interval_minutes * 60
            
            if idle_seconds >= target_seconds:
                self.move_mouse()
                # Após mover, espera um pouco antes de checar novamente
                time.sleep(2)
            else:
                time.sleep(1)
    
    def start(self, callback=None):
        """Inicia o monitoramento"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Para o monitoramento"""
        self.running = False
    
    def get_status_info(self):
        """Retorna tempo de inatividade e tempo restante para próximo movimento"""
        if not self.running:
            return 0, 0
        
        idle_seconds = self.get_idle_time()
        target = self.interval_minutes * 60
        remaining = max(0, target - idle_seconds)
        
        return idle_seconds, remaining


class MoveMouseApp:
    """Interface gráfica do aplicativo"""
    
    def __init__(self):
        self.mover = MouseMover()
        self.tray_icon = None
        self.is_running = False
        
        # Janela principal
        self.root = tk.Tk()
        self.root.title("MoveMouse")
        self.root.geometry("320x240")
        self.root.resizable(False, False)
        self.root.configure(bg='#2b2b2b')
        
        # Centralizar na tela
        self.center_window()
        
        # Carregar ícone
        self.load_icon()
        
        # Criar interface
        self.create_widgets()
        
        # Comportamento ao fechar e minimizar
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Unmap>", self.on_minimize)
    
    def center_window(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        width = 320
        height = 240
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def load_icon(self):
        """Carrega o ícone da janela"""
        try:
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Erro ao carregar ícone: {e}")
    
    def create_widgets(self):
        """Cria os widgets da interface"""
        
        # Cores do tema escuro
        bg_color = '#2b2b2b'
        fg_color = '#ffffff'
        accent_color = '#22c55e'
        frame_bg = '#3b3b3b'
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg=bg_color, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_frame = tk.Frame(main_frame, bg=bg_color)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, text="🖱️ MoveMouse", 
                               font=('Segoe UI', 18, 'bold'), 
                               bg=bg_color, fg=fg_color)
        title_label.pack()
        
        desc_label = tk.Label(title_frame, text="Evita bloqueio de tela", 
                              font=('Segoe UI', 9), bg=bg_color, fg='#888888')
        desc_label.pack()
        
        # Frame de configuração
        config_frame = tk.LabelFrame(main_frame, text=" Configuração ", 
                                      font=('Segoe UI', 9),
                                      bg=frame_bg, fg=fg_color, 
                                      padx=15, pady=10)
        config_frame.pack(fill=tk.X, pady=(5, 10))
        
        # Linha de configuração de tempo
        time_frame = tk.Frame(config_frame, bg=frame_bg)
        time_frame.pack()
        
        tk.Label(time_frame, text="Mover após", font=('Segoe UI', 10),
                 bg=frame_bg, fg=fg_color).pack(side=tk.LEFT)
        
        self.time_var = tk.StringVar(value="5")
        time_options = ["1", "2", "3", "4", "5", "10", "15", "20", "30"]
        
        self.time_combo = ttk.Combobox(time_frame, textvariable=self.time_var,
                                        values=time_options, width=4, 
                                        state="readonly", justify='center')
        self.time_combo.pack(side=tk.LEFT, padx=8)
        
        tk.Label(time_frame, text="min de inatividade", font=('Segoe UI', 10),
                 bg=frame_bg, fg=fg_color).pack(side=tk.LEFT)
        
        # Frame de botões
        btn_frame = tk.Frame(main_frame, bg=bg_color)
        btn_frame.pack(fill=tk.X, pady=(5, 10))
        
        # Estilo dos botões
        btn_style = {'font': ('Segoe UI', 10), 'width': 12, 'height': 1, 
                     'cursor': 'hand2', 'relief': 'flat', 'bd': 0}
        
        # Botão Iniciar/Parar
        self.toggle_btn = tk.Button(btn_frame, text="▶  Iniciar", 
                                     bg=accent_color, fg='white',
                                     activebackground='#16a34a', activeforeground='white',
                                     command=self.toggle_monitoring, **btn_style)
        self.toggle_btn.pack(side=tk.LEFT, padx=(0, 10), expand=True)
        
        # Botão Minimizar
        self.tray_btn = tk.Button(btn_frame, text="▽  Ocultar",
                                   bg='#4b4b4b', fg='white',
                                   activebackground='#5b5b5b', activeforeground='white',
                                   command=self.minimize_to_tray, **btn_style)
        self.tray_btn.pack(side=tk.LEFT, expand=True)
        
        # Status direto (sem frame)
        self.status_label = tk.Label(main_frame, text="Parado",
                                      font=('Segoe UI', 12, 'bold'), bg=bg_color, fg='#888888')
        self.status_label.pack(pady=(10, 0))
    
    def update_status_display(self):
        """Atualiza o display de status em tempo real"""
        if self.is_running:
            idle, remaining = self.mover.get_status_info()
            
            if remaining <= 0:
                text = "Movendo mouse..."
                color = '#f59e0b'
            else:
                mins, secs = divmod(int(remaining), 60)
                text = f"Proximo em {mins}:{secs:02d}"
                color = '#22c55e'
            
            self.status_label.config(text=text, fg=color)
            
            # Atualiza a cada 1 segundo
            self.status_update_id = self.root.after(1000, self.update_status_display)
        else:
            self.status_label.config(text="Parado", fg='#888888')
            self.status_label.configure(fg='#888888')
    
    def toggle_monitoring(self):
        """Alterna entre iniciar e parar o monitoramento"""
        if not self.is_running:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Inicia o monitoramento"""
        try:
            minutes = int(self.time_var.get())
            self.mover.interval_minutes = minutes
            self.mover.start()
            self.is_running = True
            
            self.toggle_btn.configure(text="⏹  Parar", bg='#dc2626', 
                                       activebackground='#b91c1c')
            self.time_combo.configure(state="disabled")
            
            # Inicia atualização do status
            self.update_status_display()
            
        except ValueError:
            messagebox.showerror("Erro", "Selecione um tempo válido")
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.mover.stop()
        self.is_running = False
        
        # Cancela atualização do status
        if hasattr(self, 'status_update_id'):
            self.root.after_cancel(self.status_update_id)
        
        self.toggle_btn.configure(text="▶  Iniciar", bg='#22c55e',
                                   activebackground='#16a34a')
        self.status_label.config(text="Parado", fg='#888888')
        self.time_combo.configure(state="readonly")
    
    def create_tray_icon_image(self):
        """Carrega o ícone do arquivo PNG para o tray"""
        try:
            # Tenta carregar o PNG do tray
            png_path = get_resource_path("tray_icon.png")
            if os.path.exists(png_path):
                return Image.open(png_path)
            
            # Fallback: tenta o ICO
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                return img.resize((64, 64), Image.Resampling.LANCZOS)
        except:
            pass
        
        # Fallback final: cria ícone dinamicamente
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([4, 4, 60, 60], fill=(34, 197, 94, 255), outline=(255, 255, 255, 200), width=2)
        cursor = [(18, 16), (18, 48), (26, 38), (36, 50), (42, 44), (32, 32), (44, 26)]
        draw.polygon(cursor, fill=(255, 255, 255, 255))
        return image
    
    def minimize_to_tray(self):
        """Minimiza para a bandeja do sistema"""
        if not TRAY_AVAILABLE:
            messagebox.showwarning("Aviso", "Instale 'pystray' e 'pillow' para usar a bandeja do sistema")
            return
        
        # Esconde a janela
        self.root.withdraw()
        
        # Cria o menu da bandeja
        def create_menu():
            return pystray.Menu(
                pystray.MenuItem("Mostrar", self.show_from_tray, default=True),
                pystray.MenuItem(
                    "Parar" if self.is_running else "Iniciar",
                    self.toggle_from_tray
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Sair", self.quit_app)
            )
        
        # Cria o ícone
        status_text = "Ativo" if self.is_running else "Parado"
        self.tray_icon = pystray.Icon(
            "MoveMouse",
            self.create_tray_icon_image(),
            f"MoveMouse - {status_text}",
            create_menu()
        )
        
        # Inicia o ícone em thread separada
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def show_from_tray(self, icon=None, item=None):
        """Mostra a janela a partir da bandeja"""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.after(0, self.root.deiconify)
        self.root.after(10, self.root.lift)
        self.root.after(20, self.root.focus_force)
    
    def toggle_from_tray(self, icon=None, item=None):
        """Alterna o monitoramento a partir da bandeja"""
        self.root.after(0, self.toggle_monitoring)
        
        # Atualiza o ícone após um pequeno delay
        def update_tray():
            if self.tray_icon:
                self.tray_icon.icon = self.create_tray_icon_image()
                status_text = "Ativo" if self.is_running else "Parado"
                self.tray_icon.title = f"MoveMouse - {status_text}"
        
        self.root.after(100, update_tray)
    
    def on_minimize(self, event):
        """Quando a janela é minimizada, vai para o tray"""
        if event.widget == self.root and self.root.state() == 'iconic':
            if TRAY_AVAILABLE:
                self.root.after(100, self.minimize_to_tray)
    
    def on_close(self):
        """Quando a janela é fechada"""
        if self.is_running:
            result = messagebox.askyesnocancel(
                "MoveMouse",
                "O monitoramento está ativo.\n\n"
                "Sim = Minimizar para bandeja\n"
                "Não = Fechar aplicativo"
            )
            if result is True and TRAY_AVAILABLE:
                self.minimize_to_tray()
                return
            elif result is False:
                self.quit_app()
            # Cancelar = não faz nada
        else:
            self.quit_app()
    
    def quit_app(self, icon=None, item=None):
        """Fecha o aplicativo completamente"""
        self.mover.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Inicia o aplicativo"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MoveMouseApp()
    app.run()
