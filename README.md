# ⚽🏆🌍 FIFA World Cup 2026 Prediction System

  [![Streamlit](https://img.shields.io/badge/Frontend-Streamlit%201.58-red.svg?logo=streamlit&logoColor=red)](https://streamlit.io/)
  [![FIFA](https://img.shields.io/badge/World%20Cup%202026-FIFA-blue.svg?logo=fifa&logoColor=blue)](https://www.fifa.com/worldcup/)
  [![Datacamp](https://img.shields.io/badge/Competition-Datacamp-03EF62.svg?logo=datacamp&logoColor=#03EF62)](https://www.datacamp.com/)
  [![Python](https://img.shields.io/badge/Programming%20Language-Python%203.11-blue.svg?logo=python&logoColor=blue)](https://www.python.org/)
  [![Jupyter](https://img.shields.io/badge/Notebook-Jupyter-F37626.svg?logo=jupyter&logoColor=#F37626)](https://jupyter.org/)
  [![Kaggle](https://img.shields.io/badge/Dataset-Kaggle-20BEFF.svg?logo=kaggle&logoColor=#20BEFF)](https://www.kaggle.com/)

An advanced football analytics and tournament simulation system for predicting the **2026 FIFA World Cup** using ML, Elo ratings, statistical modeling, and Monte Carlo simulations.

This project combines multiple ML models, feature engineering pipelines, and probabilistic tournament simulations to generate realistic football match predictions.

Live URL: https://fifa-worldcup26-tnp.streamlit.app/

<p align="center">
  
  <img width=auto height="400" alt="home" src="https://github.com/user-attachments/assets/c3f6d404-1103-4ccc-bf14-7b22b87cb286" />
  
  <img width=auto height="400" alt="pred" src="https://github.com/user-attachments/assets/7bd276b2-27a1-4deb-82a7-9c404195be75" />
  
  <img width=auto height="400" alt="analysis-page" src="https://github.com/user-attachments/assets/fb914bfc-48ee-4df2-9807-0f8dbeed2019" />

</p>

<br/>


**Note:** Predictions are generated using historical data and pre-trained machine learning models. The system simulates the entire 2026 FIFA World Cup from the beginning of the tournament and does not update based on live match results.

---

# 👁️‍🗨️ Overview

The FIFA World Cup 2026 will feature:

- 48 national teams
- 104 matches
- New expanded tournament format
- Hosts: USA, Canada, and Mexico

This system predicts:

- Match winners
- Goals scored
- Corners
- Yellow cards
- Red cards
- Group stage standings
- Knockout progression
- Tournament champions

using historical football data and simulation-based modeling.

---

# 🧠 System Capabilities

## ✅ Match Prediction Engine

Predicts for every match:

- Home goals
- Away goals
- Corners
- Yellow cards
- Red cards
- Match outcome probabilities

---

## ✅ Tournament Simulation Engine

Simulates:

- Group Stage
- Round of 32
- Round of 16
- Quarter-finals
- Semi-finals
- Final

---

## ✅ Monte Carlo Simulation

Runs tournament simulations multiple times to estimate:

- Championship probabilities
- Runner-up probabilities
- Podium finishes
- Team performance distributions

---

# 🤖 Prediction Models

The system uses multiple specialized machine learning models for:

| Prediction Task | Model Type |
|---|---|
| Home Goals | Poisson Regressor Model |
| Away Goals | Poisson Regressor Model |
| Corners | Ridge Model |
| Yellow Cards | Poisson Regressor Model |
| Red Cards | Logistic Regression Model |

The trained models are generated and stored as `.pkl` files after running `models.ipynb`.

---

# 📊 Feature Engineering

The prediction system uses features such as:

- Elo ratings
- Attack strength
- Defensive strength
- Team form
- Historical performance
- Goal averages
- Match statistics
- Tournament context

---

# 🏆 Simulation Pipeline

## 1️⃣ Data Processing

- Clean historical football data
- Merge Elo ratings
- Generate statistical features

---

## 2️⃣ Match Prediction

Generate statistical predictions for each match using trained models.

---

## 3️⃣ Group Stage Simulation

Teams earn:

- 3 points for a win
- 1 point for a draw

Standings determine qualification to knockout rounds.

---

## 4️⃣ Knockout Simulation

Single-elimination bracket simulation until the final.

---

## 5️⃣ Monte Carlo Tournament Analysis

The tournament is simulated many times to estimate probabilities and rankings.

---

## 🎯 50K Runs Monte Carlo Simulation

To view the results of the 50K runs Monte Carlo simulation, please access my Kaggle notebook [here](https://www.kaggle.com/code/tuongnguyenpham/fifa-world-cup-2026-prediction-system)
