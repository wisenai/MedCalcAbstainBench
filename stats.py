from typing import List, Tuple, Dict, Optional
import pandas as pd
from scipy.stats import binomtest
from statsmodels.stats.proportion import proportion_confint
from google.colab import userdata

# Fetch OpenRouter API key strictly from Colab Secrets if required
try:
    api_key = userdata.get('OPENROUTER_API_KEY')
except Exception:
    api_key = None


class MedCalcStatsReferee:
    def __init__(self, alpha: float = 0.05, mcnemar_alpha: float = 0.01):
        """
        General statistical utility for calculating proportion confidence intervals,
        hypothesis testing, and generating summary tables for clinical evaluation benchmarks.
        :param alpha: Alpha significance level for confidence intervals (default 0.05 for 95% CI).
        :param mcnemar_alpha: Alpha significance level for exact paired McNemar test (default 0.01).
        """
        self.alpha = alpha
        self.mcnemar_alpha = mcnemar_alpha

    def wilson_ci(self, count: int, total: int) -> Tuple[float, Tuple[float, float]]:
        """
        Calculates the Wilson Score Interval for a proportion.
        Returns: (p_hat, (lower_bound, upper_bound)) as raw floats bounded between 0.0 and 1.0.
        """
        if total == 0:
            return 0.0, (0.0, 0.0)
            
        p_hat = count / total
        lower, upper = proportion_confint(
            count, total, alpha=self.alpha, method='wilson'
        )
        return p_hat, (max(0.0, lower), min(1.0, upper))

    def format_wilson_ci(self, count: int, total: int) -> str:
        """
        Formats a proportion and its Wilson Score Interval as a standard string:
        Count/Total (Percentage% [Lower% - Upper%])
        """
        if total == 0:
            return "0/0 (0.0% [0.0% - 0.0%])"
            
        p_hat, (lower, upper) = self.wilson_ci(count, total)
        return f"{count}/{total} ({p_hat * 100:.1f}% [{lower * 100:.1f}% - {upper * 100:.1f}%])"

    def mcnemar_exact_test(
        self, 
        labels_condition_a: List[str], 
        labels_condition_b: List[str], 
        target_category: str = "flagged"
    ) -> Tuple[float, bool]:
        """
        Performs a two-sided Paired McNemar's Exact Test to compare categorical shifts
        between paired observations.
        Returns: (p_value, is_statistically_significant)
        """
        if len(labels_condition_a) != len(labels_condition_b):
            raise ValueError("Conditions must have paired data of the exact same length.")

        b = sum(1 for a, b_ in zip(labels_condition_a, labels_condition_b) if a == target_category and b_ != target_category)
        c = sum(1 for a, b_ in zip(labels_condition_a, labels_condition_b) if a != target_category and b_ == target_category)

        if b + c == 0:
            return 1.0, False

        test_result = binomtest(k=min(b, c), n=b + c, p=0.5, alternative='two-sided')
        p_value = float(test_result.pvalue)
        return p_value, p_value < self.mcnemar_alpha

    def generate_paper_table(self, df_results: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates raw result DataFrames into a formatted summary table.
        Expected DataFrame columns: ['model', 'variant', 'assigned_label', 'value_correct']
        """
        models = df_results['model'].unique()
        variants = df_results['variant'].unique()
        table_rows = []
        
        for model in models:
            row_data = {"Model": model}
            df_model = df_results[df_results['model'] == model]
            
            for variant in variants:
                df_variant = df_model[df_model['variant'] == variant]
                total = len(df_variant)
                
                flagged_count = len(df_variant[df_variant['assigned_label'] == 'flagged'])
                row_data[f"{variant} - Refusal Rate"] = self.format_wilson_ci(flagged_count, total)
                
                if 'value_correct' in df_variant.columns:
                    correct_count = len(df_variant[df_variant['value_correct'] == True])
                    row_data[f"{variant} - Accuracy"] = self.format_wilson_ci(correct_count, total)
                    
            table_rows.append(row_data)
            
        return pd.DataFrame(table_rows)
