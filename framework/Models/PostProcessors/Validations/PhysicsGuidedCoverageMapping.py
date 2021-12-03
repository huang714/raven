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
  Created on August 09, 2021

  @author: dhuang

  This class is for the algorithms of Physics-guided Coverage Mapping
  It inherits from the PostProcessor directly
  ##TODO: Recast it once the new PostProcesso API gets in place
"""

#External Modules------------------------------------------------------------------------------------
import numpy as np
import xarray as xr
from scipy import stats
#External Modules End--------------------------------------------------------------------------------

#Internal Modules------------------------------------------------------------------------------------
from utils import utils, randomUtils
from .. import ValidationBase
#Internal Modules End--------------------------------------------------------------------------------

class PhysicsGuidedCoverageMapping(ValidationBase):
  """
    PhysicsGuidedCoverageMapping is a base class for validation problems
    It represents the base class for most validation problems
  """

  @classmethod
  def getInputSpecification(cls):
    """
      Method to get a reference to a class that specifies the input data for
      class cls.
      @ In, cls, the class for which we are retrieving the specification
      @ Out, specs, InputData.ParameterInput, class to use for
        specifying input of cls.
    """
    specs = super(PhysicsGuidedCoverageMapping, cls).getInputSpecification()
    #specs.addSub(metricInput)
    return specs

  def __init__(self):
    """
      Constructor
      @ In, None
      @ Out, None
    """
    super().__init__()
    self.printTag = 'POSTPROCESSOR PhysicsGuidedCoverageMapping'
    self.dynamicType = ['static','dynamic'] #  for now only static is available
    self.acceptableMetrics = ["CDFAreaDifference", "PDFCommonArea", "STDReduction"] #  acceptable metrics
    self.name = 'PhysicsGuidedCoverageMapping'
    # self.pivotParameter = None

  def _handleInput(self, paramInput):
    """
      Function to handle the parsed paramInput for this class.
      @ In, paramInput, ParameterInput, the already parsed input.
      @ Out, None
    """
    super()._handleInput(paramInput)


  def run(self, inputIn):
    """
      This method executes the postprocessor action. In this case it loads the
      results to specified dataObject
      @ In, inputIn, list, dictionary of data to process
      @ Out, outputDict, dict, dictionary containing the post-processed results
    """
    dataDict = {self.getDataSetName(data): data for _, _, data in inputIn['Data']}
    pivotParameter = self.pivotParameter
    names = [self.getDataSetName(inp[-1]) for inp in inputIn['Data']]
    if len(inputIn['Data'][0][-1].indexes) and self.pivotParameter is None:
      if 'dynamic' not in self.dynamicType: #self.model.dataType:
        self.raiseAnError(IOError, "The validation algorithm '{}' is not a dynamic model but time-dependent data has been inputted in object {}".format(self._type, inputIn['Data'][0][-1].name))
    evaluation ={k: np.atleast_1d(val) for k, val in  self._evaluate(dataDict, **{'dataobjectNames': names}).items()}

    if pivotParameter:
      if len(inputIn['Data'][0][-1]['time']) != len(list(evaluation.values())[0]):
        self.raiseAnError(RuntimeError, "The pivotParameter value '{}' has size '{}' and validation output has size '{}'".format( len(dataSets[0][self.pivotParameter]), len(evaluation.values()[0])))
      if pivotParameter not in evaluation:
        evaluation[pivotParameter] = inputIn['Data'][0][-1]['time']
    return evaluation

  ### utility functions
  def _evaluate(self, datasets, **kwargs):
    """
      Main method to "do what you do".
      @ In, datasets, list, list of datasets (data1,data2,etc.) to used.
      @ In, kwargs, dict, keyword arguments
      @ Out, outputDict, dict, dictionary containing the results {"feat"_"target"_"metric_name":value}
    """
    names = kwargs.get('dataobjectNames')
    outputDict = {}
    for feat, targ in zip(self.features, self.targets):
      featData = self._getDataFromDataDict(datasets, feat, names)
      targData = self._getDataFromDataDict(datasets, targ, names)

      # Standardization
      yExp = np.array(featData[0]).reshape(len(featData[0]))
      yApp = np.array(targData[0]).reshape(len(targData[0]))
      yExpRef = np.mean(yExp)
      yAppRef = np.mean(yApp)
      yExpStd = (yExp-yExpRef)/yExpRef
      yAppStd = (yApp-yAppRef)/yAppRef

      # Kernel Desnity Estimation
      m1 = yExpStd[:]
      m2 = yAppStd[:]
      xmin = m1.min()
      xmax = m1.max()
      ymin = m2.min()
      ymax = m2.max()

      binKDE = 200j
      X, Y = np.mgrid[xmin:xmax:binKDE, ymin:ymax:binKDE]
      psts = np.vstack([X.ravel(), Y.ravel()])
      vals = np.vstack([m1, m2])
      # kernel
      knl = stats.gaussian_kde(vals)
      Z = np.reshape(knl(psts).T, X.shape)

      # Virtual Measurement
      msrMean = 0.0
      msrStd = 0.01*np.std(yAppStd)
      msrNumSmpl = 1000
      randomUtils.randomSeed(0)
      yMsr = msrStd * randomUtils.randomNormal(size=msrNumSmpl) + msrMean
      binMsr = msrNumSmpl//20
      yMsrPdf, yMsrBin = np.histogram(yMsr, binMsr, range=(xmin, xmax), density=True)

      # yAppPred by integrating f(yexp, yapp)dyexp * f(yexp)
      # on range [ymsr.min(), ymsr.max()]
      yAppPredPdf = np.zeros(Y.shape[1])
      intgrPdf = 0.0 # for normalization
      for i in range(len(Y[0, :])):
        yAppPi = 0.0
        for j in range(len(yMsrBin)-1):
          yAppPi += knl.evaluate([yMsrBin[j]+0.5*np.diff(yMsrBin)[j], Y[0, i]]) * np.diff(yMsrBin)[j] * yMsrPdf[j]
        yAppPredPdf[i] = yAppPi
        intgrPdf += yAppPredPdf[i]*(Y[0, 1]-Y[0, 0])

      # normalized PDF of predicted application
      yAppPredPdfNorm = yAppPredPdf/intgrPdf

      # Calculate Expectation (average value) of predicted application
      predMean = 0.0
      for i in range(len(Y[0, :])):
        predMean += Y[0, i]*yAppPredPdfNorm[i]*(Y[0, 1]-Y[0, 0])

      # Calculate Variance of predicted application
      predVar = 0.0
      for i in range(len(Y[0, :])):
        predVar += (Y[0, i]-predMean)**2.0 * yAppPredPdfNorm[i]*(Y[0, 1]-Y[0, 0])

      # Standard Deviation
      predStd = np.sqrt(predVar)
      priStd = np.std(yAppStd)
      stdReduct = 1.0-predStd/priStd

      # Generate distribution by yAppPredPdfNorm
      predBins = np.insert(Y[0, :]+0.5*(Y[0, 1]-Y[0, 0]), 0, Y[0, 0]-0.5*(Y[0, 1]-Y[0, 0]))
      predHist = tuple((yAppPredPdfNorm, predBins))
      predDist = stats.rv_histogram(predHist)
      yAppPred = predDist.rvs(size=len(yAppStd), random_state=randomUtils.randomSeed(0, seedBoth=True))

      # Form tuple data for metrics
      priData = tuple((yAppStd.reshape(len(yAppStd),1), targData[1]))
      postData = tuple((yAppPred.reshape(len(yAppStd),1), targData[1]))
      for metric in self.metrics:
        #name = "{}_{}_{}".format(feat.split("|")[-1], targ.split("|")[-1], metric.estimator.name)
        name = "pri_post_{}".format(metric.estimator.name)
        outputDict[name] = metric.evaluate((priData, postData), multiOutput='raw_values')

    return outputDict

  def _getDataFromDataDict(self, datasets, var, names=None):
    """
      Utility function to retrieve the data from dataDict
      @ In, datasets, list, list of datasets (data1,data2,etc.) to search from.
      @ In, names, list, optional, list of datasets names (data1,data2,etc.). If not present, the search will be done on the full list.
      @ In, var, str, the variable to find (either in fromat dataobject|var or simply var)
      @ Out, data, tuple(numpy.ndarray, xarray.DataArray or None), the retrived data (data, probability weights (None if not present))
    """
    pw = None
    if "|" in var and names is not None:
      do, feat =  var.split("|")
      dat = datasets[do][feat]
    else:
      for doIndex, ds in enumerate(datasets):
        if var in ds:
          dat = ds[var]
          break
    if 'ProbabilityWeight-{}'.format(feat) in datasets[do]:
      pw = datasets[do]['ProbabilityWeight-{}'.format(feat)].values
    elif 'ProbabilityWeight' in datasets[do]:
      pw = datasets[do]['ProbabilityWeight'].values
    dim = len(dat.shape)
    # (numRealizations,  numHistorySteps) for MetricDistributor
    dat = dat.values
    if dim == 1:
      #  the following reshaping does not require a copy
      dat.shape = (dat.shape[0], 1)
    data = dat, pw
    return data
