import geopandas as gpd

SHAPEFILE_PATH = "backend/data/RecreationalRoutes.shp"


def inspect_shapefile():
    """
    Load the recreational routes shapefile and print basic info.
    This script is read-only and does NOT modify any data.
    """
    print("Loading shapefile...")
    gdf = gpd.read_file(SHAPEFILE_PATH)

    print("\n✅ Shapefile loaded successfully")
    print(f"Number of trails: {len(gdf)}")

    print("\nColumns available:")
    for col in gdf.columns:
        print(f" - {col}")

    print("\nFirst 5 rows:")
    print(gdf.head())


if __name__ == "__main__":
    inspect_shapefile()
