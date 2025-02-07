from random import randint

def smooth_path(path, extend, collision, iterations=50):
    if path is None or len(path) == 0:
        print("Error: Received an empty or None path")
        return []  

    smoothed_path = list(path)  
    print("Initial smoothed_path:", smoothed_path)

    for _ in range(iterations):
        if len(smoothed_path) <= 2:
            print("Path is too short to smooth:", smoothed_path)
            return smoothed_path

        i = randint(0, len(smoothed_path) - 1)
        j = randint(0, len(smoothed_path) - 1)
        if abs(i - j) <= 1:
            continue
        if j < i:
            i, j = j, i

        try:
            shortcut = list(extend(smoothed_path[i], smoothed_path[j]))  
        except Exception as e:
            print(f"Error in extend function: {e}")
            continue  

        if (len(shortcut) < (j - i)) and all(not collision(q) for q in shortcut):
            smoothed_path = smoothed_path[:i + 1] + shortcut + smoothed_path[j + 1:]
            print("Smoothed path updated:", smoothed_path)

    return smoothed_path
