"""
BMI Calculator Tool
-------------------

Purpose: Calculate BMI.

"""

import math

def calculate_bmi(height_cm: float, weight_kg: float, round_digits: int = 2) -> tuple:
    """
    Calculate BMI from height (cm) and weight (kg) and return a tuple (bmi, category).

    Args:
        height_cm: Height in centimeters (must be > 0).
        weight_kg: Weight in kilograms (must be > 0).
        round_digits: Number of decimal places to round the BMI to (>= 0).

    Returns:
        (rounded_bmi, category)

    Raises:
        ValueError: If inputs are invalid (non-numeric or non-positive).
    """
    try:
        height_cm = float(height_cm)
        weight_kg = float(weight_kg)
        round_digits = int(round_digits)
    except (TypeError, ValueError):
        raise ValueError("height_cm and weight_kg must be numeric and round_digits must be an integer")

    if height_cm <= 0:
        raise ValueError("height_cm must be greater than 0")
    if weight_kg <= 0:
        raise ValueError("weight_kg must be greater than 0")
    if round_digits < 0:
        raise ValueError("round_digits must be non-negative")

    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2)
    bmi_rounded = round(bmi, round_digits)

    # Use the module's categorize_bmi to determine category from the unrounded BMI
    category = categorize_bmi(bmi)

    return bmi_rounded, category

def categorize_bmi(bmi: float) -> str:
    """
    Categorize a BMI value using WHO ranges.

    Args:
        bmi: Body Mass Index (must be a positive finite number).

    Returns:
        A string category: "Underweight", "Normal weight", "Overweight",
        "Obesity (Class I)", "Obesity (Class II)", or "Obesity (Class III)".

    Raises:
        ValueError: If bmi is not a finite positive number.
    """

    try:
        bmi = float(bmi)
    except (TypeError, ValueError):
        raise ValueError("bmi must be a numeric value")

    if not math.isfinite(bmi) or bmi <= 0:
        raise ValueError("bmi must be a positive finite number")

    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal weight"
    if bmi < 30:
        return "Overweight"
    if bmi < 35:
        return "Obesity (Class I)"
    if bmi < 40:
        return "Obesity (Class II)"
    return "Obesity (Class III)"
    