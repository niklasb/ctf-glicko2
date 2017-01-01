"""
Copyright (c) 201 by Matt Sewall.

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above
  copyright notice, this list of conditions and the following
  disclaimer in the documentation and/or other materials provided
  with the distribution.

* The names of the contributors may not be used to endorse or
  promote products derived from this software without specific
  prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# Glicko
# python 3.4.3
# Copyright (c) 2016 by Matt Sewall.
# All rights reserved.
import math

# Background information - https://en.wikipedia.org/wiki/Glicko_rating_system
# Based on this equation - http://www.glicko.net/glicko/glicko2.pdf

INITRAT = 1500.0

_MAXSIZE = 186
_MAXMULTI = .272
_MULTISLOPE = .00391
_WIN = 1.0
_LOSS = 0
_CATCH = .5
_VOL = .05
_CONV = 173.7178
_EPS = 0.0001

class GlickoPlayer:
    def __init__(self, name, place, rating, confidence, volatility):
        self.name = name
        self.place = place
        self.rating = rating
        self.confidence = confidence
        self.volatility = volatility

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

def findSigma(mu, phi, sigma, change, v):
    alpha = math.log(sigma ** 2)

    def f(x):
        tmp = phi ** 2 + v + math.exp(x)
        a = math.exp(x) * (change ** 2 - tmp) / (2 * tmp ** 2)
        b = (x - alpha) / (_VOL ** 2)
        return a - b

    a = alpha
    if change ** 2 > phi ** 2 + v:
        b = math.log(change ** 2 - phi ** 2 - v)
    else:
        k = 1
        while f(alpha - k * _VOL) < 0:
            k += 1
        b = alpha - k * _VOL
    fa = f(a)
    fb = f(b)
    # Larger _EPS used to speed iterations up slightly
    while abs(b - a) > _EPS:
        c = a + (a - b) * fa / (fb - fa)
        fc = f(c)
        if fc * fb < 0:
            a = b
            fa = fb
        else:
            fa /= 2
        b = c
        fb = fc
    return math.e ** (a / 2)


def calculateGlicko(players, contest_weight=1.0, negative_damping=1.0):
    N = len(players)
    if N > _MAXSIZE:
        multi = _MAXMULTI
    else:
        multi = _WIN - _MULTISLOPE * N

    # compare every head to head matchup in a given compeition
    for i in players:
        mu = (i.rating - INITRAT) / _CONV
        phi = i.confidence / _CONV
        sigma = i.volatility
        v_inv = 0
        delta = 0
        for j in players:
            if i is not j:
                oppMu = (j.rating - INITRAT) / _CONV
                oppPhi = j.confidence / _CONV
                if i.place > j.place:
                    S = _LOSS
                elif i.place < j.place:
                    S = _WIN
                else:
                    S = _CATCH
                # Change the weight of the matchup based on opponent confidence
                weighted = 1 / math.sqrt(1 + 3 * oppPhi ** 2 / math.pi ** 2)
                # Change the weight of the matchup based on competition size
                weighted = weighted * multi * contest_weight
                expected_score = 1 / (1 + math.exp(-weighted * (mu - oppMu)))
                v_inv += weighted ** 2 * expected_score * \
                    (1 - expected_score)
                d = weighted * (S - expected_score)
                if d < 0:
                    d *= negative_damping
                delta += d
        if v_inv != 0:
            v = 1 / v_inv
            change = v * delta
            newSigma = findSigma(mu, phi, sigma, change, v)
            phiAst = math.sqrt(phi ** 2 + newSigma ** 2)
            # New confidence based on competitors volatility and v
            newPhi = 1 / math.sqrt(1 / phiAst ** 2 + 1 / v)
            newMu = mu + newPhi ** 2 * delta
            i.rating = newMu * _CONV + INITRAT
            i.confidence = newPhi * _CONV
            i.volatility = newSigma
