# Stratégie de Pair Trading sur Cryptomonnaies

Ce projet implémente une stratégie de **pair trading statistique** sur cryptomonnaies basée sur la **coïntégration**. Il repose sur l'analyse des résidus de régressions linéaires entre paires d’actifs, la **normalisation des signaux**, et l'**optimisation des seuils** d'entrée et de sortie.

📄 Une description complète de la méthode (récupération des données, tests, stratégie, calibration) est disponible dans le document `Pair_Trading.pdf`.

---

## 🧠 Détail du Code

- `BinanceData.py` : collecte les données OHLCV depuis l’API Binance, les nettoie, les aligne et les sépare en jeu de **test** et de **backtest**.

- `TestResiduals.py` : sélectionne les **paires coïntégrées** via des régressions linéaires et des tests de **stationnarité** (ADF). Stocke les résidus, les coefficients et les statistiques.

- `BackTestResiduals.py` : calcule les **résidus de backtest** à partir des coefficients estimés sur les données de test.

- `Strategy.py` : exécute la stratégie de trading :
  - Entrée en position si le résidu dépasse un seuil `bound`
  - Sortie si le résidu revient proche de zéro ou atteint un `stopLoss`
  - Calcule le **PnL**, la **répartition du capital**, et propose une fonction de **calibration** (via Nelder-Mead) des seuils optimaux.

- `PerformancePlots.py` : visualise le PnL global, le **drawdown**, les rendements cumulés et affiche les **métriques de performance** (Sharpe, MDD).

- `main.py` : pipeline complet qui :
  - récupère ou met à jour les données
  - identifie les paires coïntégrées
  - calibre la stratégie sur la période de test
  - exécute la stratégie sur test puis backtest
  - trace les performances

---

## ⚙️ Fonctionnement

1. **Sélection des paires** sur données de test  
2. **Calibration automatique** des seuils `bound` & `stopLoss`  
3. **Application sur backtest** avec suivi du capital  
4. **Évaluation** : rendement, ratio de Sharpe, drawdown, PnL

---

## 📊 Exemple de résultats

| Date           | bound* | stopLoss* | rdm (%) | Sharpe | MDD (%) |
|----------------|--------|-----------|---------|--------|---------|
| 07-01 au 10-01 | 1.83   | 3.82      | 2.39    | 0.86   | -0.18   |
| 14-01 au 17-01 | 1.54   | 3.13      | -0.17   | -0.03  | -0.73   |

---

**Objectif** : Identifier des opportunités de **reversion à la moyenne** entre cryptos, optimiser automatiquement les seuils d'intervention, et suivre l’évolution du capital à travers des périodes de marché.

