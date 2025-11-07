"""
IRT Reports Module
==================
Report generation for IRT drift monitoring and calibration analysis.

Available reports:
- Monthly drift report (drift_monthly.py)
"""
from .drift_monthly import generate_monthly_report

__all__ = ["generate_monthly_report"]
