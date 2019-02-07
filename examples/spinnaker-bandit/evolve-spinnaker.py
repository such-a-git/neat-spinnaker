"""
2-input XOR example -- this is most likely the simplest possible example.
"""

from __future__ import print_function
import os
import neat
import visualize
from ast import literal_eval
import csv
import numpy as np
import time

arm1 = 1
arm2 = 0
# arm3 = 0.1
arm_len = 1
arms = []
for i in range(arm_len):
    arms.append([arm1, arm2])
    arms.append([arm2, arm1])
# arms = [[0, 1], [1, 0]]
# arms = [[0, 1]]

exec_thing = 'arms'
if exec_thing == 'xor':
    arms = [[0, 0], [0, 1], [1, 0], [1, 1]]
shared_probabilities = True
shape_fitness = False
spike_fitness = False
grooming = 'rank'
reward_based = 0
spike_cap = 30000
spike_weight = 0.1
noise_rate = 0
noise_weight = 0.01
keys = ['fitness']

# UDP port to read spikes from
UDP_PORT1 = 17887
UDP_PORT2 = UDP_PORT1 + 1

number_of_trials = 105
duration_of_trial = 200
runtime = number_of_trials * duration_of_trial
try_attempts = 2
all_fails = 0
working_ends = 0
not_needed_ends = 0
# empty_pre_count = 0
empty_post_count = 0

'''remember to change inputs and outputs in the config as well'''

encoding = 1
time_increment = 20
pole_length = 1
pole_angle = [[0.1], [0.2], [-0.1], [-0.2]]
reward_based = 1
force_increments = 100
max_firing_rate = 50
number_of_bins = 3
central = 1
bin_overlap = 2
tau_force = 0

weight_max = 1.0
weight_scale = 1.0
delay = 10

weight = 0.1

threading_tests = True

if exec_thing == 'pen':
    input_size = number_of_bins * 4
    output_size = 2
    config = 'pend-an{}-{}-F{}-R{}-B{} '.format(pole_angle[0], len(pole_angle), force_increments, max_firing_rate, number_of_bins)
    test_data_set = pole_angle
else:
    input_size = 2
    output_size = len(arms[0])
    config = 'bandit {}-{}'.format(arms[0], len(arms))
    test_data_set = arms

config += ' reward {}'.format(reward_based)
if spike_fitness:
    if spike_fitness == 'out':
        config += ' out-spikes'
    else:
        config += ' spikes'
if shape_fitness:
    config += ' shape'
if noise_rate:
    config += ' noise {}-{}'.format(noise_rate, noise_weight)


best_fitness = []
average_fitness = []
worst_fitness = []
best_score = []
average_score = []
worst_score = []

stats = None

def read_fitnesses(config):
    fitnesses = []
    file_name = 'fitnesses {}.csv'.format(config)
    with open(file_name) as from_file:
        csvFile = csv.reader(from_file)
        for row in csvFile:
            metric = []
            for thing in row:
                metric.append(literal_eval(thing))
            fitnesses.append(metric)
    return fitnesses

def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        genome.fitness = 4.0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        for xi, xo in zip(xor_inputs, xor_outputs):
            output = net.activate(xi)
            genome.fitness -= (output[0] - xo[0]) ** 2

def save_stats():
    statistics = stats
    generation = len(statistics.most_fit_genomes)
    best_fitness = [c.fitness for c in statistics.most_fit_genomes]
    avg_fitness = np.array(statistics.get_fitness_mean())
    stdev_fitness = np.array(statistics.get_fitness_stdev())
    with open('NEAT bandit stats {}.csv'.format(config), 'w') as file:
        writer = csv.writer(file, delimiter=',', lineterminator='\n')
        writer.writerow(['Iteration: {}'.format(generation)])
        writer.writerow(['Best fitness'])
        writer.writerow(best_fitness)
        writer.writerow(['Average fitness'])
        writer.writerow(avg_fitness)
        writer.writerow(['Standard dev fitness'])
        writer.writerow(stdev_fitness)
        writer.writerow(['Best score'])
        writer.writerow(best_score)
        writer.writerow(['Average score'])
        writer.writerow(average_score)
        writer.writerow(['Worst score'])
        writer.writerow(worst_score)
        writer.writerow(['Current time'])
        writer.writerow([time.localtime()])
        writer.writerow(['Config'])
        writer.writerow([config])
        file.close()

def spinn_genomes(genomes, neat_config):
    global input_size, output_size
    input_size = neat_config.genome_config.num_inputs
    save_stats()
    globals()['pop'] = genomes
    if exec_thing == 'xor':
        execfile("exec_xor.py", globals())
    else:
        execfile("exec_general.py", globals())
    fitnesses = read_fitnesses(config)
    if spike_fitness:
        agent_spikes = []
        for k in range(neat_config.pop_size):
            spike_total = 0
            for j in range(len(test_data_set)):
                if isinstance(fitnesses[j][k], list):
                    spike_total -= fitnesses[j][k][1]
                    fitnesses[j][k] = fitnesses[j][k][0]
                else:
                    spike_total -= 1000000
            agent_spikes.append(spike_total)
        fitnesses.append(agent_spikes)
    sorted_metrics = []
    combined_fitnesses = [0 for i in range(len(genomes))]
    combined_scores = [0 for i in range(len(genomes))]
    # combined_spikes = [[0, i] for i in range(len(genomes))]
    if exec_thing != 'xor':
        for i in range(len(fitnesses)):
            indexed_metric = []
            for j in range(len(fitnesses[i])):
                if fitnesses[i][j] == 'fail':
                    indexed_metric.append([-10000000, j])
                else:
                    indexed_metric.append([fitnesses[i][j], j])
                # combined_spikes[j][0] -= fitnesses[i][j][1]
            indexed_metric.sort()
            sorted_metrics.append(indexed_metric)
        # combined_spikes.sort()
        # sorted_metrics.append(combined_spikes)

        # combined_fitnesses = [0 for i in range(len(genomes))]
        for i in range(len(genomes)):
            for j in range(len(arms)):
                combined_fitnesses[sorted_metrics[j][i][1]] += sorted_metrics[j][i][0]
    else:
        for i in range(len(fitnesses)):
            for j in range(len(fitnesses[i])):
                combined_fitnesses[j] += fitnesses[i][j]
                # add spikes to fitness here somehow if you want
    i = 0
    for i in range(len(fitnesses[i])):
        print ("{:4} | ".format(i), end=" ")
        for j in range(len(fitnesses)):
            print (" {:6}".format(fitnesses[j][i]), end=" ")
        print (" \t {:6}".format(combined_fitnesses[i]))
    i = 0
    for genome_id, genome in genomes:
        genome.fitness = combined_fitnesses[i]
        i += 1


def run(config_file, SpiNNaker=True):
    global stats
    # Load configuration.
    neat_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(neat_config)

    # p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-55')
    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(5))

    # Run for up to 300 generations.
    if SpiNNaker:
        winner = p.run(spinn_genomes, 1000)
    else:
        winner = p.run(eval_genomes, 1000)

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    # Show output of the most fit genome against training data.
    print('\nOutput:')
    winner_net = neat.nn.FeedForwardNetwork.create(winner, neat_config)
    # for xi, xo in zip(xor_inputs, xor_outputs):
    #     output = winner_net.activate(xi)
    #     print("input {!r}, expected output {!r}, got {!r}".format(xi, xo, output))

    node_names = {-1:'A', -2: 'B', 0:'A XOR B'}
    visualize.draw_net(neat_config, winner, True, node_names=node_names)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)

    # p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-21')
    # p.run(eval_genomes, 10)


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-spinnaker')
    run(config_path)