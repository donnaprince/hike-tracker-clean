import geopandas as gpd

SHAPEFILE_PATH = "backend/data/RecreationalRoutes.shp"


def prepare_trails():
    print("Loading shapefile...")
    gdf = gpd.read_file(SHAPEFILE_PATH)

    print("Original CRS:", gdf.crs)

    # Reproject to WGS84 (lat/lon)
    print("Reprojecting to EPSG:4326...")
    gdf = gdf.to_crs(epsg=4326)

    print("Reprojected CRS:", gdf.crs)

    # Keep only fields we care about
    trails = gdf[[
        "ROUTENAME",
        "ROUTETYPE",
        "ROUTECAT",
        "SEGLNGTH",
        "TRAILDES",
        "geometry"
    ]]

    print("\nPrepared trail preview:")
    print(trails.head())

    print("\nSample GeoJSON geometry:")
    print(trails.iloc[0].geometry.__geo_interface__)


if __name__ == "__main__":
    prepare_trails()
