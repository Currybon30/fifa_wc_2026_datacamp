# ⚽🏆🌍 FIFA World Cup 2026 Prediction System

An advanced football analytics and tournament simulation system for predicting the **2026 FIFA World Cup** using ML, Elo ratings, statistical modeling, and Monte Carlo simulations.

This project combines multiple ML models, feature engineering pipelines, and probabilistic tournament simulations to generate realistic football match predictions.

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
