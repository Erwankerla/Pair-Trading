import os
import pandas as pd


def load_data(repertory):
        """ Charge les données de clôture des fichiers CSV dans un dictionnaire """
        files = [os.path.join(repertory, f) for f in os.listdir(repertory) if f.endswith('.csv')]
        if not files:
            print("Aucun fichier CSV trouvé.")
            return {}

        dfs = {os.path.basename(file): pd.read_csv(file)['close'] for file in files}
        print(f"Chargé {len(dfs)} fichiers.")
        return dfs