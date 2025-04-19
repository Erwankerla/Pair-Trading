import pandas as pd
from BinanceData import BinanceDataFetcher
from UsefullFunctions import load_data

class ResidualCalculator(BinanceDataFetcher):
    def __init__(self, alphas_betas_dict: dict):
        """
        Initialise le calculateur de résidus.
        
        :param alphas_betas_dict: Dictionnaire contenant les paires cointégrées avec leurs alphas et betas.
                                  Format : {(file1, file2): (alpha, beta)}
        """
        super().__init__()
        self.alphas_betas_dict = alphas_betas_dict
        self.backtest_data = load_data(self.backtest_output_dir)

        self.backtestResiduals = self.calculate_residuals()

    

    def calculate_residuals(self):
        """
        Calcule les résidus pour chaque paire cointégrée à partir des alphas et betas.
        
        :return: Dictionnaire des résidus pour chaque paire.
                 Format : {(file1, file2): pd.Series des résidus}
        """
        residuals_dict = {}

        for pair, alpha_beta in self.alphas_betas_dict.items():
            # Vérification que les fichiers existent dans le dictionnaire des données
            file1, file2 = pair[0], pair[1]
            alpha, beta = alpha_beta[0], alpha_beta[1]

            if file1 not in self.backtest_data or file2 not in self.backtest_data:
                print(f"Données manquantes pour {file1} ou {file2}.")
                continue

            X = self.backtest_data[file1]
            y = self.backtest_data[file2]

            # Vérification des longueurs
            if len(X) != len(y):
                print(f"Longueurs différentes pour {file1} et {file2}.")
                continue

            residuals = y - (alpha + beta * X)
            residuals_dict[(file1, file2)] = pd.Series(residuals.values, index=X.index)

        return residuals_dict

