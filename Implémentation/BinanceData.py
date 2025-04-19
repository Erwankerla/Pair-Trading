from datetime import datetime
import os
import time
import pandas as pd
import ccxt
from dateutil.relativedelta import relativedelta

class BinanceDataFetcher:
    def __init__(self, days: int = None):
        self.exchange = ccxt.binance()
        self.days = 3 if days is None else days

        self.tickers = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "XRP/USDT",
            "SOL/USDT", "DOGE/USDT", "DOT/USDT", "LTC/USDT",
            "AVAX/USDT", "TRX/USDT", "LINK/USDT", "ATOM/USDT", "SHIB/USDT",
            "NEAR/USDT", "UNI/USDT", "FTM/USDT", "XLM/USDT", "ALGO/USDT"
        ]

        self.timeframe = '1m'

        # Répertoires de sauvegarde
        self.output_dir = "crypto_data"
        self.test_output_dir = "crypto_data_test"  # Répertoire pour les tests de stratégie
        self.backtest_output_dir = "crypto_data_backtest"  # Répertoire pour les backtests

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.test_output_dir, exist_ok=True)
        os.makedirs(self.backtest_output_dir, exist_ok=True)

    def fetch_historical_data(self, symbol, timeframe, since, end_timestamp):
        """ Récupère les données historiques à partir d'une date donnée jusqu'à une date de fin spécifiée """
        all_ohlcv = []
        while since < end_timestamp:
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 60 * 1000  # Passer à la minute suivante
                time.sleep(1)  # Pause pour éviter les limites de l'API
            except ccxt.BaseError as e:
                print(f"Erreur pour {symbol}: {str(e)}")
                break
        return all_ohlcv

    def run(self, end_date: str = None, update=False):
        """
        Télécharge ou met à jour les données selon le paramètre update.
        Si end_date est spécifié, les données sont récupérées de end_date - days à end_date.
        """
        if end_date is None:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        start_date = end_date - relativedelta(days=self.days)
        start_date_exact = start_date.strftime('%Y-%m-%dT00:00:00Z')

        end_timestamp = int(end_date.timestamp() * 1000)

        for ticker in self.tickers:
            print(f"{'Actualisation' if update else 'Téléchargement'} des données pour {ticker}...")
            file_name = os.path.join(self.output_dir, f"{ticker.replace('/', '_')}_{self.days}d.csv")

            if update and os.path.exists(file_name):
                df_existing = pd.read_csv(file_name)
                last_timestamp = pd.to_datetime(df_existing['timestamp']).max()
                since = int(last_timestamp.timestamp() * 1000) + 60 * 1000
            else:
                since = self.exchange.parse8601(start_date_exact)

            ohlcv = self.fetch_historical_data(ticker, self.timeframe, since, end_timestamp)

            if not ohlcv:
                print(f"Aucune nouvelle donnée disponible pour {ticker}.")
                continue

            columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df_new = pd.DataFrame(ohlcv, columns=columns)
            df_new['timestamp'] = pd.to_datetime(df_new['timestamp'], unit='ms')

            if update and os.path.exists(file_name):
                df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset='timestamp').reset_index(drop=True)
            else:
                df_combined = df_new

            df_combined.to_csv(file_name, index=False)
            print(f"Données pour {ticker} sauvegardées dans {file_name}")

        self.adjustLenghtCSV()
        self.split_data()

    def adjustLenghtCSV(self):
        """ Tronque tous les fichiers CSV à la longueur minimale parmi eux """
        files = [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir) if f.endswith('.csv')]
        if not files:
            raise ValueError("Veuillez utiliser la fonction run avec update=False")

        min_length = float('inf')
        for file in files:
            df = pd.read_csv(file)
            file_length = len(df)
            min_length = min(min_length, file_length)

        for file in files:
            df = pd.read_csv(file)
            if len(df) > min_length:
                df = df.iloc[:min_length]
            df.to_csv(file, index=False)
            print(f"Données mises à jour pour {file}")

        print("Traitement terminé.")

    def split_data(self):
        """
        Scinde les données des fichiers CSV en jeux de test et de backtest.
        Les données de test correspondent à la dernière journée avant end_date.
        Les données de backtest correspondent au reste.
        """
        files = [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir) if f.endswith('.csv')]

        for file in files:
            df = pd.read_csv(file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            n = len(df)
            test_size = int(0.6 * n)

            df_test = df.iloc[:test_size, :]
            df_backtest = df.iloc[test_size:, :]

            file_name_test = os.path.join(self.test_output_dir, os.path.basename(file))
            file_name_backtest = os.path.join(self.backtest_output_dir, os.path.basename(file))

            df_test.to_csv(file_name_test, index=False)
            df_backtest.to_csv(file_name_backtest, index=False)

            print(f"Fichier {file} scindé : Test -> {file_name_test}, Backtest -> {file_name_backtest}")
