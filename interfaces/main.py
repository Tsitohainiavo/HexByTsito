import tkinter as tk
from tkinter import ttk, messagebox
import math
import joblib
import numpy as np
import os
import random
import torch
import torch.nn as nn

# --- ARCHITECTURE DU CERVEAU (PYTORCH) ---
class HexCNN(nn.Module):
    def __init__(self):
        super(HexCNN, self).__init__()
        self.conv1 = nn.Conv2d(2, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(64)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        self.fc1 = nn.Linear(128 * 5 * 5, 256)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(256, 25)

    def forward(self, x):
        x = torch.relu(self.bn1(self.conv1(x)))
        x = torch.relu(self.bn2(self.conv2(x)))
        x = x.view(-1, 128 * 5 * 5)
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)

# --- CONFIGURATION ESTHÉTIQUE ---
BG_COLOR = '#1e1e2e'
BLUE_COLOR = '#3498db'
RED_COLOR = '#e74c3c'
EMPTY_COLOR = '#2d2d3a'

class HexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HexByTsito - ISPM")
        self.root.geometry("800x750")
        self.root.configure(bg=BG_COLOR)
        
        # --- CHARGEMENT DES MODÈLES (Une seule fois au démarrage) ---
        self.models = {'rf': None, 'cnn': None}
        self.load_all_models()
        
        self.show_home()

    def load_all_models(self):
        # 1. Chargement du Random Forest (Débutant)
        try:
            rf_path = "../models/hexmodelrfpro.joblib"
            self.models['rf'] = joblib.load(rf_path)
            print("✅ IA Débutant (RF) prête.")
        except Exception as e:
            self.model = None
            print(f"Erreur réelle : {e}")
            messagebox.showwarning("IA Désactivée", str(e)) 

        # 2. Chargement du CNN (Intermédiaire)
        try:
            self.models['cnn'] = HexCNN()
            self.models['cnn'].load_state_dict(torch.load("../models/hex_model_pytorch.pth"))
            self.models['cnn'].eval()
            print("✅ IA Intermédiaire (CNN) prête.")
        except: print("⚠️ Modèle PyTorch introuvable.")

    def show_home(self):
        for widget in self.root.winfo_children(): widget.destroy()
        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(frame, text="HEX GAME", font=('Segoe UI', 40, 'bold'), fg='white', bg=BG_COLOR).pack(pady=20)
        
        style = ttk.Style()
        style.configure('Menu.TButton', font=('Segoe UI', 12, 'bold'), padding=10)

        ttk.Button(frame, text="Joueur vs Joueur", width=25, command=lambda: self.start_game("1v1"), style='Menu.TButton').pack(pady=10)
        ttk.Button(frame, text="Niveau Débutant (RF)", width=25, command=lambda: self.start_game("debutant"), style='Menu.TButton').pack(pady=10)
        ttk.Button(frame, text="Niveau Intermédiaire (CNN)", width=25, command=lambda: self.start_game("intermediaire"), style='Menu.TButton').pack(pady=10)

    def start_game(self, mode):
        for widget in self.root.winfo_children(): widget.destroy()
        HexGame(self.root, mode, self.models, back_callback=self.show_home)

class HexGame:
    def __init__(self, parent, mode, models, back_callback):
        self.parent = parent
        self.mode = mode
        self.models = models
        self.back_callback = back_callback
        self.size = 5
        self.board = np.zeros((self.size, self.size), dtype=int)
        self.current_player = 2 # Rouge (Humain) commence
        self.game_over = False
        self.setup_ui()

    def setup_ui(self):
        self.header = tk.Frame(self.parent, bg=BG_COLOR)
        self.header.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(self.header, text="← Menu", command=self.back_callback).pack(side=tk.LEFT)
        self.info_label = tk.Label(self.header, text="À vous de jouer (Rouge)", font=('Segoe UI', 14, 'bold'), bg=BG_COLOR, fg='white')
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

        # Bordures continues
        self.draw_slim_border("blue")
        self.draw_slim_border("red")

        for r in range(self.size):
            for c in range(self.size):
                x, y = self.get_hex_coords(r, c)
                val = self.board[r, c]
                color = BLUE_COLOR if val == 1 else RED_COLOR if val == 2 else EMPTY_COLOR
                
                pts = []
                for i in range(6):
                    angle = math.radians(60 * i - 30)
                    pts.extend([x + self.cell_radius * math.cos(angle), y + self.cell_radius * math.sin(angle)])
                self.canvas.create_polygon(pts, fill=color, outline="#3d3d50", width=1)

    def draw_slim_border(self, color_type):
        color = BLUE_COLOR if color_type == "blue" else RED_COLOR
        contrast_color = '#4d4d66'
        
        if color_type == "blue":
            # Haut et Bas
            for row in [0, self.size-1]:
                pts = []
                for i in range(self.size):
                    x, y = self.get_hex_coords(row, i)
                    indices = [4, 5, 0] if row == 0 else [1, 2, 3]
                    for ang in indices:
                        a = math.radians(60 * ang - 30)
                        pts.extend([x + self.cell_radius * math.cos(a), y + self.cell_radius * math.sin(a)])
                self.canvas.create_line(pts, fill=color, width=4, capstyle=tk.ROUND)
        else:
            # Gauche et Droite
            for col in [0, self.size-1]:
                pts = []
                for i in range(self.size):
                    x, y = self.get_hex_coords(i, col)
                    indices = [3, 4, 5] if col == 0 else [0, 1, 2]
                    for ang in indices:
                        a = math.radians(60 * ang - 30)
                        pts.extend([x + self.cell_radius * math.cos(a), y + self.cell_radius * math.sin(a)])
                self.canvas.create_line(pts, fill=color, width=4, capstyle=tk.ROUND)

    def on_click(self, event):
        if self.game_over or self.current_player == 1 and self.mode != "1v1": return
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
            winner = "IA (Bleu)" if self.current_player == 1 else "Joueur (Rouge)"
            messagebox.showinfo("Victoire", f"Félicitations ! {winner} a gagné.")
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
        if self.game_over: return
        
        # 1. Lister toutes les cases vides (Indispensable pour la sécurité)
        empty_coords = list(zip(*np.where(self.board == 0)))
        if not empty_coords: return

        best_move = None

        # --- ÉTAPE A : RÉFLEXES DE SURVIE (Heuristique Prioritaire) ---
        # Si l'IA peut gagner au prochain coup, elle le FAIT.
        for r, c in empty_coords:
            self.board[r, c] = 1
            if self.check_winner(1):
                self.execute_turn(r, c)
                return
            self.board[r, c] = 0

        # Si le joueur va gagner au prochain coup, l'IA BLOQUE.
        for r, c in empty_coords:
            self.board[r, c] = 2
            if self.check_winner(2):
                self.board[r, c] = 0 # On annule la simulation
                self.execute_turn(r, c) # On prend la place
                return
            self.board[r, c] = 0

        # --- ÉTAPE B : INTELLIGENCE ARTIFICIELLE (Si pas d'urgence) ---

        # --- MODE INTERMÉDIAIRE (CNN PyTorch avec échantillonnage) ---
        if self.mode == "intermediaire" and self.models['cnn']:
            try:
                # Préparation du tenseur (1, 2, 5, 5)
                l1 = (self.board == 1).astype(float)
                l2 = (self.board == 2).astype(float)
                tensor = torch.tensor(np.stack([l1, l2]), dtype=torch.float32).unsqueeze(0)
                
                with torch.no_grad():
                    output = self.models['cnn'](tensor)
                    # Application d'une température (1.2) pour varier les coups
                    # Plus le chiffre est haut, plus l'IA "tente" des choses
                    probs = torch.softmax(output / 1.2, dim=1).numpy()[0]
                
                # On met à ZERO la probabilité des cases déjà occupées
                flat_board = self.board.flatten()
                for i in range(25):
                    if flat_board[i] != 0:
                        probs[i] = 0
                
                # Normalisation des probabilités restantes
                sum_probs = np.sum(probs)
                if sum_probs > 0:
                    probs /= sum_probs
                    # Tirage au sort pondéré (Sampling) au lieu de argmax
                    move_idx = np.random.choice(range(25), p=probs)
                    best_move = divmod(move_idx, 5)
                else:
                    best_move = random.choice(empty_coords)
            except Exception as e:
                print(f"Erreur IA Intermédiaire : {e}")
                best_move = random.choice(empty_coords)

        # --- MODE DÉBUTANT (Random Forest) ---
        elif self.mode == "debutant" and self.models['rf']:
            try:
                states = []
                for r, c in empty_coords:
                    self.board[r, c] = 1
                    enc = []
                    for v in self.board.flatten():
                        if v == 1: enc.extend([1, 0])
                        elif v == 2: enc.extend([0, 1])
                        else: enc.extend([0, 0])
                    states.append(enc)
                    self.board[r, c] = 0
                
                # Prédiction de probabilité de victoire
                rf_probs = self.models['rf'].predict_proba(np.array(states, dtype=np.float32))[:, 1]
                best_move = empty_coords[np.argmax(rf_probs)]
            except Exception as e:
                print(f"Erreur IA Débutant : {e}")
                best_move = random.choice(empty_coords)

        # --- SÉCURITÉ FINALE (Mode 1v1 ou échec IA) ---
        if not best_move:
            best_move = random.choice(empty_coords)

        # Exécution du coup choisi
        self.execute_turn(best_move[0], best_move[1])

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