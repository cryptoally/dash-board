#!/usr/bin/env python
# encoding: utf-8
"""
Calculates masternode daily payment and roi based on these formulas:

 *** Daily payments ***
(n/t) * r * b * a

 *** ROI ***
 (n/t) * r * b * a * 365 / 1000

Where:
n is the number of Masternodes an operator controls
t is the total number of Masternodes
r is the current block reward (presently averaging about 5 DASH)
b is blocks in an average day. For the Dash network this usually is 576.
a is the average Masternode payment (45% of the average block amount)

"""
from __future__ import division


class masternodes():

    def __init__(self, nr_of_masternodes):
        self.nr_of_masternodes = nr_of_masternodes
        self.block_reward = 4.5
        self.blocks_day = 576
        self.avg_payment = 0.45
        self.masternode_collateral = 1000

    def dailyPayment(self):
        # (n/t) * r * b * a
        return (1/self.nr_of_masternodes) * self.block_reward * self.blocks_day * self.avg_payment

    def yearlyPayment(self):
        # (n/t) * r * b * a * 365
        return self.dailyPayment() * 365

    def roi(self):
        # (n/t) * r * b * a * 365 / 1000
        return self.yearlyPayment() / self.masternode_collateral
