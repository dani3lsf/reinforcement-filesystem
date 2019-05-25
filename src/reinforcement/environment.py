#-*- coding: utf-8 -*-
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import re

from multiprocessing import Queue
from collections import Counter

class Environment(object):
    """
        Implementation of the black-boxed environment

        Attributes common to the environment:
            numBins(int) -- Number of bins in the environment
            numSlots(int) -- Number of available slots per bin in the environment
            cells[numBins, numSlots] -- Stores environment occupancy
            packet_properties{struct} -- Describes packet properties inside the environment

        Attributes common to the service
            serviceLength(int) -- Length of the service
            service[serviceLength] -- Collects the service chain
            placement[serviceLength] -- Collects the packet allocation for the service chain
            first_slots[serviceLength] -- Stores the first slot occupied in the correspondent bin for each packet
            reward(float) -- Stores the reward obtained placing the service on the environment
            invalidPlacement(Bool) -- Invalid placement indicates that there is a resource overflow
    """
    def __init__(self, numBins, numSlots, numDescriptors, fileSize, metadata):

        #self.w = Watcher('mops/mp1', 'mops/mp2')

        # Environment properties
        self.numBins = numBins
        self.numSlots = numSlots
        self.numDescriptors = numDescriptors
        self.cells = {0: (8000000, []), 1: (4000000, []) }
        self.initial_cloud_size = [8000000,40000000]
        #self.cells = np.empty((numBins, numSlots))
        #self.cells[:] = np.nan
        #self.service_properties = [{"size": 1} for _ in range(numDescriptors)]

        # Placement properties
        self.serviceLength = 0
        self.service = None
        self.placement = None
        self.first_slots = None
        self.reward = 1
        self.invalidPlacement = 0

        self.fileSize = fileSize

        self.metadata = metadata

        self.acesses = {}



    def _placePacket(self, i, bin, pkt):
        """ Place Packet """


        (cloud_size, fichs) = self.cells[bin]
        if cloud_size < self.fileSize:
            self.invalidPlacement = self.invalidPlacement + 1
            self.first_slots[i] = -1
        else:
            self.first_slots[i] = self.initial_cloud_size[bin] - cloud_size
            cloud_size -= self.fileSize
            fichs.append(pkt)
            self.cells[bin] = (cloud_size, fichs)



    def _computeReward(self):
        """ Compute reward """

        pkts = {}

        for bin, (bin_size, fichs) in self.cells.items():
            for fich in fichs:
                pkts[fich] = bin

        bin_speed = [5, 1]


        total = 0.1
        suma = 0

        access = np.zeros( self.numDescriptors)

        for k1,v1 in self.acesses.items():
            v2 = int(re.findall('\d+',k1)[0])
            access[v2] = v1

        # access = [0,0,45,7,0,0,26,12,67,0,0,0,0,0,0,
        #           0,0,45,7,0,0,26,12,62,0,0,0,34,0,0,
        #           34,0,0,9,100,0,0,0,0,54,12,0,0,0,0,
        #           34,45,1,0,0,0,0,0,0,0,23,120,73,0,0,
        #           0,0,0,0,0,67,12,90,34,0,0,0,0,0,0,
        #           0,0,0,0,0,0,0,0,0,0,0,0,0,0,70,
        #           50,23,78,0,0,0,45,19,49,120
        #           ]

        #print(access)
        for i in range(self.numDescriptors):
            if i in pkts:
                    #self.watcher.get_nr_of_reads('dummy' + i)
                suma += bin_speed[pkts[i]] * access[i]
                total += access[i]
	
        next_average = suma / total


        if next_average == 0:
            reward = 5
        else:
            reward = np.power(5,5 / next_average)
            #reward = 200 * 1/next_average
            #reward = -5 * (np.log(next_average)/np.log(2)) + 35

        #print(next_average)
        #reward = np.sum(np.power(100, occupancy))
        #print(reward)

        #print(reward)

        #reward = next_average * 100;


        return reward



    def step(self, placement, service, length):
        """ Place service """

        self.placement = placement
        self.service = service
        self.serviceLength = length
        self.first_slots = np.zeros(length, dtype='int32')

        for i in range(length):
            self._placePacket(i, placement[i], service[i])

        """ Compute reward """
        if self.invalidPlacement != 0:
            self.reward = 1 - self.invalidPlacement * 0.01
        else:
            self.reward = self._computeReward()

    def calculate_accesses(self):
        self.acesses = {}
        access2_queue = self.metadata.get_files_accessed()
        access2 = []

        while not access2_queue.empty():
            access2.append(access2_queue.get())


        for item in access2:
            access2_queue.put(item)

        #get_files_cloud
        self.acesses = dict(Counter(access2))



    def clear(self):
        """ Clean environment """

        self.cells = {0: (8000000, []), 1: (4000000, []) }
        self.serviceLength = 0
        self.service = None
        self.placement = None
        self.first_slots = None
        self.reward = 1
        self.invalidPlacement = 0

    def render(self, epoch=0):
        """ Render environment using Matplotlib """

        # Creates just a figure and only one subplot
        fig, ax = plt.subplots()
        ax.set_title(f'Environment {epoch}\nreward: {self.reward}')

        margin = 0
        margin_ext = 6
        xlim = 110
        ylim = 40

        # Set drawing limits
        plt.xlim(0, xlim)
        plt.ylim(-ylim, 0)

        # Set hight and width for the box
        high = (ylim - 2 * margin_ext - margin * (self.numBins - 1)) / self.numBins
        wide = (xlim - 2 * margin_ext - margin * (max(self.initial_cloud_size) - 1)) / max(self.initial_cloud_size)

        print(high)
        print(wide)

        # Plot slot labels
    #    for slot in range(max(self.initial_cloud_size)):
     #       x = wide * slot + slot * margin + margin_ext
         #   plt.text(x + 0.5 * wide, -3, "slot{}".format(slot), ha="center", family='sans-serif', size=8)




        # Plot bin labels & place empty boxes
        for bin in range(self.numBins):
            y = -high * (bin + 1) - (bin) * margin - margin_ext
            plt.text(0, y + 0.5 * high, "bin{}".format(bin), ha="center", family='sans-serif', size=8)

            for slot in range(self.initial_cloud_size[bin]):
                x = wide * slot + slot * margin + margin_ext
                rectangle = mpatches.Rectangle((x, y), wide, high, linewidth=1, edgecolor='black', facecolor='none')
                ax.add_patch(rectangle)


        print(self.serviceLength)
        # Select serviceLength colors from a colormap
        cmap = plt.cm.get_cmap('hot')
        colormap = [cmap(np.float32(i+1)/(self.serviceLength+1)) for i in range(self.serviceLength)]

        # Plot service boxes
        for idx in range(self.serviceLength):
            pkt = self.service[idx]
            bin = self.placement[idx]
            first_slot = self.first_slots[idx]

            x = wide * first_slot + first_slot * margin + margin_ext
            y = -high * (bin + 1) - bin * margin - margin_ext
            plt.text(x + 0.5 * wide, y + 0.5 * high, "pkt{}".format(pkt), ha="center", family='sans-serif', size=8)
            for k in range(self.service_properties[pkt]["size"]):
                slot = first_slot + k
                x = wide * slot + slot * margin + margin_ext
                y = -high * (bin + 1) - bin * margin - margin_ext
                rectangle = mpatches.Rectangle((x, y), wide, high, linewidth=1, facecolor=colormap[idx], alpha=.9)
                ax.add_patch(rectangle)


        print(self.first_slots)
        print(self.cells)
        print(self.placement)
        plt.axis('off')
        plt.show()


if __name__ == "__main__":

    # Define environment
    numBins = 5
    numSlots = 5
    numDescriptors = 8
    env = Environment(numBins, numSlots, numDescriptors)

    # Allocate service in the environment
    servicelength = 5
    ns = [0, 6, 6, 7, 5, 0]
    placement = [0, 1, 1, 0, 0]
    env.step(placement, ns, servicelength)
    env.render()
    env.clear()
