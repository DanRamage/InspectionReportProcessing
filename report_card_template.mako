<%
%>

# County: ${county_name}
**Report dates from ${start_date} to ${end_date}**
**Only inspections that are not an A are shown, unless there was a non A inspection and follow-up was an A**

**Data was sourced from the South Carolina Department of Agriculture [here](https://apps.dhec.sc.gov/Environment/FoodGrades/)**

% for feature in features:
${"##"} ${feature.attributes['FACILITY']}
* Posted Grade: ${feature.attributes['POSTED_GRADE'].strip()} on ${format_inspection_date(feature.attributes['INSP_DATE'])}
* Inspection Type: ${feature.attributes['AC_CODE']} [Report](${format_report_url(feature.attributes['AuditResultGlobalID'])})
* Active: ${feature.attributes['Active']}
* Address: ${feature.attributes['ADDRESS']} ${feature.attributes['CITY']}, ${feature.attributes['STATE']}

% endfor

