#-------------------------------------------------------------------------------
# Name:        Collar Automap version 1.0
# Purpose: This tool creates a pdf map of the latest caribou collar movement.
#          This script is based off of a template map.
#          This version has no error handling.
#
# Author:      angus_smith
#
# Created:     06/04/2016
# Copyright:   (c) angus_smith 2016
#-------------------------------------------------------------------------------

# Imports
import arcpy
import numpy
import datetime
import os

# Manditory User parameters
output_location = arcpy.GetParameterAsText(0)
collar_data = arcpy.GetParameterAsText(1)

# Optional User parameters
start_date = arcpy.GetParameterAsText(2) # Enter it as mm/dd/yyyy with zero padded #s. SET DEFAULT as "none".
end_date = arcpy.GetParameterAsText(3) # Enter it as mm/dd/yyyy with zero padded #s. SET DEFAULT as "none".
use_auto_extent = arcpy.GetParameterAsText(4) # if "No" then uses the base_mxd's extent for the map. SET DEFAULT AS "Yes".

# Derived user parameters
start_date_name = "First point after " + start_date
end_date_name = "Last point before " + end_date
start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y")
end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y")

# Set parameters
ID_field = "AnimalNum"
date_field = "txtDate"
base_mxd = r"H:\JUDY\github\Wildlife-ENR-GNWT\Collar_Automap\BA_mapping_2015.mxd"
arcpy.env.overwriteOutput = True
firstSYM = r"H:\JUDY\github\Wildlife-ENR-GNWT\Collar_Automap\LYR_first.lyr"
lastSYM = r"H:\JUDY\github\Wildlife-ENR-GNWT\Collar_Automap\LYR_last.lyr"
arcpy.env.workspace = output_location
sort_field_for_lines = "ZuluTime"
pdf_name = "Test_export_pdf"
debug_script = False # Set this to True if you want to keep the intermediate files for debugging.

# Subset original data based on date
if start_date != "none":
    arcpy.MakeFeatureLayer_management(collar_data, "tmp")
    date_list = []
    date_list_FID = []
    with arcpy.da.SearchCursor("tmp", ("FID", date_field)) as cursor:
        for row in cursor:
            date_list.append(datetime.datetime.strptime(row[1], "%Y/%m/%d %H:%M"))
            date_list_FID.append(row[0])
    good_dates_FIDs = [date_list_FID[date_list.index(x)] for x in date_list if x > start_date and x < end_date]
    arcpy.SelectLayerByAttribute_management("tmp", "NEW_SELECTION", """ "FID" IN {0} """.format(str(tuple(good_dates_FIDs))))
    arcpy.CopyFeatures_management("tmp", "collar_data_date_subselection")
    collar_data = os.path.join(output_location, "collar_data_date_subselection") + ".shp"
    arcpy.Delete_management("tmp")

# Make the lines
arcpy.PointsToLine_management(collar_data, "lines_collar_paths", ID_field, sort_field_for_lines)

# Unique values of collar IDs
def unique_values(table, field):
    data = arcpy.da.TableToNumPyArray(table, [field])
    unqs = numpy.unique(data[field])
    output = [str(x) for x in unqs]
    return output

ID_list = unique_values(collar_data, ID_field)

# Create "first" and "last" shps.
##arcpy.env.workspace = output_location # Not needed? Set earlier?
SR = arcpy.Describe(collar_data).spatialReference
arcpy.CreateFeatureclass_management(output_location, "firstFC", "POINT", collar_data, "", "", SR)
arcpy.CreateFeatureclass_management(output_location, "lastFC", "POINT", collar_data, "", "", SR)

for ID in ID_list:
    # First
    arcpy.MakeFeatureLayer_management(collar_data, "tmp", """ {0} = '{1}' """.format(ID_field, ID))
    date_list = []
    date_list_FID = []
    with arcpy.da.SearchCursor("tmp", ("FID", date_field)) as cursor:
        for row in cursor:
            date_list.append(datetime.datetime.strptime(row[1], "%Y/%m/%d %H:%M"))
            date_list_FID.append(row[0])
    min_FID = date_list_FID[date_list.index(min(date_list))]
    arcpy.SelectLayerByAttribute_management("tmp", "NEW_SELECTION", """ "FID" = {0} """.format(min_FID))
    arcpy.Append_management("tmp", "firstFC.shp")
    arcpy.Delete_management("tmp")
    # Last
    arcpy.MakeFeatureLayer_management(collar_data, "tmp", """ {0} = '{1}' """.format(ID_field, ID))
    date_list = []
    date_list_FID = []
    with arcpy.da.SearchCursor("tmp", ("FID", date_field)) as cursor:
        for row in cursor:
            date_list.append(datetime.datetime.strptime(row[1], "%Y/%m/%d %H:%M"))
            date_list_FID.append(row[0])
    max_FID = date_list_FID[date_list.index(max(date_list))]
    arcpy.SelectLayerByAttribute_management("tmp", "NEW_SELECTION", """ "FID" = {0} """.format(max_FID))
    arcpy.Append_management("tmp", "lastFC.shp")
    arcpy.Delete_management("tmp")

# Create the mxd and df objects
mxd = arcpy.mapping.MapDocument(base_mxd)
df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]

# Create the legend object
legend = arcpy.mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT")[0]

# Add the first/last layers and the track files.
legend.autoAdd = True
arcpy.mapping.AddLayer(df, arcpy.mapping.Layer("lastFC.shp"))
arcpy.mapping.AddLayer(df, arcpy.mapping.Layer("firstFC.shp"))
legend.autoAdd = False
arcpy.mapping.AddLayer(df, arcpy.mapping.Layer("lines_collar_paths.shp"))

# Symbolize the layers
update_layer = arcpy.mapping.ListLayers(mxd, "firstFC", df)[0]
source_layer = arcpy.mapping.Layer(firstSYM)
arcpy.mapping.UpdateLayer(df,update_layer,source_layer, symbology_only = True)

update_layer = arcpy.mapping.ListLayers(mxd, "lastFC", df)[0]
source_layer = arcpy.mapping.Layer(lastSYM)
arcpy.mapping.UpdateLayer(df,update_layer,source_layer, symbology_only = True)

# Change the layer "name" property for first and last
first = legend.listLegendItemLayers()[0]
last = legend.listLegendItemLayers()[1]
first.name = start_date_name
last.name = end_date_name

# Set the legend style (MIGHT BREAK)
styleItem = arcpy.mapping.ListStyleItems("ESRI.style", "Legend Items", "Horizontal Single Symbol Layer Name and Label")[0]
legend.updateItem(first, styleItem)
legend.updateItem(last, styleItem)

# Set the map extent
if use_auto_extent == "Yes":
    extent_lyr = arcpy.mapping.ListLayers(mxd, "lines_collar_paths")[0]
    new_extent = extent_lyr.getExtent()
    df.extent = new_extent

# Export the map to pdf
arcpy.mapping.ExportToPDF(mxd, os.path.join(output_location, pdf_name))

# Clean up working files
if debug_script == True:
    # Save a copy of the mxd and don't delete the intermediate files.
    mxd.saveACopy(r"H:\Angus Smith\Caribou\Barren Ground Caribou\Judy_map_tool_04_2016\data\test_loc\test_out\test_out_map.mxd")
    del mxd
elif debug_script == False:
    arcpy.Delete_management("collar_data_date_subselection.shp")
    arcpy.Delete_management("firstFC.shp")
    arcpy.Delete_management("lastFC.shp")
    arcpy.Delete_management("lines_collar_paths.shp")
    del mxd