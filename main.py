from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.geometry.filters import intersects
from string import Template
import optparse
from datetime import datetime, timedelta
import dateutil.parser as dparser
from pathlib import Path
from mako import template, exceptions as makoExceptions
import traceback
SC_COUNTIES = {
    "01": "Abbeville",
    "02": "Aiken",
    "03": "Allendale",
    "04": "Anderson",
    "05": "Bamberg",
    "06": "Barnwell",
    "07": "Beaufort",
    "08": "Berkeley",
    "09": "Calhoun",
    "10": "Charleston",
    "11": "Cherokee",
    "12": "Chester",
    "13": "Chesterfield",
    "14": "Clarendon",
    "15": "Colleton",
    "16": "Darlington",
    "17": "Dillon",
    "18": "Dorchester",
    "19": "Edgefield",
    "20": "Fairfield",
    "21": "Florence",
    "22": "Georgetown",
    "23": "Greenville",
    "24": "Greenwood",
    "25": "Hampton",
    "26": "Horry",
    "27": "Jasper",
    "28": "Kershaw",
    "29": "Lancaster",
    "30": "Laurens",
    "31": "Lee",
    "32": "Lexington",
    "33": "Marion",
    "34": "Marlboro",
    "35": "McCormick",
    "36": "Newberry",
    "37": "Oconee",
    "38": "Orangeburg",
    "39": "Pickens",
    "40": "Richland",
    "41": "Saluda",
    "42": "Spartanburg",
    "43": "Sumter",
    "44": "Union",
    "45": "Williamsburg",
    "46": "York"
}

pdf_url_template = Template("http://pubdoc.dhec.sc.gov/inspection/$pdf_id.pdf")


def format_inspection_date(inspection_date):
    formatted_date = datetime.fromtimestamp(inspection_date/1000.0).strftime('%Y-%m-%d %H:%M:%S')
    return formatted_date

def format_report_url(report_name):
    report_url = pdf_url_template.substitute(pdf_id=report_name)
    return report_url

def main():
    parser = optparse.OptionParser(usage="usage: %prog [options] argument")

    parser.add_option( "--LookBackDays", dest="lookback_days", type="int", default=30,
                      help="Number of days to look back for inspection reports.")
    parser.add_option( "--OutputDirectory", dest="output_directory",
                      help="Directory to save the data.")
    parser.add_option( "--TemplateFile", dest="template_file",
                      help="Directory to save the data.")

    # 5. Parse the command-line arguments
    (options, args) = parser.parse_args()

    output_directory = Path(options.output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    now_date = datetime.now()
    start_date = now_date - timedelta(days=options.lookback_days)
    # Connect to your GIS portal or ArcGIS Online
    gis = GIS()

    # Reference your target Feature Layer URL
    layer_url = "https://services5.arcgis.com/G4BLIH7rTQoIjCFv/ArcGIS/rest/services/Restaurants/FeatureServer/4"
    parcel_layer = FeatureLayer(layer_url)


    # Define the bounding box (envelope) coordinates and spatial reference
    query_extent = {
        "xmin": -13198303.18,
        "ymin": 4059062.83,
        "xmax": -13197797.98,
        "ymax": 4059421.13,
        "spatialReference": {"wkid": 4326}
    }

    # Create a spatial filter using intersects (or contains/within)
    query_filter = intersects(query_extent, sr=102100)

    #INSP_DATE > TIMESTAMP '2026-07-01 00:00:00' AND POSTED_GRADE <> 'A' AND COUNTY = '40'
    date_filter = Template("INSP_DATE > TIMESTAMP '$date' AND COUNTY = '$county'")
    out_fields = ['PERMIT_ID', 'Active', 'POSTED_GRADE', 'FACILITY', 'ADDRESS', 'CITY', 'STATE', 'AC_CODE', 'INSP_DATE', 'AuditResultGlobalID', 'Active']
    for county_code, county_name in SC_COUNTIES.items():
        filter_string = date_filter.substitute(date=start_date.strftime("%Y-%m-%d %H:%M:%S"), county=county_code)
        # Execute the query on the feature layer
        results = parcel_layer.query(
            #geometry_filter=query_filter,
            where=filter_string,
            #out_fields=",".join(out_fields),
            order_by_fields=["FACILITY", "INSP_DATE", "POSTED_GRADE"],
        )
        #Now let's filter the results.
        facilities = {}
        for feature in results.features:
            permit_id = feature.attributes['PERMIT_ID']
            posted_grade = feature.attributes['POSTED_GRADE'].strip()
            facility_entry = facilities.setdefault(permit_id, {"has_a": False,
                                             "has_non_a": False,
                                             "features": []})
            if posted_grade == "A":
                facility_entry["has_a"] = True
            else:
                facility_entry["has_non_a"] = True
            facility_entry["features"].append(feature)

        output_results = result = [
            feature
            for permit_id, status in facilities.items()
            if (status["has_a"] and status["has_non_a"]) or status["has_non_a"]
            for feature in status['features']
        ]
        try:
            results_outfile = output_directory / f"{county_name}.md"
            mytemplate = template.Template(filename=options.template_file)
            with open(results_outfile, "w") as result_file_obj:
                results_report = mytemplate.render(county_name=county_name,
                                                   features=output_results,
                                                   format_inspection_date=format_inspection_date,
                                                   format_report_url=format_report_url)
                result_file_obj.write(results_report)

        except TypeError as e:
            print(makoExceptions.text_error_template().render())

        except (IOError, AttributeError, Exception) as e:
            traceback.print_exc()

    # Print the number of matching features found
        print(f"Features found: {len(results.features)}")


if __name__ == "__main__":
    main()