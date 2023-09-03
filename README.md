# flatseeker
#### Video Demo: https://www.youtube.com/watch?v=PzQH2LUSZpc
#### Description:
A simple web app created for CS50x 2023 that helps you and your friend(s) find a flat by providing a space for collaboration including comments and link previews.

#### Motivation:
A common response to high rents is sharing a flat with a friend or your partner. To find a good flat, it is often necessary to compare different websites part of the process. But while these platforms often offer built-in functionality to share interesting flats with others, you often have to resort to sharing individual links across different platforms, which can be rather tedious.

Flatseeker aims to solve this problem by providing a single, extensible platform that's easy to use and requires no explanation. 
Users can easily create an account, connect with their friends through the built-in friend request system and then add flats using a form. All flats are then listed in an easy-to-understand table, with more detail provided when you click on an individual entry. It is then possible to comment on flats and delete those comments as well, and view a preview of the included link.
Of course quality of life improvements such as the ability to change your username and password and delete friends have been added as well.

#### Structure:
The bulk of the project is contained in app.py, including all routes and processing. Additional functionality is contained in login_helper.py, which contains functions for making sure the user is logged in, escaping characters in error messages and making sure the user's password meets the requirements. The first two functions are analogues to the provided functions in the last problem set of CS50x.
static contains the CSS and favicon, while all HTML templates are found under templates. 
requirements.txt contains all three dependencies of the project, and sql_commands.txt contains the necessary SQL commands needed to set up the database. 

#### Design choices
The application makes use of a total of four tables. Users contains all data related to users, while all all friend requests etc. are handled through a friends table. Comments and flats also each have their own table, which should make it possible to isolate these systems and run them using different scripts if desired.
In general, each view is independent and therefore rapid improvements are possible. 
One thing I considered was directly scraping all the necessary metadata directly from the link users provide. However, a lot of websites have a policy against this and ask developers to use their API. Considering the amount of websites and the platform-agnostic character of this web application, this is not a feasible feature for an open-source project to have. 
Email support is also in the works, however this does require additional set-up and an API key for an email service while providing little benefit since notifications are not strictly necessary for a service like this. 

#### Technologies used:
The web app was built using Flask/Python, HTML and CSS and SQLite with no JavaScript besides what is included in the Bootsstrap framework. 

#### Usage:
open sql_commands.txt and paste the first command to create the database. Then paste all the following lines to create the necessary tables. Finally, use "flask run" to start the application. Note that debug information is shown in the terminal. 
