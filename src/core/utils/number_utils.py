from __future__ import annotations
import decimal

def format_indian_number(number: float | int | str, include_symbol: bool = False, decimals: int = 2) -> str:
    """
    Formats a number into Indian currency format (Lakhs and Crores).
    Example: 1234567.89 -> 12,34,567.89
    """
    try:
        if number is None:
            return "0.00"
            
        if isinstance(number, str):
            # Remove any existing commas or symbols
            number = number.replace(',', '').replace('₹', '').replace(' ', '').strip()
            if not number:
                return "0.00"
        
        num = float(number)
        is_negative = num < 0
        num = abs(num)
        
        # Format decimal part
        d_format = "{:." + str(decimals) + "f}"
        s = d_format.format(num)
        parts = s.split(".")
        int_part = parts[0]
        dec_part = parts[1] if len(parts) > 1 else ""
        
        # Indian formatting logic
        res = ""
        l = len(int_part)
        if l <= 3:
            res = int_part
        else:
            # Last 3 digits
            res = int_part[-3:]
            # Remaining digits in groups of 2
            remaining = int_part[:-3]
            while len(remaining) > 2:
                res = remaining[-2:] + "," + res
                remaining = remaining[:-2]
            if remaining:
                res = remaining + "," + res
        
        formatted = res
        if decimals > 0:
            formatted += "." + dec_part
        
        if is_negative:
            formatted = "-" + formatted
            
        if include_symbol:
            formatted = "₹ " + formatted
            
        return formatted
    except (ValueError, TypeError):
        return str(number)

def format_crore(val_in_lakhs: float, include_symbol: bool = True) -> str:
    """Formats Lacs to Crores as per bank standards with Indian digit grouping."""
    val_cr = val_in_lakhs / 100
    formatted = format_indian_number(val_cr, include_symbol=include_symbol)
    return f"{formatted} Cr"

def format_indian_currency(val: float, suffix: str = "") -> str:
    formatted = format_indian_number(val, include_symbol=True)
    if suffix:
        formatted = f"{formatted} {suffix}"
    return formatted

def format_campaign_target(value: float, metric: str) -> str:
    """Format target value dynamically based on unit size and metric type."""
    try:
        val = float(value)
    except:
        return str(value)
        
    currency_metrics = ["CASA", "GOLD", "RETAIL", "MSME", "AGRI", "JEWEL LOAN", "INSURANCE", "MUTUAL FUNDS"]
    if metric.upper() in currency_metrics:
        if val >= 10000000: # 1 Crore
            return f"₹ {format_indian_number(val / 10000000, decimals=2)} Cr"
        elif val >= 100000: # 1 Lakh
            return f"₹ {format_indian_number(val / 100000, decimals=2)} Lakhs"
        elif val >= 1000: # 1 Thousand
            return f"₹ {format_indian_number(val / 1000, decimals=2)} K"
        else:
            return f"₹ {format_indian_number(val, decimals=2)}"
    else:
        if val >= 1000000:
            return f"{format_indian_number(val / 1000000, decimals=1)}M Units"
        elif val >= 1000:
            return f"{format_indian_number(val / 1000, decimals=1)}K Units"
        else:
            return f"{format_indian_number(val, decimals=0)} Units"
