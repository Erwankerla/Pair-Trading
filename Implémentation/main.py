from TestResiduals import CointegrationTester, BinanceDataFetcher
from BackTestResiduals import ResidualCalculator
from Strategy import Strategy
from PerformancePlots import PerformancePlots

################################# INPUTS ###################################
""" Si vous voulez récupérer des nouvelles données ou update celles déjà présentes
il faut que RUN_OR_UPDATE_DATA soit True et il faut remplir UPDATE_DATA.
Si RUN_OR_UPDATE_DATA est False alors UPDATE_DATA est inutile"""
RUN_OR_UPDATE_DATA = True 
UPDATE_DATA = False

"""Possible de rentrer une date limite pour selectionner les données et de lui
donner le nombres de jours de données que l'on veut."""
END_DATE = "2025-02-15"
DAYS = 3

"""Le niveau de p-value que l'on considère comme acceptable"""
P_VALUE_LEVEL = 0.01
############################################################################



############################# GET/UPADTE DATA ##############################
fetcher = BinanceDataFetcher(days=DAYS)
if RUN_OR_UPDATE_DATA is True:
    fetcher.run(end_date=END_DATE, update=UPDATE_DATA)
############################################################################


########################## Cointegration Test ##############################
cointTester = CointegrationTester(pvalueLevel=P_VALUE_LEVEL)
goodPairs = list(cointTester.residuals_dict.keys())
############################################################################


########################## Residus Backtest ################################
btResidualsCalculator = ResidualCalculator(cointTester.alpha_beta_dict)
btResiduals = btResidualsCalculator.backtestResiduals
############################################################################


########################## Stratégie sur Test ##############################
strategy = Strategy(pairs = goodPairs, residuals = cointTester.residuals_dict,
                    alpha_betas = cointTester.alpha_beta_dict,
                    isBackTest = False, initial_capital=100)
bound, stopLoss = strategy.Calibration()
strategy.Strategy(bound, stopLoss)

plots = PerformancePlots(strategy.pnl_global, strategy.pnl, 
                         strategy.capital_per_pair, capital=100)
plots.plot_all()
############################################################################

########################## Stratégie sur Back-Test #########################
strategy1 = Strategy(pairs = goodPairs, residuals = btResiduals,
                    alpha_betas = cointTester.alpha_beta_dict,
                    isBackTest = True, mean_std = cointTester.mean_std, initial_capital=100)
strategy1.Strategy(bound, stopLoss)

plots1 = PerformancePlots(strategy1.pnl_global, strategy1.pnl, 
                          strategy1.capital_per_pair, capital=100)
plots1.plot_all()
###########################################################################