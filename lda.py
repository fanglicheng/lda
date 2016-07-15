#!/usr/bin/env python

import os
from bisect import bisect
from random import choice, random
from collections import defaultdict

DIR = './bbc'

NEGINF = float('-inf')

def color(w, c):
  return '\033[9%sm' % c + w + '\033[0m'


def tokenize(s):
  s = s.lower()
  chars = []
  for c in s:
    if c.isalnum():
      chars.append(c)
    else:
      if chars:
        yield ''.join(chars)
        chars = []
      if c not in [' ', '\n', '\r']:
        yield c


def documents():
  for x in os.listdir(DIR):
    d = os.path.join(DIR, x)
    if os.path.isdir(d):
      for f in os.listdir(d):
        full_path = os.path.join(d, f)
        yield Document(full_path, list(tokenize(open(full_path).read())))


class Counts(defaultdict):
  def __init__(self):
    defaultdict.__init__(self, float)

  def max_key(self):
    best = NEGINF
    best_key = None
    for k, v in self.items():
      if v > best:
        best_key = k
        best = v
    return best_key

  def sample(self):
    items = self.items()
    weights = [item[1] for item in items]
    for i in range(1, len(weights)):
      weights[i] += weights[i-1]
    return items[bisect(weights, random()*weights[-1])][0]


TOPICS = range(1, 6)


class Document:
  def __init__(self, name, words):
    self.name = name
    self.words = words
    self.topics = [choice(TOPICS) for word in words]

    self.topic_count = Counts()
    for t in self.topics:
      self.topic_count[t] += 1

  def topic(self):
    return self.topic_count.max_key()

  def __str__(self):
    return '%s\n%s' % (color(self.name, self.topic()),
                       ' '.join(color(w, t)
                                for w, t in zip(self.words, self.topics)))

  def resample(self, corpus):
    for i, (w, old_t) in enumerate(zip(self.words, self.topics)):
      corpus.word_topic_count[w][old_t] -= 1
      corpus.topic_count[old_t] -= 1
      self.topic_count[old_t] -= 1

      topic_weights = Counts()
      for t in TOPICS:
        topic_weights[t] = ((self.topic_count[t] + 1)
                            * (corpus.word_topic_count[w][t] + 1)
                            / (corpus.topic_count[t] + 20000))
      new_t = topic_weights.sample()
      self.topics[i] = new_t

      corpus.word_topic_count[w][new_t] += 1
      corpus.topic_count[new_t] += 1
      self.topic_count[new_t] += 1


class Corpus:
  def __init__(self, docs):
    self.docs = docs
    self.topic_count = Counts()
    self.word_topic_count = defaultdict(Counts)
    for d in docs:
      for w, t in zip(d.words, d.topics):
        self.word_topic_count[w][t] += 1
        self.topic_count[t] += 1

  def resample(self):
    for d in self.docs:
      d.resample(self)

  def overview(self):
    return ''.join(color(str(d.topic()), d.topic()) for d in self.docs)


corpus = Corpus(list(documents()))
for iteration in range(100):
  print '\n-------------- iteration %s -----------------' % iteration
  corpus.resample()
  for i, d in enumerate(corpus.docs):
    if i % 200 == 0:
      print d
      print
  print corpus.overview()
