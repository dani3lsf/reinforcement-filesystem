from random import shuffle
import random

random.seed(12345678)

dists = 8 * ['zipfian'] + 3 * ['sequential'] + ['random']
shuffle(dists)


res = []
for i in range(0, len(dists)):
	dist_idx = random.choice(range(0, len(dists)))
	dist = dists[dist_idx]
	del dists[dist_idx]
	res.append(dist)

print(res)