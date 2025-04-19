from BinanceData import *
from UsefullFunctions import load_data
import numpy as np
from scipy.optimize import minimize



class Strategy(BinanceDataFetcher): 

    def __init__(self, pairs: dict, residuals: dict, alpha_betas: dict, isBackTest: bool, mean_std: dict = None, initial_capital: float = None):
        super().__init__()

        self.pairs = pairs
        self.residuals = residuals
        self.alpha_betas = alpha_betas
        self.isBackTest = isBackTest

        if initial_capital is None:
            self.initial_capital = 100
        else:
            self.initial_capital = initial_capital

        self.capital_per_pair = {pair: [initial_capital / len(pairs)] for pair in pairs}
        self.pnl = {pair: [0] for pair in pairs}
        self.pnl_global = [0]
        self.open_trades = {}
        self.trading_fee = 0.001

        data = load_data(self.backtest_output_dir) if isBackTest else load_data(self.test_output_dir)
        self.selectedData = {key: data[key] for key in set().union(*pairs) if key in data}

        if mean_std is None and isBackTest is False:
            self.normResidus = {pair : (residuals - np.mean(residuals)) / np.std(residuals) for pair, residuals in self.residuals.items()}
        elif mean_std is not None and (isBackTest is False or isBackTest is True):
            self.normResidus = {pair : (residuals - mean_std[pair][0]) / mean_std[pair][1] for pair, residuals in self.residuals.items()}
        else:
            raise ValueError("Please give mean and std of good pairs for back testing the strategy")


    def Strategy(self, bound, stopLoss):
        for pair in self.pairs:
            isTrading, isUpperBoundTrade = False, None
            beta = self.alpha_betas[pair][1]
            data1, data2 = self.selectedData[pair[0]], self.selectedData[pair[1]] 
            normalized_residuals = self.normResidus[pair]
            
            for t in range(len(normalized_residuals)):
                current_price1 = data1[t]
                current_price2 = data2[t]
                residual = normalized_residuals[t]
                
                if not isTrading:
                    if self.capital_per_pair[pair][-1] <= 0.0:  # Seuil minimal pour éviter les micro-investissements
                        continue
                    
                    if np.abs(residual) >= bound:
                        investment = 1 * self.capital_per_pair[pair][-1] # Montant à investir (100% du capital alloué à la paire)
                        
                        omega = -1 if residual >= bound else 1

                        qty1 = omega * beta * investment / ((1 + beta) * current_price1)
                        qty2 = omega * investment / ((1 + beta) * current_price2)
                                                
                        self.open_trades[pair] = {
                            'entry_price1': current_price1,
                            'entry_price2': current_price2,
                            'qty1': qty1,
                            'qty2': qty2}

                        isTrading = True
                        isUpperBoundTrade = True if omega == -1 else False
                        if t > 0:
                            self.pnl[pair].append(self.pnl[pair][-1])
                            self.capital_per_pair[pair].append(self.capital_per_pair[pair][-1])
                    
                    else:
                        if t > 0:
                            self.pnl[pair].append(self.pnl[pair][-1])
                            self.capital_per_pair[pair].append(self.capital_per_pair[pair][-1])
                    
                else:
                    if (isUpperBoundTrade and residual <= 1e-4) or (not isUpperBoundTrade and residual >= -1e-4) or (np.abs(residual) >= stopLoss):
                        pnl_net = self.getPNL(pair, current_price1, current_price2)
                        self.pnl[pair].append(self.pnl[pair][-1] + pnl_net) # Mise à jour du P&L
                        self.capital_per_pair[pair].append(self.capital_per_pair[pair][-1] + pnl_net) # MIse à jour du capital
                        isTrading = False # Indique que l'on est plus dans un trade
                    
                    else:
                        self.pnl[pair].append(self.pnl[pair][-1]) # Le P&L ne change pas 
                        self.capital_per_pair[pair].append(self.capital_per_pair[pair][-1]) # Le capital ne change pas 

            if isTrading:  # En cas de fin de période avec un trade ouvert, on sort et calcule le PnL
                pnl_net = self.getPNL(pair, current_price1, current_price2)
                self.pnl[pair].append(self.pnl[pair][-1] + pnl_net) # Mise à jour du P&L
                self.capital_per_pair[pair].append(self.capital_per_pair[pair][-1] + pnl_net) # MIse à jour du capital
                isTrading = False # Indique que l'on est plus dans un trade    
            else: # uniquement pour avoir le même nombres de valuer de pnl pour pas fausser le zip*
                self.pnl[pair].append(self.pnl[pair][-1])                                           # important pour pas fausser le pnl à cause du zip* et ainsi avoir les mêmes longeurs
                self.capital_per_pair[pair].append(self.capital_per_pair[pair][-1])

        # Calcul du PnL global
        total_pnl = [sum(pnl) for pnl in zip(*self.pnl.values())]
        self.pnl_global = total_pnl
        
        print(f"Total PnL: {self.pnl_global[-1]}")
        #self.plot_pnl()
        #self.plot_returns()
        #self.calculate_performance_metrics()




    def getPNL(self, pair, current_price1, current_price2):
        trade = self.open_trades[pair]
        pnl_trade = (trade['qty1'] * (current_price1 - trade['entry_price1'])) + (trade['qty2'] * (current_price2 - trade['entry_price2']))
        fee_close = self.trading_fee * (abs(trade['qty1'] * current_price1) + abs(trade['qty2'] * current_price2))
        fee_open = self.trading_fee * (abs(trade['qty1'] * trade['entry_price1']) + abs(trade['qty2'] * trade['entry_price2']))
        pnl_net = pnl_trade - fee_open - fee_close

        del self.open_trades[pair]
        return pnl_net



    def StrategyForCalibration(self, bound, stopLoss):

        sumPNL = 0
        for pair in self.pairs:
            isTrading, isUpperBoundTrade = False, None
            beta = self.alpha_betas[pair][1]
            data1, data2 = self.selectedData[pair[0]], self.selectedData[pair[1]]
            normalized_residuals = self.normResidus[pair]
            
            investment = self.initial_capital / len(self.pairs)
            for t in range(len(normalized_residuals)):
                current_price1 = data1[t]
                current_price2 = data2[t]
                residual = normalized_residuals[t]
                
                if not isTrading:
                    if investment <= 0.0:
                        continue
                    
                    if np.abs(residual) >= bound:
                        omega = -1 if residual >= bound else 1

                        qty1 = omega * beta * investment / ((1 + beta) * current_price1)
                        qty2 = omega * investment / ((1 + beta) * current_price2)
                                                
                        self.open_trades[pair] = {
                            'entry_price1': current_price1,
                            'entry_price2': current_price2,
                            'qty1': qty1,
                            'qty2': qty2}

                        isTrading = True
                        isUpperBoundTrade = True if omega == -1 else False

                else:
                    if (isUpperBoundTrade and residual <= 1e-4) or (not isUpperBoundTrade and residual >= -1e-4) or (np.abs(residual) >= stopLoss):
                        pnl = self.getPNL(pair, current_price1, current_price2)
                        investment += pnl
                        sumPNL += pnl
                        isTrading = False

            if isTrading:
                sumPNL += self.getPNL(pair, current_price1, current_price2)
            
        return sumPNL




    from scipy.optimize import minimize

    def Calibration(self):
        """
        Calibre les paramètres bound et stopLoss pour maximiser le PnL de la stratégie.
        """

        # Fonction objectif à minimiser (nous maximisons le PnL, donc nous minimisons -PnL)
        def objective(params):
            bound, stopLoss = params
            if (bound < 0.5 or bound > 4.0) or (stopLoss < 0.6 or stopLoss > 5.5) or (stopLoss <= bound) or (stopLoss > 3*bound):
                return np.inf
            return -self.StrategyForCalibration(bound, stopLoss)

        # Simplex initial (utilisé uniquement pour Nelder-Mead)
        initial_simplex = np.array([[1.5, 3], [2, 4], [1, 5]])

        initial_guess = initial_simplex[0]

        options = {
            'maxiter': 200,  # Nombre maximal d'itérations
            'ftol': 1e-4,    # Tolérance sur la fonction objectif
            'xatol': 1e-4    # Tolérance sur les variables (utilisé pour Nelder-Mead et Powell)
        }

        result = minimize(objective, initial_guess, method='Nelder-Mead', options={'Initial-Simplex':initial_simplex, **options})
        
        best_bound, best_stopLoss = result.x
        best_pnl = -result.fun

        # Afficher les résultats
        print(f"Meilleur bound : {best_bound}")
        print(f"Meilleur stopLoss : {best_stopLoss}")
        print(f"Meilleur PnL : {best_pnl}")

        return best_bound, best_stopLoss