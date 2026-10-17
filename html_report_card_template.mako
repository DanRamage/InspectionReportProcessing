<!DOCTYPE html>
<html data-theme="light">
<head>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>County: ${county_name}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1.0.4/css/bulma.min.css">
</head>
<body>
<section class="section">
    <div class="container">
        <h1 class="title">
            County: ${county_name}
        </h1>
        <p class="subtitle">
            Report dates from ${start_date} to ${end_date}
        </p>
        <p>
            <b>Only inspections that are not an A are shown, unless there was a non A inspection and follow-up was an A.</b>
        </p>
        <p>
          <b>Data was sourced from the South Carolina Department of Agriculture <a href='https://dataviz.dph.sc.gov/foodgrades/'>here</a>.</b>
        </p>
    </div>
</section>
<section class="bigsection">
    <div class="container">
        % for feature in features:
        <div class="content">
            <h4>${feature.attributes['FACILITY']}</h4>
              <ul>
                  <li>Posted Grade: ${feature.attributes['POSTED_GRADE'].strip()} on
                      ${format_inspection_date(feature.attributes['INSP_DATE'])}
                  </li>
                  <li>Inspection Type: ${feature.attributes['AC_CODE']} <a
                          href=${format_report_url(feature.attributes['AuditResultGlobalID'])}> Report</a></li>
                  <li>Address: ${feature.attributes['ADDRESS']} ${feature.attributes['CITY']},
                      ${feature.attributes['STATE']}
                  </li>
              </ul>
        </div>
        % endfor
    </div>
</section>
</body>
</html>