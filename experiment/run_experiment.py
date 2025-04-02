import time, pygame, sys, math, random, os, re, glob
from time import perf_counter
from tablet_reading import Tablet
import numpy as np
import ctypes
import json
from tracking_data import TrackingData
from trajectory_analysis import Trajectory
ctypes.windll.user32.SetProcessDPIAware()  # important for correct resolution of the screen


def create_next_p_directory():
    p_dirs = glob.glob('P[0-9]*')
    numbers = [int(re.search(r'\d+', d).group()) for d in p_dirs if re.search(r'\d+', d)] if p_dirs else [0]
    next_dir = f'P{max(numbers) + 1}'
    os.makedirs(next_dir, exist_ok=True)
    print(f"Created directory {next_dir}")    
    return next_dir

folder_path = create_next_p_directory()


class MouseFallback:
    """Fallback class to use mouse if tablet is not found"""
    def __init__(self):
        self.reset_data()
        self.start_time = perf_counter()
        print("Using mouse as fallback input device.")

    def reset_data(self):
        self.start_time = perf_counter()
        self.xs = []
        self.ys = []
        self.x = 0
        self.y = 0
        self.pressures = []
        self.times = []
        self.pressure = 0

    def update(self):
        """Update mouse position"""
        x, y = pygame.mouse.get_pos()
        t = perf_counter() - self.start_time
        
        self.x = x
        self.y = y
        self.xs.append(x)
        self.ys.append(y)
        self.pressures.append(1 if pygame.mouse.get_pressed()[0] else 0)  # Left mouse button as pressure
        self.times.append(t)

    def close(self):
        """Placeholder for compatibility with Tablet class"""
        pass

# Initialize pygame
pygame.init()
pygame.mouse.set_visible(False)
WIDTH, HEIGHT = 3200, 2000
screen = pygame.display.set_mode((WIDTH, HEIGHT), vsync=True, flags=pygame.FULLSCREEN | pygame.DOUBLEBUF)

# Try to initialize tablet, fall back to mouse if not available
try:
    input_device = Tablet()
    if input_device.device is None:
        raise Exception("No tablet device found")
except Exception as e:
    print(f"Tablet initialization failed: {e}")
    input_device = MouseFallback()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Ellipse parameters
ellipse_width = 1000
ellipse_height = 500
circle_radius = 20
center_x = WIDTH // 2
center_y = HEIGHT // 2

# Initialize tracking data
data = TrackingData()
clock = pygame.time.Clock()
last_time = perf_counter()
start_time = input_device.start_time

# Experiment parameters
modes = ["train", "pause", "recording"]
frequencies = np.geomspace(0.033, 1.2, 5)
betas = [0, -1/3, -2/3]

# Training parameters - fixed order as specified
training = [ 
    {"freq_index": 0, "beta_index": 0},  
    {"freq_index": 3, "beta_index": 1}, 
    {"freq_index": 4, "beta_index": 2},              
]

# Generate all possible combinations for recording trials
recording_trials = []
for freq_idx in range(len(frequencies)):
    for beta_idx in range(len(betas)):
        recording_trials.append({"freq_index": freq_idx, "beta_index": beta_idx})

# Shuffle the recording trials to randomize order
random.shuffle(recording_trials)

# Experiment state management
experiment_phase = "training"  # "training" or "recording"
mode = "pause"
trial_index = 0
trial_start_time = None
current_trial_params = None
target_t = None
TRIAL_DURATION = 30.0  # Duration in seconds for each trial

def generate_target_trajectory(ra, rb, freq, beta, duration):
    dt = 0.001
    ts = np.arange(int(duration/dt)) * dt
    xs = ra * np.cos(ts * freq * np.pi * 2)
    ys = rb * np.sin(ts * freq * np.pi * 2)
    tr = Trajectory(xs, ys, ts, dt=dt)
    return tr.retrack(target_betaCV=beta)

def setup_next_trial():
    global experiment_phase, trial_index, current_trial_params, target_t
    
    if experiment_phase == "training":
        if trial_index < len(training):
            current_trial_params = training[trial_index]
            print(f"Training trial {trial_index+1}/{len(training)}")
        else:
            # Move to recording phase after all training trials
            experiment_phase = "recording"
            trial_index = 0
            print("Training complete. Moving to recording phase.")
            return setup_next_trial()
    
    elif experiment_phase == "recording":
        if trial_index < len(recording_trials):
            current_trial_params = recording_trials[trial_index]
            print(f"Recording trial {trial_index+1}/{len(recording_trials)}")
        else:
            # Experiment complete
            print("Experiment complete!")
            return False
    
    # Setup target trajectory based on current parameters
    freq = frequencies[current_trial_params["freq_index"]]
    beta = betas[current_trial_params["beta_index"]]
    
    print(f"Setting up trial with frequency={freq:.2f}, beta={beta}")
    target_t = generate_target_trajectory(ellipse_width, ellipse_height, freq, beta, 35)
    return True

def draw_centered_text(screen, text, font, color, y_offset=0):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    center_x = screen_width // 2
    center_y = screen_height // 2
    text_rect.center = (center_x, center_y + y_offset)
    screen.blit(text_surface, text_rect)

# Initialize fonts
font = pygame.font.SysFont("Arial", 50)
small_font = pygame.font.SysFont("Arial", 30)

# Initialize the first trial
setup_next_trial()

running = True
trial_data = {}  # Store data for each trial

# Check if the folder exists, and create it if it doesn't
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
    print(f"Folder '{folder_path}' created successfully")
else:
    print(f"Folder '{folder_path}' already exists")


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                if mode == "pause":
                    mode = "recording"
                    trial_start_time = perf_counter()                    
                    last_time = trial_start_time
                    input_device.reset_data()
                    data = TrackingData()

    screen.fill(BLACK)

    # Update mouse position if using mouse fallback
    if isinstance(input_device, MouseFallback):
        input_device.update()

    if mode == "pause":
        # Display different instructions based on experiment phase
        if experiment_phase == "training":
            draw_centered_text(screen, f"Training Trial {trial_index+1}/{len(training)}", font, WHITE, -100)
        else:
            draw_centered_text(screen, f"Recording Trial {trial_index+1}/{len(recording_trials)}", font, WHITE, -100)

        # Instructions
        draw_centered_text(screen, "Press SPACE to start a 30-second trial", font, WHITE, 0)
        
        # Show parameters of the upcoming trial
        freq = frequencies[current_trial_params["freq_index"]]
        beta = betas[current_trial_params["beta_index"]]
        param_text = f"Frequency: {freq:.2f}, Beta: {beta}"
        draw_centered_text(screen, param_text, small_font, YELLOW, 100)
    
    elif mode == "recording":
        # Check if trial should end (30 second limit)
        current_trial_time = perf_counter() - trial_start_time
        if current_trial_time >= TRIAL_DURATION:
            # Save this trial's data
            trial_filename = f"{folder_path}/{experiment_phase}_trial_{trial_index+1}_freq_{freq:.3f}_beta_{beta:.3f}.json"
            data.pen.xs = input_device.xs[:]
            data.pen.ys = input_device.ys[:]
            data.pen.ts = input_device.times[:]
            data.data = input_device.data

            data.save_to_file(trial_filename)
            
            # Move to next trial
            trial_index += 1
            if not setup_next_trial():
                # No more trials, end experiment
                running = False
            
            # Back to pause mode
            mode = "pause"
            continue
        
        # Draw time remaining
        time_left = max(0, TRIAL_DURATION - current_trial_time)
        time_text = f"Time: {time_left:.1f}s"
        phase_text = f"{experiment_phase.capitalize()} Trial {trial_index+1}"
        
        #time_surface = small_font.render(time_text, True, WHITE)
        #phase_surface = small_font.render(phase_text, True, WHITE)
        #screen.blit(time_surface, (50, 50))
        #screen.blit(phase_surface, (50, 90))
        
        # Draw ellipse path
        pygame.draw.ellipse(screen, WHITE, (center_x - ellipse_width, 
                                       center_y - ellipse_height, 
                                       ellipse_width*2, 
                                       ellipse_height*2), 2)
        
        # Get current target position
        current_time = perf_counter() - trial_start_time  # Use trial time for consistent animation
        tx = int(center_x + target_t.xf(current_time))
        ty = int(center_y + target_t.yf(current_time))
        
        # Get input device position (tablet or mouse)
        if isinstance(input_device, Tablet):
            cx = int((input_device.x / 50800) * WIDTH)
            cy = int((input_device.y / 31750) * HEIGHT)
        else:  # MouseFallback
            cx = input_device.x
            cy = input_device.y

        # Draw target and cursor
        pygame.draw.circle(screen, RED, (int(tx), int(ty)), circle_radius)
        pygame.draw.circle(screen, GREEN, (int(cx), int(cy)), int(circle_radius*0.8))
        
        # Record data
        t = perf_counter() - trial_start_time
        #dt = t - last_time
        #last_time = t
        data.target.add(tx, ty, t)
        data.cursor.add(cx, cy, t)

        # Update display and maintain frame rate
    pygame.display.flip()
    while (perf_counter() - last_time) < (1.0/60.0):
        time.sleep(1e-7)
    last_time = perf_counter()    
    #clock.tick(60)


# Save a summary file with experiment settings
experiment_summary = {
    "training_trials": training,
    "recording_trials": recording_trials,
    "frequencies": frequencies.tolist(),
    "betas": betas,
    "completion_time": time.strftime("%Y-%m-%d %H:%M:%S")
}


with open(folder_path + "/experiment_summary.json", "w") as f:
    json.dump(experiment_summary, f)

print("Experiment completed. All data saved.")
pygame.quit()
input_device.close()
sys.exit()
