import yaml
import json

# Read the YAML file
with open('schema.json', 'r', encoding='utf-8') as file:
    yaml_content = file.read()

# Parse YAML
data = yaml.safe_load(yaml_content)

# Write as JSON
with open('schema_fixed.json', 'w', encoding='utf-8') as file:
    json.dump(data, file, indent=2, ensure_ascii=False)

print("Conversion completed successfully!")
