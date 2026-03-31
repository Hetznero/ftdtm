import numpy as np
import matplotlib.pyplot as plt
import random
import os
import matplotlib.animation as animation

class Human:
    def __init__(self, age, sex):
        self.id = id(self)
        self.age = age
        self.sex = sex  # 0 for Female, 1 for Male
        self.alive = True

    def step(self, resource_level):
        """Advances the human by one year, checking for death and reproduction."""
        self.age += 1
        
        # 1. MORTALITY MECHANICS
        base_death_prob = 0.015 * np.exp(0.04 * self.age)
        actual_death_prob = base_death_prob * (1 - 0.85 * resource_level)
        
        if random.random() < actual_death_prob or self.age > 100:
            self.alive = False
            return 0  # No birth
            
        # 2. FERTILITY MECHANICS
        if self.sex == 0 and 15 <= self.age <= 45:
            base_birth_prob = 0.2
            actual_birth_prob = base_birth_prob * (1 - 0.65 * resource_level)
            
            if random.random() < actual_birth_prob:
                return 1  # 1 birth generated
        
        return 0

class World:
    def __init__(self, initial_pop=1000, years=300):
        self.years = years
        self.agents = []
        self.history = {'pop': [], 'births': [], 'deaths': [], 'resources': []}
        self.age_distributions = {}  
        self.all_years_distributions = {} 
        
        # Initialize with an exponential decay age distribution
        for _ in range(initial_pop):
            age = int(np.random.exponential(scale=20))
            if age > 80: age = 80
            sex = random.choice([0, 1])
            self.agents.append(Human(age, sex))

    def get_resource_level(self, year):
        """Sigmoid function for technological/resource progress."""
        k = 0.05
        t0 = 150
        return 1 / (1 + np.exp(-k * (year - t0)))

    def run(self):
        print(f"Starting simulation for {self.years} years...")
        for year in range(self.years):
            resources = self.get_resource_level(year)
            
            births_this_year = 0
            deaths_this_year = 0
            
            # Agents take a step
            for agent in self.agents:
                birth = agent.step(resources)
                if not agent.alive:
                    deaths_this_year += 1
                else:
                    births_this_year += birth
            
            # Remove dead agents
            self.agents = [a for a in self.agents if a.alive]
            
            # Add new babies
            for _ in range(births_this_year):
                self.agents.append(Human(age=0, sex=random.choice([0, 1])))
                
            # Record Data
            current_pop = len(self.agents)
            self.history['pop'].append(current_pop)
            self.history['births'].append((births_this_year / current_pop) * 1000 if current_pop > 0 else 0)
            self.history['deaths'].append((deaths_this_year / current_pop) * 1000 if current_pop > 0 else 0)
            self.history['resources'].append(resources)
            
            # Save data for the static plots (milestones only)
            if year in [0, 150, 299]:
                self.age_distributions[year] = [a.age for a in self.agents]
                
            # Save data for the GIF (every year, split by sex)
            self.all_years_distributions[year] = {
                'male': [a.age for a in self.agents if a.sex == 1],
                'female': [a.age for a in self.agents if a.sex == 0]
            }
        print("Simulation complete.")

    def plot_results(self):
        # 1. Plot the Demographic Transition Model
        fig, ax1 = plt.subplots(figsize=(10, 5))
        
        ax1.plot(self.history['births'], label='Birth Rate (per 1k)', color='green', linewidth=2)
        ax1.plot(self.history['deaths'], label='Death Rate (per 1k)', color='red', linewidth=2)
        ax1.set_xlabel('Years')
        ax1.set_ylabel('Rate per 1,000 people')
        
        max_rate = 0
        if self.history['births'] and self.history['deaths']:
             max_rate = max(max(self.history['births']), max(self.history['deaths']))
        ax1.set_ylim(0, max_rate + 10)
        
        ax2 = ax1.twinx()
        ax2.plot(self.history['pop'], label='Total Population', color='blue', linewidth=2)
        ax2.set_ylabel('Total Population')
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper left')
        
        plt.title('Demographic Transition Model')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        # 2. Plot the Age Pyramids (Static Histograms)
        fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
        years_to_plot = [0, 150, 299]
        
        for ax, year in zip(axes, years_to_plot):
            if year in self.age_distributions:
                ages = self.age_distributions[year]
                ax.hist(ages, bins=20, range=(0, 100), color='skyblue', edgecolor='black')
                ax.set_title(f"Year {year}")
                ax.set_xlabel("Age")
        
        axes[0].set_ylabel("Number of People")
        plt.tight_layout()
        plt.show()
    
    def plot_resources(self):
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(self.history['resources'], color='purple', linewidth=2, label='Development Level')
        ax.axvline(x=150, color='gray', linestyle='--', alpha=0.6, label='Transition Midpoint')
        ax.set_title('Development Over Time')
        ax.set_xlabel('Years')
        ax.set_ylabel('Development Level')
        ax.set_xlim(0, self.years)
        ax.set_ylim(0, 1.05)
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.tight_layout()
        plt.show()

    def create_gif(self, filename='population_pyramid.gif'):
        print("Generating animation... this might take a moment.")
        fig, ax = plt.subplots(figsize=(8, 6))
        
        output_folder = "fig"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        full_path = os.path.join(output_folder, filename)
        
        bins = np.arange(0, 105, 5)
        y_pos = bins[:-1] + 2.5 
        
        max_pop = 0
        for year, data in self.all_years_distributions.items():
            m_counts, _ = np.histogram(data['male'], bins=bins)
            f_counts, _ = np.histogram(data['female'], bins=bins)
            if len(m_counts) > 0 and max(m_counts) > max_pop: max_pop = max(m_counts)
            if len(f_counts) > 0 and max(f_counts) > max_pop: max_pop = max(f_counts)
            
        max_pop = int(max_pop * 1.1) 
        
        def update(frame):
            ax.clear()
            data = self.all_years_distributions.get(frame, {'male': [], 'female': []})
            
            m_counts, _ = np.histogram(data['male'], bins=bins)
            f_counts, _ = np.histogram(data['female'], bins=bins)
            
            ax.barh(y_pos, -m_counts, height=4.5, color='royalblue', label='Male', edgecolor='black')
            ax.barh(y_pos, f_counts, height=4.5, color='crimson', label='Female', edgecolor='black')
            
            ax.set_title(f"Year {frame} - Population Distribution")
            ax.set_xlabel("Population")
            ax.set_ylabel("Age")
            ax.set_xlim(-max_pop, max_pop)
            ax.set_ylim(0, 100)
            
            ticks = ax.get_xticks()
            ax.set_xticks(ticks)
            ax.set_xticklabels([str(abs(int(tick))) for tick in ticks])
            ax.legend(loc='upper right')
            
        ani = animation.FuncAnimation(fig, update, frames=self.years, repeat=False)
        ani.save(full_path, writer='pillow', fps=15)
        plt.close()

        print(f"Animation successfully saved as {full_path}")