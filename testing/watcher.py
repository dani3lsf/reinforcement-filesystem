import inotify.adapters

class Watcher():
    def __init__(self, folder1, folder2):
        self.folder1 = folder1
        self.folder2 = folder2
        self.reset()

    def reset(self):
        self.nr_of_reads = {}

    def run(self):
        i = inotify.adapters.Inotify()

        i.add_watch(self.folder1)
        i.add_watch(self.folder2)

        for event in i.event_gen(yield_nones=False):
            #print("EVENTO!!!!!")
            (_, type_names, path, filename) = event

            #if 'IN_CREATE' in type_names:
             #   self.nr_of_reads[filename] = 0
              #  print("CREATING " + filename)

            if 'IN_OPEN' in type_names and 'IN_DELETE' not in type_names:
                self.increment_reads(filename)            

    def increment_reads(self, file):
        self.nr_of_reads[file] = self.nr_of_reads.get(file, 0) + 1

    def get_nr_of_reads(self, file):
        return self.nr_of_reads.get(file, 0)
    
    def get_latency(self, number):
        if number == 1:
            return 2
        else:
            return 4