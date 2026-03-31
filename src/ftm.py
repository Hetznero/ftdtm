import numpy as np
import matplotlib.pyplot as plt

AGENT_UPDATE_PROB = 0.05
PENALTY_WEIGHT = 2.0
APPEAL_DEATH_THRESHOLD = 0.1

DDM_BASE_DRIFT = 0.05
DDM_NOISE = 0.05
ENERGY_REVIVE_THRESHOLD = 1.0
ENERGY_DEAD_THRESHOLD = -1.0

STATE_DEAD = -1
STATE_PASSIVE = 0
STATE_ACTIVE = 1

class Trend:
    def __init__(self, trend_id):
        self.id = trend_id
        self.quality = np.random.uniform(0.6, 1.4)
        self.state = STATE_ACTIVE
        self.age = 0
        self.energy = 0.0
        self.appeal = -999.0
        self.popularity = 0.0

    def update_ddm(self):
        if self.state == STATE_PASSIVE:
            drift = DDM_BASE_DRIFT * (self.quality - 1.0)
            self.energy += drift + np.random.normal(0, DDM_NOISE)
            
            if self.energy >= ENERGY_REVIVE_THRESHOLD:
                self.state = STATE_ACTIVE
                self.age = 0
                self.energy = 0.0
            elif self.energy <= ENERGY_DEAD_THRESHOLD:
                self.state = STATE_DEAD

    def update_active_appeal(self):
        if self.state == STATE_ACTIVE:
            self.age += 1
            peak_time = 80 * self.quality
            spread = 30 * self.quality
            
            self.appeal = self.quality * np.exp(-0.5 * ((self.age - peak_time) / spread)**2)
            
            if self.age > peak_time and self.appeal < APPEAL_DEATH_THRESHOLD:
                self.state = STATE_PASSIVE
                self.energy = 0.0
                self.appeal = -999.0
        elif self.state in [STATE_PASSIVE, STATE_DEAD]:
            self.appeal = -999.0

class Human:
    def __init__(self, human_id):
        self.id = human_id
        self.target_popularity = np.random.normal(0.0, 1)
        self.current_trend = None

    def choose_trend(self, active_trends):
        if np.random.rand() > AGENT_UPDATE_PROB or not active_trends:
            return
            
        best_utility = -np.inf
        best_trend_id = self.current_trend
        
        for trend in active_trends:
            utility = trend.appeal - PENALTY_WEIGHT * abs(trend.popularity - self.target_popularity)
            utility += np.random.normal(0, 0.1) 
            
            if utility > best_utility:
                best_utility = utility
                best_trend_id = trend.id
        self.current_trend = best_trend_id

class World:
    def __init__(self, initial_pop=1000, n_initial_trends=5, base_spawn_prob=0.01, total_steps=1200):
        self.n_agents = initial_pop
        self.base_spawn_prob = base_spawn_prob
        self.total_steps = total_steps
        self.tech_midpoint = total_steps / 2
        
        self.humans = [Human(i) for i in range(initial_pop)]
        self.trends = [Trend(i) for i in range(n_initial_trends)]
        
        for h in self.humans:
            h.current_trend = np.random.randint(0, n_initial_trends)
            
        self.history_popularity = []
        self.history_state_counts = [] 
        self.history_states = [] 
        self.history_energies = [] 
        self.current_step = 0

    def step(self):
        tech_multiplier = 1.0 + (10.0 / (1.0 + np.exp(-0.02 * (self.current_step - self.tech_midpoint))))
        
        if np.random.rand() < (self.base_spawn_prob * tech_multiplier):
            self.trends.append(Trend(len(self.trends)))

        for trend in self.trends:
            trend.update_ddm()

        trend_counts = {t.id: 0 for t in self.trends}
        for h in self.humans:
            if h.current_trend is not None:
                trend_counts[h.current_trend] += 1
                
        for trend in self.trends:
            trend.popularity = trend_counts[trend.id] / self.n_agents
            
        self.history_popularity.append([t.popularity for t in self.trends])

        active_trends = []
        for trend in self.trends:
            trend.update_active_appeal()
            if trend.state == STATE_ACTIVE:
                active_trends.append(trend)

        for human in self.humans:
            human.choose_trend(active_trends)
            
        active_count = passive_count = dead_count = 0
        for trend in self.trends:
            if trend.state == STATE_ACTIVE: active_count += 1
            elif trend.state == STATE_PASSIVE: passive_count += 1
            elif trend.state == STATE_DEAD: dead_count += 1
        self.history_state_counts.append([active_count, passive_count, dead_count])

        self.history_states.append([t.state for t in self.trends]) 
        self.history_energies.append([t.energy for t in self.trends])
        self.current_step += 1

    def run(self, steps=None):
        run_steps = steps if steps is not None else self.total_steps
        for _ in range(run_steps):
            self.step()

    def plot_results(self):
        n_total_trends = len(self.trends)
        colors = plt.cm.turbo(np.linspace(0, 1, n_total_trends))
        
        padded_pop = []
        padded_states = []
        padded_energies = []
        
        for pop_data, state_data, energy_data in zip(self.history_popularity, self.history_states, self.history_energies):
            padding = [np.nan] * (n_total_trends - len(pop_data))
            padded_pop.append(pop_data + padding)
            padded_states.append(state_data + padding)
            padded_energies.append(energy_data + padding)
            
        history_popularity_array = np.array(padded_pop)
        history_states_array = np.array(padded_states)
        history_energies_array = np.array(padded_energies)

        # Plot 1: Popularity
        plt.figure(figsize=(10, 4))
        for i in range(n_total_trends):
            plt.plot(history_popularity_array[:, i], linewidth=2, color=colors[i])
        plt.title(f"Fashion Trend Cycles over Time")
        plt.ylabel("Popularity")
        plt.xlabel("Time Steps")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        # Plot 2: Individual Trend States
        plt.figure(figsize=(10, 4))
        for i in range(n_total_trends):
            plt.plot(history_states_array[:, i] + (i * 0.01), alpha=0.4, color=colors[i]) 
        plt.title("State Tracking for Each Trend")
        plt.ylabel("State")
        plt.xlabel("Time Steps")
        plt.yticks([-1, 0, 1], ['Dead', 'Passive', 'Active'])
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        # Plot 3: Energy / Drift Process
        plt.figure(figsize=(10, 4))
        drift_array = np.where(history_states_array == STATE_PASSIVE, history_energies_array, np.nan)
        for i in range(n_total_trends):
            plt.plot(drift_array[:, i], alpha=0.7, color=colors[i]) 
        plt.axhline(y=ENERGY_REVIVE_THRESHOLD, color='r', linestyle='--', alpha=0.5, label='Revive Threshold')
        plt.axhline(y=ENERGY_DEAD_THRESHOLD, color='k', linestyle='--', alpha=0.5, label='Dead Threshold')
        plt.title("DDM Drift of Trends in Passive State")
        plt.ylabel("Energy")
        plt.xlabel("Time Steps")
        plt.grid(True, alpha=0.3)
        plt.legend(loc="upper right", fontsize='small')
        plt.tight_layout()
        plt.show()

    def plot_selection_trends(self, trend_ids):
        n_total_trends = len(self.trends)
        colors = plt.cm.turbo(np.linspace(0, 1, n_total_trends))
        valid_ids = [tid for tid in trend_ids if tid < n_total_trends]
        if not valid_ids: return

        padded_pop = [d + [np.nan] * (n_total_trends - len(d)) for d in self.history_popularity]
        history_popularity_array = np.array(padded_pop)

        plt.figure(figsize=(10, 4))
        for tid in valid_ids:
            plt.plot(history_popularity_array[:, tid], label=f'Trend {tid}', linewidth=2.5, color=colors[tid])
        plt.title(f"Popularity Over Time: Selected Trends", fontsize=14)
        plt.ylabel("Popularity")
        plt.xlabel("Time Steps")
        plt.grid(True, alpha=0.3)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.show()