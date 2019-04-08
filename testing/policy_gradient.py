import tensorflow as tf
import numpy as np
import os
import time

from shutil import move
from threading import Thread
from watcher import Watcher

class Environment(object):
    def __init__(self, start_state, w):
        self.w = w
        self.start_state=start_state
        self.reset()
    def reset(self):
        self.total_rewards = 0
        self.state = self.start_state
        return self.state

    def step(self, action):
        time.sleep(0.50)
        if action == 1:
            if self.state[2] == 1:
                next_state = [self.w.get_nr_of_reads('fich1.txt'),
                        self.w.get_nr_of_reads('fich2.txt'),
                        2]
            else:
                next_state = [self.w.get_nr_of_reads('fich1.txt'),
                        self.w.get_nr_of_reads('fich2.txt'),
                        1]
        else:
            next_state = [self.w.get_nr_of_reads('fich1.txt'),
                self.w.get_nr_of_reads('fich2.txt'),
                self.state[2]]

        if next_state[2] == 1 and next_state[0] > next_state[1]:
            reward = 10
        elif next_state[2] == 1 and next_state[1] > next_state[0]:
            reward = 10
        elif next_state[1] == next_state[0]:
            reward = 0
        else:
            reward = -50
        
        self.state = next_state
        self.total_rewards += reward
        return self.state, reward

def reset_graph(seed=42):
    tf.reset_default_graph
    tf.set_random_seed(seed)
    np.random.seed(seed)

def discount_rewards(rewards, discount_rate):
    discounted_rewards = np.zeros(len(rewards))
    cumulative_rewards = 0
    for step in reversed(range(len(rewards))):
        cumulative_rewards = rewards[step] + cumulative_rewards * discount_rate
        discounted_rewards[step] = cumulative_rewards
    return discounted_rewards

def discount_and_normalize_rewards(all_rewards, discount_rate):
    all_discounted_rewards = [discount_rewards(rewards, discount_rate) for rewards in all_rewards]
    flat_rewards = np.concatenate(all_discounted_rewards)
    reward_mean = flat_rewards.mean()
    reward_std = flat_rewards.std()
    return [(discounted_rewards - reward_mean)/reward_std for discounted_rewards in all_discounted_rewards]

    
def main():
    w = Watcher('mops/mp1', 'mops/mp2')

    thread1 = Thread(target = w.run )
    
    thread1.start()

    # To make the output stable across runs
    reset_graph()

    # [nr_file1, nr_file2, p_file1]
    n_inputs = 3
    n_hidden = 2
    # whether it chooses to switch file positions
    n_outputs = 1

    learning_rate = 0.01
    
    initializer = tf.variance_scaling_initializer()

    # inserts a placeholder for a tensor that will be always fed
    X = tf.placeholder(tf.float32, shape=[None, n_inputs])

    hidden = tf.layers.dense(X, n_hidden, activation=tf.nn.elu, kernel_initializer=initializer)

    logits = tf.layers.dense(hidden, n_outputs)

    outputs = tf.nn.sigmoid(logits)  # probability of action 0 (not to migrate)

    p_migrations = tf.concat(axis=1, values=[outputs, 1 - outputs])

    action = tf.multinomial(tf.log(p_migrations), num_samples=1)

    y = 1. - tf.to_float(action)

    cross_entropy = tf.nn.sigmoid_cross_entropy_with_logits(labels=y, logits=logits)
    optimizer = tf.train.AdamOptimizer(learning_rate)
    grads_and_vars = optimizer.compute_gradients(cross_entropy)

    gradients = [grad for grad, variable in grads_and_vars]

    gradient_placeholders = []
    grads_and_vars_feed = []

    for grad, variable in grads_and_vars:
        gradient_placeholder = tf.placeholder(tf.float32, shape=grad.get_shape())
        gradient_placeholders.append(gradient_placeholder)
        grads_and_vars_feed.append((gradient_placeholder, variable))
        
    training_op = optimizer.apply_gradients(grads_and_vars_feed)

    init = tf.global_variables_initializer()
    saver = tf.train.Saver()
    
    n_runs_per_update = 20
    n_max_steps = 10
    n_iterations = 10
    save_iterations = 5
    discount_rate = 0.95

    env = Environment([w.get_nr_of_reads('fich1.txt'), w.get_nr_of_reads('fich2.txt'), 1], w)

    with tf.Session() as sess:
        init.run()
        for iteration in range(n_iterations):
            print("=" * 79)
            print("\rIteration: {}".format(iteration), end="")
            all_rewards = []
            all_gradients = []
            for game in range(n_runs_per_update):
                current_rewards = []
                current_gradients = []
                obs = env.reset()
                print(obs)
                for step in range(n_max_steps):
                    action_val, gradients_val = sess.run([action, gradients], feed_dict={X: np.asarray(obs).reshape(1, n_inputs)})
                    print(action_val[0][0])
                    obs, reward  = env.step(action_val[0][0])
                    print(obs)
                    current_rewards.append(reward)  
                    current_gradients.append(gradients_val)
                print(current_rewards)
                all_rewards.append(current_rewards)
                all_gradients.append(current_gradients)
                w.reset()

            all_rewards = discount_and_normalize_rewards(all_rewards, discount_rate=discount_rate)
            feed_dict = {}
            for var_index, gradient_placeholder in enumerate(gradient_placeholders):
                mean_gradients = np.mean([reward * all_gradients[game_index][step][var_index] for game_index, rewards in enumerate(all_rewards) for step, reward in enumerate(rewards)], axis=0)
                feed_dict[gradient_placeholder] = mean_gradients
            sess.run(training_op, feed_dict=feed_dict)
            if iteration % save_iterations == 0:
                saver.save(sess, "./my_policy_net_pg.ckpt")

if __name__ == '__main__':
    main()