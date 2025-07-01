# GeoJson2Ugx

This repository contains a converter to transform GeoJSON-data into the unstructed grids for UG4-Simulator(https://github.com/UG4). To achieve this purpose, the coordinates and edges of the given GeoJSON-data should be firstly converted through bin/GeoJsonToUgx.py into a .ugx file. Then the .ugx file can be visualizied in ProMesh and the triangles can be filled through `Triangle Fill by known Boundary Subsets` under `Tool Browser/Scripts`, which is compiled by adding bin/`Triangle_Fill_by_BoundarySubsets.lua` into ProMesh .

## Introduction

### GeoJSON

GeoJSON is a JSON format for representing geographic data, supporting geometries such as points, lines, and polygons, as well as multiple types of these geometries. More information is available at https://de.wikipedia.org/wiki/GeoJSON. Additionally, all coordinates are based on the World Geodetic System 1984 (WGS84) https://de.wikipedia.org/wiki/World_Geodetic_System_1984.

##### Example:

{ "type": "FeatureCollection",
  "features":[
    { "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [ [100.0, 0.0], [101.0, 0.0], [101.0, 1.0],
            [100.0, 1.0], [100.0, 0.0] ]
        ]
      },
      "properties": {
        "prop0": "value0",
        "prop1": {"this": "that"}
      }
    }]}

However, determining the distance between two points on the Earth's surface using latitudes and longitudes is challenging, because Euclidean distance applies only to flat surfaces, whereas the Earth is an ellipsoid. Therefore, the WGS84 coordinate system must be converted to the Universal Transverse Mercator (UTM) system. More information is available at https://de.wikipedia.org/wiki/UTM-Koordinatensystem.

### UGX

The UGX format is based on the XML format (Extensible Markup Language), a markup language that supports the use of tags, elements, and attributes, more information is available at https://de.wikipedia.org/wiki/Extensible_Markup_Language. 

##### Example:

<?xml version='1.0' encoding='utf-8'?>

<grid name="defGrid">
    <vertices coords="3">100.0 0.0 0 101.0 0.0 0 101.0 1.0 0 100.0 1.0 0 </vertices>    <edges>0 1 1 2 2 3 3 0 </edges>
      <subset_handler name="defSH">
        <subset name="value0" color="0.588235 0.588235 1 1" state="393216">
            <vertices>0 1 2 3 0 </vertices>
              <edges>0 1 2 3 </edges>
          </subset>
      </subset_handler>
      <selector name="defSel" />
      <projection_handler name="defPH" subset_handler="0">
      <default type="default">0 0</default>
      </projection_handler>
</grid>

This example of the UGX file format is converted from the above GeoJSON example. The attribute <vertices coords="3"> indicates that every three numbers represent the coordinates of a point on the XYZ axes. Here, the Z-coordinates are set to 0 because the original GeoJSON data does not include Z-coordinates. In the <edges> tag, all edges consist of unique point indices connected in pairs. The subtags <vertices> and <edges> ensure that the unique point indices and edge indices are listed under the corresponding subsets in the <subset name=" "> attribute. Thus, all information for vertices and edges comes from the GeoJSON "coordinates" array, and the subset name is derived from the "properties" dictionary.

## Requirements:

- Python >= 3.11.7

- ProMesh(http://www.promesh3d.com)

## Convertion from GeoJSON to UGX:

##### Terminal

Starting from the TestData root directory, please execute the following command to run the GeojsonToUgx.py:

```
GeojsonToUgxMain.py [-h] -i INPUT -o OUTPUT -t -TYPE TYPE
```

Here, within the TestData root directory:

- INPUT refers to the TestData name, which can be provided with or without the .geojson extension.
- OUTPUT refers to the name of the output file, which can be provided with or without the .ugx extension. If you do not specify an output path, the .ugx file will be saved in the TestData root directory.
- TYPE indicates the selectable coordinate formats, which can be either "wgs" or "utm", the default type is "wgs".

**Note:**

- During the execution process in the terminal, you will need to manually input the desired key for the subset name. The subset names are stored in the GeoJSON 'properties' dictionary, and usually, there are several keys to choose from.             For example:
  
  "properties": { "prop0": "value0", "prop1": {"this": "that"}}
  
  If you input the key 'prop0', then the subset name will be the value corresponding   to 'prop0' in each 'properties' dictionary.

- Additionally, you will need to input the delimiter, ensuring that it is different from any hyphen used in the names. 
  For example:
  in the Germany region 'Sachsen-Anhalt', the hyphen '-' is used as a connector, so do not input '-' as a delimiter to avoid confusion.

## Running Examples:

First, use single polygon GeoJSON data from GitHub for testing. You can access the data [single polygon](https://github.com/mapbox/tokml/blob/master/test/data/polygon.geojson). Then, use Germany GeoJSON data for further testing, sourced from Cartography Vectors. You can find data of various regions and countries, including Germany, on their website [Cartography Vectors](https://cartographyvectors.com/map/276-germany). 

### WGS84 Examples:

1.Polygon:
![Polygon-WGS](./polygon.png "Polygon-WGS")
2.Germany map:
![Germany-WGS](./germany-wgs.png "Germany-WGS")

When using WGS84 coordinates, the generated .ugx data produces a visibly distorted Germany map in ProMesh, seems wider.

#### UTM Examples:

![Germany-UTM](./germany-utm.png "Germany-UTM")

When using UTM coordinates, the generated .ugx data produces a visibly realistic Germany map in ProMesh.

# Triangle Filling:

## Setup:

**Add Triangle_Fill_by_BoundarySubsets.lua to .promesh/scripts:**

Move `Triangle_Fill_by_BoundarySubsets.lua` to `.promesh/scripts`. If you cannot find it, you can copy the code into the new lua-script, which is created by clicking on `scripts/New Script` in the directory bar of ProMesh.

Reopen ProMesh. You can find `Triangle Fill by known Boundary Subsets` under `Tool Browser/Scripts`.

**Parameter Settings:**

- **Delimiter:** default is `/`, ensure this delimiter is the same delimiter that is used in `promesh/geometry name`,.
- **Angle:** Sets the angle for triangles, default is 20.
- **Quality:** default is '✅'.
- **all:** default is '✅', if you want to fill the specific area, then leave unchecked.
  - **specific target:** Default is `nil`, which means it will fill the entire map. Alternatively, you can specify the region you wish to fill. Use the same delimiter as above to separate different regions.
    (Besides the specific region(followed with a number) should be choosen from the ProMesh 'geometry name'. Because some regions have Insels, and Promesh can not fill the seperate polygons at the same time. Therefore, in order to distinguish different polygons in the same region, each region is followed with a number).
     (If 'all' is selected and 'specific target' is not 'nil', then still will fill the whole map.)

### Examples:

1. Fill one Polygon:
   ![TriangleFill](./fill-one-polygon.png "Triangle-Fill")
2. Fill one specific target: 
   ![TriangleFill](./Bayern1.png "Triangle-Fill")
3. Using delimiter to fill one than one specific target
   ![TriangleFill](./hessen1-bayern1.png "Triangle-Fill")
4. Fill the whole map:
   ![TriangleFill](./triangle-fill.png "Triangle-Fill")
