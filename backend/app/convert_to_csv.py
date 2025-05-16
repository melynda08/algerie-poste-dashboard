import pandas as pd

# Set path to your input TXT file and desired output CSV
input_path = "/home/melynda/algerie_post_ai/data/raw/sample.txt"
output_path = "/home/melynda/algerie_post_ai/data/processed/sample.csv"

# Read the file with proper delimiter and encoding
df = pd.read_csv(input_path, sep=";", encoding="utf-8", dtype=str)

# Save to CSV (you can keep utf-8 or use utf-8-sig for Excel compatibility)
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("✅ Conversion complete: saved to", output_path)
