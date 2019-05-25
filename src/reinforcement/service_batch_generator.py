#-*- coding: utf-8 -*-
import numpy as np

class ServiceBatchGenerator(object):
    """
        Implementation of a random service chain generator

        Attributes:
            state[batchSize, maxServiceLength] -- Generated random service chains
            serviceLength[batchSize] -- Generated array contining services length
    """

    #    services = ServiceBatchGenerator(config.batch_size, config.min_length, config.max_length, config.num_descriptors)
    def __init__(self, batchSize, minServiceLength, maxServiceLength, numDescriptors):
        """
        Args:
            batchSize(int) -- Number of service chains to be generated
            minServiceLength(int) -- Minimum service length
            maxServiceLength(int) -- Maximum service length
            numDescriptors(int) -- Number of unique descriptors
        """
        self.batchSize = batchSize
        self.minServiceLength = minServiceLength
        self.maxServiceLength = maxServiceLength
        self.numDescriptors = numDescriptors

        self.serviceLength = np.zeros(self.batchSize,  dtype='int32')
        self.state = np.zeros((self.batchSize, self.maxServiceLength),  dtype='int32')

    def getNewState(self):
        """ Generate new batch of service chain """

        # Clean attributes
        self.serviceLength = np.zeros(self.batchSize,  dtype='int32')
        self.state = np.zeros((self.batchSize, self.maxServiceLength),  dtype='int32')

        # Compute random services
        for batch in range(self.batchSize):
            self.serviceLength[batch] = self.maxServiceLength
                #np.random.randint(self.minServiceLength, self.maxServiceLength+1, dtype='int32')
            """for i in range(1,self.serviceLength[batch]):
                pktID = np.random.randint(1, self.numDescriptors,  dtype='int32')
                while pktID in self.state[batch]: 
                   pktID = np.random.randint(1, self.numDescriptors,  dtype='int32')
                self.state[batch][i] = pktID
            """
            #[1,2,1,31,20,0,5,0]1
            self.state[batch] = range(100)
            #[2,1,4,6,3,7,5,0]
            #self.state[batch] = [5,1,4,2,7,6,3,0]
            #self.state[batch] = [5,7,0,2,1,6,4,3]

if __name__ == "__main__":

    # Define generator
    batch_size = 8
    minServiceLength = 8
    maxServiceLength = 8
    numDescriptors = 8

    env = ServiceBatchGenerator(batch_size, minServiceLength, maxServiceLength, numDescriptors)
    env.getNewState()


