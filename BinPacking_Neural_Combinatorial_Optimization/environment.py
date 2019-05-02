#-*- coding: utf-8 -*-
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


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
    def __init__(self, numBins, numSlots, numDescriptors):

        # Environment properties
        self.numBins = numBins
        self.numSlots = numSlots
        self.numDescriptors = numDescriptors
        self.cells = {0: (100, []), 1: (50, []) }
        self.initial_cloud_size = [100,50]
        #self.cells = np.empty((numBins, numSlots))
        #self.cells[:] = np.nan
        self.service_properties = [{"size": 1} for _ in range(numDescriptors)]

        # Placement properties
        self.serviceLength = 0
        self.service = None
        self.placement = None
        self.first_slots = None
        self.reward = 1
        self.invalidPlacement = False

        # Assign ns properties within the environment
        self._get_service_propertieses()

    def _get_service_propertieses(self):
        """ Packet properties """
        # By default the size of each package in that environment is 1, should be modified here.
        self.service_properties[0]["size"] = 30
        self.service_properties[1]["size"] = 20
        self.service_properties[2]["size"] = 20
        self.service_properties[3]["size"] = 10
        self.service_properties[4]["size"] = 10
        self.service_properties[5]["size"] = 10
        self.service_properties[6]["size"] = 10
        self.service_properties[7]["size"] = 25
    """
    
        def _placeSubPakcet(self, bin, pkt):
          
    
            occupied_slot = None
    
            for slot in range(len(self.cells[bin])):
                if np.isnan(self.cells[bin][slot]):
                    self.cells[bin][slot] = pkt
                    occupied_slot = slot
                    break
                elif slot == len(self.cells[bin])-1:
                    self.invalidPlacement = True
                    occupied_slot = -1      # No space available
                    break
                else:
                    pass                    # Look for next slot
    
            return occupied_slot
    
        def _placePacket(self, i, bin, pkt):
           
           
            for slot in range(self.service_properties[pkt]["size"]):
                occupied_slot = self._placeSubPakcet(bin, pkt)
    
                # Anotate first slot used by the Packet
                if slot == 0:
                    self.first_slots[i] = occupied_slot
    
    """

    def _placePacket(self, i, bin, pkt):
        """ Place Packet """




        (cloud_size, fichs) = self.cells[bin]
        if cloud_size < self.service_properties[pkt]["size"]:
            self.invalidPlacement = True
            self.first_slots[i] = -1
        else:
            self.first_slots[i] = self.initial_cloud_size[bin] - cloud_size
            cloud_size -= self.service_properties[pkt]["size"]
            fichs.append(pkt)
            self.cells[bin] = (cloud_size, fichs)





    def _computeReward(self):
        """ Compute reward """


        pkts = {}



        for bin, (bin_size, fichs) in self.cells.items():
            for fich in fichs:
                pkts[fich] = bin



        #print("PACKET -> BIN")
        #print(pkts)

        access = [1,2,1,31,20,0,5,0]
        bin_speed = [20, 2]


        total = 1
        suma = 0

        for i in range(8):
            if i in pkts:
                suma += bin_speed[pkts[i]] * access[i]
                total += access[i]
	
        #print(suma)

        next_average = suma / total
        #c1 = self.w.get_nr_reads('fich1.txt')
        #c2 = self.w.get_nr_reads('fich2.txt')


        #next_average = (c1 * 1 + c2 * 3) / (c1 + c2)

        if next_average == 0:
            reward = 5
        else:
            reward = 100 * 2 / next_average

#-5 * (np.log(next_average)/np.log(2)) + 25

        #print(next_average)
        #reward = np.sum(np.power(100, occupancy))
        #print(reward)

        #print(reward)

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
        if self.invalidPlacement == True:
            self.reward = 1
        else:
            self.reward = self._computeReward()

    def clear(self):
        """ Clean environment """

        self.cells = {0: (100, []), 1: (50, []) }
        self.serviceLength = 0
        self.service = None
        self.placement = None
        self.first_slots = None
        self.reward = 1
        self.invalidPlacement = False

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
