import tkinter as tk
import random

class PongGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Pong: Human vs CPU")
        self.root.resizable(False, False)

        # Game Constants
        self.width = 600
        self.height = 400
        self.ball_speed = 4
        self.player_speed = 6  # Reduced because it moves every frame now
        self.cpu_speed = 3.8   # AI is slightly slower to make it beatable

        # Canvas Setup
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="black", highlightthickness=0)
        self.canvas.pack()

        # Game Objects
        self.ball = self.canvas.create_oval(290, 190, 310, 210, fill="white")
        self.player_paddle = self.canvas.create_rectangle(10, 150, 25, 250, fill="white")
        self.cpu_paddle = self.canvas.create_rectangle(575, 150, 590, 250, fill="cyan")
        
        # Scores
        self.score_player = 0
        self.score_cpu = 0
        self.score_display = self.canvas.create_text(
            300, 30, text="0  :  0", fill="white", font=("Courier", 30)
        )

        # Movement & State Variables
        self.ball_dx = self.ball_speed
        self.ball_dy = self.ball_speed
        self.pressed_keys = {} # Tracks held keys for smooth movement

        # Bindings
        self.root.bind("<KeyPress>", self.on_press)
        self.root.bind("<KeyRelease>", self.on_release)

        # Start Game Loop
        self.update_game()

    def on_press(self, event):
        self.pressed_keys[event.keysym] = True

    def on_release(self, event):
        self.pressed_keys[event.keysym] = False

    def move_player(self):
        """Checks key states and moves player paddle."""
        coords = self.canvas.coords(self.player_paddle)
        # Support both WASD and Arrow Keys
        if self.pressed_keys.get("w") or self.pressed_keys.get("Up"):
            if coords[1] > 0:
                self.canvas.move(self.player_paddle, 0, -self.player_speed)
        if self.pressed_keys.get("s") or self.pressed_keys.get("Down"):
            if coords[3] < self.height:
                self.canvas.move(self.player_paddle, 0, self.player_speed)

    def cpu_logic(self):
        """AI follows the ball's Y-position."""
        ball_coords = self.canvas.coords(self.ball)
        cpu_coords = self.canvas.coords(self.cpu_paddle)
        
        ball_center = (ball_coords[1] + ball_coords[3]) / 2
        paddle_center = (cpu_coords[1] + cpu_coords[3]) / 2

        if ball_center > paddle_center + 10 and cpu_coords[3] < self.height:
            self.canvas.move(self.cpu_paddle, 0, self.cpu_speed)
        elif ball_center < paddle_center - 10 and cpu_coords[1] > 0:
            self.canvas.move(self.cpu_paddle, 0, -self.cpu_speed)

    def check_collision(self, ball_pos, paddle):
        """Standard AABB collision detection."""
        paddle_pos = self.canvas.coords(paddle)
        return (ball_pos[2] >= paddle_pos[0] and ball_pos[0] <= paddle_pos[2] and
                ball_pos[3] >= paddle_pos[1] and ball_pos[1] <= paddle_pos[3])

    def score_point(self, winner):
        """Updates score and resets ball."""
        if winner == "player": self.score_player += 1
        else: self.score_cpu += 1
        
        self.canvas.itemconfig(self.score_display, text=f"{self.score_player}  :  {self.score_cpu}")
        self.canvas.coords(self.ball, 290, 190, 310, 210)
        
        # Reset speed and randomize vertical direction
        self.ball_dx = self.ball_speed * (1 if winner == "cpu" else -1)
        self.ball_dy = random.choice([self.ball_speed, -self.ball_speed])

    def update_game(self):
        """Main game loop (runs ~60 times per second)."""
        # 1. Handle Movement
        self.move_player()
        self.cpu_logic()
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy) # Move ball by its velocity
        
        ball_coords = self.canvas.coords(self.ball)

        # 2. Wall Bouncing
        if ball_coords[1] <= 0 or ball_coords[3] >= self.height:
            self.ball_dy *= -1

        # 3. Paddle Collisions
        if self.check_collision(ball_coords, self.player_paddle):
            self.ball_dx = abs(self.ball_dx) * 1.05 # Bounce right
        
        if self.check_collision(ball_coords, self.cpu_paddle):
            self.ball_dx = -abs(self.ball_dx) * 1.05 # Bounce left

        # 4. Scoring Logic
        if ball_coords[0] <= 0:
            self.score_point("cpu")
        elif ball_coords[2] >= self.width:
            self.score_point("player")

        # 5. Schedule next frame (call update_game every 15ms)
        self.root.after(15, self.update_game)

if __name__ == "__main__":
    root = tk.Tk()
    game = PongGame(root)
    root.mainloop()