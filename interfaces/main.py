import tkinter as tk
from tkinter import ttk, messagebox
import math
import joblib
import numpy as np
import os
import random

# Configuration Couleurs
BG_COLOR = '#1e1e2e'
BLUE_COLOR = '#3498db'
RED_COLOR = '#e74c3c'
EMPTY_COLOR = '#2d2d3a'

class HexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HexByTsito - ISPM")
        self.root.geometry("800x700")
        self.root.configure(bg=BG_COLOR)
        
        self.show_home()

    def show_home(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(frame, text="HEX GAME", font=('Segoe UI', 40, 'bold'), fg='white', bg=BG_COLOR).pack(pady=20)
        
        style = ttk.Style()
        style.configure('Menu.TButton', font=('Segoe UI', 12, 'bold'), padding=10)

        ttk.Button(frame, text="Joueur vs Joueur", width=25, command=lambda: self.start_game("1v1"), style='Menu.TButton').pack(pady=10)
        ttk.Button(frame, text="IA Débutant (RF Model)", width=25, command=lambda: self.start_game("debutant"), style='Menu.TButton').pack(pady=10)
        ttk.Button(frame, text="IA Intermédiaire", width=25, command=lambda: self.start_game("intermediaire"), style='Menu.TButton').pack(pady=10)
        ttk.Button(frame, text="IA Avancée", width=25, command=lambda: self.start_game("avance"), style='Menu.TButton').pack(pady=10)

    def start_game(self, mode):
        for widget in self.root.winfo_children():
            widget.destroy()
        HexGame(self.root, mode, back_callback=self.show_home)

class HexGame:
    def __init__(self, parent, mode, back_callback):
        self.parent = parent
        self.mode = mode
        self.back_callback = back_callback
        self.size = 5
        self.board = np.zeros((self.size, self.size), dtype=int)
        self.current_player = 2 # Rouge (Humain) commence
        self.game_over = False
        
        # Chargement IA
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        model_path = os.path.join(base_dir, "models", "hexmodelrfpro.joblib")
        try:
            self.model = joblib.load(model_path)
            print("✅ IA Débutant chargée")
        except:
            self.model = None

        self.setup_ui()

    def setup_ui(self):
        self.header = tk.Frame(self.parent, bg=BG_COLOR)
        self.header.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(self.header, text="← Menu", command=self.back_callback).pack(side=tk.LEFT)
        self.info_label = tk.Label(self.header, text="À vous de jouer", font=('Segoe UI', 14, 'bold'), bg=BG_COLOR, fg='white')
        self.info_label.pack(side=tk.LEFT, expand=True)

        self.canvas = tk.Canvas(self.parent, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", lambda e: self.draw_board())

    def get_geometry(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.cell_radius = min(w / (self.size * 3), h / (self.size * 2.5))
        self.offset_x = (w - (self.size * 1.7 * self.cell_radius * math.sqrt(3))) / 2 + (self.cell_radius)
        self.offset_y = (h - (self.size * 1.5 * self.cell_radius)) / 2

    def get_hex_coords(self, r, c):
        x = self.offset_x + (c + r * 0.5) * (self.cell_radius * math.sqrt(3))
        y = self.offset_y + r * (self.cell_radius * 1.5)
        return x, y

    def draw_board(self):
        self.canvas.delete("all")
        if self.canvas.winfo_width() < 10: return
        self.get_geometry()

        # --- DESSIN DES BORDURES POLYGONALES (LE "PLATEAU") ---
        self.draw_side_border("top", BLUE_COLOR)
        self.draw_side_border("bottom", BLUE_COLOR)
        self.draw_side_border("left", RED_COLOR)
        self.draw_side_border("right", RED_COLOR)

        # --- DESSIN DES HEXAGONES ---
        for r in range(self.size):
            for c in range(self.size):
                x, y = self.get_hex_coords(r, c)
                val = self.board[r, c]
                color = BLUE_COLOR if val == 1 else RED_COLOR if val == 2 else EMPTY_COLOR
                
                pts = []
                for i in range(6):
                    angle = math.radians(60 * i - 30)
                    pts.extend([x + self.cell_radius * math.cos(angle), y + self.cell_radius * math.sin(angle)])
                self.canvas.create_polygon(pts, fill=color, outline="#444455", width=1)

    def draw_side_border(self, side, color):
        """Dessine une bande de couleur qui suit les polygones extérieurs."""
        pts = []
        thickness = self.cell_radius * 0.3
        
        for i in range(self.size):
            r, c = (0, i) if side == "top" else (self.size-1, i) if side == "bottom" else (i, 0) if side == "left" else (i, self.size-1)
            x, y = self.get_hex_coords(r, c)
            
            # On crée un décalage pour la bordure
            dx = 0; dy = 0
            if side == "top": dy = -self.cell_radius * 0.9
            elif side == "bottom": dy = self.cell_radius * 0.9
            elif side == "left": dx = -self.cell_radius * 0.9
            elif side == "right": dx = self.cell_radius * 0.9
            
            # Dessin d'un petit hexagone de bordure pour l'effet "plein"
            border_pts = []
            for j in range(6):
                angle = math.radians(60 * j - 30)
                border_pts.extend([x + dx + self.cell_radius * 0.8 * math.cos(angle), 
                                   y + dy + self.cell_radius * 0.8 * math.sin(angle)])
            self.canvas.create_polygon(border_pts, fill=color, outline=color)

    def on_click(self, event):
        if self.game_over: return
        
        # Trouver l'hexagone cliqué
        for r in range(self.size):
            for c in range(self.size):
                hx, hy = self.get_hex_coords(r, c)
                if math.hypot(event.x - hx, event.y - hy) < self.cell_radius:
                    if self.board[r, c] == 0:
                        self.execute_turn(r, c)
                    return

    def execute_turn(self, r, c):
        self.board[r, c] = self.current_player
        self.draw_board()
        
        if self.check_winner(self.current_player):
            winner = "IA" if self.current_player == 1 else "Joueur"
            messagebox.showinfo("Fin", f"Victoire de {winner} !")
            self.game_over = True
            return

        self.current_player = 1 if self.current_player == 2 else 2
        
        if self.mode != "1v1" and self.current_player == 1:
            self.info_label.config(text="L'IA réfléchit...")
            self.parent.after(600, self.ai_play)
        else:
            p_name = "Bleu" if self.current_player == 1 else "Rouge"
            self.info_label.config(text=f"Tour : {p_name}")

    def ai_play(self):
        empty = list(zip(*np.where(self.board == 0)))
        if not empty: return

        move = None
        # Mode INTERMEDIAIRE / AVANCE : Blocage et Victoire immédiate
        if self.mode in ["intermediaire", "avance"]:
            for p in [1, 2]:
                for r, c in empty:
                    self.board[r, c] = p
                    if self.check_winner(p):
                        self.board[r, c] = 0
                        move = (r, c)
                        break
                    self.board[r, c] = 0
                if move: break

        # Mode DEBUTANT ou pas de coup critique : Modèle RF
        if not move and self.model:
            states = []
            for r, c in empty:
                self.board[r, c] = 1
                enc = []
                for v in self.board.flatten():
                    if v == 1: enc.extend([1, 0])
                    elif v == 2: enc.extend([0, 1])
                    else: enc.extend([0, 0])
                states.append(enc)
                self.board[r, c] = 0
            
            X = np.array(states, dtype=np.float32)
            probs = self.model.predict_proba(X)[:, 1]
            move = empty[np.argmax(probs)]
        
        if not move: move = random.choice(empty)
        self.execute_turn(move[0], move[1])

    def check_winner(self, player):
        visited, q = set(), []
        if player == 1: # Bleu: Haut -> Bas
            q = [(0, c) for c in range(self.size) if self.board[0, c] == 1]
            targets = [(self.size-1, c) for c in range(self.size)]
        else: # Rouge: Gauche -> Droite
            q = [(r, 0) for r in range(self.size) if self.board[r, 0] == 2]
            targets = [(r, self.size-1) for r in range(self.size)]
        
        while q:
            curr = q.pop(0)
            if curr in targets: return True
            if curr in visited: continue
            visited.add(curr)
            r, c = curr
            for dr, dc in [(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0)]:
                nr, nc = r+dr, c+dc
                if 0<=nr<self.size and 0<=nc<self.size and self.board[nr,nc] == player:
                    q.append((nr, nc))
        return False

if __name__ == "__main__":
    root = tk.Tk()
    HexApp(root)
    root.mainloop()