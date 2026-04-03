import tkinter as tk
from tkinter import messagebox
import math
import joblib
import numpy as np
import os

class HexGUI:
    def __init__(self, root, size=5):
        self.root = root
        self.root.title("Hex Game - IA Random Forest (5x5)")
        self.size = size
        self.cell_radius = 35
        self.padding = 70
        
        # --- GESTION DU MODÈLE ---
        
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        model_path = os.path.join(BASE_DIR, "models", "hexmodelrf.joblib")
        try:
            print("Chemin absolu :", model_path)
            print("Existe ?", os.path.exists(model_path))
            self.model = joblib.load(model_path)
            print(f" Modèle chargé : {model_path}")
        except Exception as e:
            self.model = None
            print(f"Erreur réelle : {e}")
            messagebox.showwarning("IA Désactivée", str(e))
        # État du jeu : 0=vide, 1=Bleu (IA), 2=Rouge (Humain)
        self.board = np.zeros((size, size), dtype=int)
        self.game_over = False

        # --- SETUP INTERFACE ---
        self.canvas_width = (size * 1.8) * (self.cell_radius * math.sqrt(3)) + self.padding
        self.canvas_height = (size * 1.6) * self.cell_radius + self.padding
        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack()

        self.draw_board()
        self.canvas.bind("<Button-1>", self.on_click)

    def get_hex_coords(self, r, c):
        # Géométrie en losange : décalage horizontal proportionnel à la ligne
        offset = r * (self.cell_radius * math.sqrt(3) / 2)
        x = self.padding + c * (self.cell_radius * math.sqrt(3)) + offset
        y = self.padding + r * (self.cell_radius * 1.5)
        return x, y

    def draw_hex(self, r, c, color="#2d2d2d", outline="#444444"):
        x, y = self.get_hex_coords(r, c)
        points = []
        for i in range(6):
            angle_rad = math.radians(60 * i - 30)
            points.extend([x + self.cell_radius * math.cos(angle_rad),
                           y + self.cell_radius * math.sin(angle_rad)])
        
        self.canvas.create_polygon(points, fill=color, outline=outline, width=2, tags=f"hex_{r}_{c}")

    def draw_board(self):
        self.canvas.delete("all")
        
        # 1. Bordures décoratives (Haut/Bas Bleu, Gauche/Droite Rouge)
        for i in range(self.size):
            # Bordures Bleues (IA) - Haut et Bas
            x_h, y_h = self.get_hex_coords(0, i)
            x_b, y_b = self.get_hex_coords(self.size-1, i)
            self.canvas.create_line(x_h-15, y_h-30, x_h+15, y_h-30, fill="#3498db", width=4)
            self.canvas.create_line(x_b-15, y_b+30, x_b+15, y_b+30, fill="#3498db", width=4)
            
            # Bordures Rouges (Joueur) - Gauche et Droite
            x_g, y_g = self.get_hex_coords(i, 0)
            x_d, y_d = self.get_hex_coords(i, self.size-1)
            self.canvas.create_line(x_g-35, y_g-10, x_g-35, y_g+10, fill="#e74c3c", width=4)
            self.canvas.create_line(x_d+35, y_d-10, x_d+35, y_d+10, fill="#e74c3c", width=4)

        # 2. Hexagones
        for r in range(self.size):
            for c in range(self.size):
                color = "#2d2d2d"
                outline = "#444444"
                if self.board[r, c] == 1: # Bleu
                    color, outline = "#3498db", "#2980b9"
                elif self.board[r, c] == 2: # Rouge
                    color, outline = "#e74c3c", "#c0392b"
                self.draw_hex(r, c, color, outline)

    def on_click(self, event):
        if self.game_over: return
        
        # Trouver la case cliquée
        clicked_hex = None
        min_dist = self.cell_radius
        for r in range(self.size):
            for c in range(self.size):
                hx, hy = self.get_hex_coords(r, c)
                dist = math.hypot(event.x - hx, event.y - hy)
                if dist < min_dist:
                    min_dist = dist
                    clicked_hex = (r, c)

        if clicked_hex and self.board[clicked_hex] == 0:
            self.make_move(clicked_hex[0], clicked_hex[1], 2) # Humain joue
            if not self.game_over:
                self.root.after(400, self.ia_play)

    def make_move(self, r, c, player):
        self.board[r, c] = player
        self.draw_board()
        if self.check_winner(player):
            self.game_over = True
            name = "IA (Bleu)" if player == 1 else "Vous (Rouge)"
            messagebox.showinfo("Fin de partie", f"Victoire de {name} !")

    def check_winner(self, player):
        # BFS pour vérifier la connexion
        q = []
        target_cells = []
        visited = set()

        for i in range(self.size):
            if player == 1: # Bleu : Haut -> Bas
                if self.board[0, i] == 1: q.append((0, i))
                target_cells.append((self.size-1, i))
            else: # Rouge : Gauche -> Droite
                if self.board[i, 0] == 2: q.append((i, 0))
                target_cells.append((i, self.size-1))

        while q:
            curr = q.pop(0)
            if curr in target_cells: return True
            if curr in visited: continue
            visited.add(curr)
            
            r, c = curr
            for dr, dc in [(-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < self.size and 0 <= nc < self.size and self.board[nr, nc] == player:
                    q.append((nr, nc))
        return False

    def encode_board(self):
        encoding = []
        for val in self.board.flatten():
            if val == 1: encoding.extend([1, 0])   # Bleu
            elif val == 2: encoding.extend([0, 1]) # Rouge
            else: encoding.extend([0, 0])          # Vide
        return encoding

    def ia_play(self):
        if not self.model or self.game_over: return
        
        empty = list(zip(*np.where(self.board == 0)))
        if not empty: return
        
        # On prépare TOUS les états possibles en une seule matrice
        all_states = []
        for r, c in empty:
            self.board[r, c] = 1 # Simulation
            all_states.append(self.encode_board())
            self.board[r, c] = 0 # Reset
        
        # Une SEULE passe dans le modèle pour toutes les cases (100x plus rapide !)
        probs = self.model.predict_proba(all_states)[:, 1]
        best_index = np.argmax(probs)
        
        best_move = empty[best_index]
        self.make_move(best_move[0], best_move[1], 1)

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#1e1e1e")
    app = HexGUI(root)
    root.mainloop()