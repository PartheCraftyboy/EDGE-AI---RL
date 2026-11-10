"""
Custom Gymnasium Environment: Adaptive Edge Sensing for Indoor Fire & Gas Detection
Simulates:
1. Environmental dynamics: Ambient temperature and gas resistance (BME680).
2. Hazard events: Sudden fires and gas leaks with realistic temperature/gas transients.
3. Hardware power dissipation:
   - Deep sleep (15 uA)
   - BME680 pulsed micro-hotplate heating (12 mA @ 30 ms)
   - ESP32-S3 active processing (25 mA @ 10 ms)
   - Wi-Fi radio transmission burst (150 mA @ 1200 ms)
4. LiFePO4 battery model (3.2V, 600 mAh capacity = 6912 Joules).
"""

import numpy as np

class AdaptiveAirQualityEnv:
    def __init__(self, random_seed=42):
        np.random.seed(random_seed)
        
        # Power & Hardware parameters (Joules)
        self.V_BAT = 3.2  # Volts
        self.BATTERY_CAPACITY_JOULES = 600 * 1e-3 * self.V_BAT * 3600  # 600 mAh = 6912 J
        
        self.P_SLEEP = 15e-6 * self.V_BAT          # 0.048 mW
        self.E_SENSE_HEAT = 12e-3 * self.V_BAT * 0.030   # 1.152 mJ (heater burst 30ms)
        self.E_SENSE_NO_HEAT = 1e-3 * self.V_BAT * 0.010 # 0.032 mJ
        self.E_MCU_ACTIVE = 25e-3 * self.V_BAT * 0.015   # 1.200 mJ (active 15ms)
        self.E_WIFI_TX = 150e-3 * self.V_BAT * 1.2       # 576.0 mJ (Wi-Fi 1.2s)
        
        # Action definitions: (sleep_duration_seconds, fire_heater, enable_wifi)
        self.ACTIONS = {
            0: {"name": "DEEP_SLEEP_LONG",  "sleep_sec": 600, "heat": False, "wifi": False},
            1: {"name": "NORMAL_CYCLE",     "sleep_sec": 60,  "heat": True,  "wifi": False},
            2: {"name": "ELEVATED_SCAN",    "sleep_sec": 10,  "heat": True,  "wifi": False},
            3: {"name": "EMERGENCY_ALERT",   "sleep_sec": 2,   "heat": True,  "wifi": True},
        }
        self.num_actions = len(self.ACTIONS)
        
        # State space discretization:
        # Temp: 0 (Normal < 35°C), 1 (Elevated 35-50°C), 2 (Critical > 50°C)
        # Gas: 0 (Clean > 30kΩ), 1 (Suspicious 10-30kΩ), 2 (Hazard < 10kΩ)
        # Gas Trend: 0 (Stable / Rising R), 1 (Dropping R fast)
        # Battery: 0 (Low < 30%), 1 (Medium 30-70%), 2 (High > 70%)
        # Total discrete states = 3 * 3 * 2 * 3 = 54
        self.num_states = 3 * 3 * 2 * 3
        
        self.reset()
        
    def reset(self):
        self.time_seconds = 0.0
        self.battery_remaining_joules = self.BATTERY_CAPACITY_JOULES
        
        # True physical state
        self.ambient_temp = 25.0 + np.random.uniform(-2, 2)
        self.gas_resistance = 45.0 + np.random.uniform(-5, 5)  # in kOhms (higher = clean)
        self.last_measured_gas = self.gas_resistance
        self.last_measured_temp = self.ambient_temp
        self.gas_derivative = 0.0
        
        # Hazard scheduling: fire starts between 3000s and 8000s with 50% probability
        self.has_fire = np.random.rand() < 0.6
        self.fire_start_time = np.random.uniform(2000, 7000) if self.has_fire else 999999
        self.fire_active = False
        self.fire_detected = False
        self.detection_delay = 0.0
        
        return self._get_state()
        
    def _get_discrete_state(self, temp, gas_r, gas_deriv, soc_pct):
        # Temp bin (0, 1, 2)
        if temp < 35.0:
            t_bin = 0
        elif temp < 50.0:
            t_bin = 1
        else:
            t_bin = 2
            
        # Gas resistance bin (0: clean, 1: suspicious, 2: hazard)
        if gas_r > 30.0:
            g_bin = 0
        elif gas_r > 10.0:
            g_bin = 1
        else:
            g_bin = 2
            
        # Derivative bin (0: stable/rising, 1: dropping fast)
        d_bin = 1 if gas_deriv < -0.5 else 0
        
        # Battery SoC bin (0: <30%, 1: 30-70%, 2: >70%)
        if soc_pct < 0.30:
            b_bin = 0
        elif soc_pct < 0.70:
            b_bin = 1
        else:
            b_bin = 2
            
        state_idx = (t_bin * 18) + (g_bin * 6) + (d_bin * 3) + b_bin
        return state_idx

    def _get_state(self):
        soc = self.battery_remaining_joules / self.BATTERY_CAPACITY_JOULES
        return self._get_discrete_state(
            self.last_measured_temp,
            self.last_measured_gas,
            self.gas_derivative,
            soc
        )

    def step(self, action_idx):
        action = self.ACTIONS[action_idx]
        dt = action["sleep_sec"]
        
        # Advance physical simulation over duration dt
        self.time_seconds += dt
        
        # Check if fire has ignited
        if self.has_fire and self.time_seconds >= self.fire_start_time:
            self.fire_active = True
            
        if self.fire_active:
            # Physical dynamics under fire: Temp rises, gas resistance plunges
            self.ambient_temp += 0.8 * dt + np.random.normal(0, 0.2)
            self.ambient_temp = min(self.ambient_temp, 95.0)
            
            # Smoke drops gas resistance exponentially toward 1-3 kOhm
            self.gas_resistance = max(1.5, self.gas_resistance - (0.4 * dt))
        else:
            # Normal ambient fluctuation
            self.ambient_temp += np.random.normal(0, 0.05)
            self.ambient_temp = np.clip(self.ambient_temp, 18.0, 32.0)
            self.gas_resistance += np.random.normal(0, 0.1)
            self.gas_resistance = np.clip(self.gas_resistance, 35.0, 60.0)

        # Energy consumed during this step
        energy_spent = self.P_SLEEP * dt + self.E_MCU_ACTIVE
        
        if action["heat"]:
            energy_spent += self.E_SENSE_HEAT
            # Accurate sensor reading when hotplate is heated
            measured_temp = self.ambient_temp + np.random.normal(0, 0.2)
            measured_gas = self.gas_resistance + np.random.normal(0, 0.3)
        else:
            energy_spent += self.E_SENSE_NO_HEAT
            # Stale / noisy estimate if unheated
            measured_temp = self.ambient_temp + np.random.normal(0, 0.8)
            measured_gas = self.last_measured_gas  # No new gas reading without heating!
            
        if action["wifi"]:
            energy_spent += self.E_WIFI_TX
            
        self.battery_remaining_joules = max(0.0, self.battery_remaining_joules - energy_spent)
        
        # Update derivatives
        if dt > 0:
            self.gas_derivative = (measured_gas - self.last_measured_gas) / dt
        self.last_measured_temp = measured_temp
        self.last_measured_gas = measured_gas
        
        # Reward calculation
        reward = 0.0
        
        # 1. Energy penalty (scaled so ~1 Joule spent = -10 reward)
        reward -= (energy_spent / 0.1) * 0.5
        
        # 2. Fire & Hazard detection dynamics
        if self.fire_active:
            if action["wifi"] and (measured_temp > 50.0 or measured_gas < 12.0):
                # Correct emergency alert transmitted!
                if not self.fire_detected:
                    self.fire_detected = True
                    time_to_detect = self.time_seconds - self.fire_start_time
                    # Large bonus for fast detection
                    reward += 150.0 - min(100.0, time_to_detect * 0.5)
                else:
                    reward += 20.0  # Continued tracking
            else:
                # Fire is active but agent is sleeping or failing to alert!
                reward -= 15.0 * (dt / 10.0)
        else:
            # False alarm penalty: Firing Wi-Fi emergency alert when no fire exists
            if action["wifi"]:
                reward -= 80.0
                
        # Episode termination
        done = False
        if self.battery_remaining_joules <= 0:
            done = True
            reward -= 200.0  # Dead battery penalty
        elif self.time_seconds >= 12000:  # ~3.3 simulated hours per episode
            done = True
        elif self.fire_detected and (self.time_seconds - self.fire_start_time > 120):
            # Episode complete 2 mins after fire safely transmitted
            done = True
            
        next_state = self._get_state()
        info = {
            "time_sec": self.time_seconds,
            "temp": self.ambient_temp,
            "gas_r": self.gas_resistance,
            "battery_j": self.battery_remaining_joules,
            "fire_active": self.fire_active,
            "fire_detected": self.fire_detected,
            "energy_spent_step": energy_spent
        }
        
        return next_state, reward, done, info
