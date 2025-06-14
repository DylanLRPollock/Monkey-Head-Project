# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import seaborn as sns
import requests


class AIProcessor:
    """Simple processor used in examples and unit tests."""

    def process_data(self, data: str) -> str:
        """Return an upper-case version of ``data``.

        This method stands in for more complex AI processing in the
        production system. It simply converts the provided string to
        upper case so tests have deterministic output.
        """

        processed_data = data.upper()
        return processed_data

    def analyze_data(self, data: str) -> dict[str, int]:
        """Analyze ``data`` and return basic statistics.

        Currently the implementation only reports the length of the input
        string, but additional metrics may be added in the future.
        """

        analysis_result = {"length": len(data)}
        return analysis_result

    def compute_mean(self, numbers: list[float]) -> float:
        """Return the arithmetic mean of ``numbers`` using NumPy."""

        array = np.array(numbers, dtype=float)
        return float(np.mean(array))

    def dataframe_summary(self, data: list[dict]) -> pd.DataFrame:
        """Convert ``data`` to a DataFrame and return ``describe()`` result."""

        df = pd.DataFrame(data)
        return df.describe()

    def train_linear_model(self, X: list[list[float]], y: list[float]) -> tuple:
        """Fit a simple linear regression model and return coefficients."""

        model = LinearRegression().fit(X, y)
        return (float(model.coef_[0]), float(model.intercept_))

    def plot_histogram(self, data: list[float], filename: str) -> str:
        """Plot ``data`` as a histogram using seaborn and save to ``filename``."""

        sns.histplot(data, kde=True)
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
        return filename

    def fetch_todo_title(self, todo_id: int) -> str:
        """Fetch a sample TODO item and return its title."""

        url = f"https://jsonplaceholder.typicode.com/todos/{todo_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()["title"]
