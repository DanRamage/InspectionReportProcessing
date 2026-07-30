cd /home/xeniaprod/scripts/InspectionReportProcessing

source ./venv/bin/activate

python3 main.py --LookBackDays=30 \
--OutputDirectory=/var/www/RestaurantRatingScraper/results \
--MarkdownTemplateFile=report_card_template.mako \
--HTMLTemplateFile=html_report_card_template.mako \

source ./venv/bin/activate deactivate