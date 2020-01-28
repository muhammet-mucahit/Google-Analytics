# Analytics-API

## Client Secrets
    Just download your own client_secret.json from Google Console

## Requirements.txt
    flask
    google-api-python-client
    oauth2client

## Setup Repo
```
git clone https://gitlab.com/rank.ai/data-collection/google-analytics.git
cd google-analytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python analytics_api.py
```

```
	get_site_list:

		Request:

			- Auth Key (no-required) (does not exist)


		Response:

			- View ID & Domain & Total Traffic & Daily Average Traffic & Start Date (13412532523, kariyer.net, 93.234.280, 185.750, 2019-08-09)

		
		Done:

		- Send requests to get all views list.
		- Ask to last 502 days organic traffic for those views.
		- Return total organic traffics for last 502 days & response details.


	get_site_data:

		Request:

		- Auth Key (no-required) (does not exist)
		- Domain Name (required) (example: kariyer.net) (only available with view_id)
		- Date Range (2019-01-01) (2019-12-31) (optional: fallback last 502 days)
		- Metrics (fallback: ga_bounce_rate, ga_session_time etc.)
		- Dimensions (fallback: landingPage, country, device, date)

            {
                "viewId": "32016404",
                "startDate": "2019-01-01",
                "endDate": "2019-12-31",
                "metrics": [
                    {
                        "expression": "ga:bounceRate"
                    },
                    {
                        "expression": "ga:sessionDuration"
                    }
                ],
                "dimensions": [
                    {
                        "name": "ga:landingPagePath"
                    },
                    {
                        "name": "ga:country"
                    },
                    {
                        "name": "ga:date"
                    }
                ]
            }


		Response:

		- Exact response come from Google Analytics. 

```