"""
BharatSHIELD — Master Pipeline Runner & Live Demo Orchestrator.

Executes the entire stack setup in one command:
  1. Generates 15,000 realistic transactions with Indian payment context.
  2. Runs the end-to-end ML model training tournament & SHAP calibration.
  3. Initializes the database & seeds demo merchant transactions with an audit trail.
  4. Tests the FastAPI prediction pipeline and evaluates baseline anomaly monitors.

Usage:
    python scripts/run_pipeline.py
"""

import sys
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

def step(title):
    print("\n" + "=" * 65)
    print(f"  STEP: {title}")
    print("=" * 65)

def run(cmd, desc):
    print(f"\n>> {desc}...")
    start = time.time()
    res = subprocess.run(cmd, cwd=PROJECT_ROOT, shell=True)
    if res.returncode != 0:
        print(f"FAILED: {desc} exited with code {res.returncode}")
        sys.exit(res.returncode)
    print(f">> Completed in {time.time() - start:.1f}s")

def main():
    print("""
  ____  _                      _    ____  _   _ ___ _____ _     ____  
 | __ )| |__   __ _ _ __ __ _| |_ / ___|| | | |_ _| ____| |   |  _ \ 
 |  _ \| '_ \ / _` | '__/ _` | __|\___ \| |_| || ||  _| | |   | | | |
 | |_) | | | | (_| | | | (_| | |_  ___) |  _  || || |___| |___| |_| |
 |____/|_| |_|\__,_|_|  \__,_|\__| |____/|_| |_|___|_____|_____|____/ 
       Real-Time Transaction Risk Intelligence Platform
    """)

    # 1. Generate Synthetic Data
    step("1 / 4 — Generating Indian UPI & Card Payment Telemetry")
    run(f'"{PYTHON}" scripts/generate_demo_data.py --num-transactions 15000', "Generating transactions.csv & demo fixtures")

    # 2. Train Model Tournament
    step("2 / 4 — Training ML Tournament (LR vs RF vs XGBoost) & SHAP Calibration")
    run(f'"{PYTHON}" ml/train_model.py', "Training model and saving feature_config.json")

    # 3. Seed Database & Compute Audit Trail
    step("3 / 4 — Initializing Database Schema & Seeding Audit Trail")
    run(f'"{PYTHON}" scripts/seed_database.py', "Seeding merchants, scores, and anomaly spikes")

    # 4. Run Automated Test Suite
    step("4 / 4 — Running Automated Test Suites (Unit + Integration + Guardrails)")
    run(f'"{PYTHON}" -m pytest backend/tests/ tests/integration/ -v', "Executing pytest suites")

    print("\n" + "*" * 65)
    print("  BHARATSHIELD PIPELINE FULLY CONFIGURED & OPERATIONAL!")
    print("*" * 65)
    print("""
  Quick Start Commands:
  ---------------------
  1. Launch FastAPI Backend:
     python -m uvicorn backend.app.main:app --reload --port 8000
     -> Swagger API Docs: http://localhost:8000/docs

  2. Launch React Merchant Dashboard:
     cd frontend && npm run dev
     -> Live Dashboard:   http://localhost:3000

  3. Launch Full Containerized Stack:
     docker-compose up --build
    """)

if __name__ == "__main__":
    main()
