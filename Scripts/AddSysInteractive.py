# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# DrawSystems.py
# Created on: 2016-06-24 12:05:46.00000
#   (generated by ArcGIS/ModelBuilder)
# Usage: DrawSystems <Feature_Set> <Output_XY_Systems> 
# Description: 
# ---------------------------------------------------------------------------

# Import all necessary module dependencies
import arcpy
import os
import sys
import csv
import json

arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(3857)

def Encode(x):
    """Encodes values into 'utf-8' format"""
    if isinstance(x, unicode):
        return x.encode("utf-8", 'ignore')
    else:
        return str(x)

def ExcludeFields(table, types=[]):
    """Return a list of fields minus those with specified field types"""
    fieldNames = []
    fds = arcpy.ListFields(table)
    for f in fds:
        if f.type not in types:
            fieldNames.append(f.name)
    return fieldNames

def ExportToCSV(fc, output):
    """Export Data to a CSV file"""
    # create the output writer
    outWriter = csv.writer(open(output, 'wb'), dialect='excel')

    excludeTypes = ['Geometry', 'OID']
    fields = ExcludeFields(fc, excludeTypes)

    # Create Search Cursor: the following only works with ArcGIS 10.1+
    with arcpy.da.SearchCursor(fc, fields) as cursor:
        outWriter.writerow(cursor.fields)
        for row in cursor:
            row = [v.decode('utf8') if isinstance(v, str) else v for v in row]
            outWriter.writerow([unicode(s).encode("utf-8") for s in row])
    del cursor

def AddSystems():
    """Draws telecoupling systems on top of basemap interactively or from table"""

    # Local variable:
    out_layer = "Systems_lyr"

    # Get the value of the input parameter
    inFeatureSet = arcpy.GetParameterAsText(0)
    in_RecordSet = arcpy.GetParameter(1)
    isChecked_AddXY = arcpy.GetParameter(2)

    arcpy.SetProgressorLabel('Creating System Components ...')
    arcpy.AddMessage('Creating System Components ...')

    if inFeatureSet or inFeatureSet != "#":
        try:
            # Process: Make Feature Layer (temporary)
            arcpy.MakeFeatureLayer_management(in_features=inFeatureSet, out_layer=out_layer)
            arcpy.AddField_management(in_table=out_layer, field_name="Name", field_type="TEXT", field_length=50)

            sysTable = json.loads(in_RecordSet.JSON)

            idx = 0
            countRows = int(arcpy.GetCount_management(out_layer).getOutput(0))

            if countRows != len(sysTable['features']):
                arcpy.AddError("Number of records in 'Input Attribute Table' MUST equal number of systems on the map!!")
                raise arcpy.ExecuteError
            else:
                with arcpy.da.UpdateCursor(out_layer, 'Name') as cursor:
                    for row in cursor:
                        row[0] = sysTable['features'][idx]['attributes']['Name']
                        # Update the cursor with the updated list
                        cursor.updateRow(row)
                        idx += 1
                del cursor

            # Process: Copy Feature Class
            outSystems_fc = os.path.join(arcpy.env.scratchGDB, "Systems")
            arcpy.CopyFeatures_management(out_layer, outSystems_fc)

            if isChecked_AddXY:
                arcpy.SetProgressorLabel('Adding XY Coordinates ...')
                arcpy.AddMessage('Adding XY Coordinates ...')
                # Process: Add Coordinates
                arcpy.AddXY_management(outSystems_fc)

            # Process: Delete Unwanted/Unnecessary fields
            arcpy.SetProgressorLabel('Removing Unwanted Fields ...')
            arcpy.AddMessage('Removing Unwanted Fields ...')
            arcpy.DeleteField_management(outSystems_fc, "Id")

            # Process: Export Data to CSV File
            arcpy.SetProgressorLabel('Exporting Feature Class Attributes to CSV ...')
            arcpy.AddMessage('Exporting Feature Class Attributes to CSV ...')
            outTable_CSV = os.path.join(arcpy.env.scratchFolder, "Systems_Table.csv")
            ExportToCSV(fc=outSystems_fc, output=outTable_CSV)

            #### Set Parameters ####
            arcpy.SetParameterAsText(3, outSystems_fc)

        except Exception:
            e = sys.exc_info()[1]
            arcpy.AddError('An error occurred: {}'.format(e.args[0]))

    else:
        arcpy.AddError('No Features Have Been Added to the Map!')


if __name__ == '__main__':
    AddSystems()






