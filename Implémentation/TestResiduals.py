import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.stattools import adfuller
from BinanceData import BinanceDataFetcher
from UsefullFunctions import load_data


class CointegrationTester(BinanceDataFetcher):
    """ On hérite de BinanceDataFetcher pour avoir la liste
        des tickers et les répertoires des fichiers CSV """

    def __init__(self, pvalueLevel: float = None):
        super().__init__()

        self.dfs = load_data(self.test_output_dir)
        self.level = 0.05 if pvalueLevel is None else pvalueLevel
        self.residuals_dict = {}  # Dictionnaire pour stocker les résidus stationnaires
        self.alpha_beta_dict = {}  # Dictionnaire pour stocker les coefficients beta des régressions linéaires
        self.numberOfPairs = 0
        self.bounds = {}
        self.mean_std = {}
        
        self.analyze_and_find_cointegrated_pairs()
        


    def analyze_and_find_cointegrated_pairs(self):
        """ Analyse toutes les paires possibles et retourne la liste des paires cointégrées """
        file_names = list(self.dfs.keys())
        numberOfPairs, goodPairs = 0, 0

        for i in range(len(file_names)):
            for j in range(i + 1, len(file_names)):
                numberOfPairs += 1
                file1, file2 = file_names[i], file_names[j]
                data1, data2 = self.dfs[file1], self.dfs[file2]

                if len(data1) != len(data2):
                    print(f"Longueurs différentes pour {file1} et {file2}.")
                    continue

                # Déterminer quelle crypto est la moins chère (moyenne historique)
                mean_price1 = data1.mean()
                mean_price2 = data2.mean()

                # On explique TOUJOURS la moins chère (y) par la plus chère (X)
                if mean_price1 <= mean_price2:
                    X = data2.values.reshape(-1, 1)  # Plus chère (variable explicative)
                    y = data1.values                # Moins chère (variable expliquée)
                    pair_key = (file2, file1)      # Ordre : (plus_chère, moins_chère)
                else:
                    X = data1.values.reshape(-1, 1)  # Plus chère (variable explicative)
                    y = data2.values                # Moins chère (variable expliquée)
                    pair_key = (file1, file2)       # Ordre : (plus_chère, moins_chère)

                # Régression linéaire
                model = LinearRegression()
                model.fit(X, y)
                y_pred = model.predict(X)
                residuals = pd.Series(y - y_pred)

                # Test de stationnarité (ADF)
                adf_result_residuals = adfuller(residuals)
                p_value_residuals = adf_result_residuals[1]

                if p_value_residuals < self.level:
                    beta = model.coef_[0]  # Doit être < 1 par construction
                    alpha = model.intercept_
                    print(f"Paire cointégrée : {pair_key} (p-valeur: {p_value_residuals:.6f}, beta: {beta:.6f})")

                    # Stockage avec la clé dans le bon ordre
                    self.residuals_dict[pair_key] = residuals
                    self.alpha_beta_dict[pair_key] = [alpha, beta]
                    self.bounds[pair_key] = np.std(residuals)
                    self.mean_std[pair_key] = [np.mean(residuals), np.std(residuals)]

                    goodPairs += 1

        self.numberOfPairs = numberOfPairs
        print(f"Pourcentage de paires cointégrées : {round(100 * goodPairs / numberOfPairs, 2)}%")

