"""
Red Team Linux Agent - Scanner GUI
===================================

Graphical User Interface for the Red Team Linux Agent.
Provides easy access to training and deployment.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env.linux_env import LinuxSecEnv
from agent.dqn_brain import RedTeamAgent
from utils.report_generator import ReportGenerator

class RedTeamGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Red Team Linux Agent - GUI")
        self.root.geometry("1200x800")
        
        # Colors (Hacker theme)
        self.colors = {
            "bg": "#0a0e27",
            "fg": "#00ff00",
            "accent": "#ff0000",
            "secondary": "#1a1e37",
            "highlight": "#2a2e47"
        }
        
        self.root.configure(bg=self.colors["bg"])
        
        # Variables
        self.mode_var = tk.StringVar(value="train")
        self.episodes_var = tk.IntVar(value=100)
        self.model_path_var = tk.StringVar(value="checkpoints/redteam_best.pth")
        self.is_running = False
        self.log_queue = queue.Queue()
        
        self._setup_ui()
        self._start_log_updater()
        
    def _setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header = tk.Label(main_frame, text="🚩 RED TEAM LINUX AGENT", 
                         font=("Courier New", 24, "bold"),
                         bg=self.colors["bg"], fg=self.colors["accent"])
        header.pack(pady=10)
        
        # Control Panel
        control_frame = tk.LabelFrame(main_frame, text="Mission Control", 
                                     bg=self.colors["secondary"], fg=self.colors["fg"],
                                     font=("Courier New", 12, "bold"))
        control_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Mode Selection
        mode_frame = tk.Frame(control_frame, bg=self.colors["secondary"])
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(mode_frame, text="Mode:", bg=self.colors["secondary"], 
                fg=self.colors["fg"], font=("Courier New", 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(mode_frame, text="Train Agent", variable=self.mode_var, value="train",
                      bg=self.colors["secondary"], fg=self.colors["fg"], 
                      selectcolor=self.colors["highlight"],
                      activebackground=self.colors["secondary"],
                      activeforeground=self.colors["accent"],
                      font=("Courier New", 10)).pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(mode_frame, text="Deploy Agent", variable=self.mode_var, value="deploy",
                      bg=self.colors["secondary"], fg=self.colors["fg"],
                      selectcolor=self.colors["highlight"],
                      activebackground=self.colors["secondary"],
                      activeforeground=self.colors["accent"],
                      font=("Courier New", 10)).pack(side=tk.LEFT, padx=10)
        
        # Settings
        settings_frame = tk.Frame(control_frame, bg=self.colors["secondary"])
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Episodes
        tk.Label(settings_frame, text="Episodes:", bg=self.colors["secondary"],
                fg=self.colors["fg"], font=("Courier New", 10)).pack(side=tk.LEFT, padx=5)
        tk.Entry(settings_frame, textvariable=self.episodes_var, width=10,
                bg=self.colors["highlight"], fg=self.colors["fg"],
                font=("Courier New", 10)).pack(side=tk.LEFT, padx=5)
        
        # Model Path
        tk.Label(settings_frame, text="Model:", bg=self.colors["secondary"],
                fg=self.colors["fg"], font=("Courier New", 10)).pack(side=tk.LEFT, padx=20)
        tk.Entry(settings_frame, textvariable=self.model_path_var, width=30,
                bg=self.colors["highlight"], fg=self.colors["fg"],
                font=("Courier New", 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(settings_frame, text="Browse", command=self.browse_model,
                 bg=self.colors["highlight"], fg=self.colors["fg"],
                 font=("Courier New", 9)).pack(side=tk.LEFT, padx=5)
        
        # Action Buttons
        button_frame = tk.Frame(control_frame, bg=self.colors["secondary"])
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = tk.Button(button_frame, text="🚀 START OPERATION",
                                   command=self.start_operation,
                                   bg=self.colors["accent"], fg="white",
                                   font=("Courier New", 12, "bold"),
                                   width=20, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="📊 View Reports",
                 command=self.view_reports,
                 bg=self.colors["highlight"], fg=self.colors["fg"],
                 font=("Courier New", 10),
                 width=15).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="🗑️ Clear Logs",
                 command=self.clear_logs,
                 bg=self.colors["highlight"], fg=self.colors["fg"],
                 font=("Courier New", 10),
                 width=15).pack(side=tk.LEFT, padx=10)
        
        # Content Area
        content_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left: Live Logs
        log_frame = tk.LabelFrame(content_frame, text="Operation Logs",
                                 bg=self.colors["secondary"], fg=self.colors["fg"],
                                 font=("Courier New", 11, "bold"))
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, bg="black", fg=self.colors["fg"],
                                                 font=("Courier New", 9),
                                                 insertbackground=self.colors["fg"])
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right: Stats
        stats_frame = tk.LabelFrame(content_frame, text="Statistics",
                                   bg=self.colors["secondary"], fg=self.colors["fg"],
                                   font=("Courier New", 11, "bold"))
        stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)
        
        self.stats_text = tk.Text(stats_frame, bg=self.colors["highlight"], fg=self.colors["fg"],
                                 font=("Courier New", 10), width=40, height=30)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self._update_stats()
        
        # Status Bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                  bg=self.colors["secondary"], fg=self.colors["fg"],
                                  font=("Courier New", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def log(self, message):
        self.log_queue.put(message)
        
    def _start_log_updater(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self._start_log_updater)
        
    def _update_stats(self):
        stats = f"""
╔═══════════════════════════════════╗
║      AGENT SPECIFICATIONS         ║
╠═══════════════════════════════════╣
║ Architecture: Dueling Double DQN  ║
║ Neurons: 8192 → 4096 → 2048 → 1024║
║ Batch Size: 4096                  ║
║ Memory: 50,000 experiences        ║
║ GPU: CUDA Enabled                 ║
║ Optimization: TF32 + CuDNN        ║
╠═══════════════════════════════════╣
║      ACTION CAPABILITIES          ║
╠═══════════════════════════════════╣
║ Reconnaissance: 5 actions         ║
║ Initial Access: 5 actions         ║
║ Privilege Escalation: 5 actions   ║
║ Persistence: 5 actions            ║
║ Total: 20 tactical actions        ║
╠═══════════════════════════════════╣
║      REWARD STRUCTURE             ║
╠═══════════════════════════════════╣
║ Port Discovery: +10               ║
║ User Access: +50                  ║
║ Reverse Shell: +30                ║
║ Vuln Discovery: +20               ║
║ Privilege Escalation: +100        ║
║ Root Flag: +500 (WIN)             ║
╚═══════════════════════════════════╝
"""
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
        
    def browse_model(self):
        filename = filedialog.askopenfilename(
            title="Select Model File",
            filetypes=[("PyTorch Models", "*.pth"), ("All Files", "*.*")]
        )
        if filename:
            self.model_path_var.set(filename)
            
    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.log("Logs cleared.")
        
    def view_reports(self):
        reports_dir = "reports"
        if os.path.exists(reports_dir):
            os.startfile(reports_dir)
        else:
            messagebox.showinfo("Info", "No reports directory found.")
            
    def start_operation(self):
        if self.is_running:
            return
            
        mode = self.mode_var.get()
        
        if mode == "train":
            self.start_training()
        else:
            self.start_deployment()
            
    def start_training(self):
        episodes = self.episodes_var.get()
        
        if messagebox.askyesno("Confirm Training", 
                              f"Start training for {episodes} episodes?\n\nThis may take a while."):
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED, text="🔄 TRAINING...")
            self.status_bar.config(text=f"Training: 0/{episodes} episodes")
            self.log_text.delete(1.0, tk.END)
            
            threading.Thread(target=self._run_training, args=(episodes,), daemon=True).start()
            
    def start_deployment(self):
        model_path = self.model_path_var.get()
        
        if not os.path.exists(model_path):
            messagebox.showerror("Error", f"Model file not found: {model_path}")
            return
            
        if messagebox.askyesno("Confirm Deployment",
                              "Deploy the trained agent?\n\nThis will run the agent in simulation mode."):
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED, text="⚔️ DEPLOYING...")
            self.status_bar.config(text="Deploying agent...")
            self.log_text.delete(1.0, tk.END)
            
            threading.Thread(target=self._run_deployment, args=(model_path,), daemon=True).start()
            
    def _run_training(self, episodes):
        try:
            self.log("🚩 Initializing Red Team Linux Operation...")
            self.log("=" * 60)
            
            env = LinuxSecEnv()
            agent = RedTeamAgent(state_dim=5, action_dim=20)
            
            os.makedirs("checkpoints", exist_ok=True)
            
            self.log(f"🎯 Target: Linux Server (Simulated)")
            self.log(f"🤖 Agent: RedTeam-v2 (Dueling Double DQN)")
            self.log(f"📚 Training for {episodes} episodes...")
            self.log("=" * 60)
            
            best_reward = -float('inf')
            
            for e in range(episodes):
                state, _ = env.reset()
                total_reward = 0
                done = False
                step_count = 0
                
                reporter = ReportGenerator(target_name=f"Sim_Server_{e}")
                
                while not done:
                    action = agent.act(state)
                    next_state, reward, terminated, truncated, info = env.step(action)
                    done = terminated or truncated
                    step_count += 1
                    
                    reporter.log_action(info['action'], info['output'])
                    
                    if "SUCCESS" in info['output']:
                        reporter.add_finding("Weak Credentials", "HIGH", 
                                           f"Found password via brute force: {info['output']}")
                    if "Connection received" in info['output']:
                        reporter.add_finding("Remote Code Execution", "CRITICAL",
                                           "Reverse shell established.")
                    if "root" in info['output'] and "whoami" in info['action']:
                        reporter.add_finding("Privilege Escalation", "CRITICAL",
                                           "Root access achieved.")
                    
                    agent.remember(state, action, reward, next_state, done)
                    state = next_state
                    total_reward += reward
                    
                    agent.replay()
                
                # Save best model
                if total_reward > best_reward:
                    best_reward = total_reward
                    best_path = os.path.join("checkpoints", "redteam_best.pth")
                    agent.save(best_path)
                
                # Save checkpoint every 50 episodes
                if (e + 1) % 50 == 0:
                    checkpoint_path = os.path.join("checkpoints", f"redteam_ep{e+1}.pth")
                    agent.save(checkpoint_path)
                
                # Progress reporting
                if (e + 1) % 10 == 0:
                    self.log(f"Episode {e+1}/{episodes} | Score: {total_reward:.1f} | "
                            f"Steps: {step_count} | Epsilon: {agent.epsilon:.3f} | Best: {best_reward:.1f}")
                    self.root.after(0, lambda ep=e+1: self.status_bar.config(
                        text=f"Training: {ep}/{episodes} episodes | Best: {best_reward:.1f}"))
            
            # Save final model
            final_path = os.path.join("checkpoints", "redteam_final.pth")
            agent.save(final_path)
            
            self.log("=" * 60)
            self.log(f"✅ Operation Complete. Agent is ready for deployment.")
            self.log(f"📊 Best Score: {best_reward:.1f}")
            self.log(f"💾 Models saved in: checkpoints/")
            self.log("=" * 60)
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL, text="🚀 START OPERATION"))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))
            
    def _run_deployment(self, model_path):
        try:
            self.log("🚀 Initializing Red Team Agent Deployment...")
            self.log("=" * 60)
            
            env = LinuxSecEnv()
            agent = RedTeamAgent(state_dim=5, action_dim=20)
            
            if not agent.load(model_path):
                self.log(f"⚠️ Warning: Could not load model from {model_path}")
                self.log("Running with untrained agent...")
            
            self.log(f"🎯 Target: Linux Server (Simulated)")
            self.log(f"🤖 Agent: RedTeam-v2 (Dueling Double DQN)")
            self.log("=" * 60)
            
            state, _ = env.reset()
            done = False
            total_reward = 0
            step_count = 0
            
            reporter = ReportGenerator(target_name="Target_Server")
            
            while not done:
                action = agent.act(state, training=False)
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                
                step_count += 1
                total_reward += reward
                
                reporter.log_action(info['action'], info['output'])
                
                if "SUCCESS" in info['output']:
                    reporter.add_finding("Weak Credentials", "HIGH",
                                       f"Found password via brute force: {info['output']}")
                if "Connection received" in info['output']:
                    reporter.add_finding("Remote Code Execution", "CRITICAL",
                                       "Reverse shell established.")
                if "root" in info['output'] and "whoami" in info['action']:
                    reporter.add_finding("Privilege Escalation", "CRITICAL",
                                       "Root access achieved.")
                
                self.log(f"Step {step_count}: {info['action']}")
                self.log(f"   └── {info['output']}")
                self.log(f"   └── Reward: {reward:.1f}")
                
                state = next_state
            
            # Generate report
            report_path = reporter.generate_report()
            
            self.log("-" * 60)
            self.log(f"🏁 Operation Finished")
            self.log(f"💰 Total Reward: {total_reward:.1f}")
            self.log(f"👣 Total Steps: {step_count}")
            self.log(f"📄 Report: {report_path}")
            
            if total_reward > 500:
                self.log("🎉 ROOT FLAG CAPTURED!")
            elif total_reward > 100:
                self.log("✅ Successful compromise")
            else:
                self.log("⚠️ Partial success")
            
            self.log("=" * 60)
            self.log("✅ Deployment Complete")
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL, text="🚀 START OPERATION"))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

if __name__ == "__main__":
    root = tk.Tk()
    app = RedTeamGUI(root)
    root.mainloop()
