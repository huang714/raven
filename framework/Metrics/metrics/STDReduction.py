# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on 2021 December 12

@author: Dongli Huang
"""

from .MetricInterface import MetricInterface
from Metrics.metrics import MetricUtilities

class STDReduction(MetricInterface):
  """
    Metric to calculate the reduction fraction of uncertainty (standard deviation) 
    from prior to posterior distribution.
  """
  def __init__(self):
    """
      Constructor
      @ In, None
      @ Out, NOne
    """
    super().__init__()
    # If True the metric needs to be able to handle (value,probability) where value and probability are lists
    #self.acceptsProbability = True
    # If True the metric needs to be able to handle a passed in Distribution
    #self.acceptsDistribution = True

  def run(self, x, y, weights=None, axis=0, **kwargs):
    """
      This method computes the reduction fraction of uncertainty from x to y based on given metric
      @ In, x, tuple or list, array containing data of x.
      @ In, y, tuple or list, array containing data of y.
      @ In, weights, array_like (numpy.array or list), optional, not used in this metric
      @ In, axis, integer, default is 0, not used for this metric.
      @ In, kwargs, dict, dictionary of parameters characteristic of each metric
      @ Out, value, float, metric result, standard deviation reduction fraction
    """
    value = MetricUtilities._getSTDReduction(x,y)
    return float(value)
