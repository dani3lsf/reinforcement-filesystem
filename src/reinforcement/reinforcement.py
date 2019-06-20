# -*- coding: utf-8 -*-
"""
    Bin-Packing using Neural Combinational Optimization.

    Author: Ruben Solozabal, PhD student at the University of the Basque Country [UPV-EHU] Bilbao
    Date: October 2018
"""
import logging
import operator
import ctypes
import tensorflow as tf
import multiprocessing as mp
import math
# from environment import *
# from service_batch_generator import *
# from agent import *
from tensorflow.python import debug as tf_debug
from src.reinforcement.environment import Environment
from src.reinforcement import get_config, Agent, vector_embedding, np
from src.reinforcement.service_batch_generator import ServiceBatchGenerator

class ReinforcementLearning(object):

    def __init__(self):

        """ Configuration """
        self.config, _ = get_config()

        """ Batch of Services """
        self.services = ServiceBatchGenerator(self.config.batch_size,
                                              self.config.min_length,
                                              self.config.max_length,
                                              self.config.num_descriptors)

        """ Agent """
        state_size_sequence = self.config.max_length
        state_size_embeddings = self.config.num_descriptors  # OH Vector embedding
        action_size = self.config.num_bins
        self.agent = Agent(state_size_embeddings, state_size_sequence,
                           action_size, self.config.batch_size,
                           self.config.learning_rate, self.config.hidden_dim,
                           self.config.num_stacks)

        """ Configure Saver to save & restore model variables """
        variables_to_save = [v for v in tf.global_variables()
                             if 'Adam' not in v.name]
        saver = tf.train.Saver(var_list=variables_to_save,
                               keep_checkpoint_every_n_hours=1.0)

        self.choosen_positions = mp.Array('i', np.zeros(self.config.num_descriptors, dtype=int), lock=True)
        self.done = mp.Value(ctypes.c_bool, False)

    def run(self, metadata):

        f = open('rewards.txt', 'w')
        self.sess = tf.Session()

        """ Environment """
        self.env = Environment(self.config.num_bins, self.config.num_slots, self.config.num_descriptors,
                               self.config.file_size, metadata)

        # Run initialize op
        self.sess.run(tf.global_variables_initializer())

        # Print total number of parameters
        total_parameters = 0
        for variable in tf.trainable_variables():
            # shape is an array of tf.Dimension
            shape = variable.get_shape()
            variable_parameters = 1
            for dim in shape:
                variable_parameters *= dim.value
            print('Shape: ', shape, 'Variables: ', variable_parameters)
            total_parameters += variable_parameters
        print('Total_parameters: ', total_parameters)

        # Restore variables from disk
        if self.config.load_model:
            self.saver.restore(self.sess, "save/tf_binpacking.ckpt")
            print("Model restored.")

        # Train model
        if self.config.train_mode:

            # Summary writer
            writer = tf.summary.FileWriter("summary/repo", self.sess.graph)

            # Main Loop
            print("\n Starting training...")
            e = 0
            # for e in tqdm(range(self.config.num_epoch)):
            while not self.done.value:

                # New batch of states
                self.services.getNewState()

                # Vector embedding
                input_state = vector_embedding(self.services)

                # Compute placement
                feed = {self.agent.input_: input_state,
                        self.agent.input_len_: [item for item in self.services.serviceLength]}
                positions = self.sess.run(self.agent.ptr.positions, feed_dict=feed)

                self.env.accesses = metadata.calculate_accesses()
                reward = np.zeros(self.config.batch_size)

                # Compute environment
                for batch in range(self.config.batch_size):
                    # print(positions[batch])
                    # print(services.state[batch])
                    self.env.clear()
                    # placement -> bin -> positions
                    # service -> ptk -> services
                    self.env.step(positions[batch], self.services.state[batch],
                                  self.services.serviceLength[batch])
                    reward[batch] = self.env.reward

                index, value = max(enumerate(reward), key=operator.itemgetter(1))

                self.env.clear()
                self.env.step(self.choosen_positions[:], range(100), 100)
                old_positions_reward = self.env.reward

                average = 5 * math.log(5)/math.log(value)
                significancy = np.power(5,5 / average) - np.power(5,5 / (average + 0.075))

                if old_positions_reward + significancy < value:
                    choosen = [xb for xa, xb in sorted(zip(
                        self.services.state[index],
                        positions[index]))]                
                    self.choosen_positions[:] = choosen
                # RL Learning

                feed = {self.agent.reward_holder: [item for item in reward],
                        self.agent.positions_holder: positions,
                        self.agent.input_: input_state, self.agent.input_len_: [item for item in self.services.serviceLength]}

                summary, _ = self.sess.run([self.agent.merged, self.agent.train_step],
                                           feed_dict=feed)

                if e % 10 == 0:
                    print("\n Mean batch ", e, "reward:", np.mean(reward), file=f)
                    writer.add_summary(summary, e)

                # Save intermediary model variables
                if self.config.save_model and e % max(1, int(self.config.num_epoch / 5)) == 0 and e != 0:
                    save_path = self.saver.save(self.sess, "save/tmp.ckpt", global_step=e)
                    print("\n Model saved in file: %s" % save_path)

                e += 1

            print("\n Training COMPLETED!")

            if self.config.save_model:
                save_path = self.saver.save(self.sess, "save/tf_binpacking.ckpt")
                print("\n Model saved in file: %s" % save_path)

            # self.env.render(0)

    def get_positions(self):
        return self.choosen_positions[:]

    def set_done(self):
        self.done.value = True



if __name__ == "__main__":

    servicelength = 5

    rl = ReinforcementLearning(servicelength)

    rl.run()

    print(rl.getPositions())
