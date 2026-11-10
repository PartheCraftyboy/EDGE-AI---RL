"""
RL Training Script: Tabular Q-Learning for Adaptive Edge Sensing
Trains the agent, compares against fixed-rate baselines, generates visual plots,
and exports the Q-table to a C-header for ESP32-S3 deployment.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from env import AdaptiveAirQualityEnv
import os

def train_q_learning(num_episodes=2000, alpha=0.15, gamma=0.95, epsilon_start=1.0, epsilon_min=0.02, decay_rate=0.997):
    env = AdaptiveAirQualityEnv(random_seed=42)
    Q = np.zeros((env.num_states, env.num_actions))
    
    epsilon = epsilon_start
    rewards_history = []
    
    print(f"Starting Q-Learning training for {num_episodes} episodes...")
    for ep in range(num_episodes):
        state = env.reset()
        total_reward = 0.0
        done = False
        
        while not done:
            # Epsilon-greedy action selection
            if np.random.rand() < epsilon:
                action = np.random.choice(env.num_actions)
            else:
                action = np.argmax(Q[state])
                
            next_state, reward, done, info = env.step(action)
            
            # Bellman update equation
            best_next_a = np.argmax(Q[next_state])
            td_target = reward + gamma * Q[next_state, best_next_a]
            Q[state, action] += alpha * (td_target - Q[state, action])
            
            state = next_state
            total_reward += reward
            
        epsilon = max(epsilon_min, epsilon * decay_rate)
        rewards_history.append(total_reward)
        
        if (ep + 1) % 250 == 0:
            avg_rew = np.mean(rewards_history[-100:])
            print(f"Episode {ep+1}/{num_episodes} | Avg Reward (last 100): {avg_rew:.2f} | Epsilon: {epsilon:.3f}")
            
    return Q, rewards_history

def evaluate_policies(Q, num_test_episodes=50):
    env = AdaptiveAirQualityEnv(random_seed=100)
    
    # Track metrics for 3 strategies:
    # 1. Fixed High-Rate (Always 10s sleep, heat, alert when temp>50)
    # 2. Fixed Low-Rate (Always 600s sleep, heat, alert when temp>50)
    # 3. RL Adaptive Policy
    results = {
        "Fixed_High_Rate": {"energy_j": [], "latency_s": [], "detected": []},
        "Fixed_Low_Rate":  {"energy_j": [], "latency_s": [], "detected": []},
        "RL_Adaptive":     {"energy_j": [], "latency_s": [], "detected": []}
    }
    
    for ep in range(num_test_episodes):
        # 1. RL Agent
        state = env.reset()
        done = False
        total_e_rl = 0.0
        detect_time_rl = None
        while not done:
            a = np.argmax(Q[state])
            state, r, done, info = env.step(a)
            total_e_rl += info["energy_spent_step"]
            if info["fire_active"] and not detect_time_rl and a == 3:
                detect_time_rl = info["time_sec"] - env.fire_start_time
                
        results["RL_Adaptive"]["energy_j"].append(total_e_rl)
        results["RL_Adaptive"]["detected"].append(env.fire_detected)
        results["RL_Adaptive"]["latency_s"].append(detect_time_rl if detect_time_rl else 120.0)

        # 2. Fixed High-Rate (Action 2: 10s sleep until temp>50 -> Action 3)
        state = env.reset()
        done = False
        total_e_high = 0.0
        detect_time_high = None
        while not done:
            a = 3 if env.ambient_temp > 50.0 or env.gas_resistance < 10.0 else 2
            state, r, done, info = env.step(a)
            total_e_high += info["energy_spent_step"]
            if info["fire_active"] and not detect_time_high and a == 3:
                detect_time_high = info["time_sec"] - env.fire_start_time
                
        results["Fixed_High_Rate"]["energy_j"].append(total_e_high)
        results["Fixed_High_Rate"]["detected"].append(env.fire_detected)
        results["Fixed_High_Rate"]["latency_s"].append(detect_time_high if detect_time_high else 120.0)

        # 3. Fixed Low-Rate (Action 0: 600s sleep until temp>50 -> Action 3)
        state = env.reset()
        done = False
        total_e_low = 0.0
        detect_time_low = None
        while not done:
            a = 3 if env.ambient_temp > 50.0 or env.gas_resistance < 10.0 else 0
            state, r, done, info = env.step(a)
            total_e_low += info["energy_spent_step"]
            if info["fire_active"] and not detect_time_low and a == 3:
                detect_time_low = info["time_sec"] - env.fire_start_time
                
        results["Fixed_Low_Rate"]["energy_j"].append(total_e_low)
        results["Fixed_Low_Rate"]["detected"].append(env.fire_detected)
        results["Fixed_Low_Rate"]["latency_s"].append(detect_time_low if detect_time_low else 300.0)
        
    return results

def export_q_table_to_c(Q, filepath):
    """Exports trained Q-table as C header file for embedded ESP32 deployment."""
    num_states, num_actions = Q.shape
    with open(filepath, "w") as f:
        f.write("/*\n")
        f.write(" * Auto-generated Q-Table for M5Stamp ESP32-S3 Fire & Gas Adaptive Sensing\n")
        f.write(f" * Dimensions: {num_states} states x {num_actions} actions\n")
        f.write(" * Actions:\n")
        f.write(" *   0: DEEP_SLEEP_LONG  (600s, no heater, no wifi)\n")
        f.write(" *   1: NORMAL_CYCLE     (60s, pulse heater, no wifi)\n")
        f.write(" *   2: ELEVATED_SCAN    (10s, pulse heater, no wifi)\n")
        f.write(" *   3: EMERGENCY_ALERT  (2s, full heater, turn on WiFi & Alert AWS)\n")
        f.write(" */\n\n")
        f.write("#ifndef Q_TABLE_EXPORT_H\n")
        f.write("#define Q_TABLE_EXPORT_H\n\n")
        f.write(f"#define NUM_STATES {num_states}\n")
        f.write(f"#define NUM_ACTIONS {num_actions}\n\n")
        f.write("static const float Q_TABLE[NUM_STATES][NUM_ACTIONS] = {\n")
        for s in range(num_states):
            row_str = ", ".join([f"{Q[s, a]:.4f}f" for a in range(num_actions)])
            f.write(f"    /* State {s:02d} */ {{ {row_str} }},\n")
        f.write("};\n\n")
        f.write("inline int get_rl_action(int state_idx) {\n")
        f.write("    if (state_idx < 0 || state_idx >= NUM_STATES) return 1; // default NORMAL_CYCLE\n")
        f.write("    int best_a = 0;\n")
        f.write("    float max_q = Q_TABLE[state_idx][0];\n")
        f.write("    for (int a = 1; a < NUM_ACTIONS; a++) {\n")
        f.write("        if (Q_TABLE[state_idx][a] > max_q) {\n")
        f.write("            max_q = Q_TABLE[state_idx][a];\n")
        f.write("            best_a = a;\n")
        f.write("        }\n")
        f.write("    }\n")
        f.write("    return best_a;\n")
        f.write("}\n\n")
        f.write("#endif // Q_TABLE_EXPORT_H\n")
    print(f"Exported Q-table header to: {filepath}")

def plot_results(rewards, results):
    os.makedirs("docs/figures", exist_ok=True)
    
    # 1. Training Convergence Curve
    plt.figure(figsize=(8, 4.5))
    window = 50
    smoothed = np.convolve(rewards, np.ones(window)/window, mode='valid')
    plt.plot(smoothed, color='#2563eb', linewidth=2, label='50-ep Moving Avg')
    plt.title('Reinforcement Learning Policy Convergence (Reward vs Episode)', fontsize=12, fontweight='bold')
    plt.xlabel('Episode', fontsize=11)
    plt.ylabel('Episode Reward', fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig('docs/figures/training_curve.png', dpi=300)
    plt.close()
    
    # 2. Energy Consumption Comparison (Bar Chart)
    labels = ['Fixed High-Rate\n(10s Poll)', 'RL Adaptive\n(Our Model)', 'Fixed Low-Rate\n(600s Poll)']
    avg_energy = [
        np.mean(results['Fixed_High_Rate']['energy_j']),
        np.mean(results['RL_Adaptive']['energy_j']),
        np.mean(results['Fixed_Low_Rate']['energy_j'])
    ]
    avg_latency = [
        np.mean(results['Fixed_High_Rate']['latency_s']),
        np.mean(results['RL_Adaptive']['latency_s']),
        np.mean(results['Fixed_Low_Rate']['latency_s'])
    ]
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    
    color = '#10b981'
    ax1.set_ylabel('Energy Consumed (Joules per Episode)', color=color, fontsize=11, fontweight='bold')
    bars = ax1.bar(labels, avg_energy, color=['#ef4444', '#10b981', '#f59e0b'], width=0.45, alpha=0.85)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Add value labels on bars
    for bar in bars:
        h = bar.get_height()
        ax1.annotate(f'{h:.2f} J',
                     xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points",
                     ha='center', va='bottom', fontweight='bold')
                     
    # Detection Latency on secondary axis
    ax2 = ax1.twinx()
    color2 = '#3b82f6'
    ax2.set_ylabel('Avg Detection Latency (Seconds)', color=color2, fontsize=11, fontweight='bold')
    ax2.plot(labels, avg_latency, color=color2, marker='o', linewidth=2.5, markersize=8)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    for i, txt in enumerate(avg_latency):
        ax2.annotate(f'{txt:.1f}s', (labels[i], avg_latency[i] + 5), ha='center', fontweight='bold', color=color2)

    plt.title('Performance & Energy Trade-off: RL vs Fixed Baselines', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('docs/figures/energy_comparison.png', dpi=300)
    plt.close()
    print("Saved evaluation charts to docs/figures/")

if __name__ == "__main__":
    Q, rewards = train_q_learning(num_episodes=1500)
    results = evaluate_policies(Q, num_test_episodes=30)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)
    
    q_table_sim = os.path.join(base_dir, "q_table_export.h")
    q_table_fw = os.path.join(root_dir, "firmware", "m5stamp_fire_gas_monitor", "q_table_export.h")
    
    export_q_table_to_c(Q, q_table_sim)
    export_q_table_to_c(Q, q_table_fw)
    
    # Save plots inside docs/figures
    os.chdir(root_dir)
    plot_results(rewards, results)
    
    e_high = np.mean(results['Fixed_High_Rate']['energy_j'])
    e_rl = np.mean(results['RL_Adaptive']['energy_j'])
    pct_saved = ((e_high - e_rl) / e_high) * 100.0
    print(f"\n================ SUMMARY ================")
    print(f"Fixed High-Rate Energy: {e_high:.2f} J")
    print(f"RL Adaptive Energy:     {e_rl:.2f} J")
    print(f"Energy Saved by RL:     {pct_saved:.1f}%")
    print(f"RL Detection Latency:   {np.mean(results['RL_Adaptive']['latency_s']):.1f} seconds")
    print(f"=========================================\n")
