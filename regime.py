import numpy as np

class regime():

    def __init__(self, candle, length, pen=None):
        self.candle = candle
        self.length = length
        self.pen = pen
        self.data = []

        candle.metrics.append(self)


    def ping(self):
        self.data = [x[1] for x in self.candle[-1:self.length]]
        self.pelt(self.normal_mean(self.data, mean=0), len(self.data), self.pen)


        def pelt(self, cost, length, pen):

            if pen is None:
                pen = np.log(length)

            F = np.zeros(length + 1)
            R = np.array([0], dtype=np.int)
            candidates = np.zeros(length + 1, dtype=np.int)

            F[0] = -pen

            for tstar in range(2, length + 1): # dynamic programming
                cpt_cands = R
                seg_costs = np.zeros(len(cpt_cands))    # cost of each segmentation
                for i in range(0, len(cpt_cands)):
                    seg_costs[i] = cost(cpt_cands[i], tstar)

                F_cost = F[cpt_cands] + seg_costs
                F[tstar], tau = find_min(F_cost, pen)   # find the one with min Bayes cost
                candidates[tstar] = cpt_cands[tau]

                ineq_prune = [val < F[tstar] for val in F_cost]  # assumption made
                R = [cpt_cands[j] for j, val in enumerate(ineq_prune) if val]
                R.append(tstar - 1)
                R = np.array(R, dtype=np.int)

            last = candidates[-1]
            changepoints = [last]
            while last > 0:
                last = candidates[last]
                changepoints.append(last)

            return sorted(changepoints)

        def normal_var(self, data, mean):

            if not isinstance(data, np.ndarray):
                data = np.array(data)

            cumm = [0.0]
            cumm.extend(np.cumsum(np.power(np.abs(data - mean), 2)))

            def cost(s, t):

                dist = float(t - s)
                diff = cumm[t] - cumm[s]
                return dist * np.log(diff/dist)

            return cost


        def find_min(self, arr, val=0.0):

            return min(arr) + val, np.argmin(arr)
