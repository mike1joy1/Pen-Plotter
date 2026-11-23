
import Rhino.Geometry as rg
import random
import math

Curves = []
Order = []
Directions = []
Distance = 0.0

if C is None or len(C) == 0:
    pass

else:
    curves = list(C)
    n = len(curves)

    # Check curves
    if any(crv is None or not crv.IsValid for crv in curves):
        raise ValueError("Input contains an invalid curve.")

    # Extract endpoints as XYZ tuples
    starts = []
    ends = []

    for crv in curves:
        p0 = crv.PointAtStart
        p1 = crv.PointAtEnd

        starts.append((p0.X, p0.Y, p0.Z))
        ends.append((p1.X, p1.Y, p1.Z))

    # Optional starting position
    start_position = None

    if S is not None:
        start_position = (S.X, S.Y, S.Z)

    # Default iteration count
    iterations = 1000 if I is None else max(0, int(I))

    # Random generator
    rng = random.Random(42)


    # ========================================================
    # 2. DISTANCE FUNCTION
    # ========================================================

    def dist(a, b):
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        dz = a[2] - b[2]

        return math.sqrt(dx*dx + dy*dy + dz*dz)


    # ========================================================
    # 3. GET CURVE ENTRY AND EXIT POINTS
    # ========================================================

    def entry(i, reverse):
        return ends[i] if reverse else starts[i]

    def exit(i, reverse):
        return starts[i] if reverse else ends[i]


    # ========================================================
    # 4. CALCULATE TOTAL TRAVEL DISTANCE
    # ========================================================

    def route_distance(route, directions):

        if not route:
            return 0.0

        total = 0.0

        # Travel from initial pen position
        if start_position is not None:
            total += dist(
                start_position,
                entry(route[0], directions[0])
            )

        # Travel between curves
        for i in range(len(route) - 1):

            total += dist(
                exit(route[i], directions[i]),
                entry(route[i+1], directions[i+1])
            )

        return total


    # ========================================================
    # 5. NEAREST NEIGHBOUR
    # ========================================================

    def nearest_neighbour(first, first_reverse):

        remaining = set(range(n))
        remaining.remove(first)

        route = [first]
        directions = [first_reverse]

        current_end = exit(first, first_reverse)

        while remaining:

            best_index = None
            best_reverse = False
            best_distance = float("inf")

            for j in remaining:

                # Original direction
                d = dist(current_end, starts[j])

                if d < best_distance:
                    best_distance = d
                    best_index = j
                    best_reverse = False

                # Reversed direction
                if R:
                    d = dist(current_end, ends[j])

                    if d < best_distance:
                        best_distance = d
                        best_index = j
                        best_reverse = True

            route.append(best_index)
            directions.append(best_reverse)

            current_end = exit(best_index, best_reverse)
            remaining.remove(best_index)

        return route, directions


    # ========================================================
    # 6. GENERATE MULTIPLE INITIAL SOLUTIONS
    # ========================================================

    best_route = None
    best_directions = None
    best_distance = float("inf")

    for first in range(n):

        # Fixed direction
        if not R:
            orientations = [False]

        # Reversible direction
        else:
            orientations = [False, True]

        for first_reverse in orientations:

            route, directions = nearest_neighbour(
                first,
                first_reverse
            )

            d = route_distance(route, directions)

            if d < best_distance:
                best_distance = d
                best_route = route[:]
                best_directions = directions[:]


    # ========================================================
    # 7. LOCAL OPTIMISATION / SIMULATED ANNEALING
    # ========================================================

    route = best_route[:]
    directions = best_directions[:]

    current_distance = best_distance

    # Initial temperature based on average travel distance
    temperature = max(best_distance / max(n, 1), 0.001)

    initial_temperature = temperature

    for iteration in range(iterations):

        if n < 2:
            break

        # Gradually reduce temperature
        progress = float(iteration) / max(iterations, 1)

        temperature = initial_temperature * (0.01 ** progress)

        new_route = route[:]
        new_directions = directions[:]

        move = rng.random()

        # ----------------------------------------------------
        # MOVE 1: SWAP TWO CURVES
        # ----------------------------------------------------

        if move < 0.40:

            i, j = rng.sample(range(n), 2)

            new_route[i], new_route[j] = (
                new_route[j], new_route[i]
            )

            new_directions[i], new_directions[j] = (
                new_directions[j], new_directions[i]
            )

        # ----------------------------------------------------
        # MOVE 2: RELOCATE A CURVE
        # ----------------------------------------------------

        elif move < 0.80:

            i, j = rng.sample(range(n), 2)

            curve = new_route.pop(i)
            direction = new_directions.pop(i)

            new_route.insert(j, curve)
            new_directions.insert(j, direction)

        # ----------------------------------------------------
        # MOVE 3: REVERSE A CURVE
        # ----------------------------------------------------

        else:

            if R:
                i = rng.randrange(n)
                new_directions[i] = not new_directions[i]

            else:
                continue

        # Evaluate new route
        new_distance = route_distance(
            new_route,
            new_directions
        )

        difference = new_distance - current_distance

        # Accept improvements, or occasionally accept worse moves
        if difference < 0:

            accept = True

        else:

            probability = math.exp(
                -difference / max(temperature, 0.000001)
            )

            accept = rng.random() < probability

        if accept:

            route = new_route
            directions = new_directions
            current_distance = new_distance

        # Record best solution
        if current_distance < best_distance:

            best_distance = current_distance
            best_route = route[:]
            best_directions = directions[:]


    # ========================================================
    # 8. OUTPUT
    # ========================================================

    Order = best_route
    Directions = best_directions
    Distance = best_distance

    # Duplicate original curves and reverse where necessary
    for i, index in enumerate(Order):

        crv = curves[index].DuplicateCurve()

        if Directions[i]:
            crv.Reverse()

        Curves.append(crv)
