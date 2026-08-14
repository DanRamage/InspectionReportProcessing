from typing import List, Any

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
import logging.config

from reddit_output import reddit_output
SC_COUNTIES = {
    #"22": "Georgetown",
    #"26": "Horry",
    "32": "Lexington",
    "40": "Richland",
    #"23": "Greenville",

}
'''
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
'''
pdf_url_template = Template("http://pubdoc.dhec.sc.gov/inspection/$pdf_id.pdf")


def format_inspection_date(inspection_date: int):
    formatted_date = datetime.fromtimestamp(inspection_date/1000.0).strftime('%Y-%m-%d %H:%M:%S')
    return formatted_date

def format_report_url(report_name: str):
    report_url = pdf_url_template.substitute(pdf_id=report_name)
    return report_url

def query_endpoint(county_code: str, start_date: datetime) -> List[Any]:
    output_results = []
    layer_url = "https://services5.arcgis.com/G4BLIH7rTQoIjCFv/ArcGIS/rest/services/Restaurants/FeatureServer/4"
    parcel_layer = FeatureLayer(layer_url)

    date_filter = Template("INSP_DATE > TIMESTAMP '$date' AND COUNTY = '$county'")
    out_fields = ['PERMIT_ID', 'Active', 'POSTED_GRADE', 'FACILITY', 'ADDRESS', 'CITY', 'STATE', 'AC_CODE', 'INSP_DATE', 'AuditResultGlobalID', 'Active']
    filter_string = date_filter.substitute(date=start_date.strftime("%Y-%m-%d %H:%M:%S"), county=county_code)
    # Execute the query on the feature layer
    results = parcel_layer.query(
        #geometry_filter=query_filter,
        where=filter_string,
        out_fields=",".join(out_fields),
        order_by_fields=["FACILITY", "INSP_DATE", "POSTED_GRADE"],
    )
    #Now let's filter the results.
    facilities = {}
    for feature in results.features:
        permit_id = feature.attributes['PERMIT_ID']
        posted_grade = feature.attributes['POSTED_GRADE'].strip()
        #What we're looking to do is get all non A inspections, but we want to show A's for
        #facilities that had a followup that was an A. In other words we want to make sure if a
        #facility has a B then gets an A on a followup, we also show that A.
        facility_entry = facilities.setdefault(permit_id, {"has_a": False,
                                         "has_non_a": False,
                                         "features": []})
        if posted_grade == "A":
            facility_entry["has_a"] = True
        else:
            facility_entry["has_non_a"] = True
        facility_entry["features"].append(feature)
        #Let's build a list of the features.
        output_results = result = [
            feature
            for permit_id, status in facilities.items()
            if (status["has_a"] and status["has_non_a"]) or status["has_non_a"]
            for feature in status['features']
        ]

    return output_results

def output_report(template_file: Path,
                  output_file_name: Path,
                  county_name: str,
                  start_date: datetime,
                  end_date: datetime,
                  output_results: List[Any]):
    logger = logging.getLogger()
    try:
        logger.info(f"Using template file: {template_file}")
        mytemplate = template.Template(filename=template_file)
        logger.info(f"Writing to {output_file_name}")
        with open(str(output_file_name), "w") as result_file_obj:
            results_report = mytemplate.render(county_name=county_name,
                                               start_date=start_date.strftime("%Y-%m-%d"),
                                               end_date=end_date.strftime("%Y-%m-%d"),
                                               features=output_results,
                                               format_inspection_date=format_inspection_date,
                                               format_report_url=format_report_url)
            result_file_obj.write(results_report)
    except TypeError as e:
        logger.error(makoExceptions.text_error_template().render())

    except (IOError, AttributeError, Exception) as e:
        logger.exception(e)

    return

def post_reddit_results(ini_file: Path, county_name: str, inspection_date: datetime, output_file: Path):
    #(self, county: str, inspection_date: datetime, report_file: Path):
    reddit_obj = reddit_output(ini_file=ini_file, county_name=county_name)
    reddit_obj.post(county_name, inspection_date, output_file)
    return

def main():
    parser = optparse.OptionParser(usage="usage: %prog [options] argument")

    parser.add_option( "--LookBackDays", dest="lookback_days", type="int", default=30,
                      help="Number of days to look back for inspection reports.")
    parser.add_option( "--OutputDirectory", dest="output_directory",
                      help="Directory to save the data.")
    parser.add_option( "--MarkdownTemplateFile", dest="markdown_template_file",
                      help="Mako templates to use for the markdown files")
    parser.add_option( "--HTMLTemplateFile", dest="html_template_file",
                      help="Mako templates to use for the HTML files")
    parser.add_option( "--LoggingConfig", dest="logging_config",
                      help="Logging conf file.")
    parser.add_option( "--RedditSettingsINI", dest="reddit_settings_ini", default="reddit_settings.ini",
                      help="INI file containing the Reddit settings.")

    (options, args) = parser.parse_args()

    logging.config.fileConfig(options.logging_config)
    logger = logging.getLogger(__name__)
    logger.info("Log file opened.")

    output_directory = Path(options.output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    now_date = datetime.now()
    start_date = now_date - timedelta(days=options.lookback_days)



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
    for county_code, county_name in SC_COUNTIES.items():
        logger.info(f"Querying: {county_code} {county_name}")
        output_results = query_endpoint(county_code=county_code, start_date=start_date)
        # Print the number of matching features found
        logger.info(f"Matching features found: {len(output_results)}")

        markdown_results_outfile = output_directory / f"{county_name}_{start_date.strftime("%Y-%m-%d")}_{now_date.strftime("%Y-%m-%d")}.md"
        output_report(template_file=options.markdown_template_file,
                      output_file_name=markdown_results_outfile,
                      county_name=county_name,
                      start_date=start_date,
                      end_date=now_date,
                      output_results=output_results
                      )
        results_outfile = output_directory / f"{county_name}_{start_date.strftime("%Y-%m-%d")}_{now_date.strftime("%Y-%m-%d")}.html"
        output_report(template_file=options.html_template_file,
                      output_file_name=results_outfile,
                      county_name=county_name,
                      start_date=start_date,
                      end_date=now_date,
                      output_results=output_results
                      )

        post_reddit_results(ini_file=Path(options.reddit_settings_ini),
                            county_name=county_name,
                            inspection_date=now_date,
                            output_file=markdown_results_outfile)


if __name__ == "__main__":
    main()