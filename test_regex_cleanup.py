import pdfplumber
import re

def parse_number(s):
    # Remove commas and convert to float
    s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None

def corregir_linea_presupuesto(line):
    # We look for lines containing RRCITA
    if "RRCITA|" not in line:
        return line

    # Split the line by spaces
    tokens = line.split()
    if len(tokens) < 5:
        return line

    # Find the last few numeric tokens
    # Typically: quantity, unit_price, days, total (e.g. 5 tokens or 4 tokens at the end)
    # Let's collect tokens from the end that look like numbers
    num_indices = []
    for idx in range(len(tokens) - 1, -1, -1):
        val = parse_number(tokens[idx])
        if val is not None or tokens[idx] in [".00", ".0"]:
            num_indices.append(idx)
        else:
            break
            
    num_indices.reverse()
    if len(num_indices) < 3:
        return line

    # Let's extract the numeric tokens
    num_tokens = [tokens[i] for i in num_indices]
    prefix_tokens = tokens[:num_indices[0]]

    # Let's try to find a combination of merging adjacent numeric tokens that satisfies:
    # A * B * C = D  (where D is the last token)
    # Usually: num_tokens has 5 or 6 items because of splits.
    # We want to combine them into 4 items: [quantity, unit_price, days, total]
    # or 3 items: [quantity, unit_price, total] (if days is missing, assume days=1.0)
    
    total_val = parse_number(num_tokens[-1])
    if total_val is None or total_val == 0:
        return line

    # Let's try to merge adjacent tokens to form a valid 4-tuple: (qty, pu, days, total)
    # where qty * pu * days = total (approximately)
    # We can do this by trying all ways to partition the num_tokens list into 4 groups.
    # Since num_tokens has small size (usually 4 to 8), we can partition it.
    n = len(num_tokens)
    
    def try_partition_4(parts):
        # parts is a list of 4 lists of tokens
        # Merge tokens in each part
        merged = []
        for p in parts:
            if not p:
                return None
            # Combine them: if one is integer and next starts with dot (like "4" and ".00"), combine as "4.00"
            # otherwise just join them or concatenate them
            val_str = ""
            for t in p:
                if val_str and (t.startswith(".") or t.isdigit() or t.startswith("0")):
                    val_str += t
                else:
                    val_str += t
            val = parse_number(val_str)
            if val is None:
                return None
            merged.append(val)
        
        qty, pu, days, tot = merged
        if abs(qty * pu * days - total_val) < 1.0 or abs(qty * pu - total_val) < 1.0:
            return merged
        return None

    # Helper to generate all partitions of list into k non-empty contiguous sublists
    def get_partitions(lst, k):
        if k == 1:
            yield [lst]
            return
        for i in range(1, len(lst) - k + 2):
            for p in get_partitions(lst[i:], k - 1):
                yield [lst[:i]] + p

    for partition in get_partitions(num_tokens, 4):
        # Merge each group
        merged_vals = []
        valid = True
        for part in partition:
            # Join the tokens in the partition group
            # E.g. ["5", "00.00"] -> "500.00"
            # E.g. ["1", "26.00"] -> "126.00"
            combined = "".join(part)
            val = parse_number(combined)
            if val is None:
                valid = False
                break
            merged_vals.append((combined, val))
        
        if not valid:
            continue
            
        qty_str, qty_val = merged_vals[0]
        pu_str, pu_val = merged_vals[1]
        days_str, days_val = merged_vals[2]
        tot_str, tot_val = merged_vals[3]
        
        # Check if qty * pu * days = tot
        if abs(qty_val * pu_val * days_val - total_val) < 1.0:
            # Reconstruct the line
            new_line = " ".join(prefix_tokens) + f" {qty_str} {pu_str} {days_str} {tot_str}"
            return new_line

    return line

def test_cleanup():
    pdf_path = r"d:\vps-program-proyects\control_soldadura\HABILITADO_TECHO_DINO_ALMACEN_NUEVO_DINO_TECHO.pdf"
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    if "RRCITA" in line:
                        cleaned = corregir_linea_presupuesto(line)
                        if cleaned != line:
                            print(f"ORIGINAL: {line}")
                            print(f"CLEANED : {cleaned}\n")

if __name__ == "__main__":
    test_cleanup()
