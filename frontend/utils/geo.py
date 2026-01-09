import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def geometry_centroid(geometry):
    """
    Supports LineString and MultiLineString GeoJSON
    """
    coords = []

    if geometry["type"] == "LineString":
        coords = geometry["coordinates"]

    elif geometry["type"] == "MultiLineString":
        for line in geometry["coordinates"]:
            coords.extend(line)

    if not coords:
        return None

    lon = sum(c[0] for c in coords) / len(coords)
    lat = sum(c[1] for c in coords) / len(coords)

    return lat, lon
