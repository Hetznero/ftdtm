import numpy as np
import matplotlib.pyplot as plt
import random

INITIAL_POP = 1000
YEARS = 300
QUARTERS_PER_YEAR = 4
TOTAL_QUARTERS = YEARS * QUARTERS_PER_YEAR 

N_INITIAL_TRENDS = 5
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
    def __init__(self, human_id, age, sex):
        self.id = human_id
        self.age = age
        self.sex = sex 
        self.alive = True
        self.target_popularity = np.random.normal(0, 1)
        self.current_trend = None

    def demographic_step(self, resource_level):
        self.age += 1
        base_death_prob = 0.015 * np.exp(0.04 * self.age)
        actual_death_prob = base_death_prob * (1 - 0.85 * resource_level)
        
        if random.random() < actual_death_prob or self.age > 100:
            self.alive = False
            self.current_trend = None 
            return 0  
            
        if self.sex == 0 and 15 <= self.age <= 45:
            base_birth_prob = 0.2
            actual_birth_prob = base_birth_prob * (1 - 0.65 * resource_level)
            if random.random() < actual_birth_prob:
                return 1 
        return 0

    def fashion_step(self, active_trends):
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
    def __init__(self, initial_pop=INITIAL_POP, n_initial_trends=5, years=YEARS, base_spawn_prob=0.01):
        self.years = years
        self.total_quarters = years * QUARTERS_PER_YEAR
        self.current_quarter = 0
        self.next_human_id = 0
        self.base_spawn_prob = base_spawn_prob
        self.tech_midpoint = self.total_quarters / 2
        
        self.agents = []
        for _ in range(initial_pop):
            age = int(np.random.exponential(scale=20))
            if age > 80: age = 80
            sex = random.choice([0, 1])
            self.agents.append(Human(self.next_human_id, age, sex))
            self.next_human_id += 1
            
        self.trends = [Trend(i) for i in range(n_initial_trends)]
        for h in self.agents:
            h.current_trend = np.random.randint(0, n_initial_trends)
            
        self.history_fashion_pop = []
        self.history_fashion_states = []
        self.history_fashion_energies = [] 
        self.demo_history = {'pop': [], 'births': [], 'deaths': [], 'resources': []}

    def get_resource_level(self, year):
        return 1 / (1 + np.exp(-0.05 * (year - 150)))

    def step(self):
        tech_multiplier = 1.0 + (10.0 / (1.0 + np.exp(-0.02 * (self.current_quarter - self.tech_midpoint))))
        if np.random.rand() < (self.base_spawn_prob * tech_multiplier):
            self.trends.append(Trend(len(self.trends)))

        for trend in self.trends:
            trend.update_ddm()

        trend_counts = {t.id: 0 for t in self.trends}
        current_pop = len(self.agents)
        for h in self.agents:
            if h.current_trend is not None:
                trend_counts[h.current_trend] += 1
                
        for trend in self.trends:
            trend.popularity = (trend_counts[trend.id] / current_pop) if current_pop > 0 else 0
            
        self.history_fashion_pop.append([t.popularity for t in self.trends])

        active_trends = []
        for trend in self.trends:
            trend.update_active_appeal()
            if trend.state == STATE_ACTIVE:
                active_trends.append(trend)

        for human in self.agents:
            human.fashion_step(active_trends)
            
        self.history_fashion_states.append([t.state for t in self.trends]) 
        self.history_fashion_energies.append([t.energy for t in self.trends])

        if (self.current_quarter + 1) % QUARTERS_PER_YEAR == 0:
            current_year = self.current_quarter // QUARTERS_PER_YEAR
            resources = self.get_resource_level(current_year)
            births_this_year = 0
            deaths_this_year = 0
            
            for agent in self.agents:
                birth = agent.demographic_step(resources)
                if not agent.alive: deaths_this_year += 1
                else: births_this_year += birth
            
            self.agents = [a for a in self.agents if a.alive]
            for _ in range(births_this_year):
                self.agents.append(Human(self.next_human_id, age=0, sex=random.choice([0, 1])))
                self.next_human_id += 1
                
            new_pop_size = len(self.agents)
            self.demo_history['pop'].append(new_pop_size)
            self.demo_history['births'].append((births_this_year / new_pop_size) * 1000 if new_pop_size > 0 else 0)
            self.demo_history['deaths'].append((deaths_this_year / new_pop_size) * 1000 if new_pop_size > 0 else 0)
            self.demo_history['resources'].append(resources)

        self.current_quarter += 1

    def run(self):
        for _ in range(self.total_quarters):
            self.step()
    def plot_results(self):
        n_total_trends = len(self.trends)
        colors = plt.cm.turbo(np.linspace(0, 1, n_total_trends))
        
        padded_pop = [d + [np.nan] * (n_total_trends - len(d)) for d in self.history_fashion_pop]
        padded_states = [d + [np.nan] * (n_total_trends - len(d)) for d in self.history_fashion_states]
        padded_energies = [d + [np.nan] * (n_total_trends - len(d)) for d in self.history_fashion_energies]
            
        history_popularity_array = np.array(padded_pop)
        history_states_array = np.array(padded_states)
        history_energies_array = np.array(padded_energies)

        # Plot 1: Fashion Popularity
        plt.figure(figsize=(10, 4))
        for i in range(n_total_trends):
            plt.plot(history_popularity_array[:, i], linewidth=1.5, alpha=0.8, color=colors[i])
        plt.title(f"Fashion Trend Cycles over Time")
        plt.ylabel("Popularity")
        plt.xlabel("Time Steps")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        # Plot 2: Individual Trend States
        plt.figure(figsize=(10, 4))
        for i in range(n_total_trends):
            plt.plot(history_states_array[:, i] + (i * 0.01), alpha=0.5, color=colors[i]) 
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
        plt.axhline(y=ENERGY_REVIVE_THRESHOLD, color='r', linestyle='--', alpha=0.5, label='Revive')
        plt.axhline(y=ENERGY_DEAD_THRESHOLD, color='k', linestyle='--', alpha=0.5, label='Death')
        plt.title("DDM Drift of Trends in Passive State")
        plt.ylabel("Energy")
        plt.xlabel("Time Steps")
        plt.grid(True, alpha=0.3)
        plt.legend(loc="upper right", fontsize='small')
        plt.tight_layout()
        plt.show()

        # Plot 4: Demographics
        years_x = np.arange(self.years)
        fig, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(years_x, self.demo_history['births'], label='Birth Rate', color='forestgreen')
        ax1.plot(years_x, self.demo_history['deaths'], label='Death Rate', color='crimson')
        ax1.set_ylabel("Rate per 1,000")
        ax1.set_xlabel("Years")
        ax1.grid(True, alpha=0.3)
        ax2 = ax1.twinx()
        ax2.plot(years_x, self.demo_history['pop'], label='Total Pop', color='royalblue', linewidth=2)
        ax2.set_ylabel('Total Population', color='royalblue')
        plt.title("Demographic Rates and Total Population")
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
        plt.tight_layout()
        plt.show()
    
    def plot_selection_trends(self, trend_ids):
        n_total_trends = len(self.trends)
        colors = plt.cm.turbo(np.linspace(0, 1, n_total_trends))
        valid_ids = [tid for tid in trend_ids if tid < n_total_trends]
        if not valid_ids: return

        padded_pop = [d + [np.nan] * (n_total_trends - len(d)) for d in self.history_fashion_pop]
        history_popularity_array = np.array(padded_pop)

        plt.figure(figsize=(10, 4))
        for tid in valid_ids:
            plt.plot(history_popularity_array[:, tid], label=f'Trend {tid}', linewidth=2.5, color=colors[tid])
        plt.title(f"Popularity Over Time: Selected Trends", fontsize=14)
        plt.ylabel("Popularity")
        plt.xlabel("Time Steps (Quarters)")
        plt.grid(True, alpha=0.3)
        plt.legend(loc="upper left")
        plt.tight_layout()
        plt.show()