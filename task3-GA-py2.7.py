import os
import json
import random
from fmm import Network, NetworkGraph, UBODTGenAlgorithm, UBODT, FastMapMatch, FastMapMatchConfig

random.seed(0)


### Read trajectory data
with open("./data/trajectory/train-1500.json", "r") as jsonfile:
    train1500 = json.load(jsonfile)

### Read network data
network = Network("./data/map/edges.shp", "fid", "u", "v")
print "Nodes {} edges {}".format(network.get_node_count(), network.get_edge_count())
graph = NetworkGraph(network)

### Precompute an UBODT table
# Can be skipped if you already generated an ubodt file
if os.path.isfile("./data/map/ubodt.txt"):
    ubodt = UBODT.read_ubodt_csv("./data/map/ubodt.txt")
    print 'Read the ubodt file'

### Read UBODT
else:
    print 'Generate and read the ubodt file'
    ubodt_gen = UBODTGenAlgorithm(network, graph)
    status = ubodt_gen.generate_ubodt("./data/map/ubodt.txt", 0.03, binary=False, use_omp=True)
    print status
    ubodt = UBODT.read_ubodt_csv("./data/map/ubodt.txt")


# Define parameter ranges
k_range = list(range(4, 32, 2))  # 4 to 32
r_range = [i/100000. for i in range(100, 1500, 10)]  # 100m to 1500m
e_range = [i/100000. for i in range(10, 150, 5)]  # 10m to 150m


def generate_individual():
    """Generates a random individual with parameters within the specified ranges."""
    return [
        random.choice(k_range), 
        random.choice(r_range), 
        random.choice(e_range),
    ]


def crossover(ind1, ind2):
    """Performs crossover between two individuals."""
    crossover_point = random.randint(1, 2)
    return ind1[:crossover_point] + ind2[crossover_point:]


def mutate(individual):
    """Randomly mutates an individual's parameters."""
    mutation_index = random.randint(0, 2)
    individual[mutation_index] = generate_individual()[mutation_index]
    return individual


def evaluate_fitness(individual):
    """Evaluates the fitness of an individual based on the average c.error."""
    # Unpack the individual's parameters
    k, r, e = individual

    # Set FMM config with these parameters
    fmm_model = FastMapMatch(network, graph, ubodt)
    fmm_config = FastMapMatchConfig(k, r, e)

    # Initialize variables to accumulate errors and count candidates
    total_error = 0
    total_candidates = float(len(train1500))

    for i, trajectory in enumerate(train1500):
        polyline = trajectory['POLYLINE']
        wkt = 'LINESTRING('+','.join([' '.join([str(_k) for _k in j]) for j in polyline])+')'
        result = fmm_model.match_wkt(wkt, fmm_config)

        if not result.candidates:
            total_error += 1
    
    # Calculate average error
    average_error = total_error / total_candidates if total_candidates > 0 else float('inf')

    # The lower the error, the better, hence we return the negative of average error as fitness
    return -average_error


def genetic_algorithm(population_size, generations):
    """Runs the genetic algorithm."""
    population = [generate_individual() for _ in range(population_size)]

    for generation in range(generations):
        # Evaluate fitness
        fitness_scores = [evaluate_fitness(individual) for individual in population]

        # Selection
        sorted_population = [x for _, x in sorted(zip(fitness_scores, population), key=lambda pair: pair[0], reverse=True)]
        population = sorted_population[:2]  # Elitism

        # Crossover and mutation
        while len(population) < population_size:
            parent1, parent2 = random.sample(sorted_population[:10], 2)
            offspring = crossover(parent1, parent2)
            offspring = mutate(offspring)
            population.append(offspring)

        # Print progress
        print("Generation {}: Best score: {} Best Parameters: {}".format(generation, sorted(fitness_scores, reverse=True)[0], sorted_population[0]))

    return sorted_population[0]


best_parameters = genetic_algorithm(population_size=50, generations=100)
print("Best Parameters:", best_parameters)
