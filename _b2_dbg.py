with open('_build_batch2.py', 'rb') as f:
    data = f.read()
lines = data.split(b'\n')
# Show lines 60-66 as hex to find problematic quote chars
for i in range(60, 67):
    if i < len(lines):
        line = lines[i]
        print(f"--- line {i+1} len={len(line)} ---")
        # Show as repr for clarity
        try:
            print(line.decode('utf-8'))
        except UnicodeDecodeError:
            print("decode failed:", line[:80])
        print()
