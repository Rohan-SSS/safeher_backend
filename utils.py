from math import radians, sin, cos, sqrt, atan2


def distance(lat1, lon1, lat2, lon2):
    # Calculate the Haversine distance between two points on the earth
    R = 6371.0  # radius of the Earth in kilometers

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def group_points(points, threshold=0.2):  # Reduced threshold
    groups = []

    for point in points:
        added_to_group = False
        for group in groups:
            center = group["center"]
            if (
                distance(
                    point["latitude"],
                    point["longitude"],
                    center["latitude"],
                    center["longitude"],
                )
                <= threshold
            ):
                group["points"].append(point)
                group["center"]["latitude"] = sum(
                    p["latitude"] for p in group["points"]
                ) / len(group["points"])
                group["center"]["longitude"] = sum(
                    p["longitude"] for p in group["points"]
                ) / len(group["points"])
                added_to_group = True
                break

        if not added_to_group:
            groups.append({"center": point.copy(), "points": [point]})

    return [
        {"center": group["center"], "radius": min(2 * len(group["points"]), 40)}
        for group in groups
    ]


points = [
    {"latitude": 28.797355, "longitude": 77.53686},
    {"latitude": 28.795077, "longitude": 77.54062},
    {"latitude": 28.796864, "longitude": 77.53910},
    {"latitude": 28.798355, "longitude": 77.53786},
    {"latitude": 28.794077, "longitude": 77.54162},
    {"latitude": 28.797864, "longitude": 77.53810},
    {"latitude": 28.796258, "longitude": 77.54236},
    {"latitude": 28.798915, "longitude": 77.54134},
    {"latitude": 28.797255, "longitude": 77.53676},
    {"latitude": 28.794977, "longitude": 77.54052},
    {"latitude": 28.796764, "longitude": 77.53900},
    {"latitude": 28.795198, "longitude": 77.54126},
    {"latitude": 28.797815, "longitude": 77.54024},
    {"latitude": 28.798455, "longitude": 77.53796},
    {"latitude": 28.794177, "longitude": 77.54172},
    {"latitude": 28.797964, "longitude": 77.53820},
    {"latitude": 28.796358, "longitude": 77.54246},
    {"latitude": 28.799015, "longitude": 77.54144}
    # ... add more points as needed
]

print(group_points(points))
