#-------------------------------------------------------------------------------
# Name:        Collar Automap version 1.0
# Purpose: This tool creates a pdf map of the latest caribou collar movement.
#          This script is based off of a template map.
#          This version has no error handling.
#          Currently the date subselection is not working.
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

# Unique defs
def unique_values(table, field):
    data = arcpy.da.TableToNumPyArray(table, [field])
    unqs = numpy.unique(data[field])
    output = [str(x) for x in unqs]
    return output

# Manditory User parameters
output_location = arcpy.GetParameterAsText(0)
collar_data = arcpy.GetParameterAsText(1)

# Optional User parameters
start_date = arcpy.GetParameterAsText(2) # Enter it as mm/dd/yyyy with zero padded #s. SET DEFAULT as "none".
end_date = arcpy.GetParameterAsText(3) # Enter it as mm/dd/yyyy with zero padded #s. SET DEFAULT as "none".
region_filter = arcpy.GetParameterAsText(4) # Enter in a region or regions to filter the data to.
herd_filter = arcpy.GetParameterAsText(5)
use_auto_extent = arcpy.GetParameterAsText(6) # if "No" then uses the base_mxd's extent for the map (custom). SET DEFAULT AS "Yes".
debug_script = arcpy.GetParameterAsText(7) # Set this to "Yes" if you want to keep the intermediate files for debugging. SET DEFAULT AS "No".

# Derived user parameters
if start_date != "None":
    start_date_name = "First point after " + start_date
    end_date_name = "Last point before " + end_date
    pdf_name = "Collar_movement_" + start_date.replace("/", "-") + "_to_" + end_date.replace("/", "-")
    start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y")
    end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y")

# Set parameters
ID_field = "AnimalNum"
date_field = "txtDate"
base_mxd = r"H:\JUDY\github\Wildlife-ENR-GNWT\Collar_Automap\BA_weekly_map_template_16.mxd"
arcpy.env.overwriteOutput = True
firstSYM = r"H:\JUDY\github\Wildlife-ENR-GNWT\Collar_Automap\LYR_first.lyr"
lastSYM = r"H:\JUDY\github\Wildlife-ENR-GNWT\Collar_Automap\LYR_last.lyr"
arcpy.env.workspace = output_location
sort_field_for_lines = "ZuluTime"
region_field = "Program"
herd_field = "Group"
sex_field = "Sex"

### Subset original data based on date
##if start_date != "None":
####    #TESTING STUFF
####    import csv
##    arcpy.MakeFeatureLayer_management(collar_data, "tmp")
##    date_list = []
##    date_list_FID = []
##    with arcpy.da.SearchCursor("tmp", ("FID", date_field)) as cursor:
##        for row in cursor:
##            date_list.append(datetime.datetime.strptime(row[1], "%Y/%m/%d %H:%M"))
##            date_list_FID.append(row[0])
##    good_dates_FIDs = [date_list_FID[date_list.index(x)] for x in date_list if x > start_date and x < end_date]
####    with open(r"H:\Angus Smith\Projects\BGC\Automap_debugging\analyzed_data\rerun_herd_filter_on\output7\output1.csv", "w") as f:
####        writer = csv.writer(f)
####        rows = zip(date_list, date_list_FID, good_dates_FIDs)
####        for row in rows:
####            writer.writerow(row)
####    arcpy.AddMessage("good_dates_FIDs follow:")
####    good_dates_FIDs.sort()
####    arcpy.AddMessage(good_dates_FIDs)
##    arcpy.SelectLayerByAttribute_management("tmp", "NEW_SELECTION", """ "FID" IN {0} """.format(str(tuple(good_dates_FIDs))))
##    arcpy.CopyFeatures_management("tmp", "collar_data_date_subselection")
##    collar_data = os.path.join(output_location, "collar_data_date_subselection") + ".shp"
##    arcpy.Delete_management("tmp")



# Subset the data based on region ("program")
if region_filter != "All":
    SQL = """ {0} IN {1} """.format(region_field, str(str(region_filter.replace("'", "")).split(";")).replace("[", "(").replace("]", ")"))
    arcpy.MakeFeatureLayer_management(collar_data, "tmp")
    arcpy.SelectLayerByAttribute_management("tmp", "NEW_SELECTION", SQL)
    arcpy.CopyFeatures_management("tmp","region_filter_subselection")
    arcpy.Delete_management("tmp")
    collar_data = os.path.join(output_location, "region_filter_subselection") + ".shp"

# Subset the data based on herd ("group")
if herd_filter != "All":
    SQL = """ {0} IN {1} """.format(herd_field, str(str(herd_filter.replace("'", "")).split(";")).replace("[", "(").replace("]", ")"))
    arcpy.MakeFeatureLayer_management(collar_data, "tmp")
    arcpy.SelectLayerByAttribute_management("tmp", "NEW_SELECTION", SQL)
    arcpy.CopyFeatures_management("tmp", "herd_filter_subselection")
    arcpy.Delete_management("tmp")
    collar_data = os.path.join(output_location, "herd_filter_subselection") + ".shp"

# Check the data for any un-sexed individuals, remove them and post a warning to
# the tool output.
sex_list = unique_values(collar_data, sex_field)
sex_list_unq = [sex for sex in sex_list if sex != "F" and sex != "M"]
if len(sex_list_unq) > 0:
    SQL = """ {0} IN ('F', 'M') """.format(sex_field)
    arcpy.AddMessage("WARNING - CONTAINS INDIVIDUALS WITH UNASSIGNED SEX.")
    arcpy.AddMessage("These individuals were removed from the map.")
    arcpy.MakeFeatureLayer_management(collar_data, "tmp")
    arcpy.SelectLayerByAttribute_management("tmp", "NEW_SELECTION", SQL)
    arcpy.CopyFeatures_management("tmp", "sex_filter_subselection")
    arcpy.Delete_management("tmp")
    collar_data = os.path.join(output_location, "sex_filter_subselection") + ".shp"

# Name the pdf output based on realized date range (if it was not user input).
if start_date == "None":
    date_list_all_1 = unique_values(collar_data, date_field)
    date_list_all_2 = [datetime.datetime.strptime(x, "%Y/%m/%d %H:%M") for x in date_list_all_1]
    start_date_name = date_list_all_1[date_list_all_2.index(min(date_list_all_2))].split(" ")[0].split("/")
    start_date_name = start_date_name[1] + "/" + start_date_name[2] + "/" + start_date_name[0]
    end_date_name = date_list_all_1[date_list_all_2.index(max(date_list_all_2))].split(" ")[0].split("/")
    end_date_name = end_date_name[1] + "/" + end_date_name[2] + "/" + end_date_name[0]
    pdf_name = "Collar_movement_" + start_date_name.replace("/", "-") + "_to_" + end_date_name.replace("/", "-")

# Make the lines
arcpy.PointsToLine_management(collar_data, "lines_collar_paths", ID_field, sort_field_for_lines)

# Unique values of collar IDs
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
if debug_script == "Yes":
    # Save a copy of the mxd and don't delete the intermediate files.
    mxd.saveACopy(os.path.join(output_location, "intermediate_mxd.mxd"))
    del mxd
else:
    arcpy.Delete_management("collar_data_date_subselection.shp")
    arcpy.Delete_management("firstFC.shp")
    arcpy.Delete_management("lastFC.shp")
    arcpy.Delete_management("lines_collar_paths.shp")
    arcpy.Delete_management("region_filter_subselection")
    arcpy.Delete_management("herd_filter_subselection")
    arcpy.Delete_management("sex_filter_subselection")

    del mxd