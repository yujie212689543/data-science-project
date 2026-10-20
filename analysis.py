"""Compare the risk and return of four stocks with the S&P 500.

Input: stock_prices.csv with a Date column and one adjusted-close column per
asset.
Outputs: three portfolio-ready figures and a summary metrics table.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter


ROOT = Path(__file__).resolve().parent
PRICE_FILE = ROOT / "stock_prices.csv"
FIGURE_DIR = ROOT / "figures"
OUTPUT_DIR = ROOT / "outputs"
TRADING_DAYS = 252

ASSET_LABELS = {
    "MSFT": "Microsoft",
    "IBM": "IBM",
    "SBUX": "Starbucks",
    "AAPL": "Apple",
    "GSPC": "S&P 500",
}
COLORS = {
    "MSFT": "#2A9D8F",
    "IBM": "#E76F51",
    "SBUX": "#7B61A8",
    "AAPL": "#F4A261",
    "GSPC": "#243447",
}


def load_prices(path: Path) -> pd.DataFrame:
    """Load and validate the price table."""
    prices = pd.read_csv(path, parse_dates=["Date"], index_col="Date").sort_index()
    prices.columns = [column.strip().upper() for column in prices.columns]

    if prices.empty:
        raise ValueError("The price table is empty.")
    if prices.index.has_duplicates:
        raise ValueError("The price table contains duplicate dates.")
    if prices.isna().any().any():
        raise ValueError("The price table contains missing values.")
    if (prices <= 0).any().any():
        raise ValueError("Adjusted prices must be strictly positive.")
    missing = set(ASSET_LABELS) - set(prices.columns)
    if missing:
        raise ValueError(f"Missing price columns: {sorted(missing)}")

    return prices[list(ASSET_LABELS)]


def calculate_metrics(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return daily returns and a table of risk/return metrics."""
    returns = prices.pct_change(fill_method=None).dropna()
    years = len(returns) / TRADING_DAYS

    wealth = prices / prices.iloc[0]
    annual_return = wealth.iloc[-1] ** (1 / years) - 1
    annual_volatility = returns.std(ddof=1) * np.sqrt(TRADING_DAYS)
    sharpe_zero_rate = returns.mean() / returns.std(ddof=1) * np.sqrt(TRADING_DAYS)
    drawdowns = prices / prices.cummax() - 1

    metrics = pd.DataFrame(
        {
            "annual_return": annual_return,
            "annual_volatility": annual_volatility,
            "sharpe_ratio_rf_0": sharpe_zero_rate,
            "max_drawdown": drawdowns.min(),
            "total_return": wealth.iloc[-1] - 1,
        }
    )
    metrics.index = [ASSET_LABELS[ticker] for ticker in metrics.index]
    return returns, metrics


def style_axis(ax: plt.Axes) -> None:
    """Apply a consistent, low-ink chart style."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#A8B3C2")
    ax.tick_params(colors="#4C596A", labelsize=10)
    ax.grid(axis="y", color="#DCE3EA", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)


def plot_cumulative_growth(prices: pd.DataFrame) -> None:
    growth = prices / prices.iloc[0] * 100
    fig, ax = plt.subplots(figsize=(12, 6.6))

    for ticker in prices:
        linewidth = 2.8 if ticker == "GSPC" else 2.0
        zorder = 5 if ticker == "GSPC" else 3
        ax.plot(
            growth.index,
            growth[ticker],
            color=COLORS[ticker],
            linewidth=linewidth,
            label=ASSET_LABELS[ticker],
            zorder=zorder,
        )

    ax.set_title(
        "Cumulative growth of a $100 investment",
        loc="left",
        fontsize=18,
        fontweight="bold",
        color="#172033",
        pad=18,
    )
    ax.text(
        0,
        1.02,
        "Adjusted-close prices, 3 January 2007 to 1 March 2016",
        transform=ax.transAxes,
        fontsize=10.5,
        color="#5D6B7C",
    )
    ax.set_ylabel("Portfolio value (indexed to 100)")
    ax.legend(frameon=False, ncols=5, loc="upper left", bbox_to_anchor=(0, 0.95))
    style_axis(ax)
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "01_cumulative_growth.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_risk_return(metrics: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.2, 6.6))

    for ticker, row in metrics.iterrows():
        color = COLORS[next(key for key, value in ASSET_LABELS.items() if value == ticker)]
        marker = "*" if ticker == "S&P 500" else "o"
        size = 260 if ticker == "S&P 500" else 110
        ax.scatter(
            row["annual_volatility"],
            row["annual_return"],
            s=size,
            color=color,
            edgecolor="white",
            linewidth=1.1,
            marker=marker,
            zorder=4,
        )
        ax.annotate(
            ticker,
            (row["annual_volatility"], row["annual_return"]),
            xytext=(8, 6),
            textcoords="offset points",
            fontsize=10.5,
            color="#243447",
            fontweight="bold",
        )

    ax.axhline(0, color="#8996A6", linewidth=1, linestyle="--")
    ax.set_title(
        "Higher return came with sharply higher volatility",
        loc="left",
        fontsize=18,
        fontweight="bold",
        color="#172033",
        pad=18,
    )
    ax.text(
        0,
        1.02,
        "Annualised arithmetic return versus annualised daily-return volatility",
        transform=ax.transAxes,
        fontsize=10.5,
        color="#5D6B7C",
    )
    ax.set_xlabel("Annualised volatility")
    ax.set_ylabel("Annualised return")
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    style_axis(ax)
    ax.grid(axis="x", color="#DCE3EA", linewidth=0.8, alpha=0.8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "02_risk_return.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_drawdowns(prices: pd.DataFrame) -> None:
    drawdowns = prices / prices.cummax() - 1
    fig, ax = plt.subplots(figsize=(12, 6.2))

    for ticker in prices:
        linewidth = 2.8 if ticker == "GSPC" else 1.8
        alpha = 1 if ticker == "GSPC" else 0.82
        ax.plot(
            drawdowns.index,
            drawdowns[ticker],
            color=COLORS[ticker],
            linewidth=linewidth,
            alpha=alpha,
            label=ASSET_LABELS[ticker],
        )

    worst_date = drawdowns["GSPC"].idxmin()
    worst_value = drawdowns["GSPC"].min()
    ax.scatter(worst_date, worst_value, color=COLORS["GSPC"], s=75, zorder=5)
    ax.annotate(
        f"S&P 500 trough: {worst_value:.1%}",
        xy=(worst_date, worst_value),
        xytext=(-115, -28),
        textcoords="offset points",
        fontsize=10,
        color="#243447",
        arrowprops={"arrowstyle": "-", "color": "#66768A", "lw": 1},
    )

    ax.set_title(
        "The 2008 crisis dominated downside risk",
        loc="left",
        fontsize=18,
        fontweight="bold",
        color="#172033",
        pad=18,
    )
    ax.text(
        0,
        1.02,
        "Drawdown measures the decline from each asset's previous peak",
        transform=ax.transAxes,
        fontsize=10.5,
        color="#5D6B7C",
    )
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylabel("Drawdown from previous peak")
    ax.legend(frameon=False, ncols=5, loc="lower left")
    style_axis(ax)
    fig.autofmt_xdate(rotation=0, ha="center")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "03_drawdowns.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURE_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    prices = load_prices(PRICE_FILE)
    returns, metrics = calculate_metrics(prices)

    metrics.to_csv(OUTPUT_DIR / "summary_metrics.csv", float_format="%.6f")
    returns.to_csv(OUTPUT_DIR / "daily_returns.csv", float_format="%.6f")

    plot_cumulative_growth(prices)
    plot_risk_return(metrics)
    plot_drawdowns(prices)

    display = metrics.copy()
    for column in ["annual_return", "annual_volatility", "max_drawdown", "total_return"]:
        display[column] = display[column].map(lambda value: f"{value:.1%}")
    display["sharpe_ratio_rf_0"] = display["sharpe_ratio_rf_0"].map(
        lambda value: f"{value:.2f}"
    )
    print(display.to_string())
    print("\nCorrelation of daily returns:")
    print(returns.corr().round(3).to_string())


if __name__ == "__main__":
    main()
