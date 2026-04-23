import os
import re

for root, dirs, files in os.walk('.'):
    # Skip build artifacts and dependencies
    if any(skip in root for skip in ['node_modules', '.next', '__tests__']):
        continue
    for f in files:
        if f.endswith(('.tsx', '.ts', '.jsx', '.js')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            # Add type="button" to <button tags that don't already have a type attribute.
            # Handle <button followed by whitespace or >.
            new_content = re.sub(r'<button(?=\s|>)', '<button type="button"', content)
            # Fix any double-added type attributes
            new_content = re.sub(r'<button type="button" type=', '<button type=', new_content)
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(new_content)
                print(f'Updated {path}')
