# Xenty Dashboard 📊

**Xenty Dashboard** is a comprehensive web application that analyzes cryptocurrency projects' engagement and sentiment on Twitter/X using machine learning and deep learning models.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Kaggle](https://img.shields.io/badge/Kaggle-20BEFF?style=for-the-badge&logo=kaggle&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)

## 🚀 Features

- **📊 Dataset Management**: Integration with Kaggle datasets for crypto Twitter data
- **🔮 ML Prediction**: KMeans clustering for engagement analysis with real-time Twitter data
- **🧠 DL Prediction**: Deep learning models for advanced sentiment analysis
- **📔 Notebook Integration**: View and interact with Jupyter notebooks
- **🏠 Interactive Dashboard**: User-friendly Streamlit interface
- **🐳 Docker Support**: Containerized deployment ready
- **🔐 Secure Authentication**: Kaggle API integration with environment-based credentials

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.11+
- **Machine Learning**: Scikit-learn, TensorFlow
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib, Seaborn
- **Data Source**: Kaggle API, Twitter/X data
- **Deployment**: Docker

## 📋 Prerequisites

- Python 3.11 or higher
- Docker (optional, for containerized deployment)
- Kaggle account and API credentials
- Git

## 🚀 Quick Start

### Option 1: Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cedric-alyra/xenty.git
   cd xenty
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   KAGGLE_USERNAME=your_kaggle_username
   KAGGLE_KEY=your_kaggle_api_key
   ```

5. **Run the application**
   ```bash
   streamlit run Xenty.py
   ```

### Option 2: Docker Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/cedric-alyra/xenty.git
   cd xenty
   ```

2. **Build the Docker image**
   ```bash
   docker build -t xenty-dashboard .
   ```

3. **Run with environment file**
   ```bash
   docker run -p 8501:8501 --env-file .env xenty-dashboard
   ```

   Or with inline environment variables:
   ```bash
   docker run -p 8501:8501 \
     -e KAGGLE_USERNAME=your_username \
     -e KAGGLE_KEY=your_api_key \
     xenty-dashboard
   ```

4. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

## 🏗️ Project Structure

```
xenty/
├── 📁 .devcontainer/          # Development container configuration
├── 📁 .github/                # GitHub workflows
├── 📁 .streamlit/             # Streamlit configuration
├── 📁 constants/              # Application constants
├── 📁 data/                   # Data storage
├── 📁 models/                 # Pre-trained ML models
│   └── 📁 engagement_kmeans/  # KMeans clustering model
├── 📁 notebooks/              # Jupyter notebooks
├── 📁 pages/                  # Streamlit pages
│   ├── 1_🏠_Home.py          # Home page
│   ├── 2_📊_Dataset.py       # Dataset management
│   ├── 3_📔_Notebooks.py     # Notebook viewer
│   ├── 3_🔮_ML_Prediction.py # ML predictions
│   └── 4_🧠_DL_Prediction.py # DL predictions
├── 📁 utils/                  # Utility modules
│   ├── clusters.py           # Clustering utilities
│   ├── env_loader.py         # Environment loading
│   ├── kaggle_auth.py        # Kaggle authentication
│   ├── pipeline.py           # ML pipeline
│   └── twitter.py            # Twitter data fetching
├── 📁 viz/                    # Visualization utilities
├── Dockerfile                 # Docker configuration
├── Xenty.py                  # Main application entry
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

The application requires the following environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `KAGGLE_USERNAME` | Your Kaggle username | Yes |
| `KAGGLE_KEY` | Your Kaggle API key | Yes |

### Kaggle API Setup

1. Go to [Kaggle Account Settings](https://www.kaggle.com/account)
2. Scroll to the "API" section
3. Click "Create New API Token"
4. Download the `kaggle.json` file
5. Extract the username and key from the JSON file
6. Set them as environment variables

## 📊 Features Deep Dive

### ML Prediction Engine

- **KMeans Clustering**: Analyzes Twitter engagement patterns
- **Feature Engineering**: Calculates engagement ratios (likes/views, retweets/views, replies/views)
- **Real-time Analysis**: Processes live Twitter data
- **Visual Analytics**: Interactive charts and metrics
- **Export Capabilities**: Download analysis results as CSV

### Data Processing Pipeline

- **Data Filtering**: Removes retweets and invalid metrics
- **Type Conversion**: Handles string-to-integer conversion from Twitter API
- **Error Handling**: Robust error management for data inconsistencies
- **Caching**: Streamlit caching for improved performance

### Visualization

- **Interactive Charts**: Plotly-based visualizations
- **Engagement Metrics**: Comprehensive dashboard with KPIs
- **Cluster Distribution**: Pie charts and scatter plots
- **Tweet Analysis**: Individual tweet cards with cluster assignments

## 🐛 Troubleshooting

### Common Issues

1. **CacheReplayClosureError**: Ensure UI elements are separated from cached functions
2. **NoSessionContext**: Use `st.toast()` instead of threading for notifications
3. **String vs Integer Errors**: Twitter API returns metrics as strings - conversion is handled automatically
4. **Environment Variables**: Ensure `.env` file is properly loaded or environment variables are set

### Docker Issues

- **Port Conflicts**: Use different port mapping if 8501 is occupied
- **Environment Variables**: Ensure proper mounting of `.env` file or inline variables
- **Health Checks**: Remove problematic HEALTHCHECK if encountering 404 errors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **GitHub**: [https://github.com/cedric-alyra/xenty](https://github.com/cedric-alyra/xenty)
- **Kaggle Competition**: [https://www.kaggle.com/competitions/xenty](https://www.kaggle.com/competitions/xenty)
- **Dataset**: [Crypto Twitter Dataset](https://www.kaggle.com/datasets/mc3labs/crypto-twitter-dataset-5k-accounts-csv)

## 👥 Authors

- **Cédric** - *Initial work* - [cedric-alyra](https://github.com/cedric-alyra)

## 🙏 Acknowledgments

- Streamlit team for the amazing framework
- Kaggle for providing the dataset platform
- The open-source community for the wonderful libraries

---

**Made with ❤️ for crypto analytics**
