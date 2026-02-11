"""
Bot handle generation utility.

Implements the clean_name logic from Zapier Step 20.
"""

import re


def generate_bot_handle(company_name: str) -> str:
    """
    Generate a clean bot handle from company name.

    Logic from Zapier Step 20:
    - Convert to lowercase
    - Remove all characters except lowercase letters, numbers, and hyphens
    - Append '-ai-agent-demo'

    Args:
        company_name: Raw company name (e.g., "Pepsi", "Acme Corp!")

    Returns:
        Clean bot handle (e.g., "pepsi-ai-agent-demo", "acmecorp-ai-agent-demo")
    """
    # Convert to lowercase
    clean_name = company_name.lower()

    # Keep only lowercase letters, numbers, and hyphens
    clean_name = re.sub(r'[^a-z0-9-]', '', clean_name)

    # Append suffix
    clean_name = clean_name + '-ai-agent-demo'

    return clean_name


# Test with Pepsi
if __name__ == "__main__":
    test_names = [
        "Pepsi",
        "Acme Corp!",
        "Tesla Inc.",
        "Amazon.com",
        "Coca-Cola"
    ]

    for name in test_names:
        handle = generate_bot_handle(name)
        print(f"{name:20s} → {handle}")
