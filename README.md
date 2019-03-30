# Let me know when it's going to rain

My attempt to learn how to use [Prefect](https://www.prefect.io) to schedule workflows.

All this script does (for now) is hit the NOAA API and get the expected rainfall amount in the next 18 hours. If it's more than 0.2 in, I want to know about it so I don't geet soaked on the way to/from work, so I get sent an email. Otherwise, it does nothing. It's scheduled to run at 5 AM every morning.