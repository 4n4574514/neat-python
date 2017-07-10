from __future__ import print_function
import os
import neat

def test_xor_example_uniform():
    test_xor_example(uniform=True)

def test_xor_example_multiparam_relu():
    test_xor_example(activation='multiparam_relu')

def test_xor_example(uniform=False, activation=None):
    # 2-input XOR inputs and expected outputs.
    xor_inputs = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]
    xor_outputs = [(0.0,), (1.0,), (1.0,), (0.0,)]

    def eval_genomes(genomes, config):
        for genome_id, genome in genomes:
            genome.fitness = 1.0
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            for xi, xo in zip(xor_inputs, xor_outputs):
                output = net.activate(xi)
                genome.fitness -= (output[0] - xo[0]) ** 2

    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'test_configuration')

    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)

    if uniform:
        config.genome_config.weight_init_type = 'uniform'

    if activation is not None:
        config.genome_config.activation_default = activation
        config.genome_config.activation_options = [activation]

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run for up to 300 generations, allowing extinction.
    winner = None
    try:
        winner = p.run(eval_genomes, 100)
    except neat.CompleteExtinctionException as e:
        pass

    if winner:
        if uniform:
            print('\nUsing uniform weight initialization:')
        # Display the winning genome.
        print('\nBest genome:\n{!s}'.format(winner))

        # Show output of the most fit genome against training data.
        print('\nOutput:')
        winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
        for xi, xo in zip(xor_inputs, xor_outputs):
            output = winner_net.activate(xi)
            print("input {!r}, expected output {!r}, got {!r}".format(xi, xo, output))


if __name__ == '__main__':
    test_xor_example()
    test_xor_example_uniform()
    test_xor_example_multiparam_relu()
