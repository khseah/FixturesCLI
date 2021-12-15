# Fixtures CLI
A Command-Line Interface program that displays football fixtures of a specified football team in SGT. The program obtain the fixtures through scraping the skysports webpage. MongoDB
was used to store the list of favourite football teams, along with the user's username and hashed password.

## Commands
* **./fixturescli.py fixtures** to display the next 3 fixtures of a specified football team.
* **./fixturescli.py initfav** to intialise a list of favourite football teams. One can then run the **favfixtures** command to display the fixtures of all the shortlisted
teams, instead of running **fixtures** for each team.
* **./fixturescli.py addfav** to add additional football teams to the favourite list. If a favourite list has not been initialised, this command will not work.
* **./fixturescli.py deletefav** to delete football teams from the favourite list. If a favourite list has not been initialised, this command will not work.
* **./fixturescli.py listfav** to list the current football teaams in the favourite list. If a favourite list has not been initialised, this command will not work.
* **./fixturescli.py favfixtures** to display the fixtures for all of the football teams in the favourite list.

## Technologies
* Python 3.10.0
* Python Typer Module
* MongoDB
