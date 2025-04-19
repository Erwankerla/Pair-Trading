import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class PerformancePlots:
    def __init__(self, pnl_global, pnl, capital_per_pair, capital):
        self.pnl_global = pnl_global
        self.pnl = pnl
        self.capital_per_pair = capital_per_pair
        self.capital = capital


    def calculate_performance_metrics(self):
        pnl_series = self.capital + pd.Series(self.pnl_global)
        returns = pnl_series.pct_change().dropna()[1:]
        sharpe_ratio = np.sqrt(126) * returns.mean() / returns.std()  # Sharpe annualisé 252/2 car on trade sur deux jours
        
        rolling_max = pnl_series.cummax()
        drawdown = (pnl_series - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        return returns, drawdown, sharpe_ratio, max_drawdown

    def plot_all(self):
        returns, drawdown, sharpe_ratio, max_drawdown = self.calculate_performance_metrics()

        plt.figure(figsize=(12, 8))

        # Subplot 1 : Évolution du PnL
        plt.subplot(2, 2, 1)
        """for pair, pnl in self.pnl.items():
            plt.plot(range(len(pnl)), self.capital + pd.Series(pnl), alpha=0.5)"""
        plt.plot(range(len(self.pnl_global)), self.capital+ pd.Series(self.pnl_global), label='PnL Global', linewidth=2, linestyle='--')
        plt.xlabel('Temps')
        plt.ylabel('PnL')
        plt.title('Évolution du PnL')
        plt.legend()
        plt.grid(True)

        # Subplot 2 : Drawdown
        plt.subplot(2, 2, 2)
        plt.plot(range(len(drawdown)), drawdown, label='Drawdown', color='red')
        plt.xlabel('Temps')
        plt.ylabel('Drawdown')
        plt.title('Évolution du Drawdown')
        plt.legend()
        plt.grid(True)

        # Subplot 3 : Rendements
        plt.subplot(2, 2, 3)
        total_returns = np.zeros(len(next(iter(self.capital_per_pair.values()))))
        for pair, capitals in self.capital_per_pair.items():
            returns_pair = pd.Series(capitals).pct_change().dropna()
            plt.plot(range(len(returns_pair)), returns_pair, alpha=0.7)
        plt.xlabel('Temps')
        plt.ylabel('Rendements')
        plt.title('Évolution des Rendements')
        plt.legend()
        plt.grid(True)

        # Subplot 4 : Rendements cumulés
        plt.subplot(2, 2, 4)
        total_returns = np.zeros(len(next(iter(self.capital_per_pair.values()))))
        for pair, capitals in self.capital_per_pair.items():
            returns_pair = pd.Series(capitals)
            total_returns += returns_pair
            plt.plot(range(len(returns_pair)), (returns_pair - returns_pair[0]) / returns_pair[0], alpha=0.6)
        plt.plot(range(len(total_returns)), (total_returns - total_returns[0]) / total_returns[0], linewidth=2, linestyle='--', color='blue', label='Rendements cumulés globaux')
        plt.xlabel('Temps')
        plt.ylabel('Rendements cumulés')
        plt.title('Évolution des Rendements cumulés')
        plt.legend()
        plt.grid(True)

        # Afficher les métriques de performance
        plt.figtext(0.5, 0.01, f"Ratio de Sharpe: {sharpe_ratio:.2f} | Maximum Drawdown: {max_drawdown:.2%}", ha="center", fontsize=12, bbox={"facecolor": "orange", "alpha": 0.5, "pad": 5})

        plt.tight_layout()
        plt.show()
