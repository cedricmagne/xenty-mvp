# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Repository overview
- Purpose: Streamlit application for analyzing crypto projects’ engagement and sentiment on Twitter/X. It combines an ML clustering pipeline for engagement and a DL sentiment model for comments.
- Stack: Python 3.10.14, Streamlit, scikit-learn, TensorFlow, Hugging Face Transformers, Plotly, SQLite, KaggleHub.
- Entry points:
  - Streamlit app: Xenty.py (redirects to pages/1_🏠_Home.py)
  - Streamlit pages: pages/2_📊_Dataset.py, pages/3_🔮_ML_Prediction.py, pages/4_🧠_DL_Prediction.py
  - CLI utilities: sync.py (batch fetch tweets + comments to SQLite), update_twitter_account.py (update user IDs)

Commands you’ll commonly use
- Python version and venv
  ```bash path=null start=null
  # Ensure Python 3.10.14 (pyenv will pick this up from .python-version if installed)
  python3 --version
  
  # Create and activate a virtual environment
  python -m venv .venv
  source .venv/bin/activate  # Windows: .venv\Scripts\activate
  ```

- Install dependencies
  ```bash path=null start=null
  pip install -r requirements.txt
  
  # Optional: editable install of the local package
  pip install -e .
  ```

- Run the Streamlit app (multi-page)
  ```bash path=null start=null
  streamlit run Xenty.py
  # App will be available at http://localhost:8501
  ```

- Run a single Streamlit page directly (useful during development)
  ```bash path=null start=null
  # ML Engagement page
  streamlit run "pages/3_🔮_ML_Prediction.py"
  
  # DL Sentiment page
  streamlit run "pages/4_🧠_DL_Prediction.py"
  
  # Dataset page
  streamlit run "pages/2_📊_Dataset.py"
  ```

- CLI utilities (require RAPIDAPI_KEY and populated SQLite DB)
  ```bash path=null start=null
  # Batch fetch tweets + comments for up to 1000 ranked users from SQLite
  python sync.py \
    --db-path data/xenty.db \
    --table x_cryptos \
    --tweet-count 20 \
    --comment-count 50 \
    --ranking-mode Relevance
  
  # Update account IDs for specific screen names (comma-separated)
  python update_twitter_account.py \
    --db-path data/xenty.db \
    --table x_cryptos \
    --accounts account1,account2
  ```

- Docker build and run
  ```bash path=null start=null
  # Build (uses requirements.docker.txt wheels stage)
  docker build -t xenty-dashboard .
  
  # Run with env file (see .env example below)
  docker run -p 8501:8501 --env-file .env xenty-dashboard
  ```

- Regenerate pinned requirements (project uses uv to pin from pyproject.toml)
  ```bash path=null start=null
  # Produces requirements.txt from pyproject.toml
  uv pip compile pyproject.toml -o requirements.txt
  ```

Environment and secrets
- Required environment variables
  - KAGGLE_USERNAME and KAGGLE_KEY for dataset download via Kaggle API (used to create ~/.kaggle/kaggle.json at runtime)
  - RAPIDAPI_KEY for Twitter241 RapidAPI access used by utils/twitter.py
- Recommended .env file at repository root (auto-loaded by utils/env_loader):
  ```bash path=null start=null
  KAGGLE_USERNAME=your_kaggle_username
  KAGGLE_KEY=your_kaggle_api_key
  RAPIDAPI_KEY=your_rapidapi_key
  ```
  Do not print or echo these values in the terminal. They will be read by the app and utilities.

Data and models prerequisites
- SQLite database: data/xenty.db
  - Dataset page (pages/2_📊_Dataset.py) reads from SQLite by default (DataLoader DEFAULT_DATA_SOURCE="sqlite").
  - sync.py and ML/DL pages rely on this DB for user/tweet storage (table: x_cryptos).
- Kaggle dataset (alternative source via KaggleHub): constants/config.py specifies
  - DATASET_KAGGLE_SOURCE = "mc3labs/crypto-twitter-dataset-5k-accounts-csv"
  - DATASET_NAME = "Cryptos_Projects.csv"
  If the CSV isn’t cached in data/, Kaggle credentials are required; the file will be downloaded and cached.
- ML engagement model assets (present in repo):
  - models/engagement_kmeans/scaler.joblib
  - models/engagement_kmeans/kmeans.joblib
  - models/engagement_kmeans/cluster_means.csv
- DL sentiment model (local file expected by pages/4_🧠_DL_Prediction.py):
  - data/best_model_bertweet.h5

High-level architecture and flows
- Streamlit UI (multi-page)
  - Xenty.py: redirects to pages/1_🏠_Home.py.
  - Home: simple overview and static visuals (viz/ML.png, viz/DL.png).
  - Dataset page (pages/2_📊_Dataset.py):
    - Loads dataset via utils/data_loader.DataLoader.
    - Defaults to SQLite: SELECT * FROM x_cryptos ORDER BY market_cap_rank.
    - Computes a derived training summary via utils/pipeline.get_dl_training_data, which filters raw posts, converts string counts to ints, and computes reply totals.
    - Provides interactive previews, filtering, statistics, and CSV download via Plotly/Streamlit.
  - ML Engagement page (pages/3_🔮_ML_Prediction.py):
    - Fetches tweets/comments on demand using utils/twitter.TwitterScraper (RapidAPI-based), persists posts JSON to SQLite (x_cryptos.posts), and reuses cached data if <24h.
    - Filters invalid tweets (retweets, zero-view anomalies) via utils/pipeline.filter_valid_tweets.
    - Computes features (likes/retweets/replies normalized by views) and predicts a cluster with utils/pipeline.EngagementKMeansPredictor using joblib scaler/kmeans.
    - Maps cluster to labels/descriptions in utils/clusters.engagement_clusters_4 and displays cluster means from models/engagement_kmeans/cluster_means.csv.
  - DL Sentiment page (pages/4_🧠_DL_Prediction.py):
    - Loads a local Keras model based on "vinai/bertweet-base" tokenizer (utils/distilbert_sentiment.XentySentimentAnalyzer).
    - Preprocesses crypto-specific text (normalizes domain terms), predicts bullish/bearish with confidences, and renders distribution and annotated comments.
  - Notebook viewer (pages/3_📔_Notebooks.py):
    - Renders .ipynb files from notebooks/ using nbconvert to HTML (utils/notebook_display.display_notebook).

- Data ingestion and storage
  - Kaggle dataset path resolution and caching via utils/data_loader; credentials are ensured/created by utils/kaggle_auth (writes ~/.kaggle/kaggle.json from env/secrets).
  - Twitter ingestion via utils/twitter.TwitterScraper using RAPIDAPI_KEY; rate-limited; writes user metadata and posts JSON into SQLite (x_cryptos table). Upserts on screen_name with conflict handling.

- Configuration & environment
  - utils/env_loader auto-loads .env at import time; secrets are never printed (sensitive keys masked in debugging helper).
  - .streamlit/config.toml disables usage stats.
  - Python version pins to 3.10.14 via .python-version and .tool-versions.

- CI/CD
  - .github/workflows/docker-publish.yml builds and pushes ghcr.io/${{ github.repository }}:latest (linux/arm64) on main pushes and manual dispatch, then deploys over SSH to a VPS.
  - Deployment script pulls image, stops/removes container "xenty" if present, and runs with:
    - --env-file $HOME/xenty/.env
    - --network caddy_proxy
    - -v $HOME/xenty/data:/app/data

Notes for development in this repo
- Tests and linting: no test suite or linter config is present in the repository at this time.
- Ports: Streamlit uses 8501 by default; adjust mapping if the port is occupied.
- Running specific Streamlit pages directly is handy during iteration; for full navigation, use Xenty.py.
- The ML engagement flow requires both a valid RAPIDAPI_KEY and an existing x_cryptos table in data/xenty.db (see sync.py for bulk population).

Referenced project docs
- README.md: contains quick start, Docker commands, environment variable setup, and a project overview.

AI assistant rules and external agent files
- No CLAUDE.md, Cursor rules, or Copilot instruction files were found in this repository.

