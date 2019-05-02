import inotify.adapters
import os

from threading import Thread

class Watcher():
    def __init__(self, folders):
        self.folders = folders
        # file => [tamanho, nr de leituras]
        self.info = {}
        self.reset()

    def reset(self):
        for folder in self.folders:
            for basename in os.listdir(folder):
                self.info[basename] = [os.path.getsize(folder + "/" + basename), 0]

        print(self.info)

    def increment_reads(self, file):
        if file not in self.info:
            self.info[file] = [0, 0]
        self.info[file][1] = self.info.get(file, [0, 0])[1] + 1

    def set_size(self, path, file):
        print(file)
        filename = path + "/" + file
        self.info[file][0] = os.path.getsize(filename)

    def get_nr_of_reads(self, file):
        return self.info.get(file, [0, 0])[1]

    def run(self):
        i = inotify.adapters.Inotify()

        for folder in self.folders:
            i.add_watch(folder)

        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            #print("="*40)
            #print(type_names)
            #print("#" + filename + "#")

            if filename != "":
                if 'IN_OPEN' in type_names and 'IN_DELETE' not in type_names:
                    self.increment_reads(filename)

                if 'IN_MODIFY' in type_names:
                    self.set_size(path, filename)

                if 'IN_DELETE' in type_names and filename in self.info:
                    self.info.pop(filename)
            print(self.info)

            #elif 'IN DELETE':
            #    del self.info[filename]
            #elif 'IN_MODIFY' in type_names and 'IN_DELETE' not in type_names:
            #    s




w = Watcher(['mops/mp1', 'mops/mp2'])

thread1 = Thread(target = w.run)
thread1.start()


